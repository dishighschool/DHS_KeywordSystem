"""Application-wide extension instances."""
from __future__ import annotations

from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
oauth = OAuth()
csrf = CSRFProtect()
