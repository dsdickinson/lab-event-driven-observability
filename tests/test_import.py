import csv
import tempfile
import unittest
from pathlib import Path

from app.import_olist import collect_products


class OlistImportTests(unittest.TestCase):
    def test_missing_files_are_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError):
                collect_products(folder)

    def test_product_uses_first_observed_price_and_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with (root / "olist_products_dataset.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["product_id", "product_category_name"])
                writer.writeheader()
                writer.writerows([{"product_id": "p1", "product_category_name": "books"},
                                  {"product_id": "p2", "product_category_name": "tools"}])
            with (root / "olist_order_items_dataset.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["product_id", "price"])
                writer.writeheader()
                writer.writerows([{"product_id": "p1", "price": "12.34"},
                                  {"product_id": "p1", "price": "15.00"},
                                  {"product_id": "p2", "price": "9.50"}])
            self.assertEqual(collect_products(root, limit=1), [("p1", "books", 1234)])


if __name__ == "__main__":
    unittest.main()
