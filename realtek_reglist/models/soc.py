from sqlalchemy.ext.hybrid import hybrid_property

from . import db
from .description import DescribedObject

class Family(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '<Family RTL{:04x} {}>'.format(self.id, self.name)


class Feature(db.Model):
    __table_args__ = (db.UniqueConstraint('family_id', 'name', name='u_family_feature'),)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)

    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    family = db.relationship('Family', backref=db.backref('features', lazy=True))

    def __repr__(self):
        return '<Feature {}/{}>'.format(self.family.name, self.name)


class Register(DescribedObject):
    __table_args__ = (db.UniqueConstraint('family_id', 'name', name='u_family_register'),)
    id = db.Column(db.Integer, db.ForeignKey(DescribedObject.id), primary_key=True)
    name = db.Column(db.Text, nullable=False)
    offset = db.Column(db.Integer, nullable=False)
    port_idx_min = db.Column(db.Integer, nullable=False)
    port_idx_max = db.Column(db.Integer, nullable=False)
    array_idx_min = db.Column(db.Integer, nullable=False)
    array_idx_max = db.Column(db.Integer, nullable=False)
    portlist_idx = db.Column(db.Integer, nullable=False)
    bit_offset = db.Column(db.Integer, nullable=False)

    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    family = db.relationship('Family', backref=db.backref('registers', lazy=True))

    feature_id = db.Column(db.Integer, db.ForeignKey('feature.id'), nullable=False)
    feature = db.relationship('Feature', backref=db.backref('registers', lazy=True))

    tables = db.relationship('Table',
        primaryjoin='or_(Register.id == Table.ctrl_register_id, Register.id == Table.data_register_id)',
        order_by='Table.name')

    __mapper_args__ = {
        'polymorphic_identity' : 'register',
    }

    def get_description_metadata(self):
        return {'regdoc_platform': self.family.name}

    def __repr__(self):
        return '<Register {}/{} : 0x{:04x}>'.format(self.family.name, self.name, self.offset)


class Field(DescribedObject):
    __table_args__ = (db.UniqueConstraint('register_id', 'lsb', name='u_register_field'),)
    id = db.Column(db.Integer, db.ForeignKey(DescribedObject.id), primary_key=True)
    name = db.Column(db.Text, nullable=False)
    lsb = db.Column(db.Integer, nullable=False)
    size = db.Column(db.Integer, nullable=False)

    register_id = db.Column(db.Integer, db.ForeignKey(Register.id), nullable=False)
    register = db.relationship(Register, backref=db.backref('fields', lazy=True), foreign_keys=[register_id])

    __mapper_args__ = {
        'polymorphic_identity' : 'field',
    }

    def get_description_metadata(self):
        return {'regdoc_platform': self.register.family.name}

    def __repr__(self):
        return '<Field {}/{}/{} : {}+{}>'.format(self.register.family.name,
                self.register.name, self.name, self.lsb, self.size)


class Table(DescribedObject):
    __table_args__ = (db.UniqueConstraint('family_id', 'name', name='u_family_table'),)
    id = db.Column(db.Integer, db.ForeignKey(DescribedObject.id), primary_key=True)
    name = db.Column(db.Text, nullable=False)
    access_type = db.Column(db.Integer, nullable=False)
    size = db.Column(db.Integer, nullable=False)

    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    family = db.relationship('Family', backref=db.backref('tables', lazy=True))

    feature_id = db.Column(db.Integer, db.ForeignKey('feature.id'), nullable=False)
    feature = db.relationship('Feature', backref=db.backref('tables', lazy=True))

    ctrl_register_id = db.Column(db.Integer, db.ForeignKey('register.id'), nullable=False)
    ctrl_register = db.relationship('Register', foreign_keys=ctrl_register_id, lazy=False)
    data_register_id = db.Column(db.Integer, db.ForeignKey('register.id'), nullable=False)
    data_register = db.relationship('Register', foreign_keys=data_register_id, lazy=False)

    __mapper_args__ = {
        'polymorphic_identity' : 'table',
    }

    def get_description_metadata(self):
        return {'regdoc_platform': self.family.name}

    def __repr__(self):
        fam_name = self.family.name
        return '<Table {}/{} : ctrl={}>'.format(fam_name, self.name, self.ctrl_register)


class TableField(DescribedObject):
    __table_args__ = (db.UniqueConstraint('table_id', 'lsb', name='u_table_field'),)
    id = db.Column(db.Integer, db.ForeignKey(DescribedObject.id), primary_key=True)
    name = db.Column(db.Text, nullable=False)
    lsb = db.Column(db.Integer, nullable=False)
    size = db.Column(db.Integer, nullable=False)

    table_id = db.Column(db.Integer, db.ForeignKey(Table.id), nullable=False)
    table = db.relationship('Table', backref=db.backref('fields', lazy=True), foreign_keys=[table_id])

    __mapper_args__ = {
        'polymorphic_identity' : 'table_field',
    }

    def get_description_metadata(self):
        return {'regdoc_platform': self.table.family.name}

    def __repr__(self):
        return '<TableField {}/{}/{} : {}+{}>'.format(self.table.family.name,
                self.table.name, self.name, self.lsb, self.size)
