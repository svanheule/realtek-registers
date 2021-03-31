from flask import Flask, Markup
from flask_migrate import Migrate
import markdown
import os

from .controller import bp
from .models import db
from .models.auth import login_manager
from .oauth import github_blueprint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///realtek-register.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config.from_object('config')

migrate = Migrate(app, db)

db.init_app(app)
login_manager.init_app(app)

app.register_blueprint(bp, url_prefix='/realtek')
app.register_blueprint(github_blueprint, url_prefix='/realtek/login')

@app.template_filter('markdown')
def markdown_filter(s):
    if s:
        return Markup(markdown.markdown(s, extensions=['sane_lists', 'smarty'], output_format='html5'))
    else:
        return ''

MAX_SUMMARY_LENGTH = 70

@app.template_filter('summary')
def summary_filter(s):
    if s:
        first_line = s.splitlines()[0]
        if len(first_line) <= MAX_SUMMARY_LENGTH:
            return first_line
        # Shorten line up to max length + phrase delimiter length
        first_line = first_line[:MAX_SUMMARY_LENGTH + 2]
        phrase_split = first_line.split('. ', maxsplit=1)
        if len(phrase_split) == 2:
            return phrase_split[0] + '.'
        # Shorten in the least clean way
        return first_line.rsplit(maxsplit=1)[0] + ' ...'
    else:
        return None
