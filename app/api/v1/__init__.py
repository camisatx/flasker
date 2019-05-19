from flask import Blueprint

bp = Blueprint('api.v1', __name__)

# NOTE: Add extra blueprint routes to this import list
from app.api.v1 import errors, planes, tokens, users
