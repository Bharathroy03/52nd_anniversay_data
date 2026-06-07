import datetime
import io
import csv
import re
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import jwt

from config import Config
from supabase_client import get_supabase

# Initialize Flask App
# We configure it to serve static files from the 'frontend' directory
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)  # Enable Cross-Origin Resource Sharing for API development flexibility

# Decorator to verify JWT token for admin routes
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 1. Check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                
        # 2. Fallback to query parameter (highly useful for CSV download links)
        if not token:
            token = request.args.get('token')
            
        if not token:
            return jsonify({"success": False, "message": "Access denied. Token is missing."}), 401
            
        try:
            # Decode the JWT token
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            if payload.get('user') != 'admin':
                return jsonify({"success": False, "message": "Access denied. Invalid user role."}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "message": "Access denied. Token has expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "message": "Access denied. Invalid token."}), 401
            
        return f(*args, **kwargs)
    return decorated

# ----------------------------------------------------
# Static Routing (Frontend Server)
# ----------------------------------------------------

@app.route('/')
def serve_index():
    """Serves the public customer form."""
    return app.send_static_file('index.html')

@app.route('/admin-login')
def serve_admin_login_page():
    """Serves the admin login page."""
    return app.send_static_file('admin-login.html')

@app.route('/admin-dashboard')
def serve_admin_dashboard_page():
    """Serves the admin dashboard page."""
    return app.send_static_file('admin-dashboard.html')

# ----------------------------------------------------
# API Routes
# ----------------------------------------------------

@app.route('/stores', methods=['GET'])
def get_stores():
    """Fetches list of all stores from Supabase."""
    try:
        supabase = get_supabase()
        response = supabase.table('stores').select('id, store_name').order('store_name').execute()
        
        # Supabase Python client v2 response data is in response.data
        return jsonify({"success": True, "data": response.data})
    except Exception as e:
        print(f"[ERROR] get_stores failed: {e}")
        return jsonify({"success": False, "message": "Failed to fetch stores. Check server logs."}), 500

@app.route('/submit', methods=['POST'])
def submit_data():
    """Validates input and saves customer submission to Supabase."""
    try:
        data = request.json or {}
        
        # Extract inputs
        store_id = data.get('store_id')
        customer_name = data.get('customer_name')
        mobile_number = data.get('mobile_number')
        app_registration_status = data.get('app_registration_status')
        invitation_card_issue = data.get('invitation_card_issue')
        issue_description = data.get('issue_description')
        
        # Validation checks
        if not store_id:
            return jsonify({"success": False, "message": "Store selection is required."}), 400
            
        if not customer_name or not str(customer_name).strip():
            return jsonify({"success": False, "message": "Customer name is required."}), 400
            
        # Mobile number must be exactly 10 digits
        if not mobile_number or not re.match(r'^[0-9]{10}$', str(mobile_number).strip()):
            return jsonify({"success": False, "message": "Mobile number must be exactly 10 digits."}), 400
            
        # App Registration Status options
        valid_statuses = ['Completed', 'Pending', 'Not Interested']
        if app_registration_status not in valid_statuses:
            return jsonify({"success": False, "message": "Invalid App Registration Status."}), 400
            
        # Invitation card issue dropdown options (Yes/No)
        if invitation_card_issue not in ['Yes', 'No']:
            return jsonify({"success": False, "message": "Invitation card issue must be 'Yes' or 'No'."}), 400
            
        # Issue description validation
        has_issue = (invitation_card_issue == 'Yes')
        if has_issue and (not issue_description or not str(issue_description).strip()):
            return jsonify({"success": False, "message": "Issue description is required when there is an invitation card issue."}), 400
            
        # Prepare DB insert model
        db_payload = {
            "store_id": int(store_id),
            "customer_name": str(customer_name).strip(),
            "mobile_number": str(mobile_number).strip(),
            "app_registration_status": app_registration_status,
            "invitation_card_issue": has_issue,
            "issue_description": str(issue_description).strip() if has_issue else None
        }
        
        supabase = get_supabase()
        response = supabase.table('customer_submissions').insert(db_payload).execute()
        
        if not response.data:
            return jsonify({"success": False, "message": "Failed to save submission."}), 500
            
        return jsonify({"success": True, "message": "Submission successfully saved!"})
        
    except ValueError:
        return jsonify({"success": False, "message": "Invalid data formats received."}), 400
    except Exception as e:
        print(f"[ERROR] submit_data failed: {e}")
        return jsonify({"success": False, "message": "Internal server error. Failed to save data."}), 500

@app.route('/admin-login', methods=['POST'])
def admin_login():
    """Authenticates admin and returns a signed JWT token."""
    try:
        data = request.json or {}
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"success": False, "message": "Username and password are required."}), 400
            
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            # Generate JWT token
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            payload = {
                'user': 'admin',
                'exp': now_utc + datetime.timedelta(seconds=Config.JWT_EXPIRY_SECONDS),
                'iat': now_utc
            }
            token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')
            return jsonify({"success": True, "token": token})
            
        return jsonify({"success": False, "message": "Invalid username or password."}), 401
    except Exception as e:
        print(f"[ERROR] admin_login failed: {e}")
        return jsonify({"success": False, "message": "Authentication failed due to internal error."}), 500

@app.route('/admin/submissions', methods=['GET'])
@admin_required
def get_submissions():
    """Fetches customer submissions filtered and searched."""
    try:
        # Extract query params for filtering/searching
        store_id = request.args.get('store_id')
        status = request.args.get('status')
        search = request.args.get('search')
        
        supabase = get_supabase()
        
        # We perform a select with a join on the stores table to get the store_name
        query = supabase.table('customer_submissions').select(
            'id, customer_name, mobile_number, app_registration_status, '
            'invitation_card_issue, issue_description, created_at, '
            'stores(id, store_name)'
        )
        
        # Apply filters
        if store_id and store_id.strip():
            query = query.eq('store_id', int(store_id))
            
        if status and status.strip():
            query = query.eq('app_registration_status', status)
            
        if search and search.strip():
            # Search by name OR mobile using Posgrest .or_() filter
            search_str = search.strip()
            query = query.or_(f"customer_name.ilike.%{search_str}%,mobile_number.ilike.%{search_str}%")
            
        # Order by created_at descending
        query = query.order('created_at', descending=True)
        
        response = query.execute()
        
        # Flatten structure for cleaner frontend parsing
        flattened_data = []
        for row in response.data:
            store_obj = row.get('stores') or {}
            flattened_data.append({
                "id": row.get('id'),
                "customer_name": row.get('customer_name'),
                "mobile_number": row.get('mobile_number'),
                "app_registration_status": row.get('app_registration_status'),
                "invitation_card_issue": "Yes" if row.get('invitation_card_issue') else "No",
                "issue_description": row.get('issue_description') or "",
                "store_name": store_obj.get('store_name', 'Unknown Store'),
                "created_at": row.get('created_at')
            })
            
        return jsonify({"success": True, "data": flattened_data})
        
    except Exception as e:
        print(f"[ERROR] get_submissions failed: {e}")
        return jsonify({"success": False, "message": "Failed to fetch submissions."}), 500

@app.route('/admin/export-csv', methods=['GET'])
@admin_required
def export_csv():
    """Generates and returns submissions data as a CSV download."""
    try:
        store_id = request.args.get('store_id')
        status = request.args.get('status')
        search = request.args.get('search')
        
        supabase = get_supabase()
        
        # Querying data with filters
        query = supabase.table('customer_submissions').select(
            'id, customer_name, mobile_number, app_registration_status, '
            'invitation_card_issue, issue_description, created_at, '
            'stores(id, store_name)'
        )
        
        if store_id and store_id.strip():
            query = query.eq('store_id', int(store_id))
            
        if status and status.strip():
            query = query.eq('app_registration_status', status)
            
        if search and search.strip():
            search_str = search.strip()
            query = query.or_(f"customer_name.ilike.%{search_str}%,mobile_number.ilike.%{search_str}%")
            
        query = query.order('created_at', descending=True)
        response = query.execute()
        
        # Write CSV into memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # CSV Headers
        writer.writerow([
            'Submission ID', 
            'Store Name', 
            'Customer Name', 
            'Mobile Number', 
            'App Registration Status', 
            'Invitation Card Issue', 
            'Issue Description', 
            'Created At'
        ])
        
        for row in response.data:
            store_obj = row.get('stores') or {}
            writer.writerow([
                row.get('id'),
                store_obj.get('store_name', 'Unknown Store'),
                row.get('customer_name'),
                row.get('mobile_number'),
                row.get('app_registration_status'),
                "Yes" if row.get('invitation_card_issue') else "No",
                row.get('issue_description') or "",
                row.get('created_at')
            ])
            
        # Prepare response
        output.seek(0)
        csv_data = output.getvalue()
        
        filename = f"submissions_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"[ERROR] export_csv failed: {e}")
        return jsonify({"success": False, "message": "Failed to generate CSV export."}), 500

if __name__ == '__main__':
    # Run locally on default port 5000
    print("Starting Store Data Collection System API Server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
