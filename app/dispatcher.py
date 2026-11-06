import json
import logging
import time

import pika
from confluent_kafka import Consumer

from app.common import KAFKA, RABBIT, TOPIC, context_from_headers, ensure_topic, payload, rabbit_headers
from app.telemetry import setup

tracer, meter = setup("order-dispatcher")
dispatched = meter.create_counter("lab_tasks_dispatched", unit="1")


def rabbit_connection():
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(RABBIT))
            channel = connection.channel()
            channel.queue_declare(queue="fulfillment", durable=True)
            channel.queue_declare(queue="fulfillment.dead", durable=True)
            channel.confirm_delivery()
            return connection, channel
        except pika.exceptions.AMQPConnectionError:
            time.sleep(3)


def main():
    ensure_topic()
    consumer = Consumer({"bootstrap.servers": KAFKA, "group.id": "fulfillment-dispatcher", "auto.offset.reset": "earliest", "enable.auto.commit": False})
    consumer.subscribe([TOPIC])
    connection, channel = rabbit_connection()
    while True:
        message = consumer.poll(1)
        if message is None:
            continue
        if message.error():
            logging.error("Kafka consume error: %s", message.error())
            continue
        data = json.loads(message.value())
        with tracer.start_as_current_span("dispatch fulfillment", context=context_from_headers(message.headers())):
            body = payload(data["order_id"], data["event_id"])
            headers = rabbit_headers()
            while True:
                try:
                    channel.basic_publish(exchange="", routing_key="fulfillment", body=body,
                                          properties=pika.BasicProperties(delivery_mode=2, message_id=data["event_id"], headers=headers), mandatory=True)
                    dispatched.add(1)
                    logging.info("task dispatched event_id=%s", data["event_id"])
                    break
                except Exception:
                    logging.exception("dispatch failed; retrying event_id=%s", data["event_id"])
                    try:
                        connection.close()
                    except Exception:
                        pass
                    connection, channel = rabbit_connection()
                    time.sleep(2)
            try:
                consumer.commit(message=message, asynchronous=False)
            except Exception:
                logging.exception("Kafka offset commit failed; task may replay event_id=%s", data["event_id"])


if __name__ == "__main__":
    main()
