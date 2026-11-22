from flask import Flask
from .routes import bp

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY="local-demo-only", DATABASE="data/civicresolve.db")
    if test_config:
        app.config.update(test_config)
    app.register_blueprint(bp)
    return app

app = create_app()
