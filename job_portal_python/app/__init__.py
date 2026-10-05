import os

from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(app.root_path), "instance"), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .auth import bp as auth_bp
    from .main import bp as main_bp
    from .employer import bp as employer_bp
    from .candidate import bp as candidate_bp
    from .admin import bp as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(employer_bp, url_prefix="/employer")
    app.register_blueprint(candidate_bp, url_prefix="/candidate")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("error.html", code=403, message="You don't have access to this page."), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(413)
    def too_large(_e):
        return render_template("error.html", code=413, message="File too large (max 5 MB)."), 413

    @app.template_filter("score_class")
    def score_class(score):
        if score is None:
            return "secondary"
        if score >= 75:
            return "success"
        if score >= 50:
            return "primary"
        if score >= 30:
            return "warning"
        return "danger"

    with app.app_context():
        from . import models  # noqa: F401

        db.create_all()

    return app
