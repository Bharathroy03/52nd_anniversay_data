import os
import re
import io
import csv
import shutil
import datetime
from flask import Flask, request, jsonify, render_template, redirect, session, Response
from flask_cors import CORS

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from config import Config
from database.supabase import get_supabase

# ----------------------------------------------------
# Directory Auto-setup and Assets Migration
# ----------------------------------------------------
def setup_directories_and_assets():
    """
    Automatically creates required project subfolders if they do not exist
    and copies original images from the old project layout.
    """
    dirs = [
        'static/css',
        'static/js',
        'static/images',
        'templates',
        'database'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        
    # Migrate images if old path is present
    old_images_path = 'store-data-app/images'
    target_images_path = 'static/images'
    if os.path.exists(old_images_path):
        try:
            for f in os.listdir(old_images_path):
                src_file = os.path.join(old_images_path, f)
                dest_file = os.path.join(target_images_path, f)
                if os.path.isfile(src_file) and not os.path.exists(dest_file):
                    shutil.copy2(src_file, dest_file)
                    print(f"[INFO] Migrated asset: {f} to {target_images_path}")
        except Exception as e:
            print(f"[WARNING] Image migration encountered error: {e}")

# Run setup
setup_directories_and_assets()

def seed_database_if_empty():
    """
    Self-healing helper: checks if the stores table in Supabase is empty,
    and automatically seeds it with the 13 required stores.
    """
    try:
        supabase = get_supabase()
        response = supabase.table('stores').select('id').limit(1).execute()
        if not response.data:
            print("[INFO] Stores table is empty. Auto-seeding stores...")
            stores_to_seed = [
                {"store_name": "Bagepalli - 1 - (23rd Block, DVG Road)"},
                {"store_name": "Chikkaballapur - 1 - (B B Road)"},
                {"store_name": "Chintamani - 1 - (GSLN Theatre)"},
                {"store_name": "Chintamani - 2 - (Minerva Stores)"},
                {"store_name": "Dabaspete - 1 - (SMN Complex)"},
                {"store_name": "Devanahalli - 1 - (19th Ward)"},
                {"store_name": "Doddaballapur - 2 - (Lions Bhavana Complex)"},
                {"store_name": "Gowribidnur - 1 - (P B Road)"},
                {"store_name": "Gowribidnur - 2 - (NVR Complex)"},
                {"store_name": "Nelamangala - 2 - (1st Block)"},
                {"store_name": "Nelamangala - 1 - (Bus Stand)"},
                {"store_name": "Sidlaghatta - 1 - (Near KSRTC Bus Stand)"},
                {"store_name": "Vijayapura - 1 - (Opp. Police Station)"}
            ]
            supabase.table('stores').insert(stores_to_seed).execute()
            print("[INFO] Database successfully seeded with 13 stores.")
        else:
            print("[INFO] Stores table already has entries. Skipping seeder.")
    except Exception as e:
        print(f"[WARNING] Database auto-seeding skipped: {e}")

# Run seed check
seed_database_if_empty()

def seed_users_if_empty():
    """
    Self-healing helper: checks if the users table is empty,
    and automatically seeds the default Super Admin and Admin & Store Head.
    """
    try:
        from werkzeug.security import generate_password_hash
        supabase = get_supabase()
        response = supabase.table('users').select('id').limit(1).execute()
        if not response.data:
            print("[INFO] Users table is empty. Auto-seeding default authority users...")
            
            # Retrieve default passwords from Config or environment
            admin_pass = Config.ADMIN_PASSWORD
            saddam_pass = Config.SADDAM_PASSWORD
            
            users_to_seed = [
                {
                    "employee_id": "22913",
                    "full_name": "Bharath Kumar (22913)",
                    "username": "bharath",
                    "password_hash": generate_password_hash(admin_pass),
                    "role": "super_admin",
                    "status": "Active"
                },
                {
                    "employee_id": "6172",
                    "full_name": "Saddam Husain (6172)",
                    "username": "saddam",
                    "password_hash": generate_password_hash(saddam_pass),
                    "role": "admin_store_head",
                    "status": "Active"
                }
            ]
            supabase.table('users').insert(users_to_seed).execute()
            print("[INFO] Database successfully seeded with default users.")
        else:
            print("[INFO] Users table already has entries. Skipping seeder.")
    except Exception as e:
        print(f"[WARNING] Users database auto-seeding skipped: {e}")

# Run users seed check
seed_users_if_empty()

# ----------------------------------------------------
# Flask App Initialization
# ----------------------------------------------------
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
CORS(app)  # Support cross-origin API development

# ----------------------------------------------------
# Global Error Handling Middleware
# ----------------------------------------------------
@app.errorhandler(Exception)
def handle_global_exception(e):
    """
    Global exception handler to catch any unhandled errors gracefully
    and return appropriate responses instead of crashing or showing tracebacks.
    """
    from werkzeug.exceptions import HTTPException
    
    # Let standard Flask HTTP exceptions (like 404, 405) propagate
    if isinstance(e, HTTPException):
        return e
        
    # Log the full exception traceback
    app.logger.error(f"Unhandled Exception: {e}", exc_info=True)
    
    # Return JSON for API routes
    if request.path.startswith('/api/'):
        return jsonify({
            "success": False,
            "message": "An unexpected server error occurred.",
            "error": str(e)
        }), 500
        
    # Return descriptive error page for web pages
    return f"""
    <html>
        <head>
            <title>Application Error</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; padding: 20px; text-align: center; }}
                .container {{ max-width: 500px; padding: 30px; background: #1e293b; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); border: 1px solid #334155; }}
                h1 {{ color: #ef4444; margin-top: 0; font-size: 1.5rem; }}
                p {{ color: #94a3b8; font-size: 0.95rem; line-height: 1.5; }}
                .btn {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px; font-weight: 500; transition: background 0.2s; }}
                .btn:hover {{ background: #2563eb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚠️ Something went wrong</h1>
                <p>An unexpected application error has occurred. If you are deploying this to Vercel, please make sure your database credentials (<b>SUPABASE_URL</b> and <b>SUPABASE_KEY</b>) are properly configured in Vercel Environment Variables.</p>
                <a href="/" class="btn">Return to Home</a>
            </div>
        </body>
    </html>
    """, 500


# ----------------------------------------------------
# Dynamic Logo Detection Logic
# ----------------------------------------------------
def get_logo_images():
    """
    Dynamically scans the static/images directory for files containing
    logo designations and maps primary and anniversary logos.
    """
    static_images_dir = 'static/images'
    logos = {'primary': None, 'anniversary': None}
    
    if not os.path.exists(static_images_dir):
        return logos
        
    try:
        files = os.listdir(static_images_dir)
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')
        img_files = [f for f in files if f.lower().endswith(image_extensions)]
        
        # 1. Detect Anniversary Logo
        for f in img_files:
            if 'anniversary' in f.lower():
                logos['anniversary'] = f
                break
                
        # 2. Detect Primary / Main Logo
        for f in img_files:
            if 'main' in f.lower() or 'primary' in f.lower():
                logos['primary'] = f
                break
                
        # Fallback 1: If primary not found, pick first file with 'logo'
        if not logos['primary']:
            for f in img_files:
                if 'logo' in f.lower() and f != logos['anniversary']:
                    logos['primary'] = f
                    break
                    
        # Fallback 2: Pick first image file that is not anniversary
        if not logos['primary']:
            remaining = [f for f in img_files if f != logos['anniversary']]
            if remaining:
                logos['primary'] = remaining[0]
                
    except Exception as e:
        print(f"[ERROR] Dynamic logo detection failed: {e}")
        
    return logos

# Inject logo variables into all Jinja templates automatically
@app.context_processor
def inject_logos():
    return dict(logos=get_logo_images())

# Prevent browser caching of templates and static resources
@app.after_request
def disable_browser_caching(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# ----------------------------------------------------
# Security Decorator for Session Auth
# ----------------------------------------------------
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        # Verify active session credentials
        if not session.get('logged_in') or session.get('role') not in ['super_admin', 'admin_store_head']:
            return jsonify({"success": False, "message": "Unauthorized access. Please log in."}), 401
        return f(*args, **kwargs)
    return decorated

def super_admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in') or session.get('role') not in ['super_admin', 'admin_store_head']:
            return jsonify({"success": False, "message": "Unauthorized access. Please log in."}), 401
        if session.get('role') != 'super_admin':
            return jsonify({"success": False, "message": "Access Denied: Super Admin privileges required."}), 403
        return f(*args, **kwargs)
    return decorated

def log_delete_action(delete_type, records_deleted, details=''):
    """Logs a delete action to the delete_logs audit table. Silently catches errors."""
    try:
        role = session.get('role', 'unknown')
        user_name = session.get('full_name', 'Unknown User')
        supabase = get_supabase()
        supabase.table('delete_logs').insert({
            "user_name": user_name,
            "user_role": role,
            "delete_type": delete_type,
            "records_deleted": records_deleted,
            "details": details
        }).execute()
    except Exception as e:
        app.logger.warning(f"Delete audit log failed (non-blocking): {e}")

def log_audit_action(user_name, action):
    """Logs an action to the audit_logs table. Silently catches errors."""
    try:
        supabase = get_supabase()
        ip_addr = request.remote_addr or '127.0.0.1'
        # Get date and time in local timezone/server time
        now = datetime.datetime.now()
        log_date = now.strftime('%Y-%m-%d')
        log_time = now.strftime('%H:%M:%S')
        
        supabase.table('audit_logs').insert({
            "user_name": user_name,
            "action": action,
            "log_date": log_date,
            "log_time": log_time,
            "ip_address": ip_addr
        }).execute()
    except Exception as e:
        app.logger.warning(f"Audit log failed (non-blocking): {e}")

# ----------------------------------------------------
# HTML Template Serving Routes
# ----------------------------------------------------

@app.route('/')
def route_index():
    """Serves the public customer feedback form."""
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Index route failed: {e}")
        raise e

@app.route('/admin-login')
def route_admin_login():
    """Serves the admin login. Redirects to dashboard if already logged in."""
    try:
        if session.get('logged_in') and session.get('role') in ['super_admin', 'admin_store_head']:
            return redirect('/admin-dashboard')
        return render_template('admin-login.html')
    except Exception as e:
        app.logger.error(f"Admin login route failed: {e}")
        raise e

@app.route('/admin-dashboard')
def route_admin_dashboard():
    """Serves the admin dashboard. Enforces server-side login check."""
    try:
        if not session.get('logged_in') or session.get('role') not in ['super_admin', 'admin_store_head']:
            return redirect('/admin-login')
        return render_template('admin-dashboard.html')
    except Exception as e:
        app.logger.error(f"Admin dashboard route failed: {e}")
        raise e


# ----------------------------------------------------
# Restructured REST API Endpoints
# ----------------------------------------------------

@app.route('/api/stores', methods=['GET'])
def api_get_stores():
    """Fetches list of all stores from Supabase."""
    try:
        supabase = get_supabase()
        response = supabase.table('stores').select('id, store_name').order('store_name').execute()
        return jsonify({"success": True, "data": response.data})
    except Exception as e:
        app.logger.error(f"Failed to fetch stores: {e}")
        return jsonify({"success": False, "message": "Failed to load stores database."}), 500

@app.route('/api/submit', methods=['POST'])
def api_submit():
    """Validates public submissions and saves details into Supabase."""
    try:
        data = request.json or {}
        
        store_id = data.get('store_id')
        customer_name = data.get('customer_name')
        mobile_number = data.get('mobile_number')
        app_registration_status = data.get('app_registration_status')
        invitation_issue = data.get('invitation_issue')
        issue_description = data.get('issue_description')
        
        # Validation checks
        if not store_id:
            return jsonify({"success": False, "message": "Store selection is required."}), 400
            
        if not customer_name or not str(customer_name).strip():
            return jsonify({"success": False, "message": "Customer name is required."}), 400
            
        # 10-digit numeric validation
        if not mobile_number or not re.match(r'^[0-9]{10}$', str(mobile_number).strip()):
            return jsonify({"success": False, "message": "Mobile number must be exactly 10 digits."}), 400
            
        # App Registration Status options
        valid_statuses = ['Completed', 'Pending', 'Not Interested']
        if app_registration_status not in valid_statuses:
            return jsonify({"success": False, "message": "Invalid App Registration Status value."}), 400
            
        # Issue option checking
        if invitation_issue not in ['Yes', 'No']:
            return jsonify({"success": False, "message": "Invitation card issue must be 'Yes' or 'No'."}), 400
            
        # Conditional description check
        has_issue = (invitation_issue == 'Yes')
        if has_issue and (not issue_description or not str(issue_description).strip()):
            return jsonify({"success": False, "message": "Issue description is required when an issue is reported."}), 400
            
        # DB payload definition
        db_payload = {
            "store_id": int(store_id),
            "customer_name": str(customer_name).strip(),
            "mobile_number": str(mobile_number).strip(),
            "app_registration_status": app_registration_status,
            "invitation_issue": has_issue,
            "issue_description": str(issue_description).strip() if has_issue else None
        }
        
        supabase = get_supabase()
        response = supabase.table('customer_entries').insert(db_payload).execute()
        
        if not response.data:
            return jsonify({"success": False, "message": "Failed to register submission."}), 500
            
        return jsonify({"success": True, "message": "Feedback submitted successfully!"})
        
    except ValueError:
        return jsonify({"success": False, "message": "Bad input formats received."}), 400
    except Exception as e:
        app.logger.error(f"API submit failed: {e}")
        return jsonify({"success": False, "message": "Internal server error. Submission failed."}), 500

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    """Authenticates admin credentials and stores flags in session cookie."""
    try:
        data = request.json or {}
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"success": False, "message": "Both username and password are required."}), 400
            
        supabase = get_supabase()
        response = supabase.table('users').select('*').eq('username', username.lower().strip()).execute()
        
        if response.data:
            user = response.data[0]
            from werkzeug.security import check_password_hash
            if check_password_hash(user.get('password_hash'), password):
                if user.get('status') != 'Active':
                    return jsonify({"success": False, "message": "This account is inactive. Please contact system administrator."}), 403
                    
                session.clear()
                session['logged_in'] = True
                session['user_id'] = user.get('id')
                session['username'] = user.get('username')
                session['role'] = user.get('role')
                session['full_name'] = user.get('full_name')
                session['employee_id'] = user.get('employee_id')
                session.permanent = True
                
                log_audit_action(user.get('full_name'), "User Logged In")
                
                return jsonify({"success": True, "message": "Login successful!"})
                
        return jsonify({"success": False, "message": "Invalid username or password."}), 401
    except Exception as e:
        app.logger.error(f"Login failed: {e}")
        return jsonify({"success": False, "message": "Internal authentication error."}), 500

@app.route('/api/admin/logout', methods=['POST', 'GET'])
def api_admin_logout():
    """Clears admin session parameters."""
    try:
        full_name = session.get('full_name', 'Unknown User')
        log_audit_action(full_name, "User Logged Out")
        session.clear()
        return jsonify({"success": True, "message": "Successfully logged out."})
    except Exception as e:
        app.logger.error(f"Logout failed: {e}")
        return jsonify({"success": False, "message": f"Logout failed: {str(e)}"}), 500


@app.route('/api/admin/dashboard', methods=['GET'])
@admin_required
def api_admin_dashboard():
    """Fetches overview stats counters for the dashboard metrics cards."""
    try:
        store_id = request.args.get('store_id')
        status = request.args.get('status')
        search = request.args.get('search')
        date_str = request.args.get('date')
        
        supabase = get_supabase()
        
        # Load joined store names
        query = supabase.table('customer_entries').select(
            'id, customer_name, mobile_number, app_registration_status, '
            'invitation_issue, issue_description, store_id, created_at'
        )
        
        # Apply filters
        if store_id and store_id.strip():
            query = query.eq('store_id', int(store_id))
            
        if status and status.strip():
            query = query.eq('app_registration_status', status)
            
        if search and search.strip():
            search_str = search.strip()
            query = query.or_(f"customer_name.ilike.%{search_str}%,mobile_number.ilike.%{search_str}%")
            
        if date_str and date_str.strip():
            query = query.gte('created_at', f"{date_str}T00:00:00Z").lte('created_at', f"{date_str}T23:59:59Z")
            
        response = query.execute()
        
        total = len(response.data)
        completed = sum(1 for x in response.data if x.get('app_registration_status') == 'Completed')
        pending = sum(1 for x in response.data if x.get('app_registration_status') == 'Pending')
        not_interested = sum(1 for x in response.data if x.get('app_registration_status') == 'Not Interested')
        issues = sum(1 for x in response.data if x.get('invitation_issue') is True)
        
        stats = {
            "total": total,
            "completed": completed,
            "pending": pending,
            "not_interested": not_interested,
            "issues": issues,
            "branches": 13
        }
        
        user_role = session.get('role')
        user_name = session.get('full_name', 'Unknown User')
        
        return jsonify({
            "success": True, 
            "stats": stats,
            "user": {
                "role": user_role,
                "name": user_name
            }
        })
    except Exception as e:
        app.logger.error(f"Dashboard metrics query failed: {e}")
        return jsonify({"success": False, "message": "Failed to compile dashboard metrics."}), 500

@app.route('/api/admin/settings', methods=['GET', 'POST'])
@admin_required
def api_admin_settings():
    """Mockup route for system settings configuration to verify Role-Based Access Control."""
    try:
        if session.get('role') != 'super_admin':
            return jsonify({"success": False, "message": "Access Denied: Super Admin privileges required."}), 403
        return jsonify({"success": True, "message": "Super Admin system configuration settings accessed successfully."})
    except Exception as e:
        app.logger.error(f"Settings config endpoint failed: {e}")
        return jsonify({"success": False, "message": f"Settings access failed: {str(e)}"}), 500


@app.route('/api/admin/customers', methods=['GET'])
@admin_required
def api_admin_customers():
    """Retrieves customer entries matching filter parameters."""
    try:
        store_id = request.args.get('store_id')
        status = request.args.get('status')
        search = request.args.get('search')
        date_str = request.args.get('date')
        
        supabase = get_supabase()
        
        # Load joined store names
        query = supabase.table('customer_entries').select(
            'id, customer_name, mobile_number, app_registration_status, '
            'invitation_issue, issue_description, created_at, '
            'stores(id, store_name)'
        )
        
        # Apply filters
        if store_id and store_id.strip():
            query = query.eq('store_id', int(store_id))
            
        if status and status.strip():
            query = query.eq('app_registration_status', status)
            
        if search and search.strip():
            search_str = search.strip()
            query = query.or_(f"customer_name.ilike.%{search_str}%,mobile_number.ilike.%{search_str}%")
            
        if date_str and date_str.strip():
            query = query.gte('created_at', f"{date_str}T00:00:00Z").lte('created_at', f"{date_str}T23:59:59Z")
            
        query = query.order('created_at', desc=True)
        response = query.execute()
        
        # Format rows for frontend tables mapping
        formatted_list = []
        for row in response.data:
            store_obj = row.get('stores') or {}
            formatted_list.append({
                "id": row.get('id'),
                "customer_name": row.get('customer_name'),
                "mobile_number": row.get('mobile_number'),
                "app_registration_status": row.get('app_registration_status'),
                "invitation_issue": "Yes" if row.get('invitation_issue') else "No",
                "issue_description": row.get('issue_description') or "",
                "store_name": store_obj.get('store_name', 'Unknown Store'),
                "created_at": row.get('created_at')
            })
            
        return jsonify({"success": True, "data": formatted_list})
        
    except Exception as e:
        app.logger.error(f"Fetch customers API failed: {e}")
        return jsonify({"success": False, "message": "Failed to query customer logs."}), 500

@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def api_admin_stats():
    """Generates statistics and analytics metrics for the dashboard charts and overview cards."""
    try:
        supabase = get_supabase()
        
        # Helper date parser
        def parse_created_at_date(dt_str):
            if not dt_str:
                return None
            try:
                return datetime.datetime.strptime(dt_str.split('T')[0], "%Y-%m-%d").date()
            except Exception:
                return None

        # Get query parameters for custom filtering
        filter_store_id = request.args.get('store_id')
        filter_date = request.args.get('date')
        filter_start_date = request.args.get('start_date')
        filter_end_date = request.args.get('end_date')
        
        # Fetch all stores and entries
        stores_resp = supabase.table('stores').select('id, store_name').order('store_name').execute()
        stores_list = stores_resp.data or []
        
        entries_resp = supabase.table('customer_entries').select('id, store_id, customer_name, mobile_number, app_registration_status, invitation_issue, issue_description, created_at').execute()
        entries_list = entries_resp.data or []
        
        total_customers = len(entries_list)
        today_date = datetime.date.today()
        todays_customers = 0
        
        day_counts = {}
        store_stats = {s['id']: {
            "store_name": s['store_name'],
            "total_customers": 0,
            "todays_customers": 0,
            "completed": 0,
            "pending": 0,
            "not_interested": 0,
            "invitation_issues": 0
        } for s in stores_list}
        
        for entry in entries_list:
            created_at = entry.get('created_at')
            entry_date = parse_created_at_date(created_at)
            
            is_today = (entry_date == today_date)
            if is_today:
                todays_customers += 1
                
            if entry_date:
                d_str = entry_date.isoformat()
                day_counts[d_str] = day_counts.get(d_str, 0) + 1
                
            sid = entry.get('store_id')
            if sid in store_stats:
                store_stats[sid]["total_customers"] += 1
                if is_today:
                    store_stats[sid]["todays_customers"] += 1
                    
                status = entry.get('app_registration_status')
                if status == 'Completed':
                    store_stats[sid]["completed"] += 1
                elif status == 'Pending':
                    store_stats[sid]["pending"] += 1
                elif status == 'Not Interested':
                    store_stats[sid]["not_interested"] += 1
                    
                if entry.get('invitation_issue') is True:
                    store_stats[sid]["invitation_issues"] += 1
                    
        # Day-wise list sorted chronologically
        day_wise_customers = []
        for d_str in sorted(day_counts.keys()):
            day_wise_customers.append({
                "date": d_str,
                "total_customers": day_counts[d_str]
            })
            
        store_wise_customers = list(store_stats.values())
        
        # Apply filters to compute store_day_wise_customers count
        filtered_entries = entries_list
        if filter_store_id and filter_store_id.strip():
            filtered_entries = [e for e in filtered_entries if e.get('store_id') == int(filter_store_id)]
            
        if filter_date and filter_date.strip():
            try:
                f_date = datetime.datetime.strptime(filter_date.strip(), "%Y-%m-%d").date()
                filtered_entries = [e for e in filtered_entries if parse_created_at_date(e.get('created_at')) == f_date]
            except Exception:
                pass
        elif filter_start_date and filter_start_date.strip() and filter_end_date and filter_end_date.strip():
            try:
                f_start = datetime.datetime.strptime(filter_start_date.strip(), "%Y-%m-%d").date()
                f_end = datetime.datetime.strptime(filter_end_date.strip(), "%Y-%m-%d").date()
                filtered_entries = [e for e in filtered_entries if f_start <= parse_created_at_date(e.get('created_at')) <= f_end]
            except Exception:
                pass
                
        store_day_wise_customers = {
            "count": len(filtered_entries)
        }
        
        return jsonify({
            "success": True,
            "total_customers": total_customers,
            "todays_customers": todays_customers,
            "day_wise_customers": day_wise_customers,
            "store_wise_customers": store_wise_customers,
            "store_day_wise_customers": store_day_wise_customers
        })
    except Exception as e:
        app.logger.error(f"Stats compilation API failed: {e}")
        return jsonify({"success": False, "message": "Failed to compile stats."}), 500

@app.route('/api/admin/customer/<int:customer_id>', methods=['PUT'])
@super_admin_required
def api_update_customer(customer_id):
    """Updates a customer entry. Resilient to missing updated_at column."""
    try:
        data = request.json or {}
        store_id = data.get('store_id')
        customer_name = data.get('customer_name')
        mobile_number = data.get('mobile_number')
        app_registration_status = data.get('app_registration_status')
        invitation_issue = data.get('invitation_issue')
        issue_description = data.get('issue_description')
        
        if not store_id:
            return jsonify({"success": False, "message": "Store selection is required."}), 400
        if not customer_name or not str(customer_name).strip():
            return jsonify({"success": False, "message": "Customer name is required."}), 400
        if not mobile_number or not re.match(r'^[0-9]{10}$', str(mobile_number).strip()):
            return jsonify({"success": False, "message": "Mobile number must be exactly 10 digits."}), 400
        if app_registration_status not in ['Completed', 'Pending', 'Not Interested']:
            return jsonify({"success": False, "message": "Invalid App Registration Status."}), 400
            
        has_issue = (invitation_issue == 'Yes' or invitation_issue is True)
        if has_issue and (not issue_description or not str(issue_description).strip()):
            return jsonify({"success": False, "message": "Issue description is required when an issue is reported."}), 400
            
        db_payload = {
            "store_id": int(store_id),
            "customer_name": str(customer_name).strip(),
            "mobile_number": str(mobile_number).strip(),
            "app_registration_status": app_registration_status,
            "invitation_issue": has_issue,
            "issue_description": str(issue_description).strip() if has_issue else None,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        supabase = get_supabase()
        try:
            response = supabase.table('customer_entries').update(db_payload.copy()).eq('id', customer_id).execute()
        except Exception as db_err:
            db_err_str = str(db_err).lower()
            if 'column' in db_err_str and 'updated_at' in db_err_str:
                # Fallback: Retry database update without updated_at column
                fallback_payload = db_payload.copy()
                fallback_payload.pop('updated_at', None)
                response = supabase.table('customer_entries').update(fallback_payload).eq('id', customer_id).execute()
            else:
                raise db_err
                
        if not response.data:
            return jsonify({"success": False, "message": "Customer entry not found or update failed."}), 404
            
        return jsonify({"success": True, "message": "Customer entry updated successfully!"})
    except Exception as e:
        app.logger.error(f"Failed to update customer: {e}")
        return jsonify({"success": False, "message": f"Update failed: {str(e)}"}), 500

@app.route('/api/admin/customer/<int:customer_id>', methods=['DELETE'])
@super_admin_required
def api_delete_customer(customer_id):
    """Deletes a specific customer entry. Available to both roles."""
    try:
        supabase = get_supabase()
        # Fetch entry details for audit log
        entry_resp = supabase.table('customer_entries').select('id, customer_name, stores(store_name)').eq('id', customer_id).execute()
        entry_detail = ''
        if entry_resp.data:
            row = entry_resp.data[0]
            store_obj = row.get('stores') or {}
            entry_detail = f"Customer: {row.get('customer_name', 'N/A')}, Store: {store_obj.get('store_name', 'N/A')}"
        
        response = supabase.table('customer_entries').delete().eq('id', customer_id).execute()
        if not response.data:
            return jsonify({"success": False, "message": "Customer entry not found or delete failed."}), 404
        
        log_delete_action('individual', 1, entry_detail)
        return jsonify({"success": True, "message": "Customer entry deleted successfully!", "records_deleted": 1})
    except Exception as e:
        app.logger.error(f"Failed to delete customer entry: {e}")
        return jsonify({"success": False, "message": f"Delete failed: {str(e)}"}), 500

# ----------------------------------------------------
# Data Management - Advanced Bulk Delete API Suite
# ----------------------------------------------------

@app.route('/api/admin/delete/preview', methods=['GET'])
@super_admin_required
def api_delete_preview():
    """Preview: counts records matching the given filter parameters before deletion."""
    try:
        delete_type = request.args.get('type', '')
        store_id = request.args.get('store_id')
        date_str = request.args.get('date')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        supabase = get_supabase()
        query = supabase.table('customer_entries').select('id, store_id, created_at')
        
        today_str = datetime.date.today().isoformat()
        
        if delete_type == 'today':
            query = query.gte('created_at', f"{today_str}T00:00:00Z").lte('created_at', f"{today_str}T23:59:59Z")
        elif delete_type == 'date' and date_str:
            query = query.gte('created_at', f"{date_str}T00:00:00Z").lte('created_at', f"{date_str}T23:59:59Z")
        elif delete_type == 'date_range' and start_date and end_date:
            query = query.gte('created_at', f"{start_date}T00:00:00Z").lte('created_at', f"{end_date}T23:59:59Z")
        elif delete_type == 'store' and store_id:
            query = query.eq('store_id', int(store_id))
        elif delete_type == 'store_date' and store_id and date_str:
            query = query.eq('store_id', int(store_id)).gte('created_at', f"{date_str}T00:00:00Z").lte('created_at', f"{date_str}T23:59:59Z")
        elif delete_type == 'store_range' and store_id and start_date and end_date:
            query = query.eq('store_id', int(store_id)).gte('created_at', f"{start_date}T00:00:00Z").lte('created_at', f"{end_date}T23:59:59Z")
        elif delete_type == 'all':
            pass  # No filter — count all
        else:
            return jsonify({"success": False, "message": "Invalid or missing preview parameters."}), 400
            
        response = query.execute()
        records = response.data or []
        store_ids_affected = list(set(r.get('store_id') for r in records if r.get('store_id')))
        
        return jsonify({
            "success": True,
            "records_count": len(records),
            "stores_affected": len(store_ids_affected),
            "date": today_str if delete_type == 'today' else (date_str or ''),
            "delete_type": delete_type
        })
    except Exception as e:
        app.logger.error(f"Delete preview failed: {e}")
        return jsonify({"success": False, "message": f"Preview failed: {str(e)}"}), 500

@app.route('/api/admin/delete/today', methods=['DELETE'])
@super_admin_required
def api_delete_today():
    """Delete all customer entries submitted today."""
    try:
        supabase = get_supabase()
        today_str = datetime.date.today().isoformat()
        
        # Count first
        count_resp = supabase.table('customer_entries').select('id').gte('created_at', f"{today_str}T00:00:00Z").lte('created_at', f"{today_str}T23:59:59Z").execute()
        count = len(count_resp.data or [])
        
        if count == 0:
            return jsonify({"success": True, "message": "No records found for today.", "records_deleted": 0})
        
        supabase.table('customer_entries').delete().gte('created_at', f"{today_str}T00:00:00Z").lte('created_at', f"{today_str}T23:59:59Z").execute()
        
        log_delete_action('today', count, f"Date: {today_str}")
        return jsonify({"success": True, "message": f"Deleted {count} records from today ({today_str}).", "records_deleted": count})
    except Exception as e:
        app.logger.error(f"Delete today failed: {e}")
        return jsonify({"success": False, "message": f"Delete failed: {str(e)}"}), 500

@app.route('/api/admin/delete/date/<date_str>', methods=['DELETE'])
@super_admin_required
def api_delete_by_date(date_str):
    """Delete all customer entries for a specific date."""
    try:
        # Validate date format
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        
        supabase = get_supabase()
        count_resp = supabase.table('customer_entries').select('id').gte('created_at', f"{date_str}T00:00:00Z").lte('created_at', f"{date_str}T23:59:59Z").execute()
        count = len(count_resp.data or [])
        
        if count == 0:
            return jsonify({"success": True, "message": f"No records found for {date_str}.", "records_deleted": 0})
        
        supabase.table('customer_entries').delete().gte('created_at', f"{date_str}T00:00:00Z").lte('created_at', f"{date_str}T23:59:59Z").execute()
        
        log_delete_action('date', count, f"Date: {date_str}")
        return jsonify({"success": True, "message": f"Deleted {count} records from {date_str}.", "records_deleted": count})
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format. Use YYYY-MM-DD."}), 400
    except Exception as e:
        app.logger.error(f"Delete by date failed: {e}")
        return jsonify({"success": False, "message": f"Delete failed: {str(e)}"}), 500

@app.route('/api/admin/delete/date-range', methods=['DELETE'])
@super_admin_required
def api_delete_date_range():
    """Delete all customer entries within a date range."""
    try:
        data = request.json or {}
        start_date = data.get('start_date') or request.args.get('start_date')
        end_date = data.get('end_date') or request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({"success": False, "message": "Both start_date and end_date are required."}), 400
        
        datetime.datetime.strptime(start_date, "%Y-%m-%d")
        datetime.datetime.strptime(end_date, "%Y-%m-%d")
        
        supabase = get_supabase()
        count_resp = supabase.table('customer_entries').select('id').gte('created_at', f"{start_date}T00:00:00Z").lte('created_at', f"{end_date}T23:59:59Z").execute()
        count = len(count_resp.data or [])
        
        if count == 0:
            return jsonify({"success": True, "message": f"No records found between {start_date} and {end_date}.", "records_deleted": 0})
        
        supabase.table('customer_entries').delete().gte('created_at', f"{start_date}T00:00:00Z").lte('created_at', f"{end_date}T23:59:59Z").execute()
        
        log_delete_action('date_range', count, f"Range: {start_date} to {end_date}")
        return jsonify({"success": True, "message": f"Deleted {count} records from {start_date} to {end_date}.", "records_deleted": count})
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format. Use YYYY-MM-DD."}), 400
    except Exception as e:
        app.logger.error(f"Delete date range failed: {e}")
        return jsonify({"success": False, "message": f"Delete failed: {str(e)}"}), 500

@app.route('/api/admin/delete/store/<int:store_id>', methods=['DELETE'])
@super_admin_required
def api_delete_by_store(store_id):
    """Delete all customer entries for a specific store."""
    try:
        supabase = get_supabase()
        
        # Get store name for logging
        store_resp = supabase.table('stores').select('store_name').eq('id', store_id).execute()
        store_name = store_resp.data[0]['store_name'] if store_resp.data else f"Store ID {store_id}"
        
        count_resp = supabase.table('customer_entries').select('id').eq('store_id', store_id).execute()
        count = len(count_resp.data or [])
        
        if count == 0:
            return jsonify({"success": True, "message": f"No records found for {store_name}.", "records_deleted": 0})
        
        supabase.table('customer_entries').delete().eq('store_id', store_id).execute()
        
        log_delete_action('store', count, f"Store: {store_name}")
        return jsonify({"success": True, "message": f"Deleted {count} records from {store_name}.", "records_deleted": count})
    except Exception as e:
        app.logger.error(f"Delete by store failed: {e}")
        return jsonify({"success": False, "message": f"Delete failed: {str(e)}"}), 500

@app.route('/api/admin/delete/store-date', methods=['DELETE'])
@super_admin_required
def api_delete_store_date():
    """Delete entries for a specific store on a specific date."""
    try:
        data = request.json or {}
        store_id = data.get('store_id') or request.args.get('store_id')
        date_str = data.get('date') or request.args.get('date')
        
        if not store_id or not date_str:
            return jsonify({"success": False, "message": "Both store_id and date are required."}), 400
        
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        store_id = int(store_id)
        
        supabase = get_supabase()
        store_resp = supabase.table('stores').select('store_name').eq('id', store_id).execute()
        store_name = store_resp.data[0]['store_name'] if store_resp.data else f"Store ID {store_id}"
        
        count_resp = supabase.table('customer_entries').select('id').eq('store_id', store_id).gte('created_at', f"{date_str}T00:00:00Z").lte('created_at', f"{date_str}T23:59:59Z").execute()
        count = len(count_resp.data or [])
        
        if count == 0:
            return jsonify({"success": True, "message": f"No records found for {store_name} on {date_str}.", "records_deleted": 0})
        
        supabase.table('customer_entries').delete().eq('store_id', store_id).gte('created_at', f"{date_str}T00:00:00Z").lte('created_at', f"{date_str}T23:59:59Z").execute()
        
        log_delete_action('store_date', count, f"Store: {store_name}, Date: {date_str}")
        return jsonify({"success": True, "message": f"Deleted {count} records from {store_name} on {date_str}.", "records_deleted": count})
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format. Use YYYY-MM-DD."}), 400
    except Exception as e:
        app.logger.error(f"Delete store+date failed: {e}")
        return jsonify({"success": False, "message": f"Delete failed: {str(e)}"}), 500

@app.route('/api/admin/delete/store-range', methods=['DELETE'])
@super_admin_required
def api_delete_store_range():
    """Delete entries for a specific store within a date range."""
    try:
        data = request.json or {}
        store_id = data.get('store_id') or request.args.get('store_id')
        start_date = data.get('start_date') or request.args.get('start_date')
        end_date = data.get('end_date') or request.args.get('end_date')
        
        if not store_id or not start_date or not end_date:
            return jsonify({"success": False, "message": "store_id, start_date, and end_date are required."}), 400
        
        datetime.datetime.strptime(start_date, "%Y-%m-%d")
        datetime.datetime.strptime(end_date, "%Y-%m-%d")
        store_id = int(store_id)
        
        supabase = get_supabase()
        store_resp = supabase.table('stores').select('store_name').eq('id', store_id).execute()
        store_name = store_resp.data[0]['store_name'] if store_resp.data else f"Store ID {store_id}"
        
        count_resp = supabase.table('customer_entries').select('id').eq('store_id', store_id).gte('created_at', f"{start_date}T00:00:00Z").lte('created_at', f"{end_date}T23:59:59Z").execute()
        count = len(count_resp.data or [])
        
        if count == 0:
            return jsonify({"success": True, "message": f"No records found for {store_name} between {start_date} and {end_date}.", "records_deleted": 0})
        
        supabase.table('customer_entries').delete().eq('store_id', store_id).gte('created_at', f"{start_date}T00:00:00Z").lte('created_at', f"{end_date}T23:59:59Z").execute()
        
        log_delete_action('store_range', count, f"Store: {store_name}, Range: {start_date} to {end_date}")
        return jsonify({"success": True, "message": f"Deleted {count} records from {store_name} ({start_date} to {end_date}).", "records_deleted": count})
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format. Use YYYY-MM-DD."}), 400
    except Exception as e:
        app.logger.error(f"Delete store+range failed: {e}")
        return jsonify({"success": False, "message": f"Delete failed: {str(e)}"}), 500

@app.route('/api/admin/delete/all', methods=['DELETE'])
@super_admin_required
def api_delete_all():
    """Delete ALL customer entries. Requires confirm='DELETE ALL' in request body."""
    try:
        data = request.json or {}
        confirm = data.get('confirm', '')
        
        if confirm != 'DELETE ALL':
            return jsonify({"success": False, "message": "Confirmation required. Send confirm='DELETE ALL' in request body."}), 400
        
        supabase = get_supabase()
        count_resp = supabase.table('customer_entries').select('id').execute()
        count = len(count_resp.data or [])
        
        if count == 0:
            return jsonify({"success": True, "message": "No records to delete.", "records_deleted": 0})
        
        supabase.table('customer_entries').delete().neq('id', 0).execute()
        
        log_delete_action('all', count, f"Purged all {count} customer entries")
        return jsonify({"success": True, "message": f"All {count} customer entries deleted successfully!", "records_deleted": count})
    except Exception as e:
        app.logger.error(f"Delete all failed: {e}")
        return jsonify({"success": False, "message": f"Bulk delete failed: {str(e)}"}), 500

@app.route('/api/admin/delete/logs', methods=['GET'])
@super_admin_required
def api_delete_logs():
    """Fetch recent delete audit logs."""
    try:
        supabase = get_supabase()
        response = supabase.table('delete_logs').select('*').order('created_at', desc=True).limit(50).execute()
        logs = []
        for log in (response.data or []):
            logs.append({
                "id": log.get('id'),
                "user_name": log.get('user_name'),
                "user_role": log.get('user_role'),
                "delete_type": log.get('delete_type'),
                "records_deleted": log.get('records_deleted'),
                "details": log.get('details'),
                "created_at": log.get('created_at')
            })
        return jsonify({"success": True, "data": logs})
    except Exception as e:
        app.logger.error(f"Fetch delete logs failed: {e}")
        return jsonify({"success": True, "data": [], "message": "Delete logs table may not exist yet."})

# Legacy endpoint kept for backwards compatibility
@app.route('/api/admin/customers/delete-all', methods=['DELETE'])
@super_admin_required
def api_delete_all_customers_legacy():
    """Legacy endpoint. Redirects logic to new delete-all."""
    try:
        supabase = get_supabase()
        count_resp = supabase.table('customer_entries').select('id').execute()
        count = len(count_resp.data or [])
        supabase.table('customer_entries').delete().neq('id', 0).execute()
        log_delete_action('all', count, 'Legacy delete-all endpoint')
        return jsonify({"success": True, "message": "All customer entries deleted successfully!", "records_deleted": count})
    except Exception as e:
        app.logger.error(f"Legacy delete all failed: {e}")
        return jsonify({"success": False, "message": f"Bulk delete failed: {str(e)}"}), 500


@app.route('/api/admin/export', methods=['GET'])
@admin_required
def api_admin_export():
    """Generates and streams a CSV of filtered customer entries."""
        
    try:
        store_id = request.args.get('store_id')
        status = request.args.get('status')
        search = request.args.get('search')
        date_str = request.args.get('date')
        
        supabase = get_supabase()
        query = supabase.table('customer_entries').select(
            'id, customer_name, mobile_number, app_registration_status, '
            'invitation_issue, issue_description, created_at, '
            'stores(id, store_name)'
        )
        
        if store_id and store_id.strip():
            query = query.eq('store_id', int(store_id))
            
        if status and status.strip():
            query = query.eq('app_registration_status', status)
            
        if search and search.strip():
            search_str = search.strip()
            query = query.or_(f"customer_name.ilike.%{search_str}%,mobile_number.ilike.%{search_str}%")
            
        if date_str and date_str.strip():
            query = query.gte('created_at', f"{date_str}T00:00:00Z").lte('created_at', f"{date_str}T23:59:59Z")
            
        query = query.order('created_at', desc=True)
        response = query.execute()
        
        # Build CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
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
                "Yes" if row.get('invitation_issue') else "No",
                row.get('issue_description') or "",
                row.get('created_at')
            ])
            
        output.seek(0)
        csv_data = output.getvalue()
        
        filename = f"submissions_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        app.logger.error(f"CSV export failed: {e}")
        return "Internal server error generating CSV export.", 500

@app.route('/api/admin/export-excel', methods=['GET'])
@admin_required
def api_admin_export_excel():
    """Generates and streams an Excel workbook with multiple worksheets and premium formatting."""
        
    try:
        store_id = request.args.get('store_id')
        status = request.args.get('status')
        search = request.args.get('search')
        date_str = request.args.get('date')
        
        supabase = get_supabase()
        
        # 1. Fetch entries matching the filter
        query = supabase.table('customer_entries').select(
            'id, customer_name, mobile_number, app_registration_status, '
            'invitation_issue, issue_description, store_id, created_at, '
            'stores(id, store_name)'
        )
        
        if store_id and store_id.strip():
            query = query.eq('store_id', int(store_id))
            
        if status and status.strip():
            query = query.eq('app_registration_status', status)
            
        if search and search.strip():
            search_str = search.strip()
            query = query.or_(f"customer_name.ilike.%{search_str}%,mobile_number.ilike.%{search_str}%")
            
        if date_str and date_str.strip():
            query = query.gte('created_at', f"{date_str}T00:00:00Z").lte('created_at', f"{date_str}T23:59:59Z")
            
        response = query.execute()
        entries = response.data or []
        
        def get_store_name(entry):
            store_obj = entry.get('stores') or {}
            return store_obj.get('store_name', 'Unknown Store')
            
        # Sort store-wise (alphabetical), then by created_at desc
        entries.sort(key=lambda x: (get_store_name(x).lower(), x.get('created_at') or ''))
        
        # 2. Fetch all stores (for Sheet 2 summary)
        stores_resp = supabase.table('stores').select('*').order('store_name').execute()
        stores_list = stores_resp.data or []
        
        # Create workbook
        wb = Workbook()
        
        # Sheet 1: All Submissions
        ws1 = wb.active
        ws1.title = "All Submissions"
        
        # Sheet 2: Store Wise Summary
        ws2 = wb.create_sheet(title="Store Wise Summary")
        
        # Sheet 3: Registration Status Summary
        ws3 = wb.create_sheet(title="Registration Status Summary")
        
        # Style definition
        font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        fill_header = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid") # Deep corporate blue
        align_header = Alignment(horizontal="center", vertical="center", wrap_text=True)
        align_left = Alignment(horizontal="left", vertical="center")
        align_center = Alignment(horizontal="center", vertical="center")
        border_thin = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )
        
        # Write Sheet 1
        headers1 = [
            'Submission ID', 
            'Store Name', 
            'Customer Name', 
            'Mobile Number', 
            'App Registration Status', 
            'Invitation Card Issue', 
            'Issue Description', 
            'Created At'
        ]
        
        ws1.append(headers1)
        for col_idx, header in enumerate(headers1, 1):
            cell = ws1.cell(row=1, column=col_idx)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = align_header
            
        for row_idx, entry in enumerate(entries, 2):
            store_name = get_store_name(entry)
            cust_name = str(entry.get('customer_name') or '').strip()
            mobile = str(entry.get('mobile_number') or '').strip()
            status_val = entry.get('app_registration_status')
            has_issue = "Yes" if entry.get('invitation_issue') else "No"
            issue_desc = str(entry.get('issue_description') or '').strip()
            if not entry.get('invitation_issue') or not issue_desc:
                issue_desc = "No Issue"
                
            created_at_val = entry.get('created_at')
            if created_at_val:
                try:
                    dt_str = created_at_val.split('.')[0].replace('T', ' ').split('+')[0]
                    created_at_formatted = dt_str
                except Exception:
                    created_at_formatted = created_at_val
            else:
                created_at_formatted = ""
                
            row_data = [
                entry.get('id'),
                store_name,
                cust_name,
                mobile,
                status_val,
                has_issue,
                issue_desc,
                created_at_formatted
            ]
            ws1.append(row_data)
            
            for col_idx in range(1, len(row_data) + 1):
                cell = ws1.cell(row=row_idx, column=col_idx)
                cell.border = border_thin
                if col_idx in [1, 4, 5, 6, 8]:
                    cell.alignment = align_center
                else:
                    cell.alignment = align_left
                    
                if col_idx == 4:
                    cell.number_format = '@'
                    
        ws1.freeze_panes = 'A2'
        
        # Write Sheet 2: Store Wise Summary
        headers2 = [
            'Store Name',
            'Total Submissions',
            'Completed Registrations',
            'Pending Registrations',
            'Not Interested',
            'Invitation Issues'
        ]
        ws2.append(headers2)
        for col_idx, header in enumerate(headers2, 1):
            cell = ws2.cell(row=1, column=col_idx)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = align_header
            
        # Build stores stats map
        store_stats = {}
        for s in stores_list:
            store_stats[s['id']] = {
                'store_name': s['store_name'],
                'total': 0,
                'completed': 0,
                'pending': 0,
                'not_interested': 0,
                'issues': 0
            }
            
        for entry in entries:
            sid = entry.get('store_id')
            if sid in store_stats:
                store_stats[sid]['total'] += 1
                reg_status = entry.get('app_registration_status')
                if reg_status == 'Completed':
                    store_stats[sid]['completed'] += 1
                elif reg_status == 'Pending':
                    store_stats[sid]['pending'] += 1
                elif reg_status == 'Not Interested':
                    store_stats[sid]['not_interested'] += 1
                    
                if entry.get('invitation_issue'):
                    store_stats[sid]['issues'] += 1
                    
        for row_idx, s in enumerate(stores_list, 2):
            stats = store_stats[s['id']]
            row_data = [
                stats['store_name'],
                stats['total'],
                stats['completed'],
                stats['pending'],
                stats['not_interested'],
                stats['issues']
            ]
            ws2.append(row_data)
            
            for col_idx in range(1, len(row_data) + 1):
                cell = ws2.cell(row=row_idx, column=col_idx)
                cell.border = border_thin
                if col_idx == 1:
                    cell.alignment = align_left
                else:
                    cell.alignment = align_center
                    
        ws2.freeze_panes = 'A2'
        
        # Write Sheet 3: Registration Status Summary
        headers3 = [
            'App Registration Status',
            'Count',
            'Percentage'
        ]
        ws3.append(headers3)
        for col_idx, header in enumerate(headers3, 1):
            cell = ws3.cell(row=1, column=col_idx)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = align_header
            
        total_all = len(entries)
        status_counts = {
            'Completed': sum(1 for e in entries if e.get('app_registration_status') == 'Completed'),
            'Pending': sum(1 for e in entries if e.get('app_registration_status') == 'Pending'),
            'Not Interested': sum(1 for e in entries if e.get('app_registration_status') == 'Not Interested')
        }
        
        statuses = ['Completed', 'Pending', 'Not Interested']
        for row_idx, stat_name in enumerate(statuses, 2):
            count = status_counts[stat_name]
            pct = f"{(count / total_all * 100):.2f}%" if total_all > 0 else "0.00%"
            row_data = [stat_name, count, pct]
            ws3.append(row_data)
            
            for col_idx in range(1, len(row_data) + 1):
                cell = ws3.cell(row=row_idx, column=col_idx)
                cell.border = border_thin
                if col_idx == 1:
                    cell.alignment = align_left
                else:
                    cell.alignment = align_center
                    
        total_row_idx = 5
        ws3.append(['Total', total_all, '100.00%' if total_all > 0 else '0.00%'])
        for col_idx in range(1, 4):
            cell = ws3.cell(row=total_row_idx, column=col_idx)
            cell.font = Font(name="Calibri", size=11, bold=True)
            cell.border = border_thin
            if col_idx == 1:
                cell.alignment = align_left
            else:
                cell.alignment = align_center
                
        ws3.freeze_panes = 'A2'
        
        for ws in [ws1, ws2, ws3]:
            for col in ws.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col:
                    if cell.value is not None:
                        max_len = max(max_len, len(str(cell.value)))
                ws.column_dimensions[col_letter].width = max(max_len + 3, 10)
                
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        excel_data = output.getvalue()
        
        filename = f"team_saddam_zone_data_{datetime.date.today().strftime('%Y-%m-%d')}.xlsx"
        
        return Response(
            excel_data,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        app.logger.error(f"Excel export failed: {e}")
        return "Internal server error generating Excel export.", 500

# ----------------------------------------------------
# Super Admin User Management API Suite
# ----------------------------------------------------

@app.route('/api/users', methods=['POST'])
@super_admin_required
def api_create_user():
    """Create a new user. Super Admin only."""
    try:
        data = request.json or {}
        full_name = data.get('full_name')
        employee_id = data.get('employee_id')
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        status = data.get('status', 'Active')
        
        if not all([full_name, employee_id, username, password, role]):
            return jsonify({"success": False, "message": "All fields are required."}), 400
            
        if role not in ['super_admin', 'admin_store_head']:
            return jsonify({"success": False, "message": "Invalid role specified."}), 400
            
        if status not in ['Active', 'Inactive']:
            return jsonify({"success": False, "message": "Invalid status specified."}), 400
            
        from werkzeug.security import generate_password_hash
        
        supabase = get_supabase()
        
        # Check if username or employee_id already exists
        check_username = supabase.table('users').select('id').eq('username', username.lower().strip()).execute()
        if check_username.data:
            return jsonify({"success": False, "message": "Username already exists."}), 400
            
        check_emp = supabase.table('users').select('id').eq('employee_id', employee_id.strip()).execute()
        if check_emp.data:
            return jsonify({"success": False, "message": "Employee ID already exists."}), 400
            
        db_payload = {
            "full_name": str(full_name).strip(),
            "employee_id": str(employee_id).strip(),
            "username": str(username).strip().lower(),
            "password_hash": generate_password_hash(password),
            "role": role,
            "status": status
        }
        
        response = supabase.table('users').insert(db_payload).execute()
        if not response.data:
            return jsonify({"success": False, "message": "Failed to create user."}), 500
            
        admin_name = session.get('full_name', 'Super Admin')
        log_audit_action(admin_name, f"Created User: {full_name} ({employee_id})")
        
        return jsonify({"success": True, "message": "User created successfully!", "data": response.data[0]})
    except Exception as e:
        app.logger.error(f"Create user failed: {e}")
        return jsonify({"success": False, "message": f"Failed to create user: {str(e)}"}), 500


@app.route('/api/users', methods=['GET'])
@super_admin_required
def api_get_users():
    """Get all users, supports search, filter, and pagination. Super Admin only."""
    try:
        search = request.args.get('search')
        role = request.args.get('role')
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        supabase = get_supabase()
        query = supabase.table('users').select('*')
        
        # Apply filters
        if role and role.strip():
            query = query.eq('role', role)
            
        if status and status.strip():
            query = query.eq('status', status)
            
        if search and search.strip():
            search_str = search.strip()
            query = query.or_(f"full_name.ilike.%{search_str}%,employee_id.ilike.%{search_str}%,username.ilike.%{search_str}%")
            
        query = query.order('created_at', desc=True)
        response = query.execute()
        
        all_users = response.data or []
        
        # Client-side style pagination in Python
        total = len(all_users)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_users = all_users[start_idx:end_idx]
        
        # Exclude password hashes from response data
        for u in paginated_users:
            u.pop('password_hash', None)
            
        return jsonify({
            "success": True,
            "data": paginated_users,
            "total": total,
            "page": page,
            "page_size": page_size
        })
    except Exception as e:
        app.logger.error(f"Fetch users failed: {e}")
        return jsonify({"success": False, "message": f"Failed to fetch users: {str(e)}"}), 500


@app.route('/api/users/<int:user_id>', methods=['GET'])
@super_admin_required
def api_get_user_detail(user_id):
    """Get detailed view of a user. Super Admin only."""
    try:
        supabase = get_supabase()
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        if not response.data:
            return jsonify({"success": False, "message": "User not found."}), 404
            
        user = response.data[0]
        user.pop('password_hash', None)
        return jsonify({"success": True, "data": user})
    except Exception as e:
        app.logger.error(f"Fetch user details failed: {e}")
        return jsonify({"success": False, "message": f"Failed to load user details: {str(e)}"}), 500


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@super_admin_required
def api_update_user(user_id):
    """Update user details. Super Admin only."""
    try:
        data = request.json or {}
        full_name = data.get('full_name')
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        status = data.get('status')
        
        if not all([full_name, username, role, status]):
            return jsonify({"success": False, "message": "Missing required fields."}), 400
            
        if role not in ['super_admin', 'admin_store_head']:
            return jsonify({"success": False, "message": "Invalid role."}), 400
            
        if status not in ['Active', 'Inactive']:
            return jsonify({"success": False, "message": "Invalid status."}), 400
            
        supabase = get_supabase()
        
        # Check username conflicts
        check_username = supabase.table('users').select('id').eq('username', username.lower().strip()).neq('id', user_id).execute()
        if check_username.data:
            return jsonify({"success": False, "message": "Username already in use by another user."}), 400
            
        db_payload = {
            "full_name": str(full_name).strip(),
            "username": str(username).strip().lower(),
            "role": role,
            "status": status,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        if password and str(password).strip():
            from werkzeug.security import generate_password_hash
            db_payload["password_hash"] = generate_password_hash(password)
            
        response = supabase.table('users').update(db_payload).eq('id', user_id).execute()
        if not response.data:
            return jsonify({"success": False, "message": "User not found or update failed."}), 404
            
        admin_name = session.get('full_name', 'Super Admin')
        log_audit_action(admin_name, f"Updated User: {full_name} (ID: {user_id})")
        
        return jsonify({"success": True, "message": "User updated successfully!"})
    except Exception as e:
        app.logger.error(f"Update user failed: {e}")
        return jsonify({"success": False, "message": f"Update failed: {str(e)}"}), 500


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@super_admin_required
def api_delete_user(user_id):
    """Delete a user. Super Admin only."""
    try:
        # Prevent self-deletion
        if session.get('user_id') == user_id:
            return jsonify({"success": False, "message": "You cannot delete your own account."}), 400
            
        supabase = get_supabase()
        # Get details for audit log
        user_resp = supabase.table('users').select('full_name, employee_id').eq('id', user_id).execute()
        if not user_resp.data:
            return jsonify({"success": False, "message": "User not found."}), 404
            
        target_user = user_resp.data[0]
        
        response = supabase.table('users').delete().eq('id', user_id).execute()
        if not response.data:
            return jsonify({"success": False, "message": "Delete failed."}), 500
            
        admin_name = session.get('full_name', 'Super Admin')
        log_audit_action(admin_name, f"Deleted User: {target_user.get('full_name')} ({target_user.get('employee_id')})")
        
        return jsonify({"success": True, "message": "User deleted successfully!"})
    except Exception as e:
        app.logger.error(f"Delete user failed: {e}")
        return jsonify({"success": False, "message": f"Delete failed: {str(e)}"}), 500


@app.route('/api/users/status', methods=['PATCH'])
@super_admin_required
def api_patch_user_status():
    """Toggle status of a user (Active/Inactive). Super Admin only."""
    try:
        data = request.json or {}
        user_id = data.get('user_id')
        status = data.get('status')
        
        if not user_id or not status or status not in ['Active', 'Inactive']:
            return jsonify({"success": False, "message": "Invalid request arguments."}), 400
            
        # Prevent deactivating self
        if session.get('user_id') == int(user_id) and status == 'Inactive':
            return jsonify({"success": False, "message": "You cannot deactivate your own account."}), 400
            
        supabase = get_supabase()
        # Fetch details
        user_resp = supabase.table('users').select('full_name').eq('id', int(user_id)).execute()
        if not user_resp.data:
            return jsonify({"success": False, "message": "User not found."}), 404
            
        full_name = user_resp.data[0].get('full_name')
        
        response = supabase.table('users').update({"status": status}).eq('id', int(user_id)).execute()
        if not response.data:
            return jsonify({"success": False, "message": "Status update failed."}), 500
            
        admin_name = session.get('full_name', 'Super Admin')
        log_audit_action(admin_name, f"Changed User Status: {full_name} to {status}")
        
        return jsonify({"success": True, "message": f"User status successfully updated to {status}!"})
    except Exception as e:
        app.logger.error(f"Patch user status failed: {e}")
        return jsonify({"success": False, "message": f"Status update failed: {str(e)}"}), 500


@app.route('/api/admin/audit-logs', methods=['GET'])
@super_admin_required
def api_get_audit_logs():
    """Fetch recent system administration audit logs. Super Admin only."""
    try:
        supabase = get_supabase()
        response = supabase.table('audit_logs').select('*').order('created_at', desc=True).limit(100).execute()
        return jsonify({"success": True, "data": response.data or []})
    except Exception as e:
        app.logger.error(f"Fetch audit logs failed: {e}")
        return jsonify({"success": False, "message": "Failed to retrieve audit logs."}), 500


# ----------------------------------------------------
# Main Startup block
# ----------------------------------------------------
if __name__ == '__main__':
    print("Starting Restructured Store Data Collection API Server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
