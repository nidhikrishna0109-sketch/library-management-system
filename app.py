from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'library-secret-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ===== 3 DATABASE TABLES =====
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student')

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True)
    category = db.Column(db.String(50))
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)

class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime)
    actual_return_date = db.Column(db.DateTime)
    fine = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='Issued')
    
    user = db.relationship('User', backref='issues')
    book = db.relationship('Book', backref='issues')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===== TEST ROUTE =====
# ===== ROUTES =====
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!')
            return redirect(url_for('register'))
        
        new_user = User(name=name, email=email, password=password, role='student')
        db.session.add(new_user)
        db.session.commit()
        flash('Registered successfully! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome {user.name}!')
            return redirect(url_for('index'))
        flash('Invalid email or password!')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied!')
        return redirect(url_for('index'))
    return render_template('admin.html')
@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    if current_user.role != 'admin':
        flash('Admin only!')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        category = request.form['category']
        copies = int(request.form['copies'])
        
        if Book.query.filter_by(isbn=isbn).first():
            flash('ISBN already exists!')
            return redirect(url_for('add_book'))
        
        new_book = Book(
            title=title, 
            author=author, 
            isbn=isbn, 
            category=category,
            total_copies=copies,
            available_copies=copies
        )
        db.session.add(new_book)
        db.session.commit()
        flash('Book added successfully!')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_book.html')

@app.route('/books', methods=['GET', 'POST'])
@login_required
def view_books():
    search = request.args.get('search')  # 👈 ഇത് Add ചെയ്യൂ
    if search:
        books = Book.query.filter(Book.title.contains(search)).all()  # 👈 Search Query
    else:
        books = Book.query.all()
    return render_template('books.html', books=books)
@app.route('/issue_book/<int:book_id>')
@login_required
def issue_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    if book.available_copies <= 0:
        flash('No copies available!')
        return redirect(url_for('view_books'))
    
    # Already issued check
    existing = Issue.query.filter_by(user_id=current_user.id, book_id=book_id, status='Issued').first()
    if existing:
        flash('You already issued this book!')
        return redirect(url_for('view_books'))
    
    # Issue the book
    new_issue = Issue(
        user_id=current_user.id,
        book_id=book_id,
        return_date=datetime.utcnow() + timedelta(days=14)
    )
    book.available_copies -= 1
    db.session.add(new_issue)
    db.session.commit()
    flash(f'Book "{book.title}" issued! Return by {(datetime.utcnow() + timedelta(days=14)).strftime("%d-%m-%Y")}')
    return redirect(url_for('view_books'))
@app.route('/my_books')
@login_required
def my_books():
    issued_books = Issue.query.filter_by(user_id=current_user.id, status='Issued').all()
    return render_template('my_books.html', issues=issued_books)

@app.route('/return_book/<int:issue_id>')
@login_required
def return_book(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    
    if issue.user_id != current_user.id:
        flash('Not your book!')
        return redirect(url_for('my_books'))
    
    days_overdue = (datetime.utcnow() - issue.return_date).days
    fine = days_overdue * 2 if days_overdue > 0 else 0
    
    issue.actual_return_date = datetime.utcnow()
    issue.fine = fine
    issue.status = 'Returned'
    issue.book.available_copies += 1
    
    db.session.commit()
    flash(f'Book returned! Fine: ₹{fine}')
    return redirect(url_for('my_books'))

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    if current_user.role != 'admin':
        return "Access Denied!",403

    book = Book.query.get_or_404(book_id)

    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        book.category = request.form['category']
        book.total_copies = int(request.form['total_copies'])
        book.available_copies = int(request.form['available_copies'])

        db.session.commit()
        flash('Book Updated Successfully!','success')
        return redirect(url_for('view_books'))
        
    return render_template('edit_book.html', book=book)

@app.route('/delete_book/<int:book_id>')
@login_required
def delete_book(book_id):
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Book Deleted Successfully!', 'danger')
    return redirect(url_for('view_books')) 
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Default Admin Account
        if not User.query.filter_by(email='admin@library.com').first():
            admin = User(
                name='Librarian',
                email='admin@library.com',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin Created: admin@library.com / admin123")
    app.run(debug=True)