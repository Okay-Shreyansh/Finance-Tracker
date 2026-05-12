from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.budget import budget_bp
from app.forms import BudgetForm
from app.models import Budget, Category, Transaction
from datetime import datetime
from sqlalchemy import func

@budget_bp.route('/', methods=['GET', 'POST'])
@login_required
def manage_budgets():
    now = datetime.now()
    month = now.month
    year = now.year
    
    form = BudgetForm()
    expense_cats = Category.query.filter(
        (Category.user_id == None) | (Category.user_id == current_user.id),
        Category.type == 'expense'
    ).all()
    form.category_id.choices = [(c.id, c.name) for c in expense_cats]
    
    if form.validate_on_submit():
        budget = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=form.category_id.data,
            month=month,
            year=year
        ).first()
        if budget:
            budget.limit_amount = form.limit_amount.data
        else:
            budget = Budget(
                user_id=current_user.id,
                category_id=form.category_id.data,
                month=month,
                year=year,
                limit_amount=form.limit_amount.data
            )
            db.session.add(budget)
        db.session.commit()
        flash('Budget saved.', 'success')
        return redirect(url_for('budget.manage_budgets'))
    
    # Show existing budgets with progress
    budgets = Budget.query.filter_by(user_id=current_user.id, month=month, year=year).all()
    budget_data = []
    for b in budgets:
        spent = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.category_id == b.category_id,
            Transaction.type == 'expense',
            Transaction.date >= datetime(year, month, 1)
        ).scalar() or 0
        percent = (spent / b.limit_amount) * 100 if b.limit_amount > 0 else 0
        percent = min(percent, 100)  # cap at 100%
        
        # Determine CSS class here (backend logic)
        if percent >= 100:
            bar_class = "bg-danger"
        elif percent >= 80:
            bar_class = "bg-warning"
        else:
            bar_class = "bg-success"
        
        budget_data.append({
            'category': b.category.name,
            'limit': b.limit_amount,
            'spent': spent,
            'percent': percent,
            'bar_class': bar_class,
            'alert_80': percent >= 80,
            'alert_100': percent >= 100
        })
    
    return render_template('budgets.html', form=form, budgets=budget_data)

@budget_bp.route('/set_from_suggestion', methods=['POST'])
@login_required
def set_from_suggestion():
    from flask import request, jsonify
    data = request.get_json()
    category_name = data.get('category')
    amount = float(data.get('amount'))
    
    category = Category.query.filter_by(name=category_name, user_id=None).first()
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'})
    
    now = datetime.now()
    budget = Budget.query.filter_by(
        user_id=current_user.id,
        category_id=category.id,
        month=now.month,
        year=now.year
    ).first()
    if budget:
        budget.limit_amount = amount
    else:
        budget = Budget(
            user_id=current_user.id,
            category_id=category.id,
            month=now.month,
            year=now.year,
            limit_amount=amount
        )
        db.session.add(budget)
    db.session.commit()
    return jsonify({'success': True})