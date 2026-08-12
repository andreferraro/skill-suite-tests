import type { Channel } from "amqplib";
import type { Client } from "pg";

import type { OrderDependencies, OrderMessage } from "./orderConsumer.js";


export class PostgresRabbitDependencies implements OrderDependencies {
  constructor(
    private readonly database: Client,
    private readonly channel: Channel,
    private readonly retryQueue = "orders.retry",
    private readonly dlqQueue = "orders.dlq",
  ) {}

  async initialize(): Promise<void> {
    await this.database.query(`
      CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        sequence INTEGER NOT NULL,
        payload JSONB NOT NULL
      );
      CREATE TABLE IF NOT EXISTS processed_messages (
        message_id TEXT PRIMARY KEY
      );
      CREATE TABLE IF NOT EXISTS acknowledged_messages (
        message_id TEXT PRIMARY KEY
      );
    `);
    await this.channel.assertQueue(this.retryQueue, { durable: false });
    await this.channel.assertQueue(this.dlqQueue, { durable: false });
  }

  async hasProcessed(messageId: string): Promise<boolean> {
    const result = await this.database.query(
      "SELECT 1 FROM processed_messages WHERE message_id = $1",
      [messageId],
    );
    return result.rowCount === 1;
  }

  async markProcessed(messageId: string): Promise<void> {
    await this.database.query(
      "INSERT INTO processed_messages (message_id) VALUES ($1) ON CONFLICT DO NOTHING",
      [messageId],
    );
  }

  async lastSequence(orderId: string): Promise<number | null> {
    const result = await this.database.query<{ sequence: number }>(
      "SELECT sequence FROM orders WHERE order_id = $1",
      [orderId],
    );
    return result.rows[0]?.sequence ?? null;
  }

  async saveOrder(message: OrderMessage): Promise<void> {
    await this.database.query(
      `INSERT INTO orders (order_id, sequence, payload)
       VALUES ($1, $2, $3)
       ON CONFLICT (order_id) DO UPDATE
       SET sequence = EXCLUDED.sequence, payload = EXCLUDED.payload
       WHERE orders.sequence < EXCLUDED.sequence`,
      [message.orderId, message.sequence, message.payload],
    );
  }

  async publishRetry(message: OrderMessage): Promise<void> {
    this.channel.sendToQueue(this.retryQueue, Buffer.from(JSON.stringify(message)));
  }

  async publishDlq(message: OrderMessage): Promise<void> {
    this.channel.sendToQueue(this.dlqQueue, Buffer.from(JSON.stringify(message)));
  }

  async ack(messageId: string): Promise<void> {
    await this.database.query(
      "INSERT INTO acknowledged_messages (message_id) VALUES ($1) ON CONFLICT DO NOTHING",
      [messageId],
    );
  }
}
