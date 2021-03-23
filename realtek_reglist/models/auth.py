from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import LoginManager, UserMixin

from . import db


login_manager = LoginManager()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True, nullable=False)

    def __repr__(self):
        return '<User {} ({}active)>'.format(self.username, '' if self.is_active else 'not ')


class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


