import os
import logging
from flask import Flask, request, jsonify
import json
from data_manager import DataManager
from twilio.rest import Client
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
data_manager = DataManager()

# --- CONFIGURATION ---
def get_env_variable(var_name, default=None, required=True):
    val = os.environ.get(var_name, default)
    if required and not val:
        logger.error(f"Environment variable {var_name} is invalid or missing.")
        raise ValueError(f"Environment variable {var_name} is invalid or missing.")
    return val

try:
    ACCOUNT_SID = get_env_variable('TWILIO_ACCOUNT_SID')
    AUTH_TOKEN = get_env_variable('TWILIO_AUTH_TOKEN')
    MESSAGING_SERVICE_SID = get_env_variable('TWILIO_MESSAGING_SERVICE_SID')
    # Try TO_NUMBER first (used in app.py), then fall back to MY_PHONE_NUMBER if defined
    TO_NUMBER = os.environ.get('TO_NUMBER') or os.environ.get('MY_PHONE_NUMBER')
    
    if not TO_NUMBER:
        raise ValueError("Neither TO_NUMBER nor MY_PHONE_NUMBER found in environment variables.")

except ValueError as e:
    logger.critical(str(e))
    exit(1)

# Replace these with your actual Template SIDs from the Content Template Builder
# These are not secrets, so keeping them in code is acceptable, but can be moved to env/config if needed.
TEMPLATES = {
    'step_1_ad': 'HX4d21f40a4db16df1b477561c66e8f188',        # Health Advice Card
    'step_2_suggest': 'HX61c1303f5517919801c31977e656a9e5',   # Suggest Slot Card/Chips
    'step_3_carousel': 'HX416c65202749e54a269c8b77b8f19ed4',  # Alternative Slots Carousel
    'step_4_confirm': 'HX92aa35c43fa6506a684f35496ce79856',   # Final Confirmation Card
    'step_5_slot_taken': 'HXa09ef3bb52f411f66ce2b6e8164a8117' # Slot Taken Error Card
}

try:
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
except Exception as e:
    logger.critical(f"Failed to initialize Twilio Client: {e}")
    exit(1)

# --- HELPER FUNCTION ---
def send_rcs_template(to_number, content_sid, variables=None):
    """Sends an RCS message using a Twilio Content Template SID."""
    try:
        message = client.messages.create(
            from_=MESSAGING_SERVICE_SID,
            to=to_number,
            content_sid=content_sid,
            # Variables must be a JSON string if your template uses {{1}}, etc.
            content_variables=variables if variables else "{}"
        )
        logger.info(f"Sent message {content_sid} to {to_number}. SID: {message.sid}")
        return message.sid
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

# --- ROUTES ---

@app.route("/trigger", methods=['GET'])
def trigger_flow():
    """Run this in your browser (e.g., localhost:5000/trigger) to start the flow."""
    # Split the TO_NUMBER string by commas to handle multiple recipients
    recipients = [num.strip() for num in TO_NUMBER.split(',') if num.strip()]
    
    results = []
    for recipient in recipients:
        sid = send_rcs_template(recipient, TEMPLATES['step_1_ad'])
        if sid:
            results.append(f"Sent to {recipient}")
        else:
            results.append(f"Failed to send to {recipient}")

    return jsonify({
        "status": "success",
        "message": "Flow triggered for recipients",
        "recipients": recipients,
        "results": results
    })

@app.route("/webhook", methods=['POST'])
def webhook():
    """Twilio Webhook: Listens for user interactions (button clicks)."""
    # Twilio sends the button text/label in the 'Body' parameter
    user_response = request.values.get('Body', '').strip()
    user_phone = request.values.get('From')
    
    logger.info(f"Received interaction: '{user_response}' from {user_phone}")

    # LOGIC BASED ON YOUR DOCUMENT FLOW
    
    # Transition: Step 1 -> Step 2
    if user_response == "Book Appointment":
        send_rcs_template(user_phone, TEMPLATES['step_2_suggest'])

    # Transition: Step 2 -> Step 4 (User accepts)
    elif user_response == "Accept":
        send_rcs_template(user_phone, TEMPLATES['step_4_confirm'])

    # Transition: Step 2 -> Step 3 (User wants alternatives) - OR - "View Other Slots" from Step 5
    elif user_response == "Reschedule" or user_response == "View Other Slots":
        send_rcs_template(user_phone, TEMPLATES['step_3_carousel'])

    # Transition: Step 3 -> Step 4 (User selects a slot from Carousel)
    # Note: Use the exact button labels you typed in your Carousel template
    elif "Select" in user_response or "PM" in user_response or "AM" in user_response:
        # Extract time from response (e.g., "Select 2:00 PM" -> "2:00 PM")
        # specific logic depends on what the button text actually is. 
        # If button is just "2:00 PM", then user_response is "2:00 PM".
        selected_time = user_response.replace("Select ", "").strip()
        
        # Check availability
        if data_manager.is_slot_available(selected_time):
            # Book the slot
            if data_manager.book_slot(selected_time, user_phone):
                # Determine the variable value for {{1}}
                # We'll use the selected_time directly.
                variables = json.dumps({"1": selected_time})
                send_rcs_template(user_phone, TEMPLATES['step_4_confirm'], variables=variables)
            else:
                # Race condition or just taken
                 logger.info(f"Slot {selected_time} taken when {user_phone} tried to book.")
                 # Send the "Slot Just Booked" template
                 send_rcs_template(user_phone, TEMPLATES['step_5_slot_taken'])
        else:
            logger.info(f"Slot {selected_time} unavailable for {user_phone}.")
            # Send the "Slot Just Booked" template
            send_rcs_template(user_phone, TEMPLATES['step_5_slot_taken'])

    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)