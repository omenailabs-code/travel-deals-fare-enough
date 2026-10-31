import os
import tempfile
import unittest

from dealengine import db


class TestDb(unittest.TestCase):
    def test_schema_and_insert(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.db")
            conn = db.connect(path)
            db.init(conn)
            rid = conn.execute(
                "INSERT INTO routes (key, origin, dest, currency, first_seen) "
                "VALUES ('JFK-LHR','JFK','LHR','USD','2026-10-01T00:00:00Z')"
            ).lastrowid
            conn.execute(
                "INSERT INTO prices (route_id, source, price, currency, observed_at) "
                "VALUES (?,?,?,?,?)",
                (rid, "test", 500.0, "USD", "2026-10-01T09:00:00Z"),
            )
            conn.execute(
                "INSERT INTO deals (route_id, price, currency, label, confidence, "
                "source_url, verified_at, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (rid, 250.0, "USD", "flash", 3, "https://example.test/deal",
                 "2026-10-31T09:00:00Z", "2026-10-31T09:00:00Z"),
            )
            conn.commit()
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM routes").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0], 1)
            row = conn.execute("SELECT label, confidence FROM deals").fetchone()
            self.assertEqual((row["label"], row["confidence"]), ("flash", 3))
            # idempotent init (re-running schema must not fail)
            db.init(conn)
            conn.close()

    def test_foreign_keys_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = db.connect(os.path.join(tmp, "fk.db"))
            db.init(conn)
            with self.assertRaises(Exception):
                conn.execute(
                    "INSERT INTO prices (route_id, source, price, currency, observed_at) "
                    "VALUES (999, 'test', 1.0, 'USD', '2026-10-01T09:00:00Z')"
                )
            conn.close()


if __name__ == "__main__":
    unittest.main()
