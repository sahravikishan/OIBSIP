"""
Unit tests for SQLite database management, multi-user isolation, and error handling.
"""

import os
import tempfile
import unittest
from src.database import DatabaseManager, DatabaseError


class TestDatabaseManager(unittest.TestCase):

    def setUp(self):
        # Create a temporary file for isolated test database
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_bmi.db")
        self.db = DatabaseManager(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_database_initialization(self):
        # Verify database file is created
        self.assertTrue(os.path.exists(self.db_path))

    def test_get_or_create_user(self):
        user_id, created = self.db.get_or_create_user("Ravi")
        self.assertTrue(created)
        self.assertGreater(user_id, 0)

        # Calling again for same name should return existing user ID without re-creating
        user_id2, created2 = self.db.get_or_create_user("Ravi")
        self.assertFalse(created2)
        self.assertEqual(user_id, user_id2)

        # Case-insensitive match check
        user_id3, created3 = self.db.get_or_create_user("ravi")
        self.assertFalse(created3)
        self.assertEqual(user_id, user_id3)

    def test_empty_user_name_error(self):
        with self.assertRaises(DatabaseError):
            self.db.get_or_create_user("")
        with self.assertRaises(DatabaseError):
            self.db.get_or_create_user("   ")

    def test_get_all_users(self):
        self.db.get_or_create_user("Ravi")
        self.db.get_or_create_user("Amit")
        self.db.get_or_create_user("Zoya")

        users = self.db.get_all_users()
        self.assertEqual(len(users), 3)
        # Should be sorted alphabetically
        names = [u["name"] for u in users]
        self.assertEqual(names, ["Amit", "Ravi", "Zoya"])

    def test_multi_user_isolation(self):
        user_ravi, _ = self.db.get_or_create_user("Ravi")
        user_amit, _ = self.db.get_or_create_user("Amit")

        # Insert records for Ravi
        self.db.insert_record(user_ravi, 70.0, 1.75, 22.86, "Normal", "2026-09-10 10:00:00")
        self.db.insert_record(user_ravi, 71.0, 1.75, 23.18, "Normal", "2026-09-12 10:00:00")

        # Insert records for Amit
        self.db.insert_record(user_amit, 85.0, 1.80, 26.23, "Overweight", "2026-09-11 11:00:00")

        # Check Ravi's records
        ravi_records = self.db.get_user_records(user_ravi, order_desc=False)
        self.assertEqual(len(ravi_records), 2)
        self.assertEqual(ravi_records[0]["bmi"], 22.86)
        self.assertEqual(ravi_records[1]["bmi"], 23.18)

        # Check Amit's records
        amit_records = self.db.get_user_records(user_amit)
        self.assertEqual(len(amit_records), 1)
        self.assertEqual(amit_records[0]["bmi"], 26.23)
        self.assertEqual(amit_records[0]["category"], "Overweight")

    def test_record_ordering(self):
        user_id, _ = self.db.get_or_create_user("TestUser")
        self.db.insert_record(user_id, 65.0, 1.70, 22.49, "Normal", "2026-09-01 10:00:00")
        self.db.insert_record(user_id, 67.0, 1.70, 23.18, "Normal", "2026-09-10 10:00:00")
        self.db.insert_record(user_id, 68.0, 1.70, 23.53, "Normal", "2026-09-20 10:00:00")

        # ASC: oldest first
        asc_records = self.db.get_user_records(user_id, order_desc=False)
        self.assertEqual(asc_records[0]["recorded_at"], "2026-09-01 10:00:00")
        self.assertEqual(asc_records[-1]["recorded_at"], "2026-09-20 10:00:00")

        # DESC: newest first
        desc_records = self.db.get_user_records(user_id, order_desc=True)
        self.assertEqual(desc_records[0]["recorded_at"], "2026-09-20 10:00:00")
        self.assertEqual(desc_records[-1]["recorded_at"], "2026-09-01 10:00:00")

    def test_delete_record(self):
        user_id, _ = self.db.get_or_create_user("DeleteUser")
        rec_id = self.db.insert_record(user_id, 70.0, 1.75, 22.86, "Normal")
        self.assertEqual(len(self.db.get_user_records(user_id)), 1)

        success = self.db.delete_record(rec_id)
        self.assertTrue(success)
        self.assertEqual(len(self.db.get_user_records(user_id)), 0)

    def test_delete_user_cascade(self):
        user_id, _ = self.db.get_or_create_user("CascadeUser")
        self.db.insert_record(user_id, 70.0, 1.75, 22.86, "Normal")
        self.db.insert_record(user_id, 72.0, 1.75, 23.51, "Normal")

        # Delete user
        self.db.delete_user(user_id)
        # Records for that user should also be gone due to CASCADE
        self.assertEqual(len(self.db.get_user_records(user_id)), 0)


if __name__ == "__main__":
    unittest.main()
