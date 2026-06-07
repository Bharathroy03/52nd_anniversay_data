# Store Data Collection System

A complete web application similar to Google Forms for collecting customer and store interaction details. It features a public-facing entry form and a secure, password-protected admin dashboard with rich filters, search functionality, and CSV export capabilities.

## Tech Stack
- **Frontend**: HTML5, Vanilla CSS3 (curated HSL palettes, glassmorphism UI, responsive layouts), Vanilla JavaScript (inline validation, conditional rendering, dynamic API fetches, debounce search)
- **Backend**: Python Flask
- **Database**: Supabase
- **Authentication**: JWT token-based auth for the admin panel

---

## Project Structure
```
store-data-app/
│
├── backend/
│   ├── app.py                 # Core Flask application, API endpoints & static serving
│   ├── config.py              # Environment variable configurations & admin credentials
│   ├── requirements.txt       # Python dependencies
│   ├── supabase_client.py     # Supabase initialization client
│   └── test_app.py            # Integration & validation unit test cases
│
├── database/
│   └── schema.sql             # SQL setup script for Supabase tables & seed data
│
├── frontend/
│   ├── index.html             # Public customer submission form
│   ├── admin-login.html       # Admin login card interface
│   ├── admin-dashboard.html   # Admin submissions dashboard
│   ├── css/
│   │   └── style.css          # Common design styles & responsive theme
│   └── js/
│       ├── form.js            # Public form logic & API interactions
│       └── admin.js           # Admin authentication & dashboard logic
│
└── README.md                  # Instructions, configuration, and API reference
```

---

## Setup Instructions

### 1. Database Setup (Supabase)
1. Create a free account on [Supabase](https://supabase.com/).
2. Create a new project (e.g. `Store Data Collection`).
3. Navigate to the **SQL Editor** in the Supabase Sidebar.
4. Click **New Query**, copy the contents of the [schema.sql](database/schema.sql) file, paste it into the editor, and click **Run**.
   - This creates the `stores` and `customer_submissions` tables with proper check constraints and primary keys.
   - It also populates the database with initial seed stores.

### 2. Backend Environment Configuration
1. Navigate to the `backend/` folder.
2. Create a new file named `.env`.
3. Retrieve your Supabase API credentials from the **Settings > API** section of your Supabase dashboard.
4. Add the credentials to the `.env` file:
   ```env
   # Supabase URL (e.g. https://xxxxxx.supabase.co)
   SUPABASE_URL=your_supabase_project_url
   
   # Supabase API Key (Use the service_role key or anon key)
   SUPABASE_KEY=your_supabase_api_key
   
   # Secret key for encrypting JWT tokens (e.g. a random long string)
   JWT_SECRET_KEY=generate_a_secure_random_key_here
   
   # Session Expire duration in seconds (optional: defaults to 7200 seconds / 2 hours)
   JWT_EXPIRY_SECONDS=7200
   ```

### 3. Local Installation
1. Make sure you have **Python 3.8+** installed.
2. Open your terminal and navigate to the project backend directory:
   ```bash
   cd store-data-app/backend
   ```
3. (Highly Recommended) Create and activate a Python virtual environment:
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows (Command Prompt)
   venv\Scripts\activate
   # On Windows (PowerShell)
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS
   source venv/bin/activate
   ```
4. Install the backend package requirements:
   ```bash
   pip install -r requirements.txt
   ```

### 4. Running the Application
1. Start the Flask application server:
   ```bash
   python app.py
   ```
2. The server will start on `http://127.0.0.1:5000/`.
3. Open your browser and navigate to:
   - **Public User Form**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
   - **Admin Login**: [http://127.0.0.1:5000/admin-login](http://127.0.0.1:5000/admin-login)
   - **Admin Dashboard**: [http://127.0.0.1:5000/admin-dashboard](http://127.0.0.1:5000/admin-dashboard)

*Note: The Flask server is pre-configured to host and serve the static files from the `frontend/` folder directly. There is no need to run a separate web server for HTML assets!*

---

## Admin Portal Access Credentials
- **Username**: `admin`
- **Password**: `Admin@123`

---

## Running Automated Tests
To verify all routes, authorization scopes, inputs, and database mocking structures, run the following command from the `backend/` folder:
```bash
python test_app.py
```

---

## Deployment Guidelines

### 1. Backend API Hosting (e.g., Render, Heroku)
1. Create a new Web Service pointing to your repository.
2. Select **Python** as the runtime.
3. Use the following build & start configurations:
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `gunicorn --dir backend app:app` (You may need to add `gunicorn` to `requirements.txt`).
4. Set the Environment Variables (`SUPABASE_URL`, `SUPABASE_KEY`, `JWT_SECRET_KEY`) in the platform's settings dashboard.

### 2. Frontend Hosting (Optional)
If you wish to host the frontend statically on platforms like Netlify, Vercel, or GitHub Pages:
1. Modify `frontend/js/form.js` and `frontend/js/admin.js` to change the backend API endpoints from relative URLs (e.g. `/submit`) to absolute URLs pointing to your hosted API server (e.g., `https://your-api.onrender.com/submit`).
2. Make sure CORS is configured in the Flask backend (the app is already initialized with `CORS(app)` which supports this out of the box).
3. Deploy the `frontend/` folder to your static host.

---

## API Documentation

### Public Endpoints
- **`GET /stores`**: Fetches an ordered list of stores.
  - *Response*: `{"success": true, "data": [{"id": 1, "store_name": "Store A"}]}`
- **`POST /submit`**: Saves customer submission data.
  - *Body*:
    ```json
    {
      "store_id": 2,
      "customer_name": "Jane Doe",
      "mobile_number": "9876543210",
      "app_registration_status": "Pending",
      "invitation_card_issue": "Yes",
      "issue_description": "Damaged QR"
    }
    ```
  - *Response*: `{"success": true, "message": "Submission successfully saved!"}`

### Admin Endpoints (Require Bearer Token)
- **`POST /admin-login`**: Verifies admin credentials.
  - *Body*: `{"username": "admin", "password": "Admin@123"}`
  - *Response*: `{"success": true, "token": "<JWT_TOKEN>"}`
- **`GET /admin/submissions`**: Retrieves all submission logs.
  - *Headers*: `Authorization: Bearer <JWT_TOKEN>`
  - *Query Parameters (Filters)*: `store_id` (int), `status` (string), `search` (string)
  - *Response*: Array of submission objects containing store details.
- **`GET /admin/export-csv`**: Downloads submissions matching filter criteria as CSV.
  - *Headers*: `Authorization: Bearer <JWT_TOKEN>` OR passing token in query string: `?token=<JWT_TOKEN>` (for file downloads).
  - *Query Parameters (Filters)*: `store_id` (int), `status` (string), `search` (string)
  - *Response*: CSV attachment download.
