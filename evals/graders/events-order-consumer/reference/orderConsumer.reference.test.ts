import { describe, expect, it, vi } from "vitest";

import {
  OrderConsumer,
  type OrderDependencies,
  type OrderMessage,
} from "../../src/orderConsumer.js";

function message(overrides: Partial<OrderMessage> = {}): OrderMessage {
  return {
    id: "message-1",
    orderId: "order-1",
    sequence: 2,
    attempt: 1,
    correlationId: "correlation-1",
    payload: { status: "paid" },
    ...overrides,
  };
}

function dependencies(overrides: Partial<OrderDependencies> = {}): OrderDependencies {
  return {
    hasProcessed: vi.fn().mockResolvedValue(false),
    markProcessed: vi.fn().mockResolvedValue(undefined),
    lastSequence: vi.fn().mockResolvedValue(1),
    saveOrder: vi.fn().mockResolvedValue(undefined),
    publishRetry: vi.fn().mockResolvedValue(undefined),
    publishDlq: vi.fn().mockResolvedValue(undefined),
    ack: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  };
}

describe("OrderConsumer reference behavior", () => {
  it("acknowledges duplicates without repeating the side effect", async () => {
    const deps = dependencies({ hasProcessed: vi.fn().mockResolvedValue(true) });
    const outcome = await new OrderConsumer(deps).handle(message());

    expect(outcome).toBe("duplicate");
    expect(deps.saveOrder).not.toHaveBeenCalled();
    expect(deps.ack).toHaveBeenCalledWith("message-1");
  });

  it("increments retry and preserves correlation", async () => {
    const deps = dependencies({ saveOrder: vi.fn().mockRejectedValue(new Error("temporary")) });
    const outcome = await new OrderConsumer(deps, 3).handle(message({ attempt: 1 }));

    expect(outcome).toBe("retry");
    expect(deps.publishRetry).toHaveBeenCalledWith(
      expect.objectContaining({ attempt: 2, correlationId: "correlation-1" }),
    );
    expect(deps.ack).toHaveBeenCalledWith("message-1");
  });

  it("sends the message to DLQ at the configured limit", async () => {
    const deps = dependencies({ saveOrder: vi.fn().mockRejectedValue(new Error("permanent")) });
    const outcome = await new OrderConsumer(deps, 3).handle(message({ attempt: 3 }));

    expect(outcome).toBe("dlq");
    expect(deps.publishDlq).toHaveBeenCalledWith(
      expect.objectContaining({ attempt: 3, correlationId: "correlation-1" }),
    );
    expect(deps.publishRetry).not.toHaveBeenCalled();
  });

  it("does not overwrite a newer order state", async () => {
    const deps = dependencies({ lastSequence: vi.fn().mockResolvedValue(5) });
    const outcome = await new OrderConsumer(deps).handle(message({ sequence: 4 }));

    expect(outcome).toBe("stale");
    expect(deps.saveOrder).not.toHaveBeenCalled();
    expect(deps.markProcessed).toHaveBeenCalledWith("message-1");
  });
});
