from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.categories import categories_bp
from app.forms import CategoryForm
from app.models import Category

@categories_bp.route('/')
@login_required
def list_categories():
    system_cats = Category.query.filter_by(user_id=None).all()
    user_cats = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('categories.html', system_cats=system_cats, user_cats=user_cats)

@categories_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        cat = Category(
            name=form.name.data,
            type=form.type.data,
            user_id=current_user.id
        )
        db.session.add(cat)
        db.session.commit()
        flash('Category added.', 'success')
        return redirect(url_for('categories.list_categories'))
    return render_template('category_form.html', form=form)

@categories_bp.route('/delete/<int:id>')
@login_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    if cat.user_id == current_user.id:
        db.session.delete(cat)
        db.session.commit()
        flash('Category deleted.', 'info')
    else:
        flash('Unauthorized.', 'danger')
    return redirect(url_for('categories.list_categories'))