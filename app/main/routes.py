from flask import render_template
from flask_login import login_required, current_user
from app import db
from app.main import main_bp
from app.models import Transaction, Budget, Category
from datetime import datetime
from sqlalchemy import func

@main_bp.route('/')
@login_required
def dashboard():
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    
    total_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'income',
        Transaction.date >= month_start
    ).scalar() or 0
    
    total_expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        Transaction.date >= month_start
    ).scalar() or 0
    
    balance = total_income - total_expense
    
    recent = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).limit(5).all()
    
    budgets = Budget.query.filter_by(user_id=current_user.id, month=now.month, year=now.year).all()
    alerts = []
    for b in budgets:
        spent = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.category_id == b.category_id,
            Transaction.type == 'expense',
            Transaction.date >= month_start
        ).scalar() or 0
        if spent > 0:
            percent = (spent / b.limit_amount) * 100 if b.limit_amount else 0
            if percent >= 80:
                alerts.append({
                    'category': b.category.name,
                    'spent': spent,
                    'limit': b.limit_amount,
                    'over': percent >= 100
                })
    
    # Get income categories (system + user)
    income_categories = Category.query.filter(
        (Category.user_id == None) | (Category.user_id == current_user.id),
        Category.type == 'income'
    ).all()
    
    return render_template('index.html', 
                         total_income=total_income, 
                         total_expense=total_expense,
                         balance=balance, 
                         recent=recent, 
                         alerts=alerts,
                         income_categories=income_categories,
                         now_date=now.date().isoformat())

@main_bp.route('/about')
@login_required
def about():
    return render_template('about.html')

@main_bp.route('/help')
@login_required
def help_page():
    return render_template('help.html')

@main_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@main_bp.route('/security')
@login_required
def security():
    return render_template('security.html')