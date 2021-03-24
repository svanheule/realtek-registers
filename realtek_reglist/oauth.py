from flask import redirect
from flask_dance.contrib.github import github, make_github_blueprint
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_login import current_user, login_user
import os

from .models import db
from .models.auth import OAuth, User

github_blueprint = make_github_blueprint(
    storage=SQLAlchemyStorage(
        OAuth,
        db.session,
        user=current_user,
        user_required=False,
    ),
)
