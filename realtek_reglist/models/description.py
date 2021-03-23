import datetime
from sqlalchemy.ext.hybrid import hybrid_property

from . import db

class DescriptionRevision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    value = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('contributions', lazy=True))


class DescriptionMixin:
    @hybrid_property
    def description(self):
        if len(self.description_revisions) > 0:
            return self.description_revisions[-1].value
        else:
            return ''


