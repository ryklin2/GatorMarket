# Import necessary libraries
from flask import Flask
from flask_cors import CORS
from flask import send_from_directory
from dotenv import load_dotenv
import mysql.connector
import os
from flask_apscheduler import APScheduler
from flask import jsonify

# Load environment variables from .env file
load_dotenv()

# Create the flask application instance
app = Flask(__name__)

# Enable Cross Origin Resource Sharing with strict settings so that frontend can make API requests
# Improved CORS configuration with proper preflight handling
CORS(app, 
     resources={r"/*": {
         "origins": ["http://localhost:5173", "https://csc648g1.me"], # allowed frontend domanis
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], # permitted HTTP protocols
         "allow_headers": ["Authorization", "Content-Type"], # headers client is allowed to send
         "expose_headers": ["Content-Type", "Authorization"], # headers exposed to client
         "supports_credentials": True, # allow credentials like cookies/JWTs
         "max_age": 3600 # cache preflight response for 1 hour
     }})


# setup JWT manager for user auth and authorization
# it reads secret from .env or falls back to default
from flask_jwt_extended import JWTManager
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'your-secret-key')
jwt = JWTManager(app)

# helper function to create MySQL db connection using creds from .env
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),  
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE')
        )
    except mysql.connector.Error as err:
        # debug statement: print error if connection fails
        print(f"Database connection error: {err}")
        return None

# Register product routes
from products import products_bp
app.register_blueprint(products_bp)

# Handle preflight OPTIONS requests explicitly, prevent CORS errors by replying w/ HTTP 204
@app.route('/', methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path=None):
    return '', 204

# basic health check route to confirm backend works
@app.route('/')
def hello():
    return {"message": "Gator Market Backend is live!"}

# register the route blueprints
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# handles login, registration, token generation
from auth import auth_bp
app.register_blueprint(auth_bp)

# admin tools for moderation, approvals
from admin import admin_bp
app.register_blueprint(admin_bp)

# rating and review system
from reviews import reviews_bp
app.register_blueprint(reviews_bp)

# in app messaging
from messaging import messaging_bp
app.register_blueprint(messaging_bp)

# handles email verification logic
from email_verification import email_bp
app.register_blueprint(email_bp)

# manages a user's wishlsits
from wishlist import wishlist_bp
app.register_blueprint(wishlist_bp)

# handles user reports
from report import report_bp
app.register_blueprint(report_bp)

# main entry point to run app during local development
# served with gunicorn + nginx during production
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)