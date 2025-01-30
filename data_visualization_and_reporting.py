from data_cleaning_export import process_sneaker_updates, SERVICE_ACCOUNT_FILE
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import base64
from typing import Optional
import logging

# Constants
GMAIL_SCOPE = ["https://www.googleapis.com/auth/gmail.send"]
GOOGLE_OAUTH2_CREDENTIALS = "keys/oauth2_credentials.json"
RECIPIENT = "thomsoiitr15@gmail.com"
TOKEN_FILE = 'keys/token.json'
URL = "https://www.thesouledstore.com/men-footwear"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def authenticate_gmail() -> Optional[build]:
    """
    Authenticates the user with Gmail API and returns the service object.
    """
    credentials = None
    if os.path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPE)
    
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_OAUTH2_CREDENTIALS, GMAIL_SCOPE)
        credentials = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(credentials.to_json())
    
    return build('gmail', 'v1', credentials=credentials)

def generate_alert_email(url: str) -> None:
    """
    Generates an alert email based on sneaker updates and sends it.
    """
    new_sneakers, removed_sneakers, price_updates = process_sneaker_updates(url)
    
    if new_sneakers.empty and removed_sneakers.empty and price_updates.empty:
        logging.info("No updates found")
        return
    
    mail_template = create_email_content(new_sneakers, removed_sneakers, price_updates)
    send_alert_email(mail_template)

def create_email_content(new_sneakers, removed_sneakers, price_updates) -> str:
    """
    Creates the email content based on the sneaker updates.
    """
    mail_template = "<html><body>"
    if not new_sneakers.empty:
        mail_template += f"<h2>New Sneakers:</h2>{new_sneakers.to_html(index=False)}"
    if not removed_sneakers.empty:
        mail_template += f"<h2>Removed Sneakers:</h2>{removed_sneakers.to_html(index=False)}"
    if not price_updates.empty:
        mail_template += f"<h2>Price Updates:</h2>{price_updates.to_html(index=False)}"
    mail_template += "</body></html>"
    return mail_template

def send_alert_email(mail_template: str) -> None:
    """
    Sends an alert email with the given HTML template.
    """
    try:
        message = create_email_message(mail_template)
        mail_service = authenticate_gmail()
        mail_service.users().messages().send(userId='me', body={'raw': message}).execute()
        logging.info("Alert email sent successfully")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def create_email_message(mail_template: str) -> str:
    """
    Creates the email message and encodes it in base64.
    """
    message = MIMEMultipart()
    message['To'] = RECIPIENT
    message['Subject'] = "Sneaker Alert"
    message.attach(MIMEText(mail_template, 'html'))
    return base64.urlsafe_b64encode(message.as_bytes()).decode()

if __name__ == "__main__":
    generate_alert_email(URL)