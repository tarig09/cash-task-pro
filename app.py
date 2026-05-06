from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 's3cr3t_k3y_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ============ نماذج قاعدة البيانات ============
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    password = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Float, default=0)
    total_earned = db.Column(db.Float, default=0)
    tasks_completed = db.Column(db.Integer, default=0)
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    reward = db.Column(db.Float, default=0)
    site_value = db.Column(db.Float, default=0)
    link = db.Column(db.String(500))
    category = db.Column(db.String(50))
    completed_by = db.Column(db.Integer, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Withdraw(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50))
    account_info = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============ الصفحات الرئيسية ============
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
            flash('اسم المستخدم موجود مسبقاً', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email, phone=phone, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('تم التسجيل بنجاح! يمكنك الدخول الآن', 'success')
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
                flash(f'حسابك محظور: {user.ban_reason}', 'danger')
                return redirect(url_for('login'))
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_banned:
        logout_user()
        flash('حسابك محظور', 'danger')
        return redirect(url_for('login'))
    
    tasks = Task.query.filter(Task.completed_by == None).all()
    pending_withdraw = Withdraw.query.filter_by(user_id=current_user.id, status='pending').first()
    
    return render_template('dashboard.html', 
                         user=current_user, 
                         tasks=tasks, 
                         pending_withdraw=pending_withdraw)

@app.route('/complete_task/<int:task_id>')
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    if task.completed_by:
        flash('هذه المهمة مكتملة بالفعل', 'warning')
        return redirect(url_for('dashboard'))
    
    # إضافة الرصيد للمستخدم
    current_user.balance += task.reward
    current_user.total_earned += task.reward
    current_user.tasks_completed += 1
    
    # تحديث المهمة
    task.completed_by = current_user.id
    task.completed_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'🎉 تم إكمال المهمة بنجاح! ربحت {task.reward} جنيه', 'success')
    return redirect(url_for('dashboard'))

@app.route('/request_withdraw', methods=['POST'])
@login_required
def request_withdraw():
    amount = float(request.form['amount'])
    method = request.form['method']
    account_info = request.form['account_info']
    
    # التحقق من الحد الأدنى
    if amount < 50:
        flash('الحد الأدنى للسحب هو 50 جنيه', 'danger')
        return redirect(url_for('dashboard'))
    
    # التحقق من الرصيد
    if amount > current_user.balance:
        flash('الرصيد غير كافٍ', 'danger')
        return redirect(url_for('dashboard'))
    
    # إنشاء طلب سحب
    withdraw = Withdraw(
        user_id=current_user.id,
        amount=amount,
        method=method,
        account_info=account_info
    )
    
    # خصم الرصيد
    current_user.balance -= amount
    
    db.session.add(withdraw)
    db.session.commit()
    
    flash('✅ تم إرسال طلب السحب بنجاح! سيتم معالجته يوم الجمعة', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ============ إنشاء مهام تجريبية ============
def create_sample_tasks():
    if Task.query.count() == 0:
        sample_tasks = [
            Task(
                title="👍 متابعة صفحة فيسبوك",
                description="ادخل على صفحتنا على فيسبوك واضغط متابعة (Like)",
                reward=5.0,
                site_value=7.0,
                link="https://www.facebook.com/mohammed.tarig.398446",
                category="فيسبوك"
            ),
            Task(
                title="🎵 متابعة تيك توك",
                description="تابع حسابنا على تيك توك",
                reward=7.0,
                site_value=10.0,
                link="https://tiktok.com/@YOUR_TIKTOK",
                category="تيك توك"
            ),
            Task(
                title="💬 انضمام لواتساب",
                description="انضم إلى مجموعة واتساب الرسمية",
                reward=3.0,
                site_value=4.5,
                link="https://wa.me/YOUR_NUMBER",
                category="واتساب"
            ),
            Task(
                title="📸 متابعة انستغرام",
                description="تابع حسابنا على انستغرام",
                reward=5.0,
                site_value=7.0,
                link="https://instagram.com/YOUR_INSTAGRAM",
                category="انستغرام"
            ),
            Task(
                title="✍️ تعليق على منشور",
                description="اكتب تعليقاً إيجابياً على صفحتنا",
                reward=6.0,
                site_value=9.0,
                link="https://www.facebook.com/mohammed.tarig.398446",
                category="تفاعل"
            ),
            Task(
                title="📢 دعوة أصدقاء",
                description="ادعُ أصدقائك للتسجيل في الموقع",
                reward=10.0,
                site_value=15.0,
                link="#",
                category="دعوة"
            )
        ]
        db.session.add_all(sample_tasks)
        db.session.commit()
        print("✓ تم إنشاء المهام التجريبية بنجاح!")

# ============ تشغيل الموقع ============
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_sample_tasks()
        print("✓ قاعدة البيانات جاهزة!")
        print("✓ الموقع جاهز للتشغيل!")
    app.run(host='0.0.0.0', port=5000, debug=True)
