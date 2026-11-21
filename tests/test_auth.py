"""
test_auth.py — Unit tests for Phase 1 Authentication and Account Lifecycle.
"""
import unittest
import sys
import os
import uuid

sys.path.insert(0, os.path.abspath("apps/api"))

from app.core.db import init_db, get_db
from app.routers.auth import register_patient, register_clinician, login, get_current_user, accept_privacy, export_my_data, delete_my_data
from app.errors import ValidationException, UnauthenticatedException, ForbiddenException

class TestAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_register_patient_success(self):
        email = f"patient_{uuid.uuid4().hex[:8]}@demo.test"
        res = register_patient({
            "email": email,
            "password": "StrongPassword123!",
            "display_name": "Test Patient"
        })
        self.assertIn("access_token", res)
        self.assertEqual(res["user"]["email"], email)
        self.assertEqual(res["user"]["role"], "patient")

    def test_02_register_duplicate_email(self):
        email = f"dup_{uuid.uuid4().hex[:8]}@demo.test"
        register_patient({"email": email, "password": "Password123!", "display_name": "User 1"})
        with self.assertRaises(ValidationException):
            register_patient({"email": email, "password": "Password123!", "display_name": "User 2"})

    def test_03_login_success_and_wrong_password(self):
        email = f"login_{uuid.uuid4().hex[:8]}@demo.test"
        register_patient({"email": email, "password": "CorrectPassword123!", "display_name": "Login User"})

        # Successful login
        res = login({"email": email, "password": "CorrectPassword123!"})
        self.assertIn("access_token", res)

        # Invalid password
        with self.assertRaises(UnauthenticatedException):
            login({"email": email, "password": "WrongPassword!"})

    def test_04_privacy_accept_and_me(self):
        email = f"privacy_{uuid.uuid4().hex[:8]}@demo.test"
        res = register_patient({"email": email, "password": "Password123!", "display_name": "Privacy User"})
        token = res["access_token"]
        user_id = res["user"]["id"]

        # Accept privacy
        p_res = accept_privacy(user_id, version="v1.0")
        self.assertEqual(p_res["status"], "ok")

        # Verify through get_current_user
        me = get_current_user(token)
        self.assertIsNotNone(me["privacy_accepted_at"])

    def test_05_export_and_delete_account(self):
        email = f"delete_{uuid.uuid4().hex[:8]}@demo.test"
        res = register_patient({"email": email, "password": "Password123!", "display_name": "Delete Me"})
        user_id = res["user"]["id"]

        # Export
        data = export_my_data(user_id)
        self.assertEqual(data["user"]["id"], user_id)

        # Delete
        del_res = delete_my_data(user_id)
        self.assertEqual(del_res["status"], "account_anonymized_and_deleted")

if __name__ == "__main__":
    unittest.main()
