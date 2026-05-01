from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
from functools import wraps
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///event_decor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads/portfolio'

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Change this
app.config['MAIL_PASSWORD'] = 'your-app-password'      # Change this
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

db = SQLAlchemy(app)
mail = Mail(app)

# Database Models
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), default='')
    event_date = db.Column(db.String(50))
    event_type = db.Column(db.String(50))
    sub_type = db.Column(db.String(50))
    budget = db.Column(db.String(50))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='new')  # new, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PortfolioItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    photos = db.relationship('EventPhoto', backref='portfolio_item', lazy=True, cascade="all, delete-orphan")

class EventPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portfolio_item_id = db.Column(db.Integer, db.ForeignKey('portfolio_item.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PricingItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # 'private' or 'corporate'
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.String(100), nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes - Main Website
@app.route('/')
def home():
    imgs = {}
    for k, v in [('hero', 'hero.jpg'), ('private', 'private_category.jpg'), ('corp', 'corp_category.jpg')]:
        imgs[f'has_{k}'] = os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], v))
    
    private_pricing = PricingItem.query.filter_by(category='private').all()
    corp_pricing = PricingItem.query.filter_by(category='corporate').all()
    
    # Fetch random photos for the portfolio category sliders
    def get_category_photos(cat):
        try:
            items = PortfolioItem.query.filter_by(category=cat).all()
            urls = []
            for item in items:
                if item.image_url:
                    urls.append(item.image_url)
                for photo in item.photos:
                    urls.append(photo.image_url)
            import random
            random.shuffle(urls)
            return urls[:12]  # Limit to 12 photos for home page sliders
        except:
            return []
    
    private_photos = get_category_photos('private')
    corporate_photos = get_category_photos('corporate')
    
    return render_template('index.html', 
                           private_pricing=private_pricing, 
                           corp_pricing=corp_pricing, 
                           private_photos=private_photos,
                           corporate_photos=corporate_photos,
                           **imgs)

@app.route('/events/<category>')
def events_list(category):
    if category not in ['private', 'corporate']:
        return redirect(url_for('home'))
    portfolio_items = PortfolioItem.query.filter_by(category=category).order_by(PortfolioItem.created_at.desc()).all()
    return render_template('events.html', category=category, portfolio_items=portfolio_items)

@app.route('/event/<int:id>')
def event_detail(id):
    item = PortfolioItem.query.get_or_404(id)
    photos = EventPhoto.query.filter_by(portfolio_item_id=id).all()
    return render_template('event_detail.html', item=item, photos=photos)


@app.route('/submit_order', methods=['POST'])
def submit_order():
    try:
        order = Order(
            name=request.form.get('name'),
            phone=request.form.get('phone'),
            email=request.form.get('email', ''),
            event_type=request.form.get('event_type'),
            sub_type=request.form.get('sub_type'),
            budget=request.form.get('budget'),
            message=request.form.get('message')
        )
        db.session.add(order)
        db.session.commit()
        
        # Send email notification
        send_order_email(order)
        
        flash('Ваша заявка успешно отправлена! Мы свяжемся с вами в ближайшее время.', 'success')
        return redirect(url_for('home'))
    except Exception as e:
        flash('Произошла ошибка при отправке заявки. Попробуйте позже.', 'error')
        return redirect(url_for('home'))

def send_order_email(order):
    try:
        msg = Message(
            subject=f'Новая заявка от {order.name}',
            recipients=[app.config['MAIL_USERNAME']],
            body=f'''
Новая заявка на сайте Event Decor!

Имя: {order.name}
Телефон: {order.phone}
Email: {order.email or 'Не указан'}
Тип мероприятия: {order.event_type or 'Не указан'}
Подтип: {order.sub_type or 'Не указан'}
Бюджет: {order.budget or 'Не указан'}
Сообщение: {order.message or 'Нет'}

Дата создания: {order.created_at}
            '''
        )
        mail.send(msg)
    except Exception as e:
        print(f'Error sending email: {e}')

# Routes - Admin Panel
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.password == password:  # In production, use password hashing!
            session['logged_in'] = True
            session['admin_username'] = username
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    session.pop('admin_username', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    stats = {
        'total_orders': Order.query.count(),
        'new_orders': Order.query.filter_by(status='new').count(),
        'completed': Order.query.filter_by(status='completed').count(),
        'portfolio_items': PortfolioItem.query.count()
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)

@app.route('/admin/orders')
@login_required
def admin_orders():
    status_filter = request.args.get('status')
    if status_filter:
        orders = Order.query.filter_by(status=status_filter).order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/order/<int:id>')
@login_required
def admin_order_detail(id):
    order = Order.query.get_or_404(id)
    return render_template('admin/order_detail.html', order=order)

@app.route('/admin/order/<int:id>/update_status', methods=['POST'])
@login_required
def admin_update_order_status(id):
    order = Order.query.get_or_404(id)
    order.status = request.form.get('status')
    db.session.commit()
    flash('Статус заказа обновлен', 'success')
    return redirect(url_for('admin_order_detail', id=id))

@app.route('/admin/order/<int:id>/delete', methods=['POST'])
@login_required
def admin_delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    flash('Заказ удален', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/portfolio')
@login_required
def admin_portfolio():
    portfolio_items = PortfolioItem.query.order_by(PortfolioItem.created_at.desc()).all()
    return render_template('admin/portfolio.html', portfolio_items=portfolio_items)

@app.route('/admin/portfolio/add', methods=['GET', 'POST'])
@login_required
def admin_portfolio_add():
    if request.method == 'POST':
        image_url = ''
        file = request.files.get('image_file')
        if file and file.filename:
            ext = os.path.splitext(file.filename)[1]
            filename = str(uuid.uuid4()) + ext
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_url = '/' + file_path.replace('\\', '/')

        item = PortfolioItem(
            title=request.form.get('title'),
            description=request.form.get('description'),
            image_url=image_url,
            category=request.form.get('category')
        )
        db.session.add(item)
        
        photos = request.files.getlist('photos')
        for photo_file in photos:
            if photo_file and photo_file.filename:
                ext = os.path.splitext(photo_file.filename)[1]
                photo_filename = str(uuid.uuid4()) + ext
                photo_file_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
                photo_file.save(photo_file_path)
                p_url = '/' + photo_file_path.replace('\\', '/')
                new_photo = EventPhoto(portfolio_item=item, image_url=p_url)
                db.session.add(new_photo)

        db.session.commit()
        flash('Элемент портфолио добавлен', 'success')
        return redirect(url_for('admin_portfolio'))
    return render_template('admin/portfolio_form.html', item=None, photos=[])

@app.route('/admin/portfolio/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_portfolio_edit(id):
    item = PortfolioItem.query.get_or_404(id)
    if request.method == 'POST':
        item.title = request.form.get('title')
        item.description = request.form.get('description')
        item.category = request.form.get('category')
        
        file = request.files.get('image_file')
        if file and file.filename:
            ext = os.path.splitext(file.filename)[1]
            filename = str(uuid.uuid4()) + ext
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            item.image_url = '/' + file_path.replace('\\', '/')
            
        photos = request.files.getlist('photos')
        for photo_file in photos:
            if photo_file and photo_file.filename:
                ext = os.path.splitext(photo_file.filename)[1]
                photo_filename = str(uuid.uuid4()) + ext
                photo_file_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
                photo_file.save(photo_file_path)
                p_url = '/' + photo_file_path.replace('\\', '/')
                new_photo = EventPhoto(portfolio_item=item, image_url=p_url)
                db.session.add(new_photo)
            
        db.session.commit()
        flash('Элемент портфолио обновлен', 'success')
        return redirect(url_for('admin_portfolio'))
        
    photos = EventPhoto.query.filter_by(portfolio_item_id=id).all()
    return render_template('admin/portfolio_form.html', item=item, photos=photos)

@app.route('/admin/portfolio/delete/<int:id>', methods=['POST'])
@login_required
def admin_portfolio_delete(id):
    item = PortfolioItem.query.get_or_404(id)
    # Delete associated photos
    photos = EventPhoto.query.filter_by(portfolio_item_id=id).all()
    for photo in photos:
        # Delete file if exists
        file_path = os.path.join(app.root_path, photo.image_url.lstrip('/'))
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        db.session.delete(photo)
    
    # Delete main image if it's not a generic one
    if item.image_url:
        file_path = os.path.join(app.root_path, item.image_url.lstrip('/'))
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
                
    db.session.delete(item)
    db.session.commit()
    flash('Работа удалена', 'success')
    return redirect(url_for('admin_portfolio'))


@app.route('/admin/pricing', methods=['GET', 'POST'])
@login_required
def admin_pricing():
    if request.method == 'POST':
        category = request.form.get('category')
        name = request.form.get('name')
        price = request.form.get('price')
        if category and name and price:
            item = PricingItem(category=category, name=name, price=price)
            db.session.add(item)
            db.session.commit()
            flash('Услуга добавлена', 'success')
        return redirect(url_for('admin_pricing'))
        
    private_items = PricingItem.query.filter_by(category='private').all()
    corporate_items = PricingItem.query.filter_by(category='corporate').all()
    return render_template('admin/pricing.html', private_items=private_items, corporate_items=corporate_items)

@app.route('/admin/pricing/delete/<int:id>', methods=['POST'])
@login_required
def admin_pricing_delete(id):
    item = PricingItem.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Услуга удалена', 'success')
    return redirect(url_for('admin_pricing'))

@app.route('/admin/portfolio/<int:id>/photos', methods=['GET', 'POST'])
@login_required
def admin_portfolio_photos(id):
    item = PortfolioItem.query.get_or_404(id)
    if request.method == 'POST':
        file = request.files.get('photo')
        if file and file.filename:
            filename = secure_filename(file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            photo_url = '/' + file_path.replace('\\', '/')
            new_photo = EventPhoto(portfolio_item_id=item.id, image_url=photo_url)
            db.session.add(new_photo)
            db.session.commit()
            flash('Фотография добавлена', 'success')
        return redirect(url_for('admin_portfolio_photos', id=id))
    
    photos = EventPhoto.query.filter_by(portfolio_item_id=id).all()
    return render_template('admin/portfolio_photos.html', item=item, photos=photos)

@app.route('/admin/portfolio/photo/delete/<int:photo_id>', methods=['POST'])
@login_required
def admin_portfolio_photo_delete(photo_id):
    photo = EventPhoto.query.get_or_404(photo_id)
    item_id = photo.portfolio_item_id
    db.session.delete(photo)
    db.session.commit()
    flash('Фотография удалена из галереи', 'success')
    return redirect(url_for('admin_portfolio_edit', id=item_id))


# Initialize database and create default admin
def init_db():
    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(username='admin', password='admin123')  # Change this!
            db.session.add(admin)
            db.session.commit()
            print('Default admin created: username=admin, password=admin123')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
