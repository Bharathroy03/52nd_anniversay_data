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

# ----------------------------------------------------
# Flask App Initialization
# ----------------------------------------------------
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
CORS(app)  # Support cross-origin API development

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
        user_name = "Bharath Kumar (22913)" if role == 'super_admin' else "Saddam Husain (6172)"
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

# ----------------------------------------------------
# HTML Template Serving Routes
# ----------------------------------------------------

@app.route('/')
def route_index():
    """Serves the public customer feedback form."""
    return render_template('index.html')

@app.route('/admin-login')
def route_admin_login():
    """Serves the admin login. Redirects to dashboard if already logged in."""
    if session.get('logged_in') and session.get('role') in ['super_admin', 'admin_store_head']:
        return redirect('/admin-dashboard')
    return render_template('admin-login.html')

@app.route('/admin-dashboard')
def route_admin_dashboard():
    """Serves the admin dashboard. Enforces server-side login check."""
    if not session.get('logged_in') or session.get('role') not in ['super_admin', 'admin_store_head']:
        return redirect('/admin-login')
    return render_template('admin-dashboard.html')

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
            
        if (username == 'bharath' or username == Config.ADMIN_USERNAME) and password == Config.ADMIN_PASSWORD:
            # Set Session credentials for Super Admin
            session.clear()
            session['logged_in'] = True
            session['role'] = 'super_admin'
            session.permanent = True
            return jsonify({"success": True, "message": "Login successful!"})
        elif (username == 'saddam' or username == Config.SADDAM_USERNAME) and password == Config.SADDAM_PASSWORD:
            # Set Session credentials for Admin & Store Head
            session.clear()
            session['logged_in'] = True
            session['role'] = 'admin_store_head'
            session.permanent = True
            return jsonify({"success": True, "message": "Login successful!"})
            
        return jsonify({"success": False, "message": "Invalid username or password."}), 401
    except Exception as e:
        app.logger.error(f"Login failed: {e}")
        return jsonify({"success": False, "message": "Internal authentication error."}), 500

@app.route('/api/admin/logout', methods=['POST', 'GET'])
def api_admin_logout():
    """Clears admin session parameters."""
    session.clear()
    return jsonify({"success": True, "message": "Successfully logged out."})

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
        user_name = "Bharath Kumar (22913)" if user_role == 'super_admin' else "Saddam Husain (6172)"
        
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
    if session.get('role') != 'super_admin':
        return jsonify({"success": False, "message": "Access Denied: Super Admin privileges required."}), 403
    return jsonify({"success": True, "message": "Super Admin system configuration settings accessed successfully."})

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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
def api_admin_export():
    """Generates and streams a CSV of filtered customer entries."""
    if not session.get('logged_in') or session.get('role') not in ['super_admin', 'admin_store_head']:
        return "Unauthorized Access. Please log in.", 401
        
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
def api_admin_export_excel():
    """Generates and streams an Excel workbook with multiple worksheets and premium formatting."""
    if not session.get('logged_in') or session.get('role') not in ['super_admin', 'admin_store_head']:
        return "Unauthorized Access. Please log in.", 401
        
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
# Main Startup block
# ----------------------------------------------------
if __name__ == '__main__':
    print("Starting Restructured Store Data Collection API Server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
