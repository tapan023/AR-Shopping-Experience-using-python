from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Product, Cart, Order, OrderItem, ProductImage
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# SQLite Database Configuration (Back to original)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize Database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin user
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Sample products
        if not Product.query.first():
            products = [
                Product(
                    name='Premium Sofa',
                    description='High-quality mesh comfort sofa',
                    price=299.99,
                    main_image='/static/img/sofa.webp',
                    stock=50,
                    category='furniture',
                    images=[
                        ProductImage(image_url='/static/img/sofaqr.png', is_secondary=True)
                    ]
                ),
                Product(
                    name='Smart Lamp',
                    description='Advanced smart lamp',
                    price=199.99,
                    main_image='/static/img/lamp.png',
                    stock=30,
                    category='Electronics',
                    images=[
                        ProductImage(image_url='/static/img/chairqr.png', is_secondary=True)
                    ]
                ),
                Product(
                    name='Designer Chair',
                    description='Premium Quality chair',
                    price=49.99,
                    main_image='/static/img/chair.jpg',
                    stock=100,
                    category='furniture',
                    images=[
                        ProductImage(image_url='/static/img/lamp qr.png', is_secondary=True)
                    ]
                )
            ]
            db.session.add_all(products)
        
        db.session.commit()

# Routes
@app.route('/')
def index():
    featured_products = Product.query.filter_by(is_active=True).limit(4).all()
    return render_template('index.html', products=featured_products)

@app.route('/products')
def products():
    category = request.args.get('category')
    search = request.args.get('search')
    
    query = Product.query.filter_by(is_active=True)
    
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    products = query.all()
    categories = db.session.query(Product.category).distinct().all()
    return render_template('products.html', products=products, categories=categories)

@app.route('/product/<int:product_id>')
def product_detail(product_id ):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    # Check if product already in cart
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Product added to cart!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/update_cart/<int:cart_id>', methods=['POST'])
@login_required
def update_cart(cart_id):
    cart_item = Cart.query.get_or_404(cart_id)
    
    if cart_item.user_id != current_user.id:
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('cart'))
    
    action = request.form.get('action')
    
    if action == 'increase':
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
        else:
            flash('Cannot add more - limited stock available!', 'warning')
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            # Remove item if quantity becomes 0
            db.session.delete(cart_item)
            db.session.commit()
            flash('Item removed from cart!', 'success')
            return redirect(url_for('cart'))
    
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/remove_from_cart/<int:cart_id>')
@login_required
def remove_from_cart(cart_id):
    cart_item = Cart.query.get_or_404(cart_id)
    if cart_item.user_id != current_user.id:
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        
        if not cart_items:
            flash('Your cart is empty!', 'warning')
            return redirect(url_for('cart'))
        
        total_amount = sum(item.product.price * item.quantity for item in cart_items)
        
        # Create order
        order = Order(
            user_id=current_user.id,
            total_amount=total_amount,
            shipping_address=request.form['shipping_address']
        )
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
            db.session.add(order_item)
        
        # Clear cart
        Cart.query.filter_by(user_id=current_user.id).delete()
        
        db.session.commit()
        flash('Order placed successfully!', 'success')
        return redirect(url_for('index'))
    
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)

# Fixed AR experience route
@app.route('/ar_experience/<int:product_id>')
def ar_experience(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('ar_experience.html', product=product)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation checks
        errors = []
        
        if len(username) < 3 or len(username) > 20:
            errors.append('Username must be between 3 and 20 characters')
        
        if not username.isalnum():
            errors.append('Username can only contain letters and numbers')
        
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists!')
        
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered!')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html')
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        remember = bool(request.form.get('remember'))
        
        # Check if input is email or username
        if '@' in username:
            user = User.query.filter_by(email=username).first()
        else:
            user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            
            # Basic security check for next parameter
            if next_page and not next_page.startswith('/'):
                next_page = None
                
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username/email or password!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Admin routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))
    
    return render_template('admin/dashboard.html')

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))
    
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)