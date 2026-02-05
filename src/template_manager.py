import os
from twilio.rest import Client
from dotenv import load_dotenv

# Ensure we can load .env from the root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
load_dotenv(os.path.join(root_dir, '.env'))

class ContentCreateRequest:
    """
    Mock wrapper for Content API payload structure.
    Useful if specific helper library methods are unavailable or vary by version.
    """
    def __init__(self, friendly_name=None, variables=None, language=None, types=None):
        self.payload = {
            "friendly_name": friendly_name,
            "variables": variables,
            "language": language,
            "types": types
        }
    def to_dict(self):
        return self.payload

def create_appointment_template(friendly_name="RCS_Static_Card_Test"):
    """
    Creates an RCS Rich Card template for appointment reminders.
    """
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    
    if not account_sid or not auth_token:
        print("Error: Twilio credentials not found.")
        return None
    
    client = Client(account_sid, auth_token)

    # Define a Rich Card Template (Standard for RCS)
    template_data = {
        "friendly_name": friendly_name,
        "variables": {},
        "language": "en",
        "types": {
            "twilio/card": {
                "title": "Appointment Reminder",
                "subtitle": "Hi there, please confirm your appointment.",
                "actions": [
                    {"type": "QUICK_REPLY", "title": "Confirm", "id": "confirm"},
                    {"type": "QUICK_REPLY", "title": "Cancel", "id": "cancel"}
                ]
            }
        }
    }

    try:
        print(f"Creating RCS Template: {friendly_name}...")
        
        # Create the request object using our shim
        content_create_request = ContentCreateRequest(**template_data)
        
        # Pass the object to the create method
        content = client.content.v1.contents.create(content_create_request)

        print(f"\nSUCCESS! Template Created.")
        print(f"Sid: {content.sid}")
        print(f"Name: {content.friendly_name}")
        
        return content.sid

    except Exception as e:
        print(f"Error creating template: {e}")
        if hasattr(e, 'response'):
             print(f"HTTP Status: {e.status}")
             print(f"Twilio Code: {e.code}")
             print(f"Details: {e.msg}")
        return None

if __name__ == "__main__":
    sid = create_appointment_template()
    if sid:
        print(f"\nAdd this to your .env file:")
        print(f"TWILIO_CONTENT_SID={sid}")
