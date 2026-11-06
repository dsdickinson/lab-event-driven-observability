import logging
import os
import random
import time

import requests

from app.telemetry import setup

setup("traffic-generator")
PRODUCTS = ["coffee", "mug", "notebook", "lamp"]


def main():
    base = os.getenv("ORDER_API_URL", "http://api:8000")
    interval = float(os.getenv("TRAFFIC_INTERVAL_SECONDS", "3"))
    products = PRODUCTS
    last_refresh = 0
    while True:
        try:
            if time.monotonic() - last_refresh > 60:
                listed = requests.get(f"{base}/products", timeout=10).json()
                products = [item["id"] for item in listed] or PRODUCTS
                last_refresh = time.monotonic()
            response = requests.post(f"{base}/orders", json={"product_id": random.choice(products), "quantity": random.randint(1, 3)}, timeout=10)
            response.raise_for_status()
            logging.info("generated order_id=%s", response.json()["order_id"])
        except requests.RequestException:
            logging.exception("traffic request failed")
        time.sleep(interval)


if __name__ == "__main__":
    main()
