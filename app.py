from flask import Flask
from models import db, bcrypt
from config import Config
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    bcrypt.init_app(app)

    # Register Blueprints (Modular Routes)
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.inventory import inventory_bp
    from routes.pos import pos_bp
    from routes.users import users_bp
    from routes.api import api_bp
    from routes.suppliers import suppliers_bp
    from routes.pricing import pricing_bp  # <-- Added

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(pricing_bp)  # <-- Added

    return app

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        os.makedirs("instance", exist_ok=True)
        db.create_all()
    app.run(debug=True)