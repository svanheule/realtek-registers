from flask import Flask
from flask import abort, render_template
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

    def __repr__(self):
        return '<Field {}/{}/{} : {}+{}>'.format(self.register.family.name,
                self.register.name, self.name, self.lsb, self.size)


@app.route('/realtek/')
def index():
    families = Family.query.order_by(Family.id).all()
    return render_template('index.html', families=families)


@app.route('/realtek/<string:platform>/')
@app.route('/realtek/<string:platform>/feature/<string:feature>')
def reglist(platform=None, feature=None):
    if platform is not None and feature is not None:
        query = db.session.query(Register)\
            .join(Feature, Feature.id == Register.feature_id)\
            .join(Family, Family.id == Register.family_id)\
            .filter(Family.name == platform, Feature.name == feature.upper())
    elif platform is not None:
        query = db.session.query(Register)\
            .join(Family, Family.id == Register.family_id)\
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
            .join(Register, Field.register_id == Register.id)\
            .join(Family, Register.family_id == Family.id)\
            .filter(Family.name == platform, Register.name == register.upper())

    rows = query.order_by(Field.lsb.desc())
    if rows.count() == 0:
        abort(404)

    query = db.session.query(Register)\
            .join(Family, Register.family_id == Family.id)\
            .filter(Family.name == platform, Register.name == register.upper())
    register = query.first()

    return render_template('regfieldlist.html', platform=platform,
            register=register, field_list=rows)
