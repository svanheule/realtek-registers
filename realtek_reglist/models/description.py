import datetime
from sqlalchemy.ext.hybrid import hybrid_property

from . import db
from .auth import User

class DescriptionRevision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    value = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    author = db.relationship(User, backref=db.backref('contributions', lazy=True))

    object_id = db.Column(db.Integer, db.ForeignKey('described_object.id'), nullable=False)
    object = db.relationship('DescribedObject', backref=db.backref('description_revisions', lazy=True))

    def __repr__(self):
        return '<DescriptionRevision [{} @ {}] {}>'.format(
                self.author.username,
                self.timestamp,
                self.object
            )

class DescribedObject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Text, nullable=False)

    #description_revisions = db.relationship('description_revision', back_populates='object')

    # TODO Create a query that selects the latest revision, and can be used as a subquery
    @hybrid_property
    def description(self):
        if len(self.description_revisions) > 0:
            return self.description_revisions[-1].value
        else:
            return ''


    __mapper_args__ = {
        'polymorphic_on' : type,
        'polymorphic_identity' : 'described_object',
    }
