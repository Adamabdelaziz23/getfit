import sqlite3
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FreshDatabaseSchemaTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute("PRAGMA foreign_keys = ON")
        schema = (PROJECT_ROOT / "sql.txt").read_text(encoding="utf-8")
        self.connection.executescript(schema)

    def tearDown(self):
        self.connection.close()

    def test_fresh_schema_includes_food_logging_tables(self):
        tables = {
            row[0]
            for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

        self.assertIn("foods", tables)
        self.assertIn("food_log", tables)

    def test_food_log_accepts_entries_linked_to_a_user_and_food(self):
        user_id = self.connection.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("test-user", "test-hash"),
        ).lastrowid
        food_id = self.connection.execute(
            """INSERT INTO foods (name, calories, protein, carbs, fats)
               VALUES (?, ?, ?, ?, ?)""",
            ("Oats", 389, 16.9, 66.3, 6.9),
        ).lastrowid

        self.connection.execute(
            """INSERT INTO food_log
               (user_id, food_id, food_name, grams, calories, protein, carbs, fats)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, food_id, "Oats", 50, 194.5, 8.45, 33.15, 3.45),
        )
        saved_entry = self.connection.execute(
            "SELECT food_name, grams FROM food_log"
        ).fetchone()

        self.assertEqual(saved_entry, ("Oats", 50.0))

    def test_food_log_rejects_non_positive_grams(self):
        user_id = self.connection.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("test-user", "test-hash"),
        ).lastrowid
        food_id = self.connection.execute(
            "INSERT INTO foods (name, calories, protein, carbs, fats) VALUES (?, 1, 1, 1, 1)",
            ("Oats",),
        ).lastrowid

        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """INSERT INTO food_log
                   (user_id, food_id, food_name, grams, calories, protein, carbs, fats)
                   VALUES (?, ?, ?, 0, 0, 0, 0, 0)""",
                (user_id, food_id, "Oats"),
            )


if __name__ == "__main__":
    unittest.main()
