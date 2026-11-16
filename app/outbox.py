import logging
import time

from confluent_kafka import Producer
from opentelemetry import trace

from app.common import KAFKA, TOPIC, carrier_headers, db, ensure_topic, payload, wait_for_database
from app.telemetry import setup

tracer, meter = setup("outbox-publisher")
published = meter.create_counter("demo_outbox_published", unit="1")


def main():
    wait_for_database()
    ensure_topic()
    while True:
        with db() as conn:
            rows = conn.execute("SELECT event_id, order_id, trace_context FROM outbox WHERE published_at IS NULL ORDER BY created_at LIMIT 20").fetchall()
        for event_id, order_id, parent in rows:
            from app.common import context_from_rabbit
            with tracer.start_as_current_span("publish order.placed", context=context_from_rabbit(parent)):
                delivered = []
                producer = None
                try:
                    producer = Producer({"bootstrap.servers": KAFKA, "enable.idempotence": True})
                    producer.produce(TOPIC, key=str(order_id), value=payload(order_id, event_id),
                                     headers=carrier_headers(), callback=lambda err, msg: delivered.append(err))
                    remaining = producer.flush(10)
                    if remaining != 0 or delivered != [None]:
                        raise RuntimeError(f"Kafka did not acknowledge event {event_id}: {delivered}")
                    with db() as conn:
                        conn.execute("UPDATE outbox SET published_at=now() WHERE event_id=%s", (event_id,))
                    published.add(1)
                    logging.info("event published event_id=%s order_id=%s", event_id, order_id)
                except Exception:
                    logging.exception("outbox publish failed event_id=%s", event_id)
                    if producer is not None:
                        producer.purge(in_queue=True, in_flight=True)
                        producer.flush(1)
                    time.sleep(3)
                finally:
                    producer = None
        time.sleep(1)


if __name__ == "__main__":
    main()
