from datetime import datetime, timedelta
from flask import abort, flash, render_template, request, redirect, url_for
from flask import current_app
from flask import Blueprint
from flask_dance.consumer import oauth_authorized
from flask_dance.contrib.github import github
from flask_login import current_user, login_user, logout_user
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import aliased, with_polymorphic
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import label
from sqlalchemy.sql.functions import coalesce

from .models import db
from .models.auth import User
from .models.description import DescriptionRevision, DescribedObject
from .models.soc import Family, Feature, Register, Field, Table, TableField
from .models.soc import CpuTag, CpuTagField
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
    last_changes = dict()
    reg_fld_fam = db.session.query(
                Field.id.label('object_id'),
                Register.family_id.label('family_id')
            )\
            .join(Field.register).subquery()
    tab_fld_fam = db.session.query(
                TableField.id.label('object_id'),
                Table.family_id.label('family_id')
            )\
            .join(TableField.table).subquery()
    for f in families:
        last_changes[f.name] = db.session.query(last_updates.c.last_update, dynamic_object)\
                .join(last_updates, dynamic_object.id == last_updates.c.object_id)\
                .outerjoin(reg_fld_fam, reg_fld_fam.c.object_id == dynamic_object.id)\
                .outerjoin(tab_fld_fam, tab_fld_fam.c.object_id == dynamic_object.id)\
                .filter(or_(
                    dynamic_object.Register.family_id == f.id,
                    dynamic_object.Table.family_id == f.id,
                    reg_fld_fam.c.family_id == f.id,
                    tab_fld_fam.c.family_id == f.id,
                ))\
                .order_by(desc(last_updates.c.last_update))\
                .limit(10)

    return render_template('index.html', families=families, recently_changed=last_changes)

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
            flash('You are now logged in as {}'.format(username), 'info')
            user = query.one()
            login_user(user)
            current_app.logger.info('Logged in Github user {}'.format(username))
        except NoResultFound:
            flash('Hi, {}! Unfortunately you cannot log in here. '.format(username) +
                    'Please contact the site admin if you would like to contribute.', 'warning')
            current_app.logger.warn('Unknown Github user {}'.format(username))
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


def query_platform_cputags(platform):
    q = db.session.query(CpuTag).join(CpuTag.family)

    return q.filter(Family.name == platform).order_by(CpuTag.direction)


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


def store_new_description(item, author, value):
    last = DescriptionRevision.query\
        .filter(DescriptionRevision.object_id == item.id)\
        .filter(DescriptionRevision.timestamp == item.last_updated).one_or_none()
    is_same_author = last.author == author if last else False
    is_new_value = last.value != value if last else len(value) > 0
    is_quick_edit = datetime.utcnow() - last.timestamp < timedelta(minutes=2) if last else False
    is_quick_edit = False

    if is_same_author and is_quick_edit and is_new_value:
        # If the same author made a quick update, let's merge those updates
        if len(value) == 0:
            db.session.delete(last)
        else:
            last.value = value
            last.timestamp = datetime.utcnow()
        db.session.commit()
    elif is_new_value:
        with db.session.no_autoflush:
            d = DescriptionRevision(author=author, value=value)
            item.description_revisions.append(d)
        db.session.commit()


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
            query = db.session.query(TableField)\
                .join(TableField.table)\
                .join(Table.family)\
                .filter(Family.name == platform, Table.name == itemname.upper(), TableField.name == itemfield.upper())
    elif itemtype == 'cputag':
        if itemfield is None:
            query = db.session.query(CpuTag)\
                .join(CpuTag.family)\
                .filter(Family.name == platform, CpuTag.direction == itemname.upper())
        else:
            query = db.session.query(CpuTagField)\
                .join(CpuTagField.cputag)\
                .join(CpuTag.family)\
                .filter(Family.name == platform, CpuTag.direction == itemname.upper(), CpuTagField.lsb == itemfield.upper())
    else:
        abort(404)

    if query.count() == 0:
        abort(404)

    item = query.one()

    if request.method == 'POST':
        user = current_user
        if not user.is_anonymous and user.is_active:
            new_value = request.form['description'].strip()
            store_new_description(item, user, new_value)
        if itemtype == 'register':
            return redirect(url_for('realtek.regfieldlist', platform=platform, register=itemname))
        elif itemtype == 'table':
            return redirect(url_for('realtek.tablefieldlist', platform=platform, table=itemname))
        elif itemtype == 'cputag':
            return redirect(url_for('realtek.cputaglist', platform=platform))
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

@bp.route('<string:platform>/cputag')
def cputaglist(platform):
    query = query_platform_cputags(platform)

    if query.count() == 0:
        abort(404)

    return render_template('cputags.html', platform=platform, cputags=query.all())
