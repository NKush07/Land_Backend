
from flask import Flask, request, jsonify, redirect, url_for, session
from flask_pymongo import PyMongo
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)
app.secret_key = os.getenv("FLASK_SECRET_KEY")  # Required for sessions

# MongoDB configuration
client = MongoClient(os.getenv('MONGODB_URL'))
db = client['AI_Chef_Master']  

# Collections
email_collection = db.Email
chef_email_collection = db.ChefEmail

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({
                'success': False,
                'message': 'Email is required'
            }), 400

        # Check if email already exists
        existing_email = email_collection.find_one({'email': email.lower()})
        if existing_email:
            return jsonify({
                'success': False,
                'message': 'Email already subscribed'
            }), 400

        # Create new email subscription
        new_email = {
            'email': email.lower(),
            'createdAt': datetime.utcnow()
        }
        email_collection.insert_one(new_email)

        return jsonify({
            'success': True,
            'message': 'Subscription successful'
        }), 201

    except Exception as error:
        print('Subscription error:', str(error))
        return jsonify({
            'success': False,
            'message': 'Server error'
        }), 500

@app.route('/api/chef', methods=['POST'])
def chef_subscribe():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({
                'success': False,
                'message': 'Email is required'
            }), 400

        # Check if email already exists
        existing_email = chef_email_collection.find_one({'email': email.lower()})
        if existing_email:
            return jsonify({
                'success': False,
                'message': 'Email already subscribed'
            }), 400

        # Create new email subscription
        new_email = {
            'email': email.lower(),
            'createdAt': datetime.utcnow()
        }
        chef_email_collection.insert_one(new_email)

        return jsonify({
            'success': True,
            'message': 'Subscription successful'
        }), 201

    except Exception as error:
        print('Subscription error:', str(error))
        return jsonify({
            'success': False,
            'message': 'Server error'
        }), 500
    
if __name__ == '__main__':
    app.debug = True
    app.run()