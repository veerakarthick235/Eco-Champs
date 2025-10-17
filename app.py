import os
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from pymongo import MongoClient
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from functools import wraps
from dotenv import load_dotenv

# --- Local Imports ---
from modules.gemini_handler import generate_quiz_questions

# --- App Initialization ---
load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# --- Direct MongoDB Connection ---
try:
    uri = os.getenv("MONGO_URI")
    client = MongoClient(uri)
    db = client['EcoChampsDB'] 
    client.admin.command('ping')
    print("✅ MongoDB connection successful.")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    db = None

# --- Extensions Initialization ---
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- Database Collections ---
if db is not None:
    users_collection = db.users
    challenges_collection = db.challenges
    submissions_collection = db.submissions
else:
    print("FATAL: Database collections could not be initialized. Check DB connection.")
    users_collection = challenges_collection = submissions_collection = None


# --- User Model for Flask-Login ---
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.name = user_data['name']
        self.role = user_data.get('role', 'student')
        self.school = user_data.get('school')
        self.city = user_data.get('city')
        self.points = user_data.get('points', 0)
        self.badges = user_data.get('badges', [])
        self.last_login = user_data.get('last_login')
        self.streak = user_data.get('streak', 0)

@login_manager.user_loader
def load_user(user_id):
    if users_collection is None: return None
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    return User(user_data) if user_data else None

# --- Decorators for Role-Based Access ---
def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- Helper Functions ---
def calculate_badges(points):
    badges = []
    badge_thresholds = {"Eco-Initiate": 100, "Green Guardian": 250, "Planet Hero": 500}
    for badge, required in badge_thresholds.items():
        if points >= required:
            badges.append(badge)
    return badges

# --- Authentication and other routes ---
# ... (No changes to /register, /login, etc.) ...
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if users_collection is None:
            flash('Database not connected. Please try again later.', 'danger')
            return redirect(url_for('register'))
        username = request.form['username']
        name = request.form['name']
        password = request.form['password']
        school = request.form['school']
        city = request.form['city']
        role = request.form['role']
        existing_user = users_collection.find_one({'username': username})
        if existing_user:
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_collection.insert_one({
            'username': username, 'name': name, 'password': hashed_password,
            'school': school, 'city': city, 'role': role, 'points': 0, 'badges': [],
            'created_at': datetime.utcnow(), 'last_login': None, 'streak': 0
        })
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if users_collection is None:
            flash('Database not connected. Please try again later.', 'danger')
            return redirect(url_for('login'))
        username = request.form['username']
        password = request.form['password']
        user_data = users_collection.find_one({'username': username})
        if user_data and bcrypt.check_password_hash(user_data['password'], password):
            user = User(user_data)
            login_user(user)
            today = datetime.utcnow().date()
            last_login_date = user.last_login.date() if user.last_login else None
            new_streak = user.streak
            if last_login_date is None or last_login_date < today:
                if last_login_date == today - timedelta(days=1):
                    new_streak += 1
                else:
                    new_streak = 1
                users_collection.update_one(
                    {'_id': ObjectId(user.id)},
                    {'$set': {'last_login': datetime.utcnow(), 'streak': new_streak}}
                )
                flash(f"Welcome back! Your daily login streak is now {new_streak}!", "info")
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check username and password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/challenges')
@login_required
def challenges_page():
    all_challenges = list(challenges_collection.find())
    user_submissions = list(submissions_collection.find({'user_id': ObjectId(current_user.id)}))
    submission_status = {str(sub['challenge_id']): sub['status'] for sub in user_submissions}
    return render_template('challenges.html', challenges=all_challenges, submission_status=submission_status)

@app.route('/challenge/<challenge_id>/submit', methods=['GET', 'POST'])
@login_required
def submit_challenge(challenge_id):
    challenge = challenges_collection.find_one({'_id': ObjectId(challenge_id)})
    if not challenge: return "Challenge not found", 404
    if request.method == 'POST':
        if 'proof_image' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['proof_image']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file:
            filename = secure_filename(f"{current_user.id}_{int(time.time())}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            submissions_collection.insert_one({
                'user_id': ObjectId(current_user.id), 'challenge_id': ObjectId(challenge_id),
                'image_path': filepath, 'status': 'pending', 'submitted_at': datetime.utcnow()
            })
            flash('Challenge submitted for verification!', 'success')
            return redirect(url_for('challenges_page'))
    return render_template('submit_challenge.html', challenge=challenge)

@app.route('/leaderboard')
@login_required
def leaderboard():
    city_pipeline = [{"$group": {"_id": "$city", "total_points": {"$sum": "$points"}}}, {"$sort": {"total_points": -1}}, {"$limit": 10}]
    city_leaders = list(users_collection.aggregate(city_pipeline))
    school_pipeline = [{"$group": {"_id": "$school", "total_points": {"$sum": "$points"}}}, {"$sort": {"total_points": -1}}, {"$limit": 10}]
    school_leaders = list(users_collection.aggregate(school_pipeline))
    return render_template('leaderboard.html', city_leaders=city_leaders, school_leaders=school_leaders)

@app.route('/quiz')
@login_required
def quiz_page():
    return render_template('quiz.html')

@app.route('/admin')
@login_required
@teacher_required
def admin_dashboard():
    pending_submissions = list(submissions_collection.aggregate([
        {'$match': {'status': 'pending'}},
        {'$lookup': {'from': 'users', 'localField': 'user_id', 'foreignField': '_id', 'as': 'user_info'}}, {'$unwind': '$user_info'},
        {'$lookup': {'from': 'challenges', 'localField': 'challenge_id', 'foreignField': '_id', 'as': 'challenge_info'}}, {'$unwind': '$challenge_info'}
    ]))
    return render_template('admin/dashboard.html', submissions=pending_submissions)

@app.route('/admin/add_challenge', methods=['GET', 'POST'])
@login_required
@teacher_required
def add_challenge():
    if request.method == 'POST':
        title = request.form['title']; description = request.form['description']; points = int(request.form['points'])
        challenges_collection.insert_one({'title': title, 'description': description, 'points': points})
        flash('New challenge added!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_challenge.html')

@app.route('/admin/submission/<submission_id>/<action>')
@login_required
@teacher_required
def handle_submission(submission_id, action):
    submission = submissions_collection.find_one({'_id': ObjectId(submission_id)})
    if not submission: return "Submission not found", 404
    if action == 'approve':
        submissions_collection.update_one({'_id': ObjectId(submission_id)}, {'$set': {'status': 'approved'}})
        challenge = challenges_collection.find_one({'_id': submission['challenge_id']})
        user_data = users_collection.find_one({'_id': submission['user_id']})
        new_points = user_data.get('points', 0) + challenge['points']; new_badges = calculate_badges(new_points)
        users_collection.update_one(
            {'_id': submission['user_id']}, {'$inc': {'points': challenge['points']}, '$set': {'badges': new_badges}}
        )
        flash('Submission approved and points awarded.', 'success')
    elif action == 'reject':
        submissions_collection.update_one({'_id': ObjectId(submission_id)}, {'$set': {'status': 'rejected'}})
        flash('Submission rejected.', 'warning')
    return redirect(url_for('admin_dashboard'))

# --- API Routes (for Quiz functionality) ---
@app.route('/generate_quiz', methods=['POST'])
@login_required
def get_quiz():
    topic = request.json.get('topic')
    quiz_data = generate_quiz_questions(topic)
    if not quiz_data or not quiz_data.get("questions"):
        return jsonify({"error": "Failed to generate quiz for this topic."}), 500
    session['current_quiz'] = quiz_data
    return jsonify(quiz_data)

# *** THIS IS THE ONLY SECTION THAT HAS CHANGED ***
@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    user_answers = request.json.get('answers')
    quiz_questions = session.get('current_quiz', {}).get('questions', [])
    correct_answers = sum(1 for i, q in enumerate(quiz_questions) if i < len(user_answers) and user_answers[i] == q['correct_answer'])
    points_earned = correct_answers * 20
    
    # Update user's points in the database
    user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})
    new_points = user_data.get('points', 0) + points_earned
    new_badges = calculate_badges(new_points)
    users_collection.update_one(
        {'_id': ObjectId(current_user.id)}, {'$inc': {'points': points_earned}, '$set': {'badges': new_badges}}
    )
    
    # *** NEW LINE ADDED HERE ***
    # Create a message with the score and flash it to the user's session.
    flash(f"Quiz Complete! You scored {correct_answers} out of {len(quiz_questions)} and earned {points_earned} Eco-Points!", "success")
    
    session.pop('current_quiz', None)
    
    # The JSON response is still sent, which the JavaScript uses to trigger the redirect.
    return jsonify({"score": correct_answers, "total": len(quiz_questions), "points_earned": points_earned})

if __name__ == '__main__':
    app.run(debug=True)
