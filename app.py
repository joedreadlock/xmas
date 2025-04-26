from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Gift, Claim
from bs4 import BeautifulSoup
import requests, os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URL', 'sqlite:///gift_registry.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

ADMIN_EMAIL = 'mize8@hotmail.com'

def fetch_preview_image(url):
    try:
        resp = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(resp.text, 'html.parser')
        og = soup.find('meta', property='og:image')
        if og and og.get('content'):
            return og['content']
        img = soup.find('img')
        return img['src'] if img and img.get('src') else None
    except:
        return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        role = 'parent' if email == ADMIN_EMAIL else 'member'
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    if current_user.role == 'parent':
        gifts = Gift.query.order_by(Gift.date_entered.desc()).all()
    else:
        gifts = Gift.query.filter_by(parents_only=False).order_by(Gift.date_entered.desc()).all()
    def display_claims(gift):
        if not gift.claims:
            return []
        claimant = gift.claims[-1].claimed_by_user
        return ['Anonymous'] if current_user.role != 'parent' else [claimant.name]
    return render_template('index.html', gifts=gifts, display_claims=display_claims)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_gift():
    if request.method == 'POST':
        name = request.form['name']
        url = request.form.get('url')
        parents_only = 'parents_only' in request.form
        gift = Gift(name=name, description_or_url=url, parents_only=parents_only, entered_by_user=current_user)
        if url:
            preview = fetch_preview_image(url)
            gift.preview_image_url = preview
        db.session.add(gift)
        db.session.commit()
        flash('Gift added!')
        return redirect(url_for('index'))
    return render_template('add_gift.html')

@app.route('/claim/<int:gift_id>', methods=['POST'])
@login_required
def claim_gift(gift_id):
    gift = Gift.query.get_or_404(gift_id)
    if gift.parents_only and current_user.role != 'parent':
        flash('Not allowed')
        return redirect(url_for('index'))
    claim = Claim(gift=gift, claimed_by_user=current_user)
    db.session.add(claim)
    db.session.commit()
    flash('Gift claimed!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email=ADMIN_EMAIL).first():
            admin_password = os.getenv('ADMIN_PASSWORD', 'changeMe123')
            admin = User(name='Admin', email=ADMIN_EMAIL, role='parent')
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
