import os
import sys
from flask import Flask, jsonify, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

# Ensure we can load .env from the root directory
# Get the directory where this script is located
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (root of the project)
root_dir = os.path.dirname(current_dir)
# Load .env from the root directory
load_dotenv(os.path.join(root_dir, '.env'))

app = Flask(__name__)

def get_twilio_client():
    """Initializes and returns the Twilio Client."""
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    
    if not account_sid or not auth_token:
        raise ValueError("Twilio credentials not found in environment variables.")
        
    return Client(account_sid, auth_token)

@app.route('/send-rcs', methods=['POST'])
def send_rcs():
    """
    Endpoint to trigger sending an RCS message.
    Expects (optional) JSON body with 'content_sid' and 'content_variables'.
    """
    try:
        # Get credentials
        messaging_service_sid = os.environ.get('TWILIO_MESSAGING_SERVICE_SID')
        to_number = os.environ.get('TO_NUMBER')

        if not messaging_service_sid or not to_number:
            return jsonify({'error': 'Missing Messaging Service SID or To Number in env'}), 500

        client = get_twilio_client()

        # Get optional parameters from request
        data = request.get_json(force=True, silent=True) or {}
        content_sid = data.get('content_sid') or os.environ.get('TWILIO_CONTENT_SID')
        
        if not content_sid:
             return jsonify({'error': 'Missing content_sid for RCS template'}), 400

        content_variables = data.get('content_variables')

        print(f"Attempting to send with Content SID: {content_sid}")
        print(f"To: {to_number}")

        message_params = {
            "messaging_service_sid": messaging_service_sid,
            "to": to_number,
            "content_sid": content_sid,
            "body": "Hi (Fallback), please confirm your appointment. Text YES or NO." # Fallback
        }
        
        if content_variables:
            message_params["content_variables"] = content_variables

        message = client.messages.create(**message_params)

        return jsonify({
            'status': 'success',
            'message_sid': message.sid,
            'body': message.body
        })

    except Exception as e:
        print(f"Error sending message: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/reply', methods=['POST'])
def reply():
    """
    Webhook to handle incoming replies from Twilio.
    Respond with TwiML.
    """
    resp = MessagingResponse()
    
    print("\n--- INCOMING REPLY ---")
    print(f"Values: {request.values}")
    
    body = request.values.get('Body', '').lower()
    
    # Dynamic reply logic
    if 'hello' in body:
        resp.message("Hi there! Thanks for testing.")
    elif 'price' in body:
        resp.message("Our prices start at $10/month.")
    elif 'confirm' in body:
        resp.message("Thank you! Your appointment is confirmed.")
    elif 'cancel' in body:
        resp.message("Your appointment has been cancelled. Call us to reschedule.")
    elif 'yes' in body:
        resp.message("Great! We'll send you the details shortly.")
    elif 'no' in body:
        resp.message("No problem. Let us know if you change your mind.")
    else:
        resp.message(f"You said: {body}. We received it!")
        
    return str(resp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
