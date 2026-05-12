from flask import Blueprint
insights_bp = Blueprint('insights', __name__)
from . import routes