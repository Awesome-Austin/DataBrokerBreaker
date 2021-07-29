# from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from email.mime.text import MIMEText
import os

from definitions import FILES_DIR

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
]

CREDENTIALS = os.path.join(FILES_DIR, 'credentials.json')


# class Requester:
#     """An abstract class for the Requester"""
#     def __init__(self):
#         self.subject = None
#         self.send_to = None
#         self.message_text = None

# @staticmethod
def get_service():
    """Creates a Gmail Service

    :return: Gmail Service
    """
    credentials = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    return build('gmail', 'v1', credentials=credentials)


def _create_message(send_to, subject, message_text):
    """Create a message for an email.

    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message['to'] = send_to
    message['from'] = 'me'
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}


def send_message(send_to, subject, message_text):
    """Send an email message.

    Args:
      send_to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.

    Returns:
      Sent Message.
    """
    # try:
    service = get_service()
    message = _create_message(send_to, subject, message_text)
    message = (service.users().messages().send(userId="me", body=message).execute())
    print(f"Message Id: {message['id']}")
    return message



