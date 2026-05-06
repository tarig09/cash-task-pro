from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 's3cr3t_k3y_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    password = db.Column(db.String(200))
    balance = db.Column(db.Float, default=0)
    total_earned = db.Column(db.Float, default=0)
    tasks_completed = db.Column(db.Integer, default=0)
    is_banned = db.Column(db.Boolean, default=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(500))
    reward = db.Column(db.Float)
    site_value = db.Column(db.Float)
    link = db.Column(db.String(500))
    category = db.Column(db.String(50))
    completed_by = db.Column(db.Integer, nullable=True)

class Withdraw(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    method = db.Column(db.String(50))
    account_info = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = generate_password_hash(request.form['password'])
        
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, phone=phone, password=password)
        db.session.add(user)
        db.session.commit()
        flash('تم التسجيل بنجاح', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            if user.is_banned:
                flash('حسابك محظور', 'danger')
                return redirect(url_for('login'))
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('بيانات غير صحيحة', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter(Task.completed_by == None).all()
    pending = Withdraw.query.filter_by(user_id=current_user.id, status='pending').first()
    return render_template('dashboard.html', user=current_user, tasks=tasks, pending_withdraw=pending)

@app.route('/complete_task/<int:task_id>')
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.completed_by:
        flash('المهمة مكتملة', 'warning')
        return redirect(url_for('dashboard'))
    
    current_user.balance += task.reward
    current_user.total_earned += task.reward
    current_user.tasks_completed += 1
    task.completed_by = current_user.id
    db.session.commit()
    flash(f'ربحت {task.reward} جنيه', 'success')
    return redirect(url_for('dashboard'))

@app.route('/request_withdraw', methods=['POST'])
@login_required
def request_withdraw():
    amount = float(request.form['amount'])
    method = request.form['method']
    account_info = request.form['account_info']
    
    if amount < 50:
        flash('الحد الأدنى 50 جنيه', 'danger')
        return redirect(url_for('dashboard'))
    if amount > current_user.balance:
        flash('الرصيد غير كاف', 'danger')
        return redirect(url_for('dashboard'))
    
    w = Withdraw(user_id=current_user.id, amount=amount, method=method, account_info=account_info)
    current_user.balance -= amount
    db.session.add(w)
    db.session.commit()
    flash('تم طلب السحب', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ============ لوحة تحكم المشرف ============

ADMIN_USERNAME = 'admin'

@app.route('/admin')
@login_required
def admin_panel():
    if current_user.username != ADMIN_USERNAME:
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('dashboard'))
    users = User.query.all()
    withdrawals = Withdraw.query.all()
    tasks = Task.query.all()
    return render_template('admin.html', users=users, withdrawals=withdrawals, tasks=tasks)

@app.route('/admin/ban/<int:user_id>')
@login_required
def admin_ban(user_id):
    if current_user.username != ADMIN_USERNAME:
        return redirect(url_for('dashboard'))
    user = User.query.get_or_404(user_id)
    user.is_banned = True
    db.session.commit()
    flash(f'تم حظر {user.username}', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/approve_withdraw/<int:withdraw_id>')
@login_required
def admin_approve_withdraw(withdraw_id):
    if current_user.username != ADMIN_USERNAME:
        return redirect(url_for('dashboard'))
    w = Withdraw.query.get_or_404(withdraw_id)
    w.status = 'approved'
    db.session.commit()
    flash('تم قبول السحب', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_task/<int:task_id>')
@login_required
def admin_delete_task(task_id):
    if current_user.username != ADMIN_USERNAME:
        return redirect(url_for('dashboard'))
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('تم حذف المهمة', 'success')
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if Task.query.count() == 0:
            tasks = [
                Task(title="متابعة فيسبوك", description="تابع صفحتنا", reward=5, site_value=7, link="#", category="فيسبوك"),
                Task(title="متابعة تيك توك", description="تابع حسابنا", reward=7, site_value=10, link="#", category="تيك توك"),
            ]
            db.session.add_all(tasks)
            db.session.commit()
    app.run(host='0.0.0.0', port=5000, debug=True)
