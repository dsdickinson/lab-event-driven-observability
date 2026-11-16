import json
import os
import time
import uuid

import psycopg
from confluent_kafka.admin import AdminClient, NewTopic
from opentelemetry import propagate, trace

DB_DSN = os.getenv("DATABASE_URL", "postgresql://demo:demo@postgres:5432/demo")
KAFKA = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
RABBIT = os.getenv("RABBITMQ_URL", "amqp://demo:demo@rabbitmq:5672/%2F")
TOPIC = "orders.placed"


def db():
    return psycopg.connect(DB_DSN)


def wait_for_database():
    while True:
        try:
            with db() as conn:
                conn.execute("SELECT 1")
            return
        except psycopg.OperationalError:
            time.sleep(2)


def ensure_topic():
    admin = AdminClient({"bootstrap.servers": KAFKA})
    while True:
        try:
            metadata = admin.list_topics(timeout=5)
            if TOPIC not in metadata.topics:
                futures = admin.create_topics([NewTopic(TOPIC, num_partitions=1, replication_factor=1)])
                futures[TOPIC].result(timeout=10)
            return
        except Exception:
            time.sleep(3)


def payload(order_id, event_id):
    return json.dumps({"order_id": str(order_id), "event_id": str(event_id)}).encode()


def carrier_headers():
    carrier = {}
    propagate.inject(carrier)
    return [(key, value.encode()) for key, value in carrier.items()]


def context_from_headers(headers):
    carrier = {key: value.decode() if isinstance(value, bytes) else value for key, value in (headers or [])}
    return propagate.extract(carrier)


def rabbit_headers():
    carrier = {}
    propagate.inject(carrier)
    return carrier


def context_from_rabbit(headers):
    return propagate.extract(headers or {})


def new_id():
    return uuid.uuid4()
