# backend/users/utils.py
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

def send_email(subject, template, to_email, context):
    html_content = render_to_string(template, context)
    email = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email]
    )
    email.content_subtype = "html" 
    try:
        email.send()
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")