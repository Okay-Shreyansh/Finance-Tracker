from app import create_app, db
from app.models import User, Category

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    print("Tables created successfully.")

    # Default categories
    default_cats = [
        ('Food', 'expense'),
        ('Transport', 'expense'),
        ('Housing', 'expense'),
        ('Healthcare', 'expense'),
        ('Education', 'expense'),
        ('Entertainment', 'expense'),
        ('Shopping', 'expense'),
        ('Personal Care', 'expense'),
        ('Savings', 'expense'),
        ('Household Help', 'expense'),
        ('Festival', 'expense'),
        ('Other', 'expense'),
        ('Salary', 'income'),
        ('Freelance', 'income'),
        ('Business', 'income'),
        ('Investment', 'income'),
        ('Rental', 'income'),
        ('Other Income', 'income')
    ]

    for name, typ in default_cats:
        # Check if category already exists (system-wide, user_id=None)
        exists = Category.query.filter_by(name=name, user_id=None).first()
        if not exists:
            cat = Category(name=name, type=typ, user_id=None)
            db.session.add(cat)
            print(f"Added category: {name} ({typ})")

    db.session.commit()
    print("Database initialized with default categories!")