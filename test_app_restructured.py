import os
import unittest
from unittest.mock import patch, MagicMock
import json

# Set dummy environment variables before importing Config and App
os.environ['SUPABASE_URL'] = 'https://abc.supabase.co'
os.environ['SUPABASE_KEY'] = 'dummy-key-99999'
os.environ['SECRET_KEY'] = 'test-session-key'

from config import Config
from app import app

class RestructuredAppTestCase(unittest.TestCase):
    def setUp(self):
        # Create Flask test client
        self.app = app.test_client()
        self.app.testing = True

    def test_directory_setup(self):
        """Test that the application automatically creates the required folder structure."""
        dirs = [
            'static/css',
            'static/js',
            'static/images',
            'templates',
            'database'
        ]
        for d in dirs:
            self.assertTrue(os.path.exists(d), f"Folder {d} was not automatically created.")

    def test_page_routes_serve_html(self):
        """Test page routes serve index, login, and dashboard templates."""
        # Public form page
        with self.app.get('/') as res:
            self.assertEqual(res.status_code, 200)
            
        # Admin login page - when session is empty, it serves 200
        with self.app.get('/admin-login') as res:
            self.assertEqual(res.status_code, 200)

        # Admin dashboard page - when session is empty, it should redirect to login (302)
        with self.app.get('/admin-dashboard') as res:
            self.assertEqual(res.status_code, 302)
            self.assertIn('/admin-login', res.headers.get('Location', ''))

    def test_admin_api_login_success(self):
        """Test admin login API with correct credentials sets session values."""
        credentials = {
            "username": "admin",
            "password": "Admin@123"
        }
        with self.app as client:
            response = client.post('/api/admin/login', 
                                   data=json.dumps(credentials),
                                   content_type='application/json')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            
            # Verify session has credentials
            with client.session_transaction() as sess:
                self.assertEqual(sess.get('logged_in'), True)
                self.assertEqual(sess.get('role'), 'super_admin')

    def test_admin_api_login_failure(self):
        """Test admin login API with incorrect credentials."""
        # Wrong password
        credentials = {"username": "admin", "password": "WrongPassword"}
        response = self.app.post('/api/admin/login', 
                                 data=json.dumps(credentials),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 401)
        
        # Verify session is empty
        with self.app as client:
            client.get('/')
            with client.session_transaction() as sess:
                self.assertNotEqual(sess.get('logged_in'), True)

    @patch('app.get_supabase')
    def test_api_get_stores(self, mock_get_supabase):
        """Test fetching stores list from API."""
        mock_db = MagicMock()
        mock_get_supabase.return_value = mock_db
        mock_stores = [
            {"id": 1, "store_name": "Metro Outlet"},
            {"id": 2, "store_name": "Uptown Shop"}
        ]
        mock_db.table.return_value.select.return_value.order.return_value.execute.return_value.data = mock_stores

        response = self.app.get('/api/stores')
        self.assertEqual(response.status_code, 200)
        
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        self.assertEqual(result['data'], mock_stores)

    def test_submit_validation_failures(self):
        """Test public API submit input validation checks."""
        # 1. Missing Customer Name
        payload = {
            "store_id": 1,
            "mobile_number": "9876543210",
            "app_registration_status": "Completed",
            "invitation_issue": "No",
            "issue_description": ""
        }
        res = self.app.post('/api/submit', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertIn("Customer name is required", json.loads(res.data)['message'])

        # 2. Invalid Mobile Number length (less than 10)
        payload["customer_name"] = "Alice Smith"
        payload["mobile_number"] = "9876"
        res = self.app.post('/api/submit', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertIn("Mobile number must be exactly 10 digits", json.loads(res.data)['message'])

        # 3. Invalid Mobile Number characters
        payload["mobile_number"] = "987654321a"
        res = self.app.post('/api/submit', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 400)

        # 4. Conditional Description missing when issue is 'Yes'
        payload["mobile_number"] = "9876543210"
        payload["invitation_issue"] = "Yes"
        payload["issue_description"] = "  " # Empty whitespaces
        res = self.app.post('/api/submit', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertIn("Issue description is required", json.loads(res.data)['message'])

    @patch('app.get_supabase')
    def test_submit_api_success(self, mock_get_supabase):
        """Test submit API successfully inserts valid data into customer_entries."""
        mock_db = MagicMock()
        mock_get_supabase.return_value = mock_db
        mock_db.table.return_value.insert.return_value.execute.return_value.data = [{"id": 15}]

        payload = {
            "store_id": 3,
            "customer_name": "Bob Vance",
            "mobile_number": "1112223333",
            "app_registration_status": "Pending",
            "invitation_issue": "Yes",
            "issue_description": "Card printed offset"
        }
        res = self.app.post('/api/submit', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data)
        self.assertTrue(result['success'])
        
        # Verify db insert call mapping
        mock_db.table.assert_called_with('customer_entries')
        mock_db.table().insert.assert_called_with({
            "store_id": 3,
            "customer_name": "Bob Vance",
            "mobile_number": "1112223333",
            "app_registration_status": "Pending",
            "invitation_issue": True,
            "issue_description": "Card printed offset"
        })

    def test_admin_api_protection(self):
        """Test that admin endpoints restrict unauthorized session access."""
        # 1. Stats endpoint
        res = self.app.get('/api/admin/dashboard')
        self.assertEqual(res.status_code, 401)

        # 2. Customers logs list
        res2 = self.app.get('/api/admin/customers')
        self.assertEqual(res2.status_code, 401)

        # 3. Export CSV endpoint
        res3 = self.app.get('/api/admin/export')
        self.assertEqual(res3.status_code, 401)

    @patch('app.get_supabase')
    def test_admin_apis_authenticated(self, mock_get_supabase):
        """Test that admin endpoints fetch data successfully when session is active."""
        # Setup session using client context manager
        with self.app as client:
            # Fake logging in
            with client.session_transaction() as sess:
                sess['logged_in'] = True
                sess['role'] = 'super_admin'
                
            mock_db = MagicMock()
            mock_get_supabase.return_value = mock_db
            
            # Setup database mock values
            mock_entries = [
                {
                    "id": 1,
                    "customer_name": "Dwight Schrute",
                    "mobile_number": "9998887777",
                    "app_registration_status": "Completed",
                    "invitation_issue": True,
                    "issue_description": "Damaged barcode",
                    "created_at": "2026-06-07T12:00:00Z",
                    "stores": {"id": 2, "store_name": "Dunder Mifflin Outlet"}
                }
            ]
            
            # 1. Test Dashboard Statistics API
            mock_db.table.return_value.select.return_value.execute.return_value.data = [
                {"id": 1, "app_registration_status": "Completed", "invitation_issue": True},
                {"id": 2, "app_registration_status": "Pending", "invitation_issue": False}
            ]
            
            res_stats = client.get('/api/admin/dashboard')
            self.assertEqual(res_stats.status_code, 200)
            stats_result = json.loads(res_stats.data)
            self.assertTrue(stats_result['success'])
            self.assertEqual(stats_result['stats']['total'], 2)
            self.assertEqual(stats_result['stats']['completed'], 1)
            self.assertEqual(stats_result['stats']['issues'], 1)

            # 2. Test Customers List API
            mock_db.table.return_value.select.return_value.order.return_value.execute.return_value.data = mock_entries
            
            res_cust = client.get('/api/admin/customers')
            self.assertEqual(res_cust.status_code, 200)
            cust_result = json.loads(res_cust.data)
            self.assertTrue(cust_result['success'])
            self.assertEqual(len(cust_result['data']), 1)
            self.assertEqual(cust_result['data'][0]['store_name'], "Dunder Mifflin Outlet")
            self.assertEqual(cust_result['data'][0]['invitation_issue'], "Yes")

            # 3. Test Export CSV API
            res_export = client.get('/api/admin/export')
            self.assertEqual(res_export.status_code, 200)
            self.assertEqual(res_export.mimetype, 'text/csv')
            self.assertIn("attachment; filename=", res_export.headers.get('Content-Disposition', ''))
            csv_content = res_export.data.decode('utf-8')
            self.assertIn("Submission ID,Store Name,Customer Name,Mobile Number,App Registration Status,Invitation Card Issue,Issue Description,Created At", csv_content)
            self.assertIn("Dwight Schrute", csv_content)

if __name__ == '__main__':
    unittest.main()
