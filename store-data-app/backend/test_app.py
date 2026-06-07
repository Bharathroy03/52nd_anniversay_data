import os
import unittest
from unittest.mock import patch, MagicMock
import json
import jwt

# Set dummy environment variables before importing Config and App
os.environ['SUPABASE_URL'] = 'https://xyz.supabase.co'
os.environ['SUPABASE_KEY'] = 'dummy-anon-key-12345'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-12345'

from config import Config
from app import app

class StoreAppTestCase(unittest.TestCase):
    def setUp(self):
        # Create Flask test client
        self.app = app.test_client()
        self.app.testing = True

    def test_static_pages_load(self):
        """Test if static HTML page paths are accessible and return 200."""
        # Note: If frontend folder is empty during testing, Flask send_static_file will raise 404.
        # But we already created frontend/index.html, admin-login.html and admin-dashboard.html, so they will succeed.
        with self.app.get('/') as res_index:
            self.assertEqual(res_index.status_code, 200)

        with self.app.get('/admin-login') as res_login:
            self.assertEqual(res_login.status_code, 200)

        with self.app.get('/admin-dashboard') as res_dashboard:
            self.assertEqual(res_dashboard.status_code, 200)

    def test_admin_login_success(self):
        """Test admin login with correct hardcoded credentials."""
        credentials = {
            "username": "admin",
            "password": "Admin@123"
        }
        response = self.app.post('/admin-login', 
                                 data=json.dumps(credentials),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('token', data)

    def test_admin_login_failure(self):
        """Test admin login with incorrect credentials."""
        # 1. Invalid username
        credentials = {"username": "wrong_admin", "password": "Admin@123"}
        response = self.app.post('/admin-login', 
                                 data=json.dumps(credentials),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        
        # 2. Invalid password
        credentials = {"username": "admin", "password": "wrong_password"}
        response = self.app.post('/admin-login', 
                                 data=json.dumps(credentials),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 401)

    @patch('app.get_supabase')
    def test_get_stores(self, mock_get_supabase):
        """Test fetching stores from database."""
        # Mocking Supabase tables query chain
        mock_db = MagicMock()
        mock_get_supabase.return_value = mock_db
        
        mock_data = [
            {"id": 1, "store_name": "Store A"},
            {"id": 2, "store_name": "Store B"}
        ]
        
        # Chain mocking: supabase.table().select().order().execute()
        mock_db.table.return_value.select.return_value.order.return_value.execute.return_value.data = mock_data

        response = self.app.get('/stores')
        self.assertEqual(response.status_code, 200)
        
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        self.assertEqual(result['data'], mock_data)

    def test_submit_validation_missing_fields(self):
        """Test submit validation fails when required fields are missing."""
        # Missing customer name
        payload = {
            "store_id": 1,
            "mobile_number": "1234567890",
            "app_registration_status": "Completed",
            "invitation_card_issue": "No",
            "issue_description": ""
        }
        res = self.app.post('/submit', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertIn("Customer name is required", json.loads(res.data)['message'])

    def test_submit_validation_invalid_mobile(self):
        """Test submit validation fails when mobile number is invalid."""
        # Mobile number less than 10 digits
        payload = {
            "store_id": 1,
            "customer_name": "John Doe",
            "mobile_number": "12345",
            "app_registration_status": "Completed",
            "invitation_card_issue": "No",
            "issue_description": ""
        }
        res = self.app.post('/submit', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertIn("Mobile number must be exactly 10 digits", json.loads(res.data)['message'])

        # Mobile number containing characters
        payload["mobile_number"] = "123456789a"
        res = self.app.post('/submit', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_submit_validation_conditional_description(self):
        """Test submit validation fails when card issue is 'Yes' but description is empty."""
        payload = {
            "store_id": 1,
            "customer_name": "John Doe",
            "mobile_number": "1234567890",
            "app_registration_status": "Completed",
            "invitation_card_issue": "Yes",
            "issue_description": "   " # Empty whitespaces
        }
        res = self.app.post('/submit', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertIn("Issue description is required", json.loads(res.data)['message'])

    @patch('app.get_supabase')
    def test_submit_success(self, mock_get_supabase):
        """Test submit is saved successfully under correct conditions."""
        mock_db = MagicMock()
        mock_get_supabase.return_value = mock_db
        mock_db.table.return_value.insert.return_value.execute.return_value.data = [{"id": 99}]

        payload = {
            "store_id": 2,
            "customer_name": "Jane Doe",
            "mobile_number": "9876543210",
            "app_registration_status": "Pending",
            "invitation_card_issue": "No",
            "issue_description": ""
        }
        res = self.app.post('/submit', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data)
        self.assertTrue(result['success'])
        
        # Verify db mock inserts correct type (boolean false for invitation_card_issue)
        mock_db.table.assert_called_with('customer_submissions')
        mock_db.table().insert.assert_called_with({
            "store_id": 2,
            "customer_name": "Jane Doe",
            "mobile_number": "9876543210",
            "app_registration_status": "Pending",
            "invitation_card_issue": False,
            "issue_description": None
        })

    def test_admin_auth_required(self):
        """Test that admin endpoints block unauthorized requests."""
        # Call without Authorization header
        res = self.app.get('/admin/submissions')
        self.assertEqual(res.status_code, 401)
        
        # Call with invalid token
        res2 = self.app.get('/admin/submissions', headers={"Authorization": "Bearer invalidtoken123"})
        self.assertEqual(res2.status_code, 401)

    @patch('app.get_supabase')
    def test_get_submissions_authenticated(self, mock_get_supabase):
        """Test that admin submissions load successfully with a valid token."""
        # 1. Generate valid token
        import datetime
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        payload = {
            'user': 'admin',
            'exp': now_utc + datetime.timedelta(seconds=60)
        }
        token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')

        # 2. Mock Supabase data
        mock_db = MagicMock()
        mock_get_supabase.return_value = mock_db
        mock_sub_data = [
            {
                "id": 10,
                "customer_name": "Alice Smith",
                "mobile_number": "1112223333",
                "app_registration_status": "Completed",
                "invitation_card_issue": True,
                "issue_description": "Damaged barcode",
                "created_at": "2026-06-07T10:00:00Z",
                "stores": {"id": 1, "store_name": "Main Outlet"}
            }
        ]
        
        # Dynamic filter builders mapping mock
        mock_db.table.return_value.select.return_value.order.return_value.execute.return_value.data = mock_sub_data

        # 3. Call endpoint
        res = self.app.get('/admin/submissions', headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        
        result = json.loads(res.data)
        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']), 1)
        self.assertEqual(result['data'][0]['store_name'], "Main Outlet")
        self.assertEqual(result['data'][0]['invitation_card_issue'], "Yes")

if __name__ == '__main__':
    unittest.main()
