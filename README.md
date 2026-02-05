# RCS Verification Tool

This project enables verification of RCS (Rich Communication Services) messaging using Twilio. It includes a Flask server to handle incoming replies and scripts to create RCS rich card templates.

## Prerequisites

- Python 3.8+
- A Twilio Account with RCS enabled
- Ngrok (for local testing of webhooks)

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd Test-RCS
    ```

2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Set up environment variables:
    Create a `.env` file in the root directory (see `.env.example` if available) with the following:
    ```
    TWILIO_ACCOUNT_SID=your_account_sid
    TWILIO_AUTH_TOKEN=your_auth_token
    TWILIO_MESSAGING_SERVICE_SID=your_messaging_service_sid
    TWILIO_CONTENT_SID=your_content_sid # Optional, can be generated via script
    TO_NUMBER=recipient_phone_number
    ```

## Usage

### 1. Start the Flask Server
The server handles sending messages and receiving replies.

```bash
python src/app.py
```
The server will start on `http://127.0.0.1:5000`.

### 2. Expose Local Server
Use ngrok to expose your local server so Twilio can send webhooks to it.

```bash
ngrok http 5000
```
Copy the forwarding URL (e.g., `https://your-domain.ngrok-free.app`) and configure it in your Twilio Messaging Service > Integration > Incoming Webhook.

### 3. Create a Template (Optional)
If you need to create a new RCS Rich Card template:

```bash
python src/template_manager.py
```
This will output a new `NEW_CONTENT_SID`. Update your `.env` file with this ID if you wish to use it.

### 4. Send an RCS Message
Send a POST request to your local server:

```bash
curl -X POST http://127.0.0.1:5000/send-rcs
```

## Project Structure

- `src/app.py`: Main Flask application.
- `src/template_manager.py`: Utility to create Twilio Content API templates.
