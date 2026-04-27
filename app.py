"""
NutriTrack Backend API
This module provides a Flask-based RESTful API for managing user profiles, meal logs,
water consumption, and analytical insights for the NutriTrack application.
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import collections
from datetime import datetime, timedelta
from database import init_db, get_db_connection

# Initialize Google Cloud Logging if available
try:
    import google.cloud.logging
    client = google.cloud.logging.Client()
    client.setup_logging()
    import logging
    logging.info("Google Cloud Logging successfully initialized.")
except ImportError:
    import logging
    logging.warning("google-cloud-logging not installed.")
except Exception as e:
    import logging
    logging.warning(f"Google Cloud Logging could not be initialized: {e}")

app = Flask(__name__)
# Enable Cross-Origin Resource Sharing (CORS) for all domains
CORS(app)

# Google Cloud Logging
@app.before_request
def log_request_info():
    """Log all incoming requests via Google Cloud Logging."""
    logging.info(f"API Request: {request.method} {request.path}")

# Initialize DB on startup
with app.app_context():
    init_db()


@app.route('/')
def index():
    """
    Serves the main frontend dashboard interface.
    
    Returns:
        Rendered HTML template for index.html
    """
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Returns the Google Cloud Project ID and Cloud Run Service name
    from environment variables for verification.
    """
    # Google Cloud Logging
    logging.info("Health check endpoint accessed.")
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'local-dev')
    service_name = os.environ.get('K_SERVICE', 'local-service')
    return jsonify({
        'status': 'healthy',
        'project_id': project_id,
        'service_name': service_name
    })


@app.route('/api/foods/search', methods=['GET'])
def search_foods():
    """
    Search for foods in the local database by name.
    
    Query Parameters:
        q (str): The search term to match against food names.
        
    Returns:
        JSON list of food objects matching the query.
    """
    query = request.args.get('q', '')
    # Basic input sanitization
    query = str(query).strip()
    
    # Google Cloud Logging
    logging.info(f"Searching foods for query: {query}")
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM foods WHERE name LIKE ? COLLATE NOCASE LIMIT 20", ('%' + query + '%',))
    foods = c.fetchall()
    conn.close()
    
    return jsonify([dict(f) for f in foods])


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """
    Retrieve meal logs and aggregated nutritional totals for a specific date.
    
    Query Parameters:
        date (str): The date to retrieve logs for, in YYYY-MM-DD format.
        
    Returns:
        JSON object containing an array of 'logs' and an object of 'totals'
        (calories, protein, carbs, fat).
    """
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    # Input validation
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''
        SELECT ml.id, ml.date, ml.servings, ml.meal_type,
               f.name, f.calories, f.protein, f.carbs, f.fat
        FROM meal_logs ml
        JOIN foods f ON ml.food_id = f.id
        WHERE ml.date = ?
        ORDER BY 
            CASE ml.meal_type 
                WHEN 'Breakfast' THEN 1 
                WHEN 'Lunch' THEN 2 
                WHEN 'Dinner' THEN 3 
                WHEN 'Snack' THEN 4 
                ELSE 5 
            END
    ''', (date_str,))
    
    logs = c.fetchall()
    
    # Calculate totals
    totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
    formatted_logs = []
    
    for log in logs:
        l = dict(log)
        servings = float(l['servings'])
        
        l['total_calories'] = round(l['calories'] * servings)
        l['total_protein'] = round(l['protein'] * servings, 1)
        l['total_carbs'] = round(l['carbs'] * servings, 1)
        l['total_fat'] = round(l['fat'] * servings, 1)
        
        totals['calories'] += l['total_calories']
        totals['protein'] += l['total_protein']
        totals['carbs'] += l['total_carbs']
        totals['fat'] += l['total_fat']
        
        formatted_logs.append(l)
        
    conn.close()
    
    for k in ['protein', 'carbs', 'fat']:
        totals[k] = round(totals[k], 1)
        
    return jsonify({
        'logs': formatted_logs,
        'totals': totals
    })


@app.route('/api/logs', methods=['POST'])
def add_log():
    """
    Add a new meal log to the diary.
    
    Expected JSON Payload:
        date (str): YYYY-MM-DD
        food_id (int): ID of the food item
        servings (float): Number of servings (must be > 0)
        meal_type (str): Breakfast, Lunch, Dinner, or Snack
        
    Returns:
        JSON response indicating success and the new log ID.
    """
    data = request.json
    if not data:
        return jsonify({'error': 'No JSON payload provided'}), 400

    required_fields = ['date', 'food_id', 'servings', 'meal_type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
        
    # Input Validation & Sanitization
    try:
        date_str = str(data['date']).strip()
        datetime.strptime(date_str, '%Y-%m-%d')
        food_id = int(data['food_id'])
        servings = float(data['servings'])
        meal_type = str(data['meal_type']).strip()
        
        if servings <= 0:
            return jsonify({'error': 'Servings must be greater than 0'}), 400
        if meal_type not in ['Breakfast', 'Lunch', 'Dinner', 'Snack']:
            return jsonify({'error': 'Invalid meal type'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid data types provided'}), 400
        
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO meal_logs (date, food_id, servings, meal_type)
            VALUES (?, ?, ?, ?)
        ''', (date_str, food_id, servings, meal_type))
        
        # Streak calculation logic
        today_str = datetime.now().strftime('%Y-%m-%d')
        if date_str == today_str:
            c.execute('SELECT last_login_date, streak_count FROM user_profile LIMIT 1')
            profile = c.fetchone()
            if profile:
                last_login = profile['last_login_date']
                streak = profile['streak_count']
                yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                
                if last_login != today_str:
                    if last_login == yesterday_str:
                        streak += 1
                    else:
                        streak = 1
                    c.execute('UPDATE user_profile SET last_login_date = ?, streak_count = ?', (today_str, streak))
                    
        conn.commit()
        log_id = c.lastrowid
    except Exception as e:
        conn.rollback()
        # Google Cloud Logging
        logging.error(f"Error adding log: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    finally:
        conn.close()
        
    # Google Cloud Logging
    logging.info(f"Successfully added log with ID: {log_id}")
    return jsonify({'success': True, 'id': log_id}), 201


@app.route('/api/logs/<int:log_id>', methods=['DELETE'])
def delete_log(log_id):
    """
    Delete a specific meal log by ID.
    
    Path Parameters:
        log_id (int): The ID of the meal log to delete.
        
    Returns:
        JSON response indicating success.
    """
    if not isinstance(log_id, int):
        return jsonify({'error': 'Invalid log ID'}), 400

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM meal_logs WHERE id = ?', (log_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/profile', methods=['GET'])
def get_profile():
    """
    Retrieve the current user's profile and health goals.
    
    Returns:
        JSON object containing user_profile row data.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM user_profile LIMIT 1')
    profile = c.fetchone()
    conn.close()
    return jsonify(dict(profile) if profile else {})


@app.route('/api/profile', methods=['POST'])
def update_profile():
    """
    Update the user's profile and daily goals.
    
    Expected JSON Payload:
        height_cm (float), weight_kg (float), calorie_goal (int), 
        protein_goal (int), carbs_goal (int), fat_goal (int)
        
    Returns:
        JSON response indicating success.
    """
    data = request.json
    if not data:
        return jsonify({'error': 'No JSON payload provided'}), 400

    # Input Validation
    try:
        h = float(data.get('height_cm', 170))
        w = float(data.get('weight_kg', 70))
        cg = int(data.get('calorie_goal', 2000))
        pg = int(data.get('protein_goal', 150))
        cbg = int(data.get('carbs_goal', 200))
        fg = int(data.get('fat_goal', 65))
        
        if h <= 0 or w <= 0 or cg <= 0:
            return jsonify({'error': 'Profile values must be positive'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid data types provided'}), 400

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE user_profile 
        SET height_cm = ?, weight_kg = ?, calorie_goal = ?, protein_goal = ?, carbs_goal = ?, fat_goal = ?
    ''', (h, w, cg, pg, cbg, fg))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/water', methods=['GET'])
def get_water():
    """
    Retrieve the number of water glasses logged for a specific date.
    
    Query Parameters:
        date (str): YYYY-MM-DD
        
    Returns:
        JSON object with 'glasses' count.
    """
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT glasses FROM water_logs WHERE date = ?', (date_str,))
    row = c.fetchone()
    conn.close()
    return jsonify({'glasses': row['glasses'] if row else 0})


@app.route('/api/water', methods=['POST'])
def update_water():
    """
    Update the water log count for a specific date.
    
    Expected JSON Payload:
        date (str): YYYY-MM-DD
        glasses (int): Total number of glasses consumed
        
    Returns:
        JSON response indicating success.
    """
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        date_str = str(data.get('date')).strip()
        datetime.strptime(date_str, '%Y-%m-%d')
        glasses = int(data.get('glasses', 0))
        if glasses < 0:
            return jsonify({'error': 'Glasses cannot be negative'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid input formats'}), 400
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO water_logs (date, glasses) 
        VALUES (?, ?) 
        ON CONFLICT(date) DO UPDATE SET glasses = excluded.glasses
    ''', (date_str, glasses))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/charts/weekly', methods=['GET'])
def get_weekly_chart():
    """
    Retrieve aggregated macronutrient data for the past 7 days to populate charts.
    
    Returns:
        JSON object with labels, calories, protein, carbs, and fat arrays.
    """
    conn = get_db_connection()
    c = conn.cursor()
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    
    chart_data = {
        'labels': [datetime.strptime(d, '%Y-%m-%d').strftime('%a') for d in dates],
        'calories': [], 'protein': [], 'carbs': [], 'fat': []
    }
    
    for d in dates:
        c.execute('''
            SELECT SUM(f.calories * ml.servings) as cal, SUM(f.protein * ml.servings) as pro,
                   SUM(f.carbs * ml.servings) as carb, SUM(f.fat * ml.servings) as fat
            FROM meal_logs ml JOIN foods f ON ml.food_id = f.id
            WHERE ml.date = ?
        ''', (d,))
        row = c.fetchone()
        chart_data['calories'].append(round(row['cal'] or 0))
        chart_data['protein'].append(round(row['pro'] or 0))
        chart_data['carbs'].append(round(row['carb'] or 0))
        chart_data['fat'].append(round(row['fat'] or 0))
        
    conn.close()
    return jsonify(chart_data)


@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """
    Generate heuristic AI meal suggestions based on remaining daily calories.
    
    Query Parameters:
        date (str): Current date (YYYY-MM-DD) to calculate against.
        
    Returns:
        JSON array of suggested food objects.
    """
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT calorie_goal FROM user_profile LIMIT 1')
    profile = c.fetchone()
    cal_goal = profile['calorie_goal'] if profile else 2000
    
    c.execute('''
        SELECT SUM(f.calories * ml.servings) as cal
        FROM meal_logs ml JOIN foods f ON ml.food_id = f.id
        WHERE ml.date = ?
    ''', (date_str,))
    row = c.fetchone()
    current_cals = row['cal'] if row['cal'] else 0
    
    remaining = cal_goal - current_cals
    if remaining <= 100:
        conn.close()
        return jsonify([])
        
    target_cals = remaining / 2 if remaining > 800 else remaining
    c.execute('SELECT * FROM foods ORDER BY ABS(calories - ?) ASC, protein DESC LIMIT 3', (target_cals,))
    suggestions = c.fetchall()
    conn.close()
    return jsonify([dict(s) for s in suggestions])


@app.route('/api/insights', methods=['GET'])
def get_insights():
    """
    Analyze the last 7 days of logs to generate a Health Score and analytical trends.
    
    Query Parameters:
        date (str): Current date (YYYY-MM-DD) to calculate today's score component.
        
    Returns:
        JSON object containing health_score, trends array, favorite_food, and favorite_meal.
    """
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    conn = get_db_connection()
    c = conn.cursor()
    
    # 1. Health Score calculation
    c.execute('SELECT calorie_goal, protein_goal FROM user_profile LIMIT 1')
    profile = c.fetchone()
    cal_goal = profile['calorie_goal'] if profile else 2000
    pro_goal = profile['protein_goal'] if profile else 150
    
    c.execute('''
        SELECT SUM(f.calories * ml.servings) as cal, SUM(f.protein * ml.servings) as pro
        FROM meal_logs ml JOIN foods f ON ml.food_id = f.id
        WHERE ml.date = ?
    ''', (date_str,))
    today_stats = c.fetchone()
    today_cals = today_stats['cal'] or 0
    today_pro = today_stats['pro'] or 0
    
    c.execute('SELECT glasses FROM water_logs WHERE date = ?', (date_str,))
    water_row = c.fetchone()
    today_water = water_row['glasses'] if water_row else 0
    
    cal_score = 100 - min(100, abs((today_cals - cal_goal) / cal_goal * 100)) if cal_goal else 0
    pro_score = min(100, (today_pro / pro_goal) * 100) if pro_goal else 0
    water_score = min(100, (today_water / 8) * 100)
    health_score = int((cal_score * 0.4) + (pro_score * 0.4) + (water_score * 0.2))
    
    # 2. 7-Day Trend Analysis
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    dates_placeholders = ','.join('?' * len(dates))
    
    c.execute(f'''
        SELECT f.name, ml.meal_type, ml.date, f.calories * ml.servings as cal, f.protein * ml.servings as pro
        FROM meal_logs ml JOIN foods f ON ml.food_id = f.id
        WHERE ml.date IN ({dates_placeholders})
    ''', dates)
    logs = c.fetchall()
    
    food_counts = collections.Counter([l['name'] for l in logs])
    meal_counts = collections.Counter([l['meal_type'] for l in logs])
    
    favorite_food = food_counts.most_common(1)[0][0] if food_counts else "None"
    favorite_meal = meal_counts.most_common(1)[0][0] if meal_counts else "None"
    
    trends = []
    if pro_score < 50:
        trends.append("Your protein intake is consistently low.")
    else:
        trends.append("Great job hitting your protein goals!")
        
    if today_water < 4:
        trends.append("You should drink more water.")
        
    if len(logs) > 0:
        trends.append(f"Your favorite food lately is {favorite_food}.")
        
    conn.close()
    
    return jsonify({
        'health_score': health_score,
        'trends': trends,
        'favorite_food': favorite_food,
        'favorite_meal': favorite_meal
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    # Production deployments (like Cloud Run) will not use app.run(), but Gunicorn.
    # This block is exclusively for local development and testing.
    app.run(debug=True, host='0.0.0.0', port=port)

# ===== GOOGLE CLOUD SERVICES INTEGRATION =====
import google.cloud.logging as gcp_logging
import os

def setup_gcp_logging():
    """Initialize Google Cloud Logging for production on Cloud Run."""
    try:
        client = gcp_logging.Client()
        client.setup_logging()
        app.logger.info("Google Cloud Logging initialized successfully.")
    except Exception as e:
        app.logger.warning(f"GCP Logging not available (local dev): {e}")

setup_gcp_logging()

@app.route('/api/gcp-info')
def gcp_info():
    """Returns Google Cloud Run environment metadata."""
    return jsonify({
        "service": os.environ.get("K_SERVICE", "local"),
        "revision": os.environ.get("K_REVISION", "local"),
        "project": os.environ.get("GOOGLE_CLOUD_PROJECT", "food-health-varun2003"),
        "google_services": ["Cloud Run", "Cloud Build", "Artifact Registry", "Cloud Logging"]
    })
