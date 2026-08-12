import amqp from "amqplib";
import { Client } from "pg";
import { GenericContainer, StartedTestContainer, Wait } from "testcontainers";

export type StartedInfrastructure = {
  rabbitmq: StartedTestContainer;
  postgres: StartedTestContainer;
  rabbitmqUrl: string;
  postgresUrl: string;
  stop(): Promise<void>;
};

export async function startInfrastructure(): Promise<StartedInfrastructure> {
  const rabbitmq = await new GenericContainer(
    "rabbitmq@sha256:d7af1c87c5f1eda13fcfca06db452bf3aeab6619fc3358b68535c0c02c4e52bc",
  )
    .withExposedPorts(5672)
    .withWaitStrategy(Wait.forLogMessage("Server startup complete"))
    .start();
  let postgres: StartedTestContainer | undefined;
  try {
    const startedPostgres = await new GenericContainer(
      "postgres@sha256:e013e867e712fec275706a6c51c966f0bb0c93cfa8f51000f85a15f9865a28cb",
    )
      .withEnvironment({
        POSTGRES_DB: "orders",
        POSTGRES_PASSWORD: "orders",
        POSTGRES_USER: "orders",
      })
      .withExposedPorts(5432)
      .withWaitStrategy(Wait.forLogMessage("database system is ready to accept connections", 2))
      .start();
    postgres = startedPostgres;

    const rabbitmqUrl = `amqp://${rabbitmq.getHost()}:${rabbitmq.getMappedPort(5672)}`;
    const postgresUrl = `postgres://orders:orders@${startedPostgres.getHost()}:${startedPostgres.getMappedPort(5432)}/orders`;

    const rabbitConnection = await amqp.connect(rabbitmqUrl);
    await rabbitConnection.close();
    const postgresClient = new Client({ connectionString: postgresUrl });
    await postgresClient.connect();
    await postgresClient.query("SELECT 1");
    await postgresClient.end();

    return {
      rabbitmq,
      postgres: startedPostgres,
      rabbitmqUrl,
      postgresUrl,
      async stop() {
        await Promise.all([rabbitmq.stop(), startedPostgres.stop()]);
      },
    };
  } catch (error) {
    await Promise.allSettled([rabbitmq.stop(), postgres?.stop()]);
    throw error;
  }
}
