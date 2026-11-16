import json
import logging

from confluent_kafka import Consumer

from app.common import KAFKA, TOPIC, context_from_headers, db, ensure_topic, wait_for_database
from app.telemetry import setup

tracer, meter = setup("analytics-consumer")
count = meter.create_counter("demo_analytics_orders", unit="1")


def main():
    wait_for_database()
    ensure_topic()
    consumer = Consumer({"bootstrap.servers": KAFKA, "group.id": "order-analytics", "auto.offset.reset": "earliest", "enable.auto.commit": False})
    consumer.subscribe([TOPIC])
    while True:
        message = consumer.poll(1)
        if message is None:
            continue
        if message.error():
            logging.error("Kafka consume error: %s", message.error())
            continue
        data = json.loads(message.value())
        with tracer.start_as_current_span("aggregate order", context=context_from_headers(message.headers())):
            with db() as conn:
                inserted = conn.execute("INSERT INTO analytics_events (event_id, order_id) VALUES (%s,%s) ON CONFLICT DO NOTHING RETURNING event_id",
                                        (data["event_id"], data["order_id"])).fetchone()
            consumer.commit(message=message, asynchronous=False)
            if inserted:
                count.add(1)
            logging.info("analytics consumed event_id=%s", data["event_id"])


if __name__ == "__main__":
    main()
