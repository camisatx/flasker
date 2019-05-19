import requests
from threading import Thread

from flask import current_app
from flask_mail import Message

from app import mail


def send_async_email(app, msg):
    """Send an email message using the application instance. Used for sending
    mail asynchronously."""
    # Make the application instance accessible, enabling mail. to work
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body,
        attachments=None, sync=False):
    """Build the email object and then send it out"""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if attachments:     # List of tuples
        for attachment in attachments:
            # attach method needs filename, media type, and actual file data
            msg.attach(*attachment)
    if sync:
        mail.send(msg)
    else:
        Thread(target=send_async_email,
               args=(current_app._get_current_object(), msg)).start()


def send_mg_email(subject, sender, recipients, text_body, html_body):
    """Send an email using Mailgun's API"""
    return requests.post(
            current_app.config['MAILGUN_ADDRESS'],
            auth=("api", current_app.config['MAILGUN_API']),
            data={"from": "%s <%s>" % (current_app.config['SITE_NAME'], sender),
                  "to": recipients,
                  "subject": subject,
                  "text": text_body,
                  "html": html_body,
                  })
