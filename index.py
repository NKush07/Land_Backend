import urllib
import json
from flask import Flask, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from flask_dance.contrib.google import make_google_blueprint, google
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)
jwt = JWTManager(app)
app.secret_key = os.getenv("JWT_SECRET_KEY")  # Required for sessions

# MongoDB configuration
client = MongoClient(os.getenv('MONGODB_URL'))
db = client['AI_Chef_Master']

# Collections
email_collection = db.Email
chef_email_collection = db.ChefEmail

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = os.getenv("SMTP_PORT", 587)
SMTP_EMAIL = str(os.getenv("SMTP_EMAIL"))  # Your email
SMTP_PASSWORD = str(os.getenv("SMTP_PASSWORD"))  # Your email password

# google login
app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')

google_blueprint = make_google_blueprint(
    client_id=os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
    scope=["https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile",
           "openid"]
)
app.register_blueprint(google_blueprint, url_prefix="/login")
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


# =======================================================================================================================================

# Function to send email
def send_email(recipient_email, subject, user_name):
    try:
        # Create email message
        message = MIMEMultipart()
        message["From"] = SMTP_EMAIL
        message["To"] = recipient_email
        message["Subject"] = subject

        # Attach the email body
        company_name = "AI Chef Master"
        logo_url = "https://www.aichefmaster.com/assets/logo.jpeg"  # Replace with your logo URL
        social_links = {
            "LinkedIn": "https://linkedin.com/company/aichefmaster",
            "Instagram": "https://instagram.com/aichefmaster",
            "Twitter": "https://x.com/AIChefMaster",
            "Facebook": "https://www.facebook.com/profile.php?id=61557270956883"
        }

        # Create social media links HTML
        social_media_html = "".join(
            f'<a href="{link}" style="margin: 0 10px; text-decoration: none; color: #1a73e8;">{platform}</a>'
            for platform, link in social_links.items()
        )

        # User details
        user_first_name = "John"  # Replace with dynamic data if available

        # Email subject and HTML content
        subject = f"Welcome to {company_name}!"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; background-color: #f9f9f9;">
                <!-- Header -->
                <div style="background-color: #1f2937; padding: 20px; text-align: center;">
                    <img src="{logo_url}" alt="Company Logo" style="max-width: 150px; margin-bottom: 10px;border-radius: 9999px"; />
                    <h1 style="color: #ffffff; margin: 0;">Welcome to AI Chef Master</h1>
                </div>

                <!-- Body -->
                <div style="padding: 20px; background-color: #ffffff; margin: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                    <p>Hi <strong>{user_name}</strong>,</p>
                    <p>We’re thrilled to have you on board. Your first step towards AI Chef Master.</p>
                    <p>
                        We started AI Chef Master to address common challenges in cooking, such as time constraints, lack of personalisation, 
                        and inefficient ingredient management. Our motivation stems from a passion for culinary innovation and a desire to make 
                        cooking more accessible, enjoyable, and efficient for everyone.
                    </p>
                    <p>
                        By leveraging AI technology, we aim to empower home cooks with personalised recipes, regional language support, 
                        and step-by-step guidance, revolutionising the cooking experience and helping individuals create delicious meals with ease.
                    </p>
                    <p>
                        If you want to explore your cooking journey further with AI Chef Master, please connect with us on social media for daily updates.
                    </p>
                    <p>If you have any queries, please contact us at <a href="mailto:support.acm@aichefmaster.com" style="color: #1a73e8;">support.acm@aichefmaster.com</a>. We will get back to you as soon as possible.</p>
                    <p>Thank you!</p>
                    <p>Best regards,<br><strong>AI Chef Master</strong></p>
                    <strong>info.ai@aichefmaster.com</strong>
                </div>

                <!-- Footer -->
                <div style="text-align: center; padding: 20px; background-color: #f4f4f4; font-size: 14px; color: #666;">
                    <div style="margin-bottom: 10px;">{social_media_html}</div>
                    <p style="margin: 0;">&copy; AI Chef Master, 2023. All rights reserved.</p>
                </div>
            </body>
        </html>
        """
        message.attach(MIMEText(body, "html"))

        # Connect to SMTP server and send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, recipient_email, message.as_string())
        print(f"Email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False


@app.route("/")
def index():
    try:
        if not google.authorized:
            return redirect(url_for("google.login"))
        return redirect(url_for("google_callback", col=request.args.get("user")))

    except Exception as e:
        return jsonify({'message': f'Something went wrong: {str(e)}'}), 400


@app.route("/callback")
def google_callback():
    try:
        if not google.authorized:
            return jsonify({"error": "Failed to log in."}), 400
        resp = google.get("/oauth2/v2/userinfo")
        assert resp.ok, resp.text

        user_info = resp.json()
        col = request.args.get("col")
        exist_user = db[str(col)].find_one({'email': user_info['email']})

        if not exist_user:
            db[str(col)].insert_one({
                'email': user_info['email'].lower(),
                'createdAt': datetime.utcnow()
            })
        else:
            user_id = exist_user['email']
        send_email(user_info['email'].lower(), "Welcome to AiChefMaster", user_info['given_name'])
        return redirect(f"{os.getenv('FRONTEND_URL')}", code=302)

    except Exception as e:
        return jsonify({'message': f'Something went wrong: {str(e)}'}), 400



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

        # Send a welcome email
        subject = "Welcome to AI Chef Master!"

        email_sent = send_email(email, "Welcome to AiChefMaster", email)
        if not email_sent:
            return jsonify({
                'success': False,
                'message': 'Subscription successful, but email failed to send'
            }), 500
        return jsonify({
            'success': True,
            'message': 'Subscription successful and email sent'
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

        send_email(email, "Welcome to AiChefMaster", email)
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

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        # Count documents in each collection
        subscriber_count = email_collection.count_documents({})
        chef_count = chef_email_collection.count_documents({})

        return jsonify({
            'success': True,
            'data': {
                'subscribers': subscriber_count,
                'chefs': chef_count
            }
        }), 200

    except Exception as error:
        print('Error fetching stats:', str(error))
        return jsonify({
            'success': False,
            'message': 'Server error'
        }), 500

if __name__ == '__main__':
    app.debug = True
    app.run()
