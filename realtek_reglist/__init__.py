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
app.secret_key = os.environb.get(b'SECRET_KEY')

migrate = Migrate(app, db)

db.init_app(app)
login_manager.init_app(app)

app.register_blueprint(bp, url_prefix='/realtek')
app.register_blueprint(github_blueprint, url_prefix='/realtek/login')

@app.template_filter('markdown')
def markdown_filter(s):
    return Markup(markdown.markdown(s, extensions=['sane_lists', 'smarty'], output_format='html5'))
