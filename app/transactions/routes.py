from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.transactions import transactions_bp
from app.forms import TransactionForm
from app.models import Transaction, Category
from datetime import datetime

@transactions_bp.route('/')
@login_required
def list_transactions():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    # For quick income form
    income_categories = Category.query.filter(
        (Category.user_id == None) | (Category.user_id == current_user.id),
        Category.type == 'income'
    ).all()
    return render_template('transactions.html', 
                         transactions=transactions,
                         income_categories=income_categories,
                         now_date=datetime.now().date().isoformat())


@transactions_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    form = TransactionForm()
    # Populate category choices
    categories = Category.query.filter((Category.user_id == None) | (Category.user_id == current_user.id)).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit():
        txn = Transaction(
            user_id=current_user.id,
            category_id=form.category_id.data,
            amount=form.amount.data,
            type=form.type.data,
            description=form.description.data,
            date=form.date.data
        )
        db.session.add(txn)
        db.session.commit()
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('transactions.list_transactions'))
    return render_template('transaction_form.html', form=form, title='Add Transaction')

@transactions_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    txn = Transaction.query.get_or_404(id)
    if txn.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('transactions.list_transactions'))
    
    form = TransactionForm(obj=txn)
    categories = Category.query.filter((Category.user_id == None) | (Category.user_id == current_user.id)).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit():
        txn.amount = form.amount.data
        txn.type = form.type.data
        txn.category_id = form.category_id.data
        txn.description = form.description.data
        txn.date = form.date.data
        db.session.commit()
        flash('Transaction updated.', 'success')
        return redirect(url_for('transactions.list_transactions'))
    return render_template('transaction_form.html', form=form, title='Edit Transaction')

@transactions_bp.route('/delete/<int:id>')
@login_required
def delete_transaction(id):
    txn = Transaction.query.get_or_404(id)
    if txn.user_id == current_user.id:
        db.session.delete(txn)
        db.session.commit()
        flash('Transaction deleted.', 'info')
    else:
        flash('Unauthorized.', 'danger')
    return redirect(url_for('transactions.list_transactions'))