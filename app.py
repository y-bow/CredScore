from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import bcrypt
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///credscore.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth'

# --- Database Models ---

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False) # 'Student', 'Business', 'Recruiter', 'Admin'
    college = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False)

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    credscore = db.Column(db.Integer, default=0)
    tasks_done = db.Column(db.Integer, default=0)
    on_time_rate = db.Column(db.Float, default=0.0)
    avg_rating = db.Column(db.Float, default=0.0)
    verified = db.Column(db.Boolean, default=False)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    budget = db.Column(db.Integer, nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    business_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='open') # open, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    business = db.relationship('User', foreign_keys=[business_id])
    applications = db.relationship('Application', backref='task', lazy=True)
    submissions = db.relationship('Submission', backref='task', lazy=True)

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='pending') # pending, accepted, rejected
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('User', foreign_keys=[student_id])

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    revision_number = db.Column(db.Integer, default=1)

class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    rater_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ratee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    revealed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Flag(db.Model):
    __tablename__ = 'flags'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', foreign_keys=[user_id])

class Shortlist(db.Model):
    __tablename__ = 'shortlists'
    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Anti-Gaming Logic ---
def check_anti_gaming_flags(task_id, rater_id, ratee_id, score):
    # 1. Same business rates same student 5 stars 3 or more times consecutively
    if score == 5:
        recent_ratings = Rating.query.filter_by(rater_id=rater_id, ratee_id=ratee_id).order_by(Rating.created_at.desc()).limit(3).all()
        if len(recent_ratings) == 3 and all(r.score == 5 for r in recent_ratings):
            flag = Flag(type='Suspicious Rating Pattern', user_id=rater_id, task_id=task_id, reason='Business rated same student 5 stars 3+ times consecutively.')
            db.session.add(flag)
    
    # 2. Rating submitted within 60 seconds of task submission
    submission = Submission.query.filter_by(task_id=task_id).order_by(Submission.submitted_at.desc()).first()
    if submission and (datetime.utcnow() - submission.submitted_at).total_seconds() < 60:
        flag = Flag(type='Pressure Rating', user_id=rater_id, task_id=task_id, reason='Rating submitted within 60s of work submission.')
        db.session.add(flag)
        return False # Block it
        
    # 3. Student account less than 7 days old with 3 or more five-star ratings
    ratee = User.query.get(ratee_id)
    if ratee and ratee.role == 'Student' and (datetime.utcnow() - ratee.created_at).days < 7:
        five_star_count = Rating.query.filter_by(ratee_id=ratee_id, score=5).count()
        if five_star_count >= 3:
            flag = Flag(type='Rapid High Ratings', user_id=ratee_id, task_id=task_id, reason='Account < 7 days old with 3+ 5-star ratings.')
            db.session.add(flag)
            
    # 4. Task completed in under 10 percent of total deadline duration
    task = Task.query.get(task_id)
    if task and submission:
        total_duration = (task.deadline - task.created_at.date()).days
        time_taken = (submission.submitted_at.date() - task.created_at.date()).days
        if total_duration > 0 and (time_taken / total_duration) < 0.1:
            flag = Flag(type='Unrealistic Completion Time', user_id=ratee_id, task_id=task_id, reason='Task completed in < 10% of deadline duration.')
            db.session.add(flag)

    # 5. Student has zero revision history on submission but received 5 stars
    if score == 5 and submission and submission.revision_number == 1:
        flag = Flag(type='Perfect First Submission', user_id=ratee_id, task_id=task_id, reason='Zero revision history but received 5 stars.')
        db.session.add(flag)
        
    db.session.commit()
    return True

def recalculate_credscore(student_id):
    profile = StudentProfile.query.filter_by(user_id=student_id).first()
    if not profile: return
    
    # Logic for average rating
    ratings = Rating.query.filter_by(ratee_id=student_id, revealed=True).all()
    if ratings:
        profile.avg_rating = sum(r.score for r in ratings) / len(ratings)
        
    # Calculate CredScore
    # credscore = (avg_rating/5 * 40) + (on_time_rate * 30) + (min(tasks_done,20)/20 * 20) + (verified * 10)
    # For on_time_rate, we'd need more data tracking, assuming placeholder here based on tasks_done
    
    score = (profile.avg_rating / 5.0 * 40) + (profile.on_time_rate * 30) + (min(profile.tasks_done, 20) / 20.0 * 20) + (10 if profile.verified else 0)
    profile.credscore = min(int(score), 100)
    db.session.commit()

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'login':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
                login_user(user)
                if user.role == 'Student': return redirect(url_for('student_dashboard'))
                elif user.role == 'Business': return redirect(url_for('business_dashboard'))
                elif user.role == 'Recruiter': return redirect(url_for('recruiter_dashboard'))
                elif user.role == 'Admin': return redirect(url_for('admin_flags'))
            else:
                flash('Invalid email or password.', 'error')
                
        elif action == 'signup':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role')
            college = request.form.get('college') if role == 'Student' else None
            
            if User.query.filter_by(email=email).first():
                flash('Email already registered.', 'error')
            else:
                hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                new_user = User(name=name, email=email, password_hash=hashed_pw, role=role, college=college)
                db.session.add(new_user)
                db.session.commit()
                
                if role == 'Student':
                    profile = StudentProfile(user_id=new_user.id)
                    db.session.add(profile)
                    db.session.commit()
                    
                login_user(new_user)
                flash('Account created successfully!', 'success')
                if role == 'Student': return redirect(url_for('student_dashboard'))
                elif role == 'Business': return redirect(url_for('business_dashboard'))
                elif role == 'Recruiter': return redirect(url_for('recruiter_dashboard'))
                
    return render_template('auth.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'Student': return redirect(url_for('index'))
    profile = current_user.student_profile
    active_tasks = Task.query.join(Application).filter(Application.student_id == current_user.id, Application.status == 'accepted', Task.status == 'in_progress').all()
    completed_tasks = Task.query.join(Application).filter(Application.student_id == current_user.id, Task.status == 'completed').all()
    return render_template('student_dashboard.html', profile=profile, active_tasks=active_tasks, completed_tasks=completed_tasks)

@app.route('/business/dashboard')
@login_required
def business_dashboard():
    if current_user.role != 'Business': return redirect(url_for('index'))
    tasks = Task.query.filter_by(business_id=current_user.id).all()
    completed_tasks = [t for t in tasks if t.status == 'completed']
    return render_template('business_dashboard.html', tasks=tasks, completed_tasks=completed_tasks)

@app.route('/recruiter/dashboard')
@login_required
def recruiter_dashboard():
    if current_user.role != 'Recruiter': return redirect(url_for('index'))
    students = User.query.filter_by(role='Student').join(StudentProfile).all()
    shortlisted = [s.student_id for s in Shortlist.query.filter_by(recruiter_id=current_user.id).all()]
    return render_template('recruiter_dashboard.html', students=students, shortlisted=shortlisted)

@app.route('/explore')
def explore():
    tasks = Task.query.filter_by(status='open').all()
    applied_tasks = []
    if current_user.is_authenticated and current_user.role == 'Student':
        applied_tasks = [a.task_id for a in Application.query.filter_by(student_id=current_user.id).all()]
    return render_template('explore.html', tasks=tasks, applied_tasks=applied_tasks)

@app.route('/apply/<int:task_id>', methods=['POST'])
@login_required
def apply_task(task_id):
    if current_user.role != 'Student': return jsonify({'success': False, 'message': 'Only students can apply.'})
    
    if not Application.query.filter_by(task_id=task_id, student_id=current_user.id).first():
        app = Application(task_id=task_id, student_id=current_user.id)
        db.session.add(app)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/task/post', methods=['POST'])
@login_required
def post_task():
    if current_user.role != 'Business': return jsonify({'success': False})
    
    title = request.form.get('title')
    desc = request.form.get('description')
    budget = request.form.get('budget')
    deadline_str = request.form.get('deadline')
    category = request.form.get('category')
    
    deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
    
    task = Task(title=title, description=desc, budget=budget, deadline=deadline, category=category, business_id=current_user.id)
    db.session.add(task)
    db.session.commit()
    
    flash('Task posted successfully!', 'success')
    return redirect(url_for('business_dashboard'))

@app.route('/task/hire', methods=['POST'])
@login_required
def hire_student():
    if current_user.role != 'Business': return jsonify({'success': False})
    
    task_id = request.form.get('task_id')
    student_id = request.form.get('student_id')
    
    task = Task.query.get(task_id)
    if task and task.business_id == current_user.id:
        app = Application.query.filter_by(task_id=task_id, student_id=student_id).first()
        if app:
            app.status = 'accepted'
            task.status = 'in_progress'
            db.session.commit()
            return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/task/submit', methods=['POST'])
@login_required
def submit_work():
    if current_user.role != 'Student': return jsonify({'success': False})
    
    task_id = request.form.get('task_id')
    file_url = request.form.get('file_url')
    
    existing = Submission.query.filter_by(task_id=task_id, student_id=current_user.id).order_by(Submission.revision_number.desc()).first()
    rev = existing.revision_number + 1 if existing else 1
    
    sub = Submission(task_id=task_id, student_id=current_user.id, file_url=file_url, revision_number=rev)
    db.session.add(sub)
    db.session.commit()
    flash('Work submitted successfully!', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/task/complete', methods=['POST'])
@login_required
def complete_task():
    if current_user.role != 'Business': return jsonify({'success': False})
    task_id = request.form.get('task_id')
    task = Task.query.get(task_id)
    if task and task.business_id == current_user.id:
        task.status = 'completed'
        # student profile tasks_done += 1
        app = Application.query.filter_by(task_id=task_id, status='accepted').first()
        if app:
            profile = StudentProfile.query.filter_by(user_id=app.student_id).first()
            if profile:
                profile.tasks_done += 1
                recalculate_credscore(app.student_id)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/rate', methods=['POST'])
@login_required
def rate():
    task_id = request.form.get('task_id')
    ratee_id = request.form.get('ratee_id')
    score = int(request.form.get('score'))
    
    if not check_anti_gaming_flags(task_id, current_user.id, ratee_id, score):
        return jsonify({'success': False, 'message': 'Rating blocked due to suspicious activity.'})
        
    rating = Rating(task_id=task_id, rater_id=current_user.id, ratee_id=ratee_id, score=score)
    db.session.add(rating)
    
    # Check if both have rated to reveal
    other_rating = Rating.query.filter_by(task_id=task_id, rater_id=ratee_id, ratee_id=current_user.id).first()
    if other_rating:
        rating.revealed = True
        other_rating.revealed = True
        
        # Recalculate scores if applicable
        if current_user.role == 'Business': recalculate_credscore(ratee_id)
        else: recalculate_credscore(current_user.id)
        
    db.session.commit()
    return jsonify({'success': True})

@app.route('/profile/<int:student_id>')
def profile(student_id):
    student = User.query.get_or_404(student_id)
    if student.role != 'Student': return "Not found", 404
    completed_tasks = Task.query.join(Application).filter(Application.student_id == student_id, Task.status == 'completed').all()
    ratings = Rating.query.filter_by(ratee_id=student_id, revealed=True).all()
    return render_template('profile.html', student=student, tasks=completed_tasks, ratings=ratings)

@app.route('/admin/flags')
@login_required
def admin_flags():
    if current_user.role != 'Admin': return redirect(url_for('index'))
    flags = Flag.query.order_by(Flag.created_at.desc()).all()
    return render_template('admin_flags.html', flags=flags)

@app.route('/admin/flags/review/<int:flag_id>', methods=['POST'])
@login_required
def review_flag(flag_id):
    if current_user.role != 'Admin': return jsonify({'success': False})
    flag = Flag.query.get_or_404(flag_id)
    flag.reviewed = not flag.reviewed
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/shortlist', methods=['POST'])
@login_required
def shortlist():
    if current_user.role != 'Recruiter': return jsonify({'success': False})
    student_id = request.form.get('student_id')
    if not Shortlist.query.filter_by(recruiter_id=current_user.id, student_id=student_id).first():
        s = Shortlist(recruiter_id=current_user.id, student_id=student_id)
        db.session.add(s)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/how-it-works')
def how_it_works(): return render_template('how_it_works.html')

@app.route('/pricing')
def pricing(): return render_template('pricing.html')

@app.route('/about')
def about(): return render_template('about.html')

@app.route('/contact')
def contact(): return render_template('contact.html')

def seed_db():
    if User.query.count() > 0: return
    
    hashed_pw = bcrypt.hashpw(b'demo123', bcrypt.gensalt())
    hashed_admin = bcrypt.hashpw(b'admin123', bcrypt.gensalt())
    
    users = [
        User(name='B.Vaibhav', email='vaibhav@sai.edu', password_hash=hashed_pw, role='Student', college='SAI University'),
        User(name='Lingaesh S G', email='lingaesh@vit.edu', password_hash=hashed_pw, role='Student', college='VIT Vellore'),
        User(name='Navyathrega', email='navya@srm.edu', password_hash=hashed_pw, role='Student', college='SRM Institute'),
        User(name='Brew & Bites Café', email='cafe@brewbites.com', password_hash=hashed_pw, role='Business'),
        User(name='Zestify Foods', email='info@zestify.com', password_hash=hashed_pw, role='Business'),
        User(name='TechNova Solutions', email='hr@technova.com', password_hash=hashed_pw, role='Recruiter'),
        User(name='Admin', email='admin@credscore.io', password_hash=hashed_admin, role='Admin')
    ]
    
    for u in users: db.session.add(u)
    db.session.commit()
    
    for u in User.query.filter_by(role='Student'):
        profile = StudentProfile(user_id=u.id, credscore=85, tasks_done=5, on_time_rate=0.9, avg_rating=4.5, verified=True)
        db.session.add(profile)
        
    db.session.commit()
    
    task1 = Task(title='Design a menu banner', description='Need a modern menu banner', budget=400, deadline=datetime.utcnow().date() + timedelta(days=3), category='Design', business_id=4)
    db.session.add(task1)
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_db()
    app.run(debug=True)
