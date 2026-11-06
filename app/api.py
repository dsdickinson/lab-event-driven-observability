import logging
import os
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from opentelemetry import trace

from app.common import db, new_id, wait_for_database, rabbit_headers
from app.telemetry import setup

tracer, meter = setup("order-api")
requests_counter = meter.create_counter("lab_http_requests", unit="1")
orders_counter = meter.create_counter("lab_orders_created", unit="1")
request_duration = meter.create_histogram("lab_http_duration", unit="s")
app = FastAPI(title="Local Observability Lab")


class OrderInput(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, le=20)


@app.on_event("startup")
def startup():
    wait_for_database()


@app.get("/health")
def health():
    with db() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/products")
def products():
    with db() as conn:
        rows = conn.execute("SELECT id, name, price_cents FROM products ORDER BY id").fetchall()
    return [{"id": row[0], "name": row[1], "price_cents": row[2]} for row in rows]


@app.post("/orders", status_code=201)
def create_order(order: OrderInput):
    started = time.monotonic()
    status = "created"
    with tracer.start_as_current_span("POST /orders") as span:
        try:
            delay = int(os.getenv("SLOW_API_MS", "0"))
            if delay:
                time.sleep(delay / 1000)
            order_id, event_id = new_id(), new_id()
            with db() as conn:
                row = conn.execute("SELECT price_cents FROM products WHERE id = %s", (order.product_id,)).fetchone()
                if row is None:
                    status = "invalid_product"
                    raise HTTPException(404, "Unknown product")
                conn.execute("INSERT INTO orders (id, product_id, quantity, amount_cents) VALUES (%s,%s,%s,%s)",
                             (order_id, order.product_id, order.quantity, row[0] * order.quantity))
                from psycopg.types.json import Jsonb
                conn.execute("INSERT INTO outbox (event_id, order_id, trace_context) VALUES (%s,%s,%s)",
                             (event_id, order_id, Jsonb(rabbit_headers())))
            span.set_attribute("order.id", str(order_id))
            trace_id = f"{span.get_span_context().trace_id:032x}"
            logging.info("order accepted order_id=%s event_id=%s trace_id=%s", order_id, event_id, trace_id)
            orders_counter.add(1)
            return {"order_id": str(order_id), "status": "placed", "trace_id": trace_id}
        finally:
            requests_counter.add(1, {"route": "/orders", "result": status})
            request_duration.record(time.monotonic() - started, {"route": "/orders"})


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    with db() as conn:
        try:
            row = conn.execute("SELECT id, product_id, quantity, amount_cents, status, created_at, fulfilled_at FROM orders WHERE id=%s", (order_id,)).fetchone()
        except Exception:
            raise HTTPException(400, "Invalid order ID")
    if row is None:
        raise HTTPException(404, "Order not found")
    return {"id": str(row[0]), "product_id": row[1], "quantity": row[2], "amount_cents": row[3],
            "status": row[4], "created_at": row[5], "fulfilled_at": row[6]}
