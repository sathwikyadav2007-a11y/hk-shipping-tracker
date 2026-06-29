import os
import sqlite3
import datetime
import contextlib
from functools import wraps
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# Database configuration
DATABASE_FILE = 'hk_shipping.db'

def require_role(allowed_roles):
    """Decorator to enforce role-based access control checking headers."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = request.headers.get('X-User-Role') or request.args.get('role')
            if not user_role:
                return jsonify({'error': 'Unauthorized: Missing user role'}), 401
            if user_role not in allowed_roles:
                return jsonify({'error': 'Forbidden: Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class AILogisticsEngine:
    @staticmethod
    def generate_feedback(invoice_data):
        """
        Rule-based AI engine that analyzes transit details, weights, routes, and alerts to suggest:
        1. Suggested rate comparison
        2. Narrative summary of status
        3. ETA delay risk explanation
        4. Customer updates template (Email & WhatsApp text)
        """
        freight = invoice_data.get('freight_charges', 0.0)
        weight = invoice_data.get('weight', 0.0)
        source = invoice_data.get('pickup_location', '')
        dest = invoice_data.get('drop_location', '')
        status = invoice_data.get('payment_status', '')
        trip_status = invoice_data.get('trip_status', '') or invoice_data.get('status', '')
        vehicle = invoice_data.get('vehicle_number', '')
        driver = invoice_data.get('driver_name', '')
        gps = invoice_data.get('gps_checkpoint', '')
        eta = invoice_data.get('eta', '')
        balance = invoice_data.get('balance_payment', 0.0)
        customer = invoice_data.get('customer_name', '')
        goods = invoice_data.get('goods_type', '')

        # 1. Suggested Rate comparison (standard base of ₹3000/ton)
        standard_rate_per_ton = 3000.0
        suggested_rate = round(standard_rate_per_ton * weight, 2)
        diff = freight - suggested_rate
        
        if diff > 0:
            rate_comparison = f"Charged rate (₹{freight:,.2f}) is higher than standard rate card (₹{suggested_rate:,.2f}) by ₹{diff:,.2f} (Premium surcharge applied)."
        elif diff < 0:
            rate_comparison = f"Charged rate (₹{freight:,.2f}) is discounted below standard rate card (₹{suggested_rate:,.2f}) by ₹{abs(diff):,.2f}."
        else:
            rate_comparison = f"Charged rate matches standard rate card (₹{suggested_rate:,.2f}) exactly."

        # 2. Narrative Summary
        narrative = f"Consignment for client {customer} carrying {goods} ({weight} tons) from {source} to {dest}. "
        if trip_status == 'Completed' or trip_status == 'Delivered':
            narrative += f"The transit on vehicle {vehicle} was successfully completed by driver {driver}. Proof of delivery has been received."
        elif trip_status == 'Active' or trip_status == 'In Transit':
            narrative += f"The transit is currently Active. Truck {vehicle} (Driver: {driver}) is active on route and was last tracked at '{gps}'. Current ETA: {eta}."
        else:
            narrative += f"Booking is logged, waiting for vehicle {vehicle} dispatch assignment."

        # 3. ETA Delay Risk
        delay_risk = "No delay risk detected. Transit normal."
        if trip_status == 'Active' or trip_status == 'In Transit':
            if gps and ('Toll' in gps or 'Border' in gps or 'Bypass' in gps):
                delay_risk = f"Transit is currently navigating '{gps}'. Standard congestion at checkpoint may cause a minor delay of 45-60 minutes."
            elif not gps:
                delay_risk = "GPS tracking device is currently offline. Route delay risk cannot be fully ruled out."
        elif trip_status == 'Completed' or trip_status == 'Delivered':
            delay_risk = "Consignment has been safely delivered. No pending risks."

        # 4. Customer messaging updates
        email_subject = f"HK Shipping Dispatch Update - Invoice #INV-{invoice_data.get('id', 'TBD')}"
        email_body = (
            f"Dear {customer} Team,\n\n"
            f"We are pleased to update you on your consignment status:\n\n"
            f"- Shipment: {goods} ({weight} Tons)\n"
            f"- Route: {source} to {dest}\n"
            f"- Vehicle: {vehicle} (Driver: {driver})\n"
            f"- Transit Status: {trip_status}\n"
            f"- Current GPS Checkpoint: {gps or 'N/A'}\n"
            f"- Estimated Time of Arrival: {eta or 'TBD'}\n"
            f"- Outstanding Invoiced Balance: ₹{balance:,.2f} ({status})\n\n"
            f"Thank you for choosing HK Shipping Private Limited.\n"
            f"Operations Team"
        )

        whatsapp_text = (
            f"*HK Shipping Consignment Update*\n"
            f"Client: {customer}\n"
            f"Cargo: {goods} ({weight} Tons)\n"
            f"Route: {source} -> {dest}\n"
            f"Truck: {vehicle} | Driver: {driver}\n"
            f"GPS Checkpoint: {gps or 'Pending'}\n"
            f"ETA: {eta or 'TBD'}\n"
            f"Pending Balance: ₹{balance:,.2f}"
        )

        return {
            'suggested_rate': suggested_rate,
            'rate_comparison': rate_comparison,
            'narrative': narrative,
            'delay_risk': delay_risk,
            'email_subject': email_subject,
            'email_body': email_body,
            'whatsapp_text': whatsapp_text
        }

@contextlib.contextmanager
def get_db_connection():
    """Establish a connection to the SQLite database with row factory."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()

def upgrade_db_schema():
    """Alter the database to add missing invoice columns if they don't already exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(invoices)")
        columns = [row['name'] for row in cursor.fetchall()]
        
        if 'due_date' not in columns:
            conn.execute("ALTER TABLE invoices ADD COLUMN due_date TEXT;")
        if 'source' not in columns:
            conn.execute("ALTER TABLE invoices ADD COLUMN source TEXT DEFAULT 'Web Wizard';")
        if 'owner' not in columns:
            conn.execute("ALTER TABLE invoices ADD COLUMN owner TEXT DEFAULT 'Accounts Staff';")
        conn.commit()

def init_db():
    """Create the SQLite database schema and seed initial data if empty."""
    schema_queries = [
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS trucks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_number TEXT UNIQUE NOT NULL,
            capacity_tons REAL,
            insurance_expiry TEXT,
            permit_expiry TEXT,
            maintenance_status TEXT DEFAULT 'Fit'
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            license_number TEXT UNIQUE NOT NULL,
            license_expiry TEXT,
            phone TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            pickup_location TEXT NOT NULL,
            drop_location TEXT NOT NULL,
            goods_type TEXT NOT NULL,
            weight REAL NOT NULL,
            vehicle_type TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            gps_checkpoint TEXT,
            eta TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shipment_id INTEGER NOT NULL,
            truck_id INTEGER NOT NULL,
            driver_id INTEGER NOT NULL,
            pod_photo_url TEXT,
            receiver_signature TEXT,
            status TEXT DEFAULT 'Active',
            FOREIGN KEY (shipment_id) REFERENCES shipments (id),
            FOREIGN KEY (truck_id) REFERENCES trucks (id),
            FOREIGN KEY (driver_id) REFERENCES drivers (id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            freight_charges REAL NOT NULL,
            gst_amount REAL NOT NULL,
            advance_payment REAL NOT NULL DEFAULT 0.0,
            balance_payment REAL NOT NULL,
            payment_status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            due_date TEXT,
            source TEXT DEFAULT 'Web Wizard',
            owner TEXT DEFAULT 'Accounts Staff',
            FOREIGN KEY (trip_id) REFERENCES trips (id),
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            distance_km REAL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS rate_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER NOT NULL,
            vehicle_type TEXT NOT NULL,
            rate REAL NOT NULL,
            FOREIGN KEY (route_id) REFERENCES routes (id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            invoice_id INTEGER NOT NULL,
            field_name TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            timestamp TEXT NOT NULL
        );
        """
    ]

    with get_db_connection() as conn:
        for query in schema_queries:
            conn.execute(query)
        conn.commit()

    # Upgrade db schema if columns are missing
    upgrade_db_schema()

    # Seed dummy data if empty
    seed_dummy_data()

def seed_dummy_data():
    """Seeds default routes, rate cards, drivers, trucks, and invoices for testing/demo."""
    with get_db_connection() as conn:
        # Check if already seeded
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers")
        if cursor.fetchone()[0] > 0:
            return # Already seeded

        # Seed Customers
        conn.execute("INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)", 
                     ("Tata Motors Logistics", "logistics@tatamotors.com", "+91 99999 88888"))
        conn.execute("INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)", 
                     ("Reliance Retail Ltd", "supplychain@reliance.com", "+91 98888 77777"))
        
        # Seed Trucks (with expiry dates for compliance alerts)
        # Note: Current system date in request context is 2026-06-18
        conn.execute("INSERT INTO trucks (vehicle_number, capacity_tons, insurance_expiry, permit_expiry, maintenance_status) VALUES (?, ?, ?, ?, ?)",
                     ("MH-43-AA-1234", 16.0, "2026-06-25", "2026-08-15", "Fit")) # Insurance expiring in 7 days
        conn.execute("INSERT INTO trucks (vehicle_number, capacity_tons, insurance_expiry, permit_expiry, maintenance_status) VALUES (?, ?, ?, ?, ?)",
                     ("MH-12-XY-9876", 24.5, "2026-10-12", "2026-06-22", "Fit")) # Permit expiring in 4 days
        conn.execute("INSERT INTO trucks (vehicle_number, capacity_tons, insurance_expiry, permit_expiry, maintenance_status) VALUES (?, ?, ?, ?, ?)",
                     ("DL-01-CP-5566", 10.0, "2026-05-15", "2026-12-01", "Required")) # Insurance already expired
        conn.execute("INSERT INTO trucks (vehicle_number, capacity_tons, insurance_expiry, permit_expiry, maintenance_status) VALUES (?, ?, ?, ?, ?)",
                     ("KA-03-MM-7788", 12.0, "2027-02-28", "2027-03-15", "Fit")) # Fully compliant

        # Seed Drivers
        conn.execute("INSERT INTO drivers (name, license_number, license_expiry, phone) VALUES (?, ?, ?, ?)",
                     ("Rajesh Kumar", "DL-1234567890", "2028-11-20", "+91 90000 11111"))
        conn.execute("INSERT INTO drivers (name, license_number, license_expiry, phone) VALUES (?, ?, ?, ?)",
                     ("Suresh Yadav", "DL-9876543210", "2026-06-30", "+91 91111 22222")) # License expiring in 12 days
        conn.execute("INSERT INTO drivers (name, license_number, license_expiry, phone) VALUES (?, ?, ?, ?)",
                     ("Amit Singh", "DL-5555555555", "2026-04-01", "+91 92222 33333")) # License expired

        # Seed Routes
        conn.execute("INSERT INTO routes (source, destination, distance_km) VALUES (?, ?, ?)", ("Mumbai", "Pune", 150.0))
        conn.execute("INSERT INTO routes (source, destination, distance_km) VALUES (?, ?, ?)", ("Delhi", "Jaipur", 270.0))

        # Seed Invoices/Trips/Shipments for testing
        # 1. Tata Motors shipment Mumbai -> Pune
        conn.execute("""
            INSERT INTO shipments (customer_id, pickup_location, drop_location, goods_type, weight, vehicle_type, preferred_date, gps_checkpoint, eta, status)
            VALUES (1, 'Tata Plant, Pune', 'JNPT Port, Mumbai', 'Auto Components', 12.5, 'Container Truck', '2026-06-15', 'Panvel Bypass', 'Delivered', 'Delivered')
        """)
        conn.execute("""
            INSERT INTO trips (shipment_id, truck_id, driver_id, pod_photo_url, receiver_signature, status)
            VALUES (1, 1, 1, 'https://storage.hks.com/pod/pod_Tata.jpg', 'Signed by K. Roy', 'Completed')
        """)
        conn.execute("""
            INSERT INTO invoices (trip_id, customer_id, freight_charges, gst_amount, advance_payment, balance_payment, payment_status, created_at)
            VALUES (1, 1, 45000.0, 5400.0, 20000.0, 30400.0, 'Partial', '2026-06-15 10:30:00')
        """)

        # 2. Reliance shipment Delhi -> Jaipur
        conn.execute("""
            INSERT INTO shipments (customer_id, pickup_location, drop_location, goods_type, weight, vehicle_type, preferred_date, gps_checkpoint, eta, status)
            VALUES (2, 'Reliance WH, Delhi', 'Retail Hub, Jaipur', 'FMCG Goods', 8.0, 'Multi-Axle Truck', '2026-06-17', 'Gurgaon Toll', 'In Transit', 'In Transit')
        """)
        conn.execute("""
            INSERT INTO trips (shipment_id, truck_id, driver_id, pod_photo_url, receiver_signature, status)
            VALUES (2, 2, 2, NULL, NULL, 'Active')
        """)
        conn.execute("""
            INSERT INTO invoices (trip_id, customer_id, freight_charges, gst_amount, advance_payment, balance_payment, payment_status, created_at)
            VALUES (2, 2, 35000.0, 1750.0, 36750.0, 0.0, 'Paid', '2026-06-17 14:45:00')
        """)

        conn.commit()

# Initialize DB on load
init_db()


# ---------------- PAGE ROUTES ----------------

@app.route('/')
def index_page():
    """Renders the landing page."""
    return render_template('index.html')

@app.route('/booking/crm')
def crm_page():
    """Renders Step 1: Customer CRM Form."""
    return render_template('crm.html')

@app.route('/booking/trip')
def trip_page():
    """Renders Step 2: Trip & Cargo Details Form."""
    return render_template('trip.html')

@app.route('/booking/fleet')
def fleet_page():
    """Renders Step 3: Fleet & Driver Assignment Form."""
    return render_template('fleet.html')

@app.route('/booking/accounts')
def accounts_page():
    """Renders Step 4: Accounts & Invoicing Billing Form."""
    return render_template('accounts.html')

@app.route('/dashboard')
def dashboard_page():
    """Renders the Fleet & Invoicing Dashboard."""
    return render_template('dashboard.html')


# ---------------- API ENDPOINTS ----------------

@app.route('/api/invoices', methods=['POST'])
@require_role(['Customer', 'Accounts Staff', 'Admin/Owner'])
def create_invoice():
    """
    POST /api/invoices
    Create a new invoice entry, including customer, shipment, vehicle, and driver tracking info.
    Validates missing fields, calculates balance payment, and logs timestamp.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400

        user_role = request.headers.get('X-User-Role')
        if user_role == 'Customer':
            freight = float(data.get('freight_charges') or 0.0)
            advance = float(data.get('advance_payment') or 0.0)
            status = data.get('payment_status') or 'Pending'
            if freight > 0.0 or advance > 0.0 or status != 'Pending':
                return jsonify({'error': 'Forbidden: Customers are not permitted to set billing rates, payments, or invoicing status'}), 403

        # 1. Fields Validation
        required_fields = [
            'customer_name', 'customer_email', 'pickup_location', 'drop_location',
            'goods_type', 'weight', 'preferred_date', 'vehicle_number',
            'vehicle_type', 'driver_name', 'freight_charges', 'gst_rate'
        ]
        
        missing = [f for f in required_fields if data.get(f) is None or data.get(f) == '']
        if missing:
            return jsonify({'error': f"Missing required fields: {', '.join(missing)}"}), 400

        # Extract numeric inputs
        try:
            freight = float(data['freight_charges'])
            gst_rate = float(data['gst_rate'])
            weight = float(data['weight'])
            advance = float(data.get('advance_payment') or 0.0)
        except ValueError:
            return jsonify({'error': 'Freight, GST Rate, Weight, and Advance must be valid numbers'}), 400

        if freight < 0 or (freight == 0 and user_role != 'Customer') or weight <= 0:
            return jsonify({'error': 'Freight charges must be greater than zero'}), 400

        # 2. Automatically calculate GST and Balance Payment
        gst_amount = float(round(freight * (gst_rate / 100.0), 2))
        balance_payment = float(round(freight + gst_amount - advance, 2))

        # Log timestamp
        now_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # A. Check or Insert Customer
            cursor.execute("SELECT id FROM customers WHERE email = ?", (data['customer_email'],))
            customer_row = cursor.fetchone()
            if customer_row:
                customer_id = customer_row['id']
            else:
                cursor.execute(
                    "INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)",
                    (data['customer_name'], data['customer_email'], data.get('customer_phone'))
                )
                customer_id = cursor.lastrowid

            # B. Check or Insert Truck
            cursor.execute("SELECT id FROM trucks WHERE vehicle_number = ?", (data['vehicle_number'],))
            truck_row = cursor.fetchone()
            if truck_row:
                truck_id = truck_row['id']
                # Update optional compliance details if provided
                update_fields = []
                params = []
                if data.get('capacity_tons'):
                    update_fields.append("capacity_tons = ?")
                    params.append(float(data['capacity_tons']))
                if data.get('insurance_expiry'):
                    update_fields.append("insurance_expiry = ?")
                    params.append(data['insurance_expiry'])
                if data.get('permit_expiry'):
                    update_fields.append("permit_expiry = ?")
                    params.append(data['permit_expiry'])
                if data.get('maintenance_status'):
                    update_fields.append("maintenance_status = ?")
                    params.append(data['maintenance_status'])
                
                if update_fields:
                    params.append(truck_id)
                    cursor.execute(f"UPDATE trucks SET {', '.join(update_fields)} WHERE id = ?", params)
            else:
                cursor.execute(
                    """INSERT INTO trucks (vehicle_number, capacity_tons, insurance_expiry, permit_expiry, maintenance_status)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        data['vehicle_number'],
                        float(data.get('capacity_tons') or 0.0),
                        data.get('insurance_expiry'),
                        data.get('permit_expiry'),
                        data.get('maintenance_status') or 'Fit'
                    )
                )
                truck_id = cursor.lastrowid

            # C. Check or Insert Driver
            cursor.execute("SELECT id FROM drivers WHERE name = ?", (data['driver_name'],))
            driver_row = cursor.fetchone()
            if driver_row:
                driver_id = driver_row['id']
                if data.get('license_expiry'):
                    cursor.execute("UPDATE drivers SET license_expiry = ? WHERE id = ?", (data['license_expiry'], driver_id))
            else:
                cursor.execute(
                    "INSERT INTO drivers (name, license_number, license_expiry, phone) VALUES (?, ?, ?, ?)",
                    (
                        data['driver_name'],
                        data.get('license_number') or f"LIC-{data['driver_name'].replace(' ', '').upper()}",
                        data.get('license_expiry'),
                        data.get('driver_phone')
                    )
                )
                driver_id = cursor.lastrowid

            # D. Insert Shipment Request
            cursor.execute(
                """INSERT INTO shipments (customer_id, pickup_location, drop_location, goods_type, weight, vehicle_type, preferred_date, gps_checkpoint, eta, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    customer_id, data['pickup_location'], data['drop_location'],
                    data['goods_type'], weight, data['vehicle_type'], data['preferred_date'],
                    data.get('gps_checkpoint'), data.get('eta'),
                    'In Transit' if data.get('gps_checkpoint') else 'Pending'
                )
            )
            shipment_id = cursor.lastrowid

            # E. Insert Trip Details
            trip_status = 'Active'
            if data.get('payment_status') == 'Paid' or data.get('receiver_signature'):
                trip_status = 'Completed'

            cursor.execute(
                """INSERT INTO trips (shipment_id, truck_id, driver_id, pod_photo_url, receiver_signature, status)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    shipment_id, truck_id, driver_id,
                    data.get('pod_photo_url'), data.get('receiver_signature'),
                    trip_status
                )
            )
            trip_id = cursor.lastrowid

            # F. Insert Invoice details
            payment_status = data.get('payment_status') or ('Paid' if balance_payment <= 0 else 'Pending')
            due_date = data.get('due_date')
            if not due_date:
                due_date = (datetime.date.today() + datetime.timedelta(days=15)).strftime('%Y-%m-%d')
            source = data.get('source') or 'Web Wizard'
            owner = data.get('owner') or 'Accounts Staff'

            cursor.execute(
                """INSERT INTO invoices (trip_id, customer_id, freight_charges, gst_amount, advance_payment, balance_payment, payment_status, created_at, due_date, source, owner)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    trip_id, customer_id, freight, gst_amount,
                    advance, balance_payment,
                    payment_status, now_timestamp, due_date, source, owner
                )
            )
            invoice_id = cursor.lastrowid
            conn.commit()

        return jsonify({
            'success': True,
            'message': 'Invoice registered successfully',
            'invoice_id': invoice_id,
            'balance_payment': balance_payment,
            'gst_amount': gst_amount,
            'timestamp': now_timestamp,
            'due_date': due_date
        }), 201

    except Exception as e:
        # Strict try/except returning clean JSON error responses
        return jsonify({'error': 'Server Error during invoice creation', 'details': str(e)}), 500


@app.route('/api/invoices', methods=['GET'])
@require_role(['Customer', 'Accounts Staff', 'Admin/Owner'])
def get_invoices():
    """
    GET /api/invoices
    Retrieves all records with filter support for status/date.
    Filters:
      - status: paid, pending, partial (matching payment_status)
      - date: YYYY-MM-DD (matches created_at date portion)
    """
    try:
        status_filter = request.args.get('status')
        date_filter = request.args.get('date')

        query = """
            SELECT 
                i.id, i.freight_charges, i.gst_amount, i.advance_payment, i.balance_payment, i.payment_status, i.created_at,
                i.due_date, i.source, i.owner,
                c.name as customer_name, c.email as customer_email,
                s.pickup_location, s.drop_location, s.goods_type, s.weight, s.vehicle_type, s.gps_checkpoint, s.eta,
                t.vehicle_number, d.name as driver_name
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            JOIN trips tr ON i.trip_id = tr.id
            JOIN shipments s ON tr.shipment_id = s.id
            JOIN trucks t ON tr.truck_id = t.id
            JOIN drivers d ON tr.driver_id = d.id
        """
        
        conditions = []
        params = []

        if status_filter:
            conditions.append("i.payment_status = ?")
            params.append(status_filter)

        if date_filter:
            conditions.append("i.created_at LIKE ?")
            params.append(f"{date_filter}%")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Order by newest first
        query += " ORDER BY i.id DESC"

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            invoices = [dict(row) for row in rows]

        return jsonify(invoices), 200

    except Exception as e:
        return jsonify({'error': 'Server Error during invoices retrieval', 'details': str(e)}), 500


@app.route('/api/dashboard/stats', methods=['GET'])
@require_role(['Accounts Staff', 'Admin/Owner'])
def get_dashboard_stats():
    """
    GET /api/dashboard/stats
    Return computed summaries: total revenue, pending balances, active trips, and upcoming compliance alerts.
    """
    try:
        # Fixed point in time for mock data tracking relative to system clock (or use datetime.date.today())
        # Today is 2026-06-18 as per user context
        today_val = datetime.date(2026, 6, 18)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Total Revenue (sum of freight + gst across all invoices)
            cursor.execute("SELECT SUM(freight_charges + gst_amount) FROM invoices")
            total_revenue = cursor.fetchone()[0] or 0.0

            # 2. Pending Balances (sum of balance_payment)
            cursor.execute("SELECT SUM(balance_payment) FROM invoices")
            pending_balances = cursor.fetchone()[0] or 0.0

            # 3. Active Trips (count of trips in status = 'Active')
            cursor.execute("SELECT COUNT(*) FROM trips WHERE status = 'Active'")
            active_trips = cursor.fetchone()[0] or 0

            # 4. Compliance Alerts (permits/insurance/license expiring within 30 days)
            alerts = []

            # Fetch all trucks for compliance checks
            cursor.execute("SELECT vehicle_number, insurance_expiry, permit_expiry FROM trucks")
            trucks = cursor.fetchall()
            for truck in trucks:
                v_num = truck['vehicle_number']
                
                # Check Insurance
                if truck['insurance_expiry']:
                    try:
                        exp_date = datetime.datetime.strptime(truck['insurance_expiry'], '%Y-%m-%d').date()
                        days_left = (exp_date - today_val).days
                        if days_left <= 30:
                            alerts.append({
                                'type': 'Insurance Expiry',
                                'entity_name': f"Truck {v_num}",
                                'vehicle_number': v_num,
                                'expiry_date': truck['insurance_expiry'],
                                'days_remaining': days_left
                            })
                    except ValueError:
                        pass
                
                # Check Permit
                if truck['permit_expiry']:
                    try:
                        exp_date = datetime.datetime.strptime(truck['permit_expiry'], '%Y-%m-%d').date()
                        days_left = (exp_date - today_val).days
                        if days_left <= 30:
                            alerts.append({
                                'type': 'National Permit Expiry',
                                'entity_name': f"Truck {v_num}",
                                'vehicle_number': v_num,
                                'expiry_date': truck['permit_expiry'],
                                'days_remaining': days_left
                            })
                    except ValueError:
                        pass

            # Fetch all drivers for compliance checks
            cursor.execute("SELECT name, license_expiry FROM drivers")
            drivers = cursor.fetchall()
            for driver in drivers:
                d_name = driver['name']
                if driver['license_expiry']:
                    try:
                        exp_date = datetime.datetime.strptime(driver['license_expiry'], '%Y-%m-%d').date()
                        days_left = (exp_date - today_val).days
                        if days_left <= 30:
                            alerts.append({
                                'type': 'Driver License Expiry',
                                'entity_name': d_name,
                                'vehicle_number': None,
                                'expiry_date': driver['license_expiry'],
                                'days_remaining': days_left
                            })
                    except ValueError:
                        pass

            # Sort alerts so already expired ones appear first (lowest days_remaining)
            alerts.sort(key=lambda x: x['days_remaining'])

        return jsonify({
            'total_revenue': float(round(total_revenue, 2)),
            'pending_balances': float(round(pending_balances, 2)),
            'active_trips': active_trips,
            'upcoming_compliance_alerts': alerts
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error during stats calculation', 'details': str(e)}), 500


@app.route('/api/invoices/<int:invoice_id>', methods=['GET'])
@require_role(['Customer', 'Accounts Staff', 'Admin/Owner'])
def get_invoice_detail(invoice_id):
    """
    GET /api/invoices/<invoice_id>
    Retrieves full details for a single invoice along with AI analysis.
    """
    try:
        query = """
            SELECT 
                i.id, i.freight_charges, i.gst_amount, i.advance_payment, i.balance_payment, i.payment_status, i.created_at,
                i.due_date, i.source, i.owner,
                c.name as customer_name, c.email as customer_email, c.phone as customer_phone,
                s.pickup_location, s.drop_location, s.goods_type, s.weight, s.vehicle_type, s.gps_checkpoint, s.eta,
                t.vehicle_number, t.capacity_tons, t.insurance_expiry, t.permit_expiry, t.maintenance_status,
                d.name as driver_name, d.license_number, d.license_expiry, d.phone as driver_phone,
                tr.status as trip_status, tr.pod_photo_url, tr.receiver_signature
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            JOIN trips tr ON i.trip_id = tr.id
            JOIN shipments s ON tr.shipment_id = s.id
            JOIN trucks t ON tr.truck_id = t.id
            JOIN drivers d ON tr.driver_id = d.id
            WHERE i.id = ?
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (invoice_id,))
            row = cursor.fetchone()
            
            if not row:
                return jsonify({'error': 'Invoice not found'}), 404
            
            invoice_data = dict(row)
            # Generate AI metrics
            ai_feedback = AILogisticsEngine.generate_feedback(invoice_data)
            invoice_data['ai'] = ai_feedback

        return jsonify(invoice_data), 200

    except Exception as e:
        return jsonify({'error': 'Server Error during invoice details retrieval', 'details': str(e)}), 500


def log_financial_changes(invoice_id, old_data, new_data, username, role):
    """Inserts a row in the audit_logs table for every modified financial field."""
    financial_fields = [
        'freight_charges', 'gst_amount', 'advance_payment', 'balance_payment', 'payment_status', 'due_date'
    ]
    now_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with get_db_connection() as conn:
        for field in financial_fields:
            old_val = old_data.get(field)
            new_val = new_data.get(field)
            
            # Normalize numeric fields
            if field in ['freight_charges', 'gst_amount', 'advance_payment', 'balance_payment']:
                try:
                    old_val = float(old_val) if old_val is not None else 0.0
                    new_val = float(new_val) if new_val is not None else 0.0
                except (ValueError, TypeError):
                    pass
            
            if old_val != new_val:
                conn.execute(
                    """INSERT INTO audit_logs (username, role, invoice_id, field_name, old_value, new_value, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (username, role, invoice_id, field, str(old_val), str(new_val), now_timestamp)
                )
        conn.commit()


@app.route('/api/invoices/<int:invoice_id>', methods=['PUT'])
@require_role(['Customer', 'Accounts Staff', 'Admin/Owner'])
def update_invoice(invoice_id):
    """
    PUT /api/invoices/<invoice_id>
    Update consignment details. Enforces RBAC checks on financial billing fields.
    """
    try:
        user_role = request.headers.get('X-User-Role')
        user_username = request.headers.get('X-User-Username') or 'unknown_user'
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400

        # Get existing details
        query_exist = """
            SELECT 
                i.id, i.freight_charges, i.gst_amount, i.advance_payment, i.balance_payment, i.payment_status, i.due_date,
                tr.status as trip_status
            FROM invoices i
            JOIN trips tr ON i.trip_id = tr.id
            WHERE i.id = ?
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query_exist, (invoice_id,))
            row = cursor.fetchone()
            
            if not row:
                return jsonify({'error': 'Invoice not found'}), 404
                
            old_data = dict(row)

        # Enforce RBAC constraints on financial parameters
        financial_fields = ['freight_charges', 'gst_rate', 'gst_amount', 'advance_payment', 'balance_payment', 'payment_status', 'due_date']
        if user_role == 'Customer':
            for field in financial_fields:
                if field in data:
                    new_val = data[field]
                    old_val = old_data.get(field)
                    
                    # Convert to float for numerical comparison
                    if field in ['freight_charges', 'gst_amount', 'advance_payment', 'balance_payment']:
                        try:
                            new_val = float(new_val)
                            old_val = float(old_val) if old_val is not None else 0.0
                        except (ValueError, TypeError):
                            pass
                    
                    if old_val != new_val:
                        return jsonify({'error': f'Forbidden: Customers are not permitted to modify billing fields ({field})'}), 403

        # Update calculations
        freight = float(data['freight_charges']) if 'freight_charges' in data else float(old_data['freight_charges'])
        gst_rate = float(data.get('gst_rate', 5.0))
        
        if 'freight_charges' in data or 'gst_rate' in data:
            gst_amount = float(round(freight * (gst_rate / 100.0), 2))
        else:
            gst_amount = float(old_data['gst_amount'])
            
        advance = float(data['advance_payment']) if 'advance_payment' in data else float(old_data['advance_payment'])
        balance = float(round(freight + gst_amount - advance, 2))
        
        payment_status = data.get('payment_status') if 'payment_status' in data else old_data['payment_status']
        due_date = data.get('due_date') if 'due_date' in data else old_data['due_date']

        new_financials = {
            'freight_charges': freight,
            'gst_amount': gst_amount,
            'advance_payment': advance,
            'balance_payment': balance,
            'payment_status': payment_status,
            'due_date': due_date
        }

        # Log changes to audit table
        log_financial_changes(invoice_id, old_data, new_financials, user_username, user_role)

        # Update records
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Fetch relational IDs
            cursor.execute("SELECT trip_id, customer_id FROM invoices WHERE id = ?", (invoice_id,))
            inv_row = cursor.fetchone()
            trip_id = inv_row['trip_id']
            customer_id = inv_row['customer_id']
            
            cursor.execute("SELECT shipment_id, truck_id, driver_id FROM trips WHERE id = ?", (trip_id,))
            trip_row = cursor.fetchone()
            shipment_id = trip_row['shipment_id']
            truck_id = trip_row['truck_id']
            driver_id = trip_row['driver_id']

            # 1. Update Invoice table
            cursor.execute(
                """UPDATE invoices 
                   SET freight_charges = ?, gst_amount = ?, advance_payment = ?, balance_payment = ?, payment_status = ?, due_date = ?
                   WHERE id = ?""",
                (freight, gst_amount, advance, balance, payment_status, due_date, invoice_id)
            )

            # 2. Update Customer table
            if 'customer_name' in data or 'customer_email' in data or 'customer_phone' in data:
                cursor.execute(
                    """UPDATE customers 
                       SET name = COALESCE(?, name), email = COALESCE(?, email), phone = COALESCE(?, phone)
                       WHERE id = ?""",
                    (data.get('customer_name'), data.get('customer_email'), data.get('customer_phone'), customer_id)
                )

            # 3. Update Shipment table
            if any(f in data for f in ['pickup_location', 'drop_location', 'goods_type', 'weight', 'preferred_date', 'gps_checkpoint', 'eta']):
                cursor.execute(
                    """UPDATE shipments 
                       SET pickup_location = COALESCE(?, pickup_location), drop_location = COALESCE(?, drop_location),
                           goods_type = COALESCE(?, goods_type), weight = COALESCE(?, weight), preferred_date = COALESCE(?, preferred_date),
                           gps_checkpoint = COALESCE(?, gps_checkpoint), eta = COALESCE(?, eta)
                       WHERE id = ?""",
                    (
                        data.get('pickup_location'), data.get('drop_location'), data.get('goods_type'),
                        float(data['weight']) if data.get('weight') else None, data.get('preferred_date'),
                        data.get('gps_checkpoint'), data.get('eta'), shipment_id
                    )
                )

            # 4. Update Driver/Vehicle
            if 'vehicle_number' in data:
                cursor.execute("UPDATE trucks SET vehicle_number = ? WHERE id = ?", (data['vehicle_number'], truck_id))
            if 'driver_name' in data:
                cursor.execute("UPDATE drivers SET name = ? WHERE id = ?", (data['driver_name'], driver_id))

            conn.commit()

        return jsonify({
            'success': True,
            'message': 'Invoice updated successfully',
            'balance_payment': balance,
            'gst_amount': gst_amount
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error during invoice update', 'details': str(e)}), 500


@app.route('/api/invoices/<int:invoice_id>', methods=['DELETE'])
@require_role(['Admin/Owner'])
def delete_invoice(invoice_id):
    """
    DELETE /api/invoices/<invoice_id>
    Restricted to Admin/Owner. Manually cascade deletes related trip and shipment records.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT trip_id FROM invoices WHERE id = ?", (invoice_id,))
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Invoice not found'}), 404
            trip_id = row['trip_id']
            
            cursor.execute("SELECT shipment_id FROM trips WHERE id = ?", (trip_id,))
            shipment_id = cursor.fetchone()['shipment_id']

            conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            conn.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
            conn.execute("DELETE FROM shipments WHERE id = ?", (shipment_id,))
            conn.commit()
            
        return jsonify({'success': True, 'message': f'Invoice #INV-{invoice_id} successfully deleted'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Server Error during invoice deletion', 'details': str(e)}), 500


@app.route('/api/audit-logs', methods=['GET'])
@require_role(['Admin/Owner'])
def get_audit_logs():
    """
    GET /api/audit-logs
    Retrieves history logs of financial corrections. Restricted to Admin/Owner.
    """
    try:
        query = "SELECT id, username, role, invoice_id, field_name, old_value, new_value, timestamp FROM audit_logs ORDER BY id DESC"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            logs = [dict(row) for row in rows]
        return jsonify(logs), 200
    except Exception as e:
        return jsonify({'error': 'Server Error retrieving audit logs', 'details': str(e)}), 500


@app.route('/invoices/<int:invoice_id>')
def detail_page(invoice_id):
    """Renders the detailed consignment tracking and AI analysis page."""
    return render_template('detail.html', invoice_id=invoice_id)

from itsdangerous import URLSafeSerializer
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hk-shipping-secret-key-2026')

@app.route('/login')
def login_page():
    """Renders the modern premium SaaS login page."""
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """
    POST /api/login
    Authenticates email and password, returning a signed token and user role payload.
    """
    try:
        data = request.get_json() or {}
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        # Test Credentials Database
        user_db = {
            'admin@hkshipping.com': {'password': 'admin123', 'role': 'Admin/Owner', 'username': 'admin_user'},
            'staff@hkshipping.com': {'password': 'staff123', 'role': 'Accounts Staff', 'username': 'accounts_user'},
            'customer@hkshipping.com': {'password': 'customer123', 'role': 'Customer', 'username': 'customer_user'},
            'sathwikyadav2007@gmail.com': {'password': 'hkshipping2026', 'role': 'Admin/Owner', 'username': 'sathwik_admin'}
        }
        
        if email not in user_db or user_db[email]['password'] != password:
            return jsonify({'error': 'Invalid email or password'}), 401
            
        user = user_db[email]
        role = user['role']
        username = user['username']
        
        # Generate securely signed token holding email and role
        serializer = URLSafeSerializer(app.config['SECRET_KEY'])
        token = serializer.dumps({'email': email, 'role': role})
        
        return jsonify({
            'success': True,
            'token': token,
            'role': role,
            'username': username,
            'email': email
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Server Error during login', 'details': str(e)}), 500


if __name__ == '__main__':
    # Support both local and cloud deployments
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
