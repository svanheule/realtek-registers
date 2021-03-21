import datetime
from flask import Flask
from flask import abort, render_template
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///realtek-register.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Description linking tables
register_description = db.Table('register_description',
    db.Column('register_id', db.ForeignKey('register.id'), nullable=False),
    db.Column('revision_id', db.ForeignKey('description_revision.id'), nullable=False)
)
field_description = db.Table('field_description',
    db.Column('field_id', db.ForeignKey('field.id'), nullable=False),
    db.Column('revision_id', db.ForeignKey('description_revision.id'), nullable=False)
)
table_description = db.Table('table_description',
    db.Column('register_id', db.ForeignKey('table.id'), nullable=False),
    db.Column('revision_id', db.ForeignKey('description_revision.id'), nullable=False)
)
table_field_description = db.Table('table_field_description',
    db.Column('table_field_id', db.ForeignKey('table_field.id'), nullable=False),
    db.Column('revision_id', db.ForeignKey('description_revision.id'), nullable=False)
)


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


class Register(db.Model):
    __table_args__ = (db.UniqueConstraint('family_id', 'name', name='u_family_register'),)
    id = db.Column(db.Integer, primary_key=True)
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

    description_revisions = db.relationship('DescriptionRevision',
            secondary=register_description, order_by='DescriptionRevision.timestamp')

    def __repr__(self):
        return '<Register {}/{} : 0x{:04x}>'.format(self.family.name, self.name, self.offset)


class Field(db.Model):
    __table_args__ = (db.UniqueConstraint('register_id', 'lsb', name='u_register_field'),)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    lsb = db.Column(db.Integer, nullable=False)
    size = db.Column(db.Integer, nullable=False)

    register_id = db.Column(db.Integer, db.ForeignKey('register.id'), nullable=False)
    register = db.relationship('Register', backref=db.backref('fields', lazy=True))

    description_revisions = db.relationship('DescriptionRevision',
            secondary=field_description, order_by='DescriptionRevision.timestamp')

    def __repr__(self):
        return '<Field {}/{}/{} : {}+{}>'.format(self.register.family.name,
                self.register.name, self.name, self.lsb, self.size)


class Table(db.Model):
    __table_args__ = (db.UniqueConstraint('family_id', 'name', name='u_family_table'),)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    access_type = db.Column(db.Integer, nullable=False)
    size = db.Column(db.Integer, nullable=False)

    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    family = db.relationship('Family', backref=db.backref('tables', lazy=True))

    feature_id = db.Column(db.Integer, db.ForeignKey('feature.id'), nullable=False)
    feature = db.relationship('Feature', backref=db.backref('tables', lazy=True))

    ctrl_register_id = db.Column(db.Integer, db.ForeignKey('register.id'), nullable=False)
    ctrl_register = db.relationship('Register', foreign_keys=ctrl_register_id)
    data_register_id = db.Column(db.Integer, db.ForeignKey('register.id'), nullable=False)
    data_register = db.relationship('Register', foreign_keys=data_register_id)

    description_revisions = db.relationship('DescriptionRevision',
            secondary=table_description, order_by='DescriptionRevision.timestamp')

    def __repr__(self):
        fam_name = self.family.name
        return '<Table {}/{} : ctrl={}>'.format(fam_name, self.name, self.ctrl_register)


class TableField(db.Model):
    __table_args__ = (db.UniqueConstraint('table_id', 'lsb', name='u_table_field'),)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    lsb = db.Column(db.Integer, nullable=False)
    size = db.Column(db.Integer, nullable=False)

    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=False)
    table = db.relationship('Table', backref=db.backref('fields', lazy=True))

    description_revisions = db.relationship('DescriptionRevision',
            secondary=table_field_description, order_by='DescriptionRevision.timestamp')

    def __repr__(self):
        return '<TableField {}/{}/{} : {}+{}>'.format(self.table.family.name,
                self.table.name, self.name, self.lsb, self.size)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True, nullable=False)


class DescriptionRevision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    value = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('contributions', lazy=True))


@app.route('/realtek/')
def index():
    families = Family.query.order_by(Family.id).all()
    return render_template('index.html', families=families)


@app.route('/realtek/<string:platform>/')
@app.route('/realtek/<string:platform>/feature/<string:feature>')
def reglist(platform=None, feature=None):
    if platform is not None and feature is not None:
        query = db.session.query(Register)\
            .join(Register.feature)\
            .join(Register.family)\
            .filter(Family.name == platform, Feature.name == feature.upper())
    elif platform is not None:
        query = db.session.query(Register)\
            .join(Register.family)\
            .filter(Family.name == platform)
    else:
        abort(400)

    if query.count() == 0:
        abort(404)

    registers = query.order_by(Register.offset).all()

    return render_template('reglist.html', platform=platform, feature=feature,
            register_list=registers)


@app.route('/realtek/<string:platform>/register/<string:register>')
def regfieldlist(platform, register):
    query = db.session.query(Field)\
            .join(Field.register)\
            .join(Register.family)\
            .filter(Family.name == platform, Register.name == register.upper())

    rows = query.order_by(Field.lsb.desc())
    if rows.count() == 0:
        abort(404)

    query = db.session.query(Register)\
            .join(Register.family)\
            .filter(Family.name == platform, Register.name == register.upper())
    register = query.first()

    return render_template('regfieldlist.html', platform=platform,
            register=register, field_list=rows)


@app.route('/realtek/<string:platform>/table')
def tablelist(platform):
    query = db.session.query(Table).join(Table.family)\
            .filter(Family.name == platform).order_by(Table.name.asc())

    if query.count() == 0:
        abort(404)

    tables = query.all()

    return render_template('tablelist.html', platform=platform, tables=query.all())


@app.route('/realtek/<string:platform>/table/<string:table>')
def tablefieldlist(platform, table):
    query = db.session.query(TableField)\
            .join(TableField.table)\
            .join(Table.family)\
            .filter(Family.name == platform, Table.name == table.upper())

    rows = query.order_by(TableField.lsb.desc())
    if rows.count() == 0:
        abort(404)

    query = db.session.query(Table)\
            .join(Table.family)\
            .filter(Family.name == platform, Table.name == table.upper())
    table = query.first()

    return render_template('tablefieldlist.html', platform=platform,
            table=table, field_list=rows)


if __name__ == '__main__':
    app.run(debug=True)
