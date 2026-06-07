-- Disable RLS on users, audit_logs and delete_logs tables
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE delete_logs DISABLE ROW LEVEL SECURITY;
