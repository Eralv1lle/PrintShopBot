from flask import Flask, send_from_directory
from flask_cors import CORS
from web.api import products_bp, orders_bp
from database import db_manager
from config import config

app = Flask(__name__, static_folder='web/static', template_folder='web/templates')
CORS(app)

app.register_blueprint(products_bp, url_prefix='/api')
app.register_blueprint(orders_bp, url_prefix='/api')

@app.route('/')
def index():
    return send_from_directory('web/templates', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('web/static', path)

@app.before_request
def before_request():
    if db_manager.db.is_closed():
        db_manager.db.connect()

@app.teardown_request
def teardown_request(exception=None):
    if not db_manager.db.is_closed():
        db_manager.db.close()

if __name__ == '__main__':
    try:
        config.validate()
        db_manager.initialize()
        db_manager.create_tables()
        print("Database initialized")
        
        ssl_context = (config.SSL_CERT_PATH, config.SSL_KEY_PATH)
        print(f"Starting on {config.FLASK_HOST}:{config.FLASK_PORT}")
        
        app.run(
            host=config.FLASK_HOST,
            port=config.FLASK_PORT,
            ssl_context=ssl_context,
            debug=False
        )
    except Exception as e:
        print(f"Error: {e}")
        raise
