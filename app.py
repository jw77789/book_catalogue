from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import requests
from models import db, User, Book

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash("Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(username=request.form['username'], password=request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully! Please log in.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        isbn = request.form['isbn']
        res = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}')
        data = res.json()
        if 'items' in data:
            info = data['items'][0]['volumeInfo']
            title = info.get('title', 'Unknown')
            authors = ', '.join(info.get('authors', ['Unknown']))
            page_count = info.get('pageCount', 0)
            average_rating = info.get('averageRating', 0.0)
            book = Book(title=title, author=authors, page_count=page_count,
                        average_rating=average_rating, user_id=current_user.id)
            db.session.add(book)
            db.session.commit()
            flash("Book added!")
        else:
            flash("Book not found.")
    books = Book.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', books=books)

@app.route('/delete/<int:book_id>')
@login_required
def delete(book_id):
    book = Book.query.get_or_404(book_id)
    if book.user_id == current_user.id:
        db.session.delete(book)
        db.session.commit()
        flash("Book deleted.")
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
