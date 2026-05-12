from flask import Blueprint
budget_bp = Blueprint('budget', __name__)
from . import routes