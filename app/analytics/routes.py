from flask import render_template, jsonify
from flask_login import login_required, current_user
from app import db
from app.analytics import analytics_bp
from app.models import Transaction, Category
from datetime import datetime, timedelta
from sqlalchemy import func

@analytics_bp.route('/')
@login_required
def analytics():
    return render_template('analytics.html')

@analytics_bp.route('/data')
@login_required
def chart_data():
    # Expense distribution pie (current month)
    now = datetime.now()
    start = datetime(now.year, now.month, 1)
    expenses = db.session.query(
        Category.name, func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        Transaction.date >= start,
        Transaction.category_id == Category.id
    ).group_by(Category.name).all()
    
    pie_labels = [e[0] for e in expenses]
    pie_values = [float(e[1]) for e in expenses]
    
    # Monthly income vs expense (last 6 months)
    monthly = []
    for i in range(5, -1, -1):
        month_date = now.replace(day=1) - timedelta(days=30*i)
        month_start = datetime(month_date.year, month_date.month, 1)
        month_end = datetime(month_date.year, month_date.month+1, 1) if month_date.month < 12 else datetime(month_date.year+1, 1, 1)
        
        inc = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'income',
            Transaction.date >= month_start,
            Transaction.date < month_end
        ).scalar() or 0
        
        exp = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'expense',
            Transaction.date >= month_start,
            Transaction.date < month_end
        ).scalar() or 0
        
        monthly.append({
            'month': month_start.strftime('%b %Y'),
            'income': float(inc),
            'expense': float(exp)
        })
    
    return jsonify({
        'pie_labels': pie_labels,
        'pie_values': pie_values,
        'monthly': monthly
    })