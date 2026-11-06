CREATE TABLE IF NOT EXISTS products (
  id text PRIMARY KEY,
  name text NOT NULL,
  price_cents integer NOT NULL CHECK (price_cents >= 0)
);
INSERT INTO products (id, name, price_cents) VALUES
  ('coffee', 'Coffee beans', 1800), ('mug', 'Ceramic mug', 1200),
  ('notebook', 'Notebook', 900), ('lamp', 'Desk lamp', 3200)
ON CONFLICT (id) DO NOTHING;
CREATE TABLE IF NOT EXISTS orders (
  id uuid PRIMARY KEY,
  product_id text NOT NULL REFERENCES products(id),
  quantity integer NOT NULL CHECK (quantity BETWEEN 1 AND 20),
  amount_cents integer NOT NULL,
  status text NOT NULL DEFAULT 'placed',
  created_at timestamptz NOT NULL DEFAULT now(),
  fulfilled_at timestamptz
);
CREATE TABLE IF NOT EXISTS outbox (
  event_id uuid PRIMARY KEY,
  order_id uuid NOT NULL REFERENCES orders(id),
  trace_context jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz
);
CREATE TABLE IF NOT EXISTS processed_events (
  event_id uuid PRIMARY KEY,
  processed_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS analytics_events (
  event_id uuid PRIMARY KEY,
  order_id uuid NOT NULL,
  processed_at timestamptz NOT NULL DEFAULT now()
);
CREATE USER grafana_read WITH PASSWORD 'grafana_read';
GRANT CONNECT ON DATABASE lab TO grafana_read;
GRANT USAGE ON SCHEMA public TO grafana_read;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_read;
