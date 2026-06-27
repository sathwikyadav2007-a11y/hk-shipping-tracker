import os
import unittest
import json
import sqlite3
import datetime

# Import flask app and override database file for testing
import app as flask_app
flask_app.DATABASE_FILE = 'hk_shipping_test.db'

class HKShippingTestCase(unittest.TestCase):

    def setUp(self):
        """Set up test database and client before each test."""
        # Remove test database if it exists
        if os.path.exists(flask_app.DATABASE_FILE):
            try:
                os.remove(flask_app.DATABASE_FILE)
            except PermissionError:
                pass
        
        # Initialize test database
        flask_app.init_db()
        
        # Set up Flask test client
        self.app = flask_app.app.test_client()
        self.app.testing = True

        # Intercept client request methods to append default X-User-Role headers
        self.orig_get = self.app.get
        self.orig_post = self.app.post
        self.orig_put = self.app.put
        self.orig_delete = self.app.delete

        def wrap_get(*args, **kwargs):
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            if 'X-User-Role' not in kwargs['headers']:
                kwargs['headers']['X-User-Role'] = 'Admin/Owner'
                kwargs['headers']['X-User-Username'] = 'admin_user'
            return self.orig_get(*args, **kwargs)

        def wrap_post(*args, **kwargs):
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            if 'X-User-Role' not in kwargs['headers']:
                kwargs['headers']['X-User-Role'] = 'Admin/Owner'
                kwargs['headers']['X-User-Username'] = 'admin_user'
            return self.orig_post(*args, **kwargs)

        def wrap_put(*args, **kwargs):
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            if 'X-User-Role' not in kwargs['headers']:
                kwargs['headers']['X-User-Role'] = 'Admin/Owner'
                kwargs['headers']['X-User-Username'] = 'admin_user'
            return self.orig_put(*args, **kwargs)

        def wrap_delete(*args, **kwargs):
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            if 'X-User-Role' not in kwargs['headers']:
                kwargs['headers']['X-User-Role'] = 'Admin/Owner'
                kwargs['headers']['X-User-Username'] = 'admin_user'
            return self.orig_delete(*args, **kwargs)

        self.app.get = wrap_get
        self.app.post = wrap_post
        self.app.put = wrap_put
        self.app.delete = wrap_delete

    def tearDown(self):
        """Clean up test database after each test."""
        # Close any lingering connections (SQLite connections close on context exit)
        if os.path.exists(flask_app.DATABASE_FILE):
            try:
                os.remove(flask_app.DATABASE_FILE)
            except PermissionError:
                pass

    def test_create_invoice_success(self):
        """Test POST /api/invoices with valid parameters."""
        payload = {
            'customer_name': 'Test Cargo Corp',
            'customer_email': 'test@cargocorp.com',
            'customer_phone': '+91 99999 00000',
            'pickup_location': 'Mumbai Port',
            'drop_location': 'Delhi Terminal',
            'goods_type': 'Pharmaceuticals',
            'weight': 5.5,
            'preferred_date': '2026-07-01',
            'vehicle_number': 'MH-02-AB-5555',
            'vehicle_type': 'Container Truck',
            'driver_name': 'Harish Patel',
            'freight_charges': 10000.0,
            'gst_rate': 18.0,
            'advance_payment': 2000.0,
            'payment_status': 'Partial'
        }
        
        response = self.app.post(
            '/api/invoices',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        
        self.assertTrue(data['success'])
        # GST = 10000 * 18% = 1800.0
        self.assertEqual(data['gst_amount'], 1800.0)
        # Balance = 10000 + 1800 - 2000 = 9800.0
        self.assertEqual(data['balance_payment'], 9800.0)
        self.assertIn('invoice_id', data)
        self.assertIn('timestamp', data)

    def test_create_invoice_missing_fields(self):
        """Test POST /api/invoices with missing required fields (validates and returns 400)."""
        payload = {
            # Missing customer_name and freight_charges
            'customer_email': 'test@cargocorp.com',
            'pickup_location': 'Mumbai Port',
            'drop_location': 'Delhi Terminal',
            'goods_type': 'Pharmaceuticals',
            'weight': 5.5,
            'preferred_date': '2026-07-01',
            'vehicle_number': 'MH-02-AB-5555',
            'vehicle_type': 'Container Truck',
            'driver_name': 'Harish Patel',
            'gst_rate': 18.0
        }
        
        response = self.app.post(
            '/api/invoices',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('error', data)
        self.assertIn('customer_name', data['error'])
        self.assertIn('freight_charges', data['error'])

    def test_get_invoices_no_filters(self):
        """Test GET /api/invoices returns seeded invoices."""
        response = self.app.get('/api/invoices')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        
        # Verify both seeded invoices are retrieved
        self.assertEqual(len(data), 2)
        # Verify structure
        first_invoice = data[0]
        self.assertIn('customer_name', first_invoice)
        self.assertIn('freight_charges', first_invoice)
        self.assertIn('balance_payment', first_invoice)

    def test_get_invoices_filters(self):
        """Test GET /api/invoices with status and date filters."""
        # Query with status = Paid (Reliance seeded invoice has status = Paid)
        response_paid = self.app.get('/api/invoices?status=Paid')
        self.assertEqual(response_paid.status_code, 200)
        data_paid = json.loads(response_paid.data.decode('utf-8'))
        self.assertEqual(len(data_paid), 1)
        self.assertEqual(data_paid[0]['customer_name'], 'Reliance Retail Ltd')

        # Query with status = Partial (Tata Motors seeded invoice has status = Partial)
        response_partial = self.app.get('/api/invoices?status=Partial')
        self.assertEqual(response_partial.status_code, 200)
        data_partial = json.loads(response_partial.data.decode('utf-8'))
        self.assertEqual(len(data_partial), 1)
        self.assertEqual(data_partial[0]['customer_name'], 'Tata Motors Logistics')

        # Query by date (Reliance is 2026-06-17)
        response_date = self.app.get('/api/invoices?date=2026-06-17')
        self.assertEqual(response_date.status_code, 200)
        data_date = json.loads(response_date.data.decode('utf-8'))
        self.assertEqual(len(data_date), 1)
        self.assertEqual(data_date[0]['customer_name'], 'Reliance Retail Ltd')

    def test_dashboard_stats(self):
        """Test GET /api/dashboard/stats returns correct aggregations and alerts."""
        response = self.app.get('/api/dashboard/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        
        # Seeded 1: Tata Motors (45000 + 5400 = 50400, advance=20000, balance=30400, Active trip status is Completed? No, seeded as Completed, count active trips = 1)
        # Seeded 2: Reliance (35000 + 1750 = 36750, advance=36750, balance=0.0, Active trip status is Active, count active trips = 1)
        # Total Revenue = 50400 + 36750 = 87150.0
        # Pending Balance = 30400.0 + 0.0 = 30400.0
        # Active transits = 1 (Reliance trip status is 'Active')
        
        self.assertEqual(data['total_revenue'], 87150.0)
        self.assertEqual(data['pending_balances'], 30400.0)
        self.assertEqual(data['active_trips'], 1)
        
        # Verify compliance alerts exist
        self.assertIn('upcoming_compliance_alerts', data)
        alerts = data['upcoming_compliance_alerts']
        self.assertTrue(len(alerts) > 0)
        
        # Check that expired assets show up (e.g. DL-01-CP-5566 or Amit Singh)
        expired_entities = [a['entity_name'] for a in alerts if a['days_remaining'] <= 0]
        self.assertIn('Truck DL-01-CP-5566', expired_entities)
        self.assertIn('Amit Singh', expired_entities)

    def test_get_invoice_detail_with_ai(self):
        """Test GET /api/invoices/<id> details API and AI feedback object."""
        response = self.app.get('/api/invoices/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['customer_name'], 'Tata Motors Logistics')
        self.assertIn('ai', data)
        self.assertIn('suggested_rate', data['ai'])
        self.assertIn('rate_comparison', data['ai'])
        self.assertIn('narrative', data['ai'])
        self.assertIn('delay_risk', data['ai'])
        self.assertIn('email_body', data['ai'])

    def test_create_invoice_with_due_date(self):
        """Test creating an invoice with custom due_date, source, and owner."""
        payload = {
            'customer_name': 'Tata Motors Logistics',
            'customer_email': 'logistics@tatamotors.com',
            'pickup_location': 'Tata Plant, Pune',
            'drop_location': 'JNPT Port, Mumbai',
            'goods_type': 'Auto Components',
            'weight': 10.0,
            'preferred_date': '2026-07-01',
            'vehicle_number': 'MH-43-AA-1234',
            'vehicle_type': 'Container Truck',
            'driver_name': 'Rajesh Kumar',
            'freight_charges': 25000.0,
            'gst_rate': 5.0,
            'advance_payment': 5000.0,
            'payment_status': 'Partial',
            'due_date': '2026-07-15',
            'source': 'Logistics App Wizard',
            'owner': 'Compliance Manager'
        }
        response = self.app.post(
            '/api/invoices',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        res_data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(res_data['due_date'], '2026-07-15')
        
        # Verify it was stored correctly by fetching details
        detail_res = self.app.get(f"/api/invoices/{res_data['invoice_id']}")
        self.assertEqual(detail_res.status_code, 200)
        detail_data = json.loads(detail_res.data.decode('utf-8'))
        self.assertEqual(detail_data['due_date'], '2026-07-15')
        self.assertEqual(detail_data['source'], 'Logistics App Wizard')
        self.assertEqual(detail_data['owner'], 'Compliance Manager')

    def test_rbac_customer_actions(self):
        """Test that Customer has read permissions but 403s on billing edits."""
        # 1. Customer creates booking with default/zero billing (Allowed)
        payload = {
            'customer_name': 'Customer Logistics Inc',
            'customer_email': 'info@customerlog.com',
            'pickup_location': 'Chennai Port',
            'drop_location': 'Bangalore City',
            'goods_type': 'Apparel',
            'weight': 4.0,
            'preferred_date': '2026-07-02',
            'vehicle_number': 'TN-01-AA-9999',
            'vehicle_type': 'Mini Truck',
            'driver_name': 'Senthil Kumar',
            'freight_charges': 0.0,
            'gst_rate': 5.0,
            'advance_payment': 0.0,
            'payment_status': 'Pending'
        }
        headers = {'X-User-Role': 'Customer', 'X-User-Username': 'customer_user'}
        response = self.app.post(
            '/api/invoices',
            data=json.dumps(payload),
            content_type='application/json',
            headers=headers
        )
        self.assertEqual(response.status_code, 201)
        res_data = json.loads(response.data.decode('utf-8'))
        invoice_id = res_data['invoice_id']

        # 2. Customer attempts to create booking with set freight charges (Blocked)
        payload_invalid = payload.copy()
        payload_invalid['freight_charges'] = 5000.0
        response_invalid = self.app.post(
            '/api/invoices',
            data=json.dumps(payload_invalid),
            content_type='application/json',
            headers=headers
        )
        self.assertEqual(response_invalid.status_code, 403)

        # 3. Customer views invoice (Allowed)
        response_view = self.app.get(f'/api/invoices/{invoice_id}', headers=headers)
        self.assertEqual(response_view.status_code, 200)

        # 4. Customer edits GST (Blocked)
        response_edit_gst = self.app.put(
            f'/api/invoices/{invoice_id}',
            data=json.dumps({'freight_charges': 0.0, 'gst_rate': 12.0}),
            content_type='application/json',
            headers=headers
        )
        self.assertEqual(response_edit_gst.status_code, 403)

        # 5. Customer edits freight charges (Blocked)
        response_edit_freight = self.app.put(
            f'/api/invoices/{invoice_id}',
            data=json.dumps({'freight_charges': 15000.0}),
            content_type='application/json',
            headers=headers
        )
        self.assertEqual(response_edit_freight.status_code, 403)

        # 6. Customer edits payment status (Blocked)
        response_edit_status = self.app.put(
            f'/api/invoices/{invoice_id}',
            data=json.dumps({'payment_status': 'Paid'}),
            content_type='application/json',
            headers=headers
        )
        self.assertEqual(response_edit_status.status_code, 403)

    def test_rbac_accounts_staff_actions(self):
        """Test Accounts Staff can edit billing fields and write audit logs."""
        headers_staff = {'X-User-Role': 'Accounts Staff', 'X-User-Username': 'accounts_user'}
        
        # Accounts staff updates freight and gst of invoice #1
        response = self.app.put(
            '/api/invoices/1',
            data=json.dumps({
                'freight_charges': 48000.0,
                'gst_rate': 12.0
            }),
            content_type='application/json',
            headers=headers_staff
        )
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data.decode('utf-8'))
        
        # Verify calculated fields
        # GST = 48000 * 12% = 5760.0
        # Balance = 48000 + 5760 - 20000 = 33760.0
        self.assertEqual(res_data['balance_payment'], 33760.0)

        # Accounts staff updates payment status to Paid
        response_status = self.app.put(
            '/api/invoices/1',
            data=json.dumps({
                'payment_status': 'Paid',
                'advance_payment': 53760.0
            }),
            content_type='application/json',
            headers=headers_staff
        )
        self.assertEqual(response_status.status_code, 200)

        # Accounts staff is forbidden from deleting invoices
        response_delete = self.app.delete('/api/invoices/1', headers=headers_staff)
        self.assertEqual(response_delete.status_code, 403)

    def test_rbac_admin_full_access(self):
        """Test Admin has unrestricted access including audit logs and deletion."""
        headers_admin = {'X-User-Role': 'Admin/Owner', 'X-User-Username': 'admin_user'}

        # 1. Admin edits invoice
        response_edit = self.app.put(
            '/api/invoices/1',
            data=json.dumps({'freight_charges': 50000.0, 'gst_rate': 18.0, 'payment_status': 'Paid', 'advance_payment': 59000.0}),
            content_type='application/json',
            headers=headers_admin
        )
        self.assertEqual(response_edit.status_code, 200)

        # 2. Admin retrieves audit logs (checks if logs were written for the edits)
        response_logs = self.app.get('/api/audit-logs', headers=headers_admin)
        self.assertEqual(response_logs.status_code, 200)
        logs = json.loads(response_logs.data.decode('utf-8'))
        self.assertTrue(len(logs) > 0)
        
        # Verify log values
        freight_logs = [l for l in logs if l['field_name'] == 'freight_charges']
        self.assertTrue(len(freight_logs) > 0)
        self.assertEqual(freight_logs[0]['username'], 'admin_user')
        self.assertEqual(freight_logs[0]['role'], 'Admin/Owner')

        # 3. Admin deletes invoice (Succeeds)
        response_delete = self.app.delete('/api/invoices/1', headers=headers_admin)
        self.assertEqual(response_delete.status_code, 200)

if __name__ == '__main__':
    unittest.main()
