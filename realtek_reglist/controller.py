from flask import abort, render_template, request, redirect, url_for
from flask import Blueprint
from flask_dance.consumer import oauth_authorized
from flask_dance.contrib.github import github
from flask_login import current_user, login_user, logout_user
from sqlalchemy import asc, desc, func
from sqlalchemy.orm import aliased, with_polymorphic
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import label
from sqlalchemy.sql.functions import coalesce

from .models import db
from .models.auth import User
from .models.description import DescriptionRevision, DescribedObject
from .models.soc import Family, Feature, Register, Field, Table, TableField
from .oauth import github_blueprint

bp = Blueprint('realtek', __name__, static_folder='static')


@bp.route('/')
def index():
    dynamic_object = with_polymorphic(
        DescribedObject,
        [Register, Field, Table, TableField]
    )

    families = Family.query.order_by(Family.id).all()
    dr = aliased(DescriptionRevision)
    last_updates = db.session.query(
            dr.object_id.label('object_id'),
            func.max(dr.timestamp).label('last_update'),
        ).group_by(dr.object_id).subquery()
    recently_changed = db.session.query(last_updates.c.last_update, dynamic_object, dynamic_object.description)\
            .join(last_updates, dynamic_object.id == last_updates.c.object_id)\
            .order_by(desc(last_updates.c.last_update)).limit(15)

    return render_template('index.html', families=families, recently_changed=recently_changed)

@bp.route('/github')
def login():
    if not github.authorized:
        return redirect(url_for('github.login'))
    return redirect(url_for('realtek.index'))

@bp.route('/logout/')
def logout():
    logout_user()
    return redirect(url_for('realtek.index'))


@oauth_authorized.connect_via(github_blueprint)
def github_logged_in(blueprint, token):
    info = blueprint.session.get('/user')
    if info.ok:
        account_info = info.json()
        username = account_info['login']

        query = User.query.filter_by(username=username)
        try:
            user = query.one()
            login_user(user)
        except NoResultFound:
            # TODO Warn user on website that account is not known
            print('Unknown Github user {}'.format(username))
    return redirect(url_for('realtek.index'))


def query_platform_registers(platform, feature=None):
    q = db.session.query(
            Register.offset.label('offset'),
            Feature.name.label('feature_name'),
            Register.name.label('name'),
            Register.description.label('description')
        ).join(Register.family).join(Register.feature)
    if feature is not None:
        q = q.filter(Feature.name == feature.upper())

    return q.filter(Family.name == platform).order_by(Register.offset)


def query_platform_tables(platform, feature=None):
    q = db.session.query(Table).join(Table.family).join(Table.ctrl_register)
    if feature is not None:
        q = q.join(Table.feature).filter(Feature.name == feature.upper())

    return q.filter(Family.name == platform).order_by(Register.name, Table.access_type, Table.name)


@bp.route('/<string:platform>/')
def reglist(platform):
    query = query_platform_registers(platform)

    if query.count() == 0:
        abort(404)

    registers = query.all()

    return render_template('reglist.html', platform=platform, registers=registers)

@bp.route('/<string:platform>/feature/')
def featurelist(platform):
    table_counts = db.session.query(
                Table.feature_id,
                func.count(Table.id).label('count')
            )\
            .group_by(Table.feature_id).subquery()
    register_counts = db.session.query(
                Register.feature_id,
                func.count(Register.id).label('count')
            )\
            .group_by(Register.feature_id).subquery()
    query = db.session.query(
            Feature.name.label('name'),
            label('table_count', coalesce(table_counts.c.count, 0)),
            label('register_count', coalesce(register_counts.c.count, 0))
        )\
        .outerjoin(table_counts, table_counts.c.feature_id == Feature.id)\
        .outerjoin(register_counts, register_counts.c.feature_id == Feature.id)\
        .join(Feature.family)\
        .filter(Family.name == platform)\
        .order_by(Feature.name)

    if query.count() == 0:
        abort(404)

    return render_template('featurelist.html', platform=platform, features=query.all())


@bp.route('/<string:platform>/feature/<string:feature>')
def featuredetail(platform, feature):
    query_tables = query_platform_tables(platform, feature)
    query_registers = query_platform_registers(platform, feature)

    if query_tables.count() == 0 and query_registers.count() == 0:
        abort(404)

    return render_template('featuredetail.html', platform=platform, feature=feature,
            registers=query_registers.all(), tables=query_tables.all())


@bp.route('/<string:platform>/register/<string:register>')
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
    register = query.one()

    return render_template('regfieldlist.html', platform=platform,
            register=register, field_list=rows)


@bp.route('/<string:platform>/<string:itemtype>/<string:itemname>/edit/', methods=['GET', 'POST'])
@bp.route('/<string:platform>/<string:itemtype>/<string:itemname>/<string:itemfield>/edit/', methods=['GET', 'POST'])
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

    item = query.one()

    if request.method == 'POST':
        user = current_user
        if not user.is_anonymous and user.is_active:
            old_value = item.description
            new_value = request.form['description'].strip()
            if old_value != new_value:
                with db.session.no_autoflush:
                    d = DescriptionRevision(author=user, value=new_value)
                    item.description_revisions.append(d)
                db.session.commit()
        if itemtype == 'register':
            return redirect(url_for('realtek.regfieldlist', platform=platform, register=itemname))
        elif itemtype == 'table':
            return redirect(url_for('realtek.tablefieldlist', platform=platform, table=itemname))
        else:
            abort(404)
    else:
        return render_template('description_edit.html', platform=platform,
                itemtype=itemtype, itemname=itemname, itemfield=itemfield, item=item)


@bp.route('/<string:platform>/table')
def tablelist(platform):
    query = query_platform_tables(platform)

    if query.count() == 0:
        abort(404)

    tables = query.all()

    return render_template('tablelist.html', platform=platform, tables=query.all())


@bp.route('/<string:platform>/table/<string:table>')
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
    table = query.one()

    return render_template('tablefieldlist.html', platform=platform,
            table=table, field_list=rows)
