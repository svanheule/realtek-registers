import datetime
from sqlalchemy import func, select, and_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import aliased, column_property

from . import db
from .auth import User

class DescriptionRevision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    value = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    author = db.relationship(User, backref=db.backref('contributions', lazy=True))

    object_id = db.Column(db.Integer, db.ForeignKey('described_object.id'), nullable=False)
    object = db.relationship('DescribedObject', back_populates='description_revisions')

    def __repr__(self):
        return '<DescriptionRevision [{} @ {}] {}>'.format(
                self.author.username,
                self.timestamp,
                self.object
            )

class DescribedObject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Text, nullable=False)

    description_revisions = db.relationship(DescriptionRevision, back_populates='object')
    last_updated = column_property(
            select([func.max(DescriptionRevision.timestamp)])\
                .group_by(DescriptionRevision.object_id)\
                .where(DescriptionRevision.object_id == id)\
                .correlate_except(DescriptionRevision)\
                .scalar_subquery()
        )
    description = column_property(
            select([DescriptionRevision.value]).where(
                and_(
                    DescriptionRevision.object_id == id,
                    DescriptionRevision.timestamp == last_updated
                )
            ).scalar_subquery()
        )

    @hybrid_property
    def meta_description(self):
        meta_attr = self.get_description_metadata()
        desc = self.description

        if len(meta_attr) and desc:
            meta_tags = '\n'.join('{}: {}'.format(k,v) for k,v in meta_attr.items())
            return meta_tags + '\n\n' + desc
        else:
            return desc

    def get_description_metadata(self):
        return dict()

    __mapper_args__ = {
        'polymorphic_on' : type,
        'polymorphic_identity' : 'described_object',
    }
