import amqp from "amqplib";
import { Client } from "pg";
import { expect, it } from "vitest";

import { startInfrastructure } from "../../src/integrationHarness.js";
import { OrderConsumer, type OrderDependencies, type OrderMessage } from "../../src/orderConsumer.js";
import { PostgresRabbitDependencies } from "../../src/postgresRabbitDependencies.js";


function message(overrides: Partial<OrderMessage> = {}): OrderMessage {
  return {
    id: "message-integration-1",
    orderId: "order-integration-1",
    sequence: 2,
    attempt: 1,
    correlationId: "correlation-integration-1",
    payload: { status: "paid" },
    ...overrides,
  };
}

it.skipIf(process.env.RUN_INFRA_TESTS !== "1")(
  "runs deduplication, ordering and retry across PostgreSQL and RabbitMQ",
  async () => {
    const infrastructure = await startInfrastructure();
    const rabbitConnection = await amqp.connect(infrastructure.rabbitmqUrl);
    const channel = await rabbitConnection.createChannel();
    const database = new Client({ connectionString: infrastructure.postgresUrl });
    await database.connect();

    try {
      const dependencies = new PostgresRabbitDependencies(database, channel);
      await dependencies.initialize();
      const consumer = new OrderConsumer(dependencies);

      expect(await consumer.handle(message())).toBe("processed");
      expect(await consumer.handle(message())).toBe("duplicate");
      expect(await consumer.handle(message({ id: "message-stale", sequence: 1 }))).toBe("stale");
      const stored = await database.query("SELECT sequence, payload FROM orders WHERE order_id = $1", [
        "order-integration-1",
      ]);
      expect(stored.rows).toEqual([{ sequence: 2, payload: { status: "paid" } }]);

      const failingDependencies: OrderDependencies = {
        hasProcessed: dependencies.hasProcessed.bind(dependencies),
        markProcessed: dependencies.markProcessed.bind(dependencies),
        lastSequence: dependencies.lastSequence.bind(dependencies),
        saveOrder: async () => {
          throw new Error("temporary database failure");
        },
        publishRetry: dependencies.publishRetry.bind(dependencies),
        publishDlq: dependencies.publishDlq.bind(dependencies),
        ack: dependencies.ack.bind(dependencies),
      };
      const retryMessage = message({ id: "message-retry", orderId: "order-retry" });
      expect(await new OrderConsumer(failingDependencies).handle(retryMessage)).toBe("retry");
      const retried = await channel.get("orders.retry", { noAck: true });
      expect(retried).not.toBe(false);
      if (retried !== false) {
        expect(JSON.parse(retried.content.toString())).toMatchObject({
          id: "message-retry",
          attempt: 2,
          correlationId: "correlation-integration-1",
        });
      }
    } finally {
      await database.end();
      await channel.close();
      await rabbitConnection.close();
      await infrastructure.stop();
    }
  },
  120_000,
);
