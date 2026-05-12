import os
import json
from datetime import datetime
from flask import render_template, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.insights import insights_bp
from app.models import Transaction, Category, Budget
from sqlalchemy import func
from groq import Groq

def get_days_in_month(year, month):
    if month == 12:
        next_month = datetime(year+1, 1, 1)
    else:
        next_month = datetime(year, month+1, 1)
    return (next_month - datetime(year, month, 1)).days

@insights_bp.route('/')
@login_required
def insights():
    now = datetime.now()
    year = now.year
    month = now.month
    current_day = now.day
    total_days = get_days_in_month(year, month)

    # -------------------------------
    # 1. Overall totals (for general advice)
    # -------------------------------
    total_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'income',
        Transaction.date >= datetime(year, month, 1)
    ).scalar() or 0
    total_expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        Transaction.date >= datetime(year, month, 1)
    ).scalar() or 0
    net = total_income - total_expense

        # -------------------------------
    # 2. Overall AI advice (EXTENSIVE version – like before)
    # -------------------------------
    overall_advice = "Add your Groq API key to get detailed financial advice."
    if os.environ.get('GROQ_API_KEY'):
        try:
            client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
            prompt = f"""You are an expert financial advisor for Indian college students and young adults. 
Based on this month's data, provide a **detailed, actionable financial advice** in 4-6 sentences. 
Cover these topics if relevant: saving habits, investment options (e.g., mutual funds, RD, gold), 
emergency fund, reducing unnecessary expenses, and setting financial goals. Be encouraging but practical. 
Use a friendly, conversational tone.

Data for this month:
- Total Income: ₹{total_income:.2f}
- Total Expenses: ₹{total_expense:.2f}
- Net Savings: ₹{net:.2f}

Give specific numbers and percentages where possible. Do NOT just say "save 20%". Provide reasoning and next steps."""
            
            resp = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=350  # Enough for a rich paragraph
            )
            overall_advice = resp.choices[0].message.content
        except Exception as e:
            overall_advice = f"AI advice unavailable. Error: {str(e)[:100]}"

    # -------------------------------
    # 3. Per‑category: burn rate, projection, and witty nudges
    # -------------------------------
    expense_cats = Category.query.filter(
        (Category.user_id == None) | (Category.user_id == current_user.id),
        Category.type == 'expense'
    ).all()

    category_data = []
    for cat in expense_cats:
        spent = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.category_id == cat.id,
            Transaction.type == 'expense',
            Transaction.date >= datetime(year, month, 1)
        ).scalar() or 0.0

        budget_entry = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=cat.id,
            month=month,
            year=year
        ).first()
        budget_limit = budget_entry.limit_amount if budget_entry else 0.0

        if spent == 0 and budget_limit == 0:
            continue

        if current_day > 0 and spent > 0:
            burn_rate = spent / current_day
            projected = burn_rate * total_days
        else:
            burn_rate = 0.0
            projected = 0.0

        warning = (projected > budget_limit) if budget_limit > 0 else (spent > 0)

        category_data.append({
            'name': cat.name,
            'spent': round(spent, 2),
            'budget': round(budget_limit, 2),
            'burn_rate': round(burn_rate, 2),
            'projected': round(projected, 2),
            'warning': warning
        })

    # Batch AI for witty nudges (only categories with warning)
    nudge_dict = {}
    categories_to_nudge = [c for c in category_data if c['warning']]
    if categories_to_nudge and os.environ.get('GROQ_API_KEY'):
        try:
            client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
            cat_summaries = [f"{c['name']}: spent ₹{c['spent']}, budget ₹{c['budget']}, projected ₹{c['projected']} at ₹{c['burn_rate']}/day" 
                             for c in categories_to_nudge]
            prompt = f"""You are a witty financial advisor for Indian college students. 
For each category below, provide a SINGLE very short (max 12 words) actionable nudge. Be funny but sharp. 
Return a JSON object: category name -> nudge.

Categories:
{chr(10).join(cat_summaries)}

Example: {{"Food": "Bro, mess food exists! Cut 2 Zomato orders.", "Entertainment": "Netflix & chill? More like net loss."}}
Respond ONLY with valid JSON."""
            resp = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.8,
                max_tokens=400
            )
            raw = resp.choices[0].message.content.strip()
            # Strip possible markdown code blocks
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            nudge_dict = json.loads(raw)
        except Exception as e:
            flash(f"Could not generate witty nudges: {str(e)[:100]}", "warning")

    for c in category_data:
        c['nudge'] = nudge_dict.get(c['name'], "Set a budget or slow down spending!")

    return render_template('insights.html',
                         overall_advice=overall_advice,
                         total_income=total_income,
                         total_expense=total_expense,
                         net=net,
                         category_data=category_data)