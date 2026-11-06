"""Import a user-supplied Olist product sample without customer information."""
import csv
import os
from decimal import Decimal
from pathlib import Path

from app.common import db, wait_for_database


def collect_products(folder, limit=500):
    folder = Path(folder)
    products_file = folder / "olist_products_dataset.csv"
    items_file = folder / "olist_order_items_dataset.csv"
    if not products_file.is_file() or not items_file.is_file():
        raise FileNotFoundError("Expected olist_products_dataset.csv and olist_order_items_dataset.csv")
    prices = {}
    with items_file.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            pid = row.get("product_id", "")
            if pid and pid not in prices:
                prices[pid] = int(Decimal(row["price"]) * 100)
    products = []
    with products_file.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            pid = row.get("product_id", "")
            if pid in prices:
                products.append((pid, row.get("product_category_name") or "Uncategorized", prices[pid]))
                if len(products) >= limit:
                    break
    if not products:
        raise ValueError("No valid products with prices found")
    return products


def main():
    folder = os.getenv("OLIST_DATA_DIR", "/data/olist")
    products = collect_products(folder)
    wait_for_database()
    with db() as conn:
        conn.executemany("INSERT INTO products (id, name, price_cents) VALUES (%s,%s,%s) ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, price_cents=EXCLUDED.price_cents", products)
    print(f"Imported {len(products)} products; live traffic refreshes its catalog within one minute.")


if __name__ == "__main__":
    main()
