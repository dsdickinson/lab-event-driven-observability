import json
import logging
import os
import time

import pika

from app.common import RABBIT, context_from_rabbit, db, wait_for_database
from app.telemetry import setup

tracer, meter = setup("fulfillment-worker")
fulfilled = meter.create_counter("demo_orders_fulfilled", unit="1")
failed = meter.create_counter("demo_fulfillment_failures", unit="1")
duration = meter.create_histogram("demo_fulfillment_duration", unit="s")


def apply_fulfillment(event_id, order_id):
    with db() as conn:
        first = conn.execute("INSERT INTO processed_events (event_id) VALUES (%s) ON CONFLICT DO NOTHING RETURNING event_id", (event_id,)).fetchone()
        if first is None:
            return False
        conn.execute("UPDATE orders SET status='fulfilled', fulfilled_at=now() WHERE id=%s AND status='placed'", (order_id,))
    return True


def main():
    wait_for_database()
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(RABBIT))
            channel = connection.channel()
            channel.queue_declare(queue="fulfillment", durable=True)
            channel.queue_declare(queue="fulfillment.dead", durable=True)
            channel.confirm_delivery()
            channel.basic_qos(prefetch_count=1)

            def handle(ch, method, props, body):
                data = json.loads(body)
                started = time.monotonic()
                with tracer.start_as_current_span("fulfill order", context=context_from_rabbit(props.headers)) as span:
                    span.set_attribute("order.id", data["order_id"])
                    try:
                        if os.getenv("FAIL_FULFILLMENT", "false").lower() == "true":
                            raise RuntimeError("configured fulfillment failure")
                        if apply_fulfillment(data["event_id"], data["order_id"]):
                            fulfilled.add(1)
                            duration.record(time.monotonic() - started)
                            logging.info("fulfillment complete order_id=%s", data["order_id"])
                        else:
                            logging.info("duplicate fulfillment ignored order_id=%s", data["order_id"])
                        ch.basic_ack(method.delivery_tag)
                    except Exception:
                        failed.add(1)
                        logging.exception("fulfillment failed order_id=%s", data["order_id"])
                        attempt = int((props.headers or {}).get("attempt", 0)) + 1
                        target = "fulfillment.dead" if attempt >= 3 else "fulfillment"
                        headers = dict(props.headers or {})
                        headers["attempt"] = attempt
                        try:
                            ch.basic_publish(exchange="", routing_key=target, body=body,
                                             properties=pika.BasicProperties(delivery_mode=2, message_id=data["event_id"], headers=headers), mandatory=True)
                            ch.basic_ack(method.delivery_tag)
                        except Exception:
                            ch.basic_nack(method.delivery_tag, requeue=True)

            channel.basic_consume(queue="fulfillment", on_message_callback=handle)
            channel.start_consuming()
        except Exception:
            logging.exception("worker connection failed")
            time.sleep(3)


if __name__ == "__main__":
    main()
