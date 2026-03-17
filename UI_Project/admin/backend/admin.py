import os
import sqlite3
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# ============================================
# CONFIGURATION & CUSTOM FOLDER PATHS
# ============================================

# Get the directory where admin.py is currently located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Point to your custom frontend folder (up one level, then into frontend)
FRONTEND_DIR = os.path.join(BASE_DIR, '../frontend')

# Point to your custom db folder (up two levels, then into db)
DB_FILE = os.path.join(BASE_DIR, '../../db/alerts.db')

# Tell Flask to use your frontend folder for both HTML templates and static files (CSS)
app = Flask(__name__, 
            template_folder=FRONTEND_DIR, 
            static_folder=FRONTEND_DIR,
            static_url_path='/static')

CORS(app)

def get_db_connection():
    """Helper function to connect to the DB and return dictionary-like rows"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================
# ADMIN DASHBOARD ROUTES
# ============================================

@app.route('/admin')
def admin_dashboard():
    """Serve the Admin HTML Interface"""
    return render_template('admin.html')

# ============================================
# API ENDPOINTS FOR ADMIN.HTML
# ============================================

@app.route('/api/alerts/all', methods=['GET'])
def get_all_alerts():
    """Fetch all alerts from the database to display on the dashboard"""
    conn = get_db_connection()
    # Fetch alerts ordered by newest first
    alerts = conn.execute('SELECT * FROM alerts ORDER BY created_at DESC').fetchall()
    conn.close()
    
    # Format the data so it matches the expected JSON structure
    result = []
    for row in alerts:
        result.append({
            'id': row['id'],
            'type': row['type'],
            'situation': row['situation'],
            'location': {'lat': row['location_lat'], 'lng': row['location_lng']},
            'contactInfo': {'name': row['contact_name'], 'phone': row['contact_phone']},
            'status': row['status'],
            'createdAt': row['created_at'],
            'updatedAt': row['updated_at']
        })
        
    return jsonify(result), 200

@app.route('/api/alerts', methods=['POST'])
def dispatch_alert():
    """Save a new alert dispatched directly from the admin dashboard"""
    data = request.json
    alert_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO alerts 
        (id, type, situation, location_lat, location_lng, contact_name, contact_phone, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        alert_id,
        data.get('emergencyType', 'general'),
        data.get('description', ''),
        data.get('location', {}).get('lat', 0.0),
        data.get('location', {}).get('lng', 0.0),
        data.get('contactInfo', {}).get('name', 'Admin Dispatch'),
        data.get('contactInfo', {}).get('phone', 'N/A'),
        'confirmed', # Set to confirmed/active immediately
        timestamp,
        timestamp
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Alert dispatched successfully', 'id': alert_id}), 201

@app.route('/api/alerts/<alert_id>/status', methods=['PATCH'])
def update_alert_status(alert_id):
    """Update an alert's status (e.g., mark it as 'resolved')"""
    data = request.json
    new_status = data.get('status')
    timestamp = datetime.utcnow().isoformat()
    
    conn = get_db_connection()
    conn.execute(
        'UPDATE alerts SET status = ?, updated_at = ? WHERE id = ?',
        (new_status, timestamp, alert_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'message': f'Alert {alert_id} marked as {new_status}'}), 200

# ============================================
# RUN SERVER
# ============================================
if __name__ == '__main__':
    # Running on Port 5000 so main.py can run on Port 3000 simultaneously
    print("""
    ╔═══════════════════════════════════════╗
    ║  🛡️ ADMIN COMMAND SERVER (FLASK)      ║
    ╠═══════════════════════════════════════╣
    ║  Dashboard: http://127.0.0.1:5000/admin║
    ╚═══════════════════════════════════════╝
    """)
    app.run(port=5000, debug=True)