from flask import Flask

app = Flask(__name__)

from app.webhook.routes import webhook_bp
app.register_blueprint(webhook_bp)