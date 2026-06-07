# Store Data Collection System

A complete web application for collecting store and customer feedback, structured as a standard Flask repository.

## Features
- **Public Form Card**: Standard Google Forms layout with dynamic dropdowns, conditional sub-inputs, numeric validations, and toast notifications.
- **Admin Panel**: Secure dashboard displaying statistics counters, real-time debounced filters, and data export functions.
- **Dynamic Assets**: Scans and loads anniversary and primary logos automatically from the static assets directory.
- **Session Authentication**: Cookie-based user sessions for dashboard route protection and admin security.
- **Automated Directory Setup**: Automatically sets up project directories and migrates logo files at startup.

---

## Folder Structure
```
project/
│
├── app.py                     # Flask server with page routing and REST API endpoints
├── config.py                  # Configurations and admin credentials loading
├── requirements.txt           # Application dependencies
├── .env                       # Local environment variables
│
├── database/
│   ├── supabase.py            # Supabase database initialization
│   └── schema.sql             # SQL script for stores and customer_entries
│
├── static/
│   ├── css/
│   │   └── style.css          # Common styling system
│   ├── js/
│   │   ├── form.js            # Public form logic
│   │   └── admin.js           # Admin dashboard and authentication logic
│   └── images/
│       ├── main_Logo.png      # Auto-detected Primary Logo
│       └── anniversary_logo.png # Auto-detected Anniversary Logo
│
├── templates/
│   ├── index.html             # Public user feedback template
│   ├── admin-login.html       # Credentials entry card template
│   └── admin-dashboard.html   # Submissions console telemetry template
│
└── README.md                  # Project overview and installation instructions
```

---

## Setup Instructions

### 1. Supabase Database
1. Create a project on [Supabase](https://supabase.com/).
2. Open the **SQL Editor**, click **New Query**, copy the script in [database/schema.sql](database/schema.sql), and click **Run**.
   - This configures the `stores` and `customer_entries` tables and loads initial stores seed data.

### 2. Local Environment variables
1. Create a `.env` file at the root folder.
2. Get your Supabase keys from the project **Settings > API** panel and configure your environment:
   ```env
   # Supabase project URL
   SUPABASE_URL=https://your-project.supabase.co
   
   # Supabase API key (anon key or service role key)
   SUPABASE_KEY=your-supabase-api-key
   
   # Session secret key for cookies cryptographic signing
   SECRET_KEY=choose-a-secure-random-phrase
   ```

### 3. Local Installation
1. Move to the project root directory:
   ```bash
   cd c:\Users\91845\Desktop\52nd_Anniversary_data
   ```
2. Initialize and load a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install package requirements:
   ```bash
   pip install -r requirements.txt
   ```

### 4. Running the Application
1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Open your browser:
   - **Public User Form**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
   - **Admin Login**: [http://127.0.0.1:5000/admin-login](http://127.0.0.1:5000/admin-login)
   - **Admin Dashboard**: [http://127.0.0.1:5000/admin-dashboard](http://127.0.0.1:5000/admin-dashboard)

---

## Administrative Credentials
- **Username**: `admin`
- **Password**: `Admin@123`

---

## Verification Test Runner
Run unit and integrations tests verifying API payloads, validation rules, page routing, and session authentication:
```bash
python test_app_restructured.py
```

---

## Flask REST APIs

### Public Operations
- **`GET /api/stores`**: Retrieves ordered stores list.
  - *Response*: `{"success": true, "data": [{"id": 1, "store_name": "Store A"}]}`
- **`POST /api/submit`**: Saves a new submission.
  - *Body*:
    ```json
    {
      "store_id": 2,
      "customer_name": "John Smith",
      "mobile_number": "9876543210",
      "app_registration_status": "Completed",
      "invitation_issue": "Yes",
      "issue_description": "Card printed offset"
    }
    ```
  - *Response*: `{"success": true, "message": "Feedback submitted successfully!"}`

### Administrative Operations (Cookie Auth Required)
- **`POST /api/admin/login`**: Authenticates credentials and sets session cookies.
  - *Body*: `{"username": "admin", "password": "Admin@123"}`
  - *Response*: `{"success": true, "message": "Login successful!"}`
- **`POST /api/admin/logout`**: Clears active session credentials.
- **`GET /api/admin/dashboard`**: Compiles counter widgets counts.
  - *Response*: `{"success": true, "stats": {"total": 50, "completed": 30, "pending": 15, "issues": 5}}`
- **`GET /api/admin/customers`**: Retrieves entries matching query parameters.
  - *Query Parameters*: `store_id` (int), `status` (string), `search` (string)
- **`GET /api/admin/export`**: Downloads CSV of filtered customer entries.
