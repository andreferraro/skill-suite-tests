export type OrderMessage = {
  id: string;
  orderId: string;
  sequence: number;
  attempt: number;
  correlationId: string;
  payload: Record<string, unknown>;
};

export type OrderDependencies = {
  hasProcessed(messageId: string): Promise<boolean>;
  markProcessed(messageId: string): Promise<void>;
  lastSequence(orderId: string): Promise<number | null>;
  saveOrder(message: OrderMessage): Promise<void>;
  publishRetry(message: OrderMessage): Promise<void>;
  publishDlq(message: OrderMessage): Promise<void>;
  ack(messageId: string): Promise<void>;
};

export type ConsumeOutcome = "processed" | "duplicate" | "stale" | "retry" | "dlq";

export class OrderConsumer {
  constructor(
    private readonly dependencies: OrderDependencies,
    private readonly maxAttempts = 3,
  ) {}

  async handle(message: OrderMessage): Promise<ConsumeOutcome> {
    if (await this.dependencies.hasProcessed(message.id)) {
      await this.dependencies.ack(message.id);
      return "duplicate";
    }

    const lastSequence = await this.dependencies.lastSequence(message.orderId);
    if (lastSequence !== null && message.sequence <= lastSequence) {
      await this.dependencies.markProcessed(message.id);
      await this.dependencies.ack(message.id);
      return "stale";
    }

    try {
      await this.dependencies.saveOrder(message);
      await this.dependencies.markProcessed(message.id);
      await this.dependencies.ack(message.id);
      return "processed";
    } catch {
      if (message.attempt >= this.maxAttempts) {
        await this.dependencies.publishDlq({
          ...message,
          correlationId: message.correlationId,
        });
        await this.dependencies.ack(message.id);
        return "dlq";
      }

      await this.dependencies.publishRetry({
        ...message,
        attempt: message.attempt + 1,
        correlationId: message.correlationId,
      });
      await this.dependencies.ack(message.id);
      return "retry";
    }
  }
}
