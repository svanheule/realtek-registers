from flask import Flask, Markup
from flask import abort, render_template, request, redirect, url_for
from flask_login import current_user
from flask_migrate import Migrate
import markdown
import os

from .models import db
from .models.auth import login_manager
from .models.description import DescriptionRevision
from .models.soc import Family, Feature, Register, Field, Table, TableField

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///realtek-register.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environb.get(b'SECRET_KEY')

migrate = Migrate(app, db)

db.init_app(app)
login_manager.init_app(app)

@app.template_filter('markdown')
def markdown_filter(s):
    return Markup(markdown.markdown(s, extensions=['sane_lists', 'smarty'], output_format='html5'))


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


@app.route('/realtek/<string:platform>/<string:itemtype>/<string:itemname>/edit/', methods=['GET', 'POST'])
@app.route('/realtek/<string:platform>/<string:itemtype>/<string:itemname>/<string:itemfield>/edit/', methods=['GET', 'POST'])
def description_edit(platform, itemtype, itemname, itemfield=None):
    # Deny unauthenticated users
    if not current_user.is_authenticated:
        abort(403)

    if itemtype == 'register':
        if itemfield is None:
            query = db.session.query(Register)\
                .join(Register.family)\
                .filter(Family.name == platform, Register.name == itemname.upper())
        else:
            query = db.session.query(Field)\
                .join(Field.register)\
                .join(Register.family)\
                .filter(Family.name == platform, Register.name == itemname.upper(), Field.name == itemfield.upper())
    elif itemtype == 'table':
        if itemfield is None:
            query = db.session.query(Table)\
                .join(Table.family)\
                .filter(Family.name == platform, Table.name == itemname.upper())
        else:
            query = db.session.query(Field)\
                .join(Field.register)\
                .join(Register.family)\
                .filter(Family.name == platform, Table.name == itemname.upper(), TableField.name == itemfield.upper())
    else:
        abort(404)

    if query.count() == 0:
        abort(404)

    item = query.first()

    if request.method == 'POST':
        user = current_user
        if not user.is_anonymous and  user.is_active:
            d = DescriptionRevision(author=user, value=request.form['description'].strip())
            item.description_revisions.append(d)
            db.session.commit()
        if itemtype == 'register':
            return redirect(url_for('regfieldlist', platform=platform, register=itemname))
        elif itemtype == 'table':
            return redirect(url_for('tablefieldlist', platform=platform, table=itemname))
        else:
            abort(404)
    else:
        return render_template('description_edit.html', platform=platform,
                itemtype=itemtype, itemname=itemname, itemfield=itemfield, item=item)


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
