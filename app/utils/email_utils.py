from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from app.core.config import EMAIL, APP_PASSWORD, PORT

conf = ConnectionConfig(
    MAIL_USERNAME=EMAIL,
    MAIL_PASSWORD=APP_PASSWORD,
    MAIL_FROM="FeelLog <noreply@feellog.app>",
    MAIL_PORT=PORT,
    MAIL_SERVER="smtp.gmail.com",
    USE_CREDENTIALS=True,
    MAIL_SSL_TLS=False,
    MAIL_STARTTLS=True,
)

async def send_onboard_email(to_email: EmailStr):
    subject = "🎉 Welcome to FeelLog!"
    recipients = [to_email]

    body = f"""
    Hi there,<br><br>
    Welcome to <strong>FeelLog</strong> – we're so glad you're here!<br><br>
    FeelLog is your space to reflect, express, and grow emotionally.<br>
    You're not alone on this journey—we're with you every step of the way.<br><br>
    Log your feelings anytime, and let us help you find clarity and calm.<br><br>
    With warmth,<br>
    The FeelLog Team
    """

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
          <h2 style="color: #2c3e50;">🎉 Welcome to FeelLog!</h2>
          <p style="font-size: 16px;">Hi there,</p>
          <p style="font-size: 16px;">
            We're so happy you've joined <strong>FeelLog</strong> – your space for emotional clarity and self-reflection.
          </p>
          <p style="font-size: 16px;">
            Start logging your thoughts and feelings whenever you need. It's private, supportive, and built just for you.
          </p>
          <p style="font-size: 16px;">
            You're not alone – we're here with you, every step of the way.
          </p>
          <br>
          <p style="font-size: 14px;">With warmth,</p>
          <p style="font-size: 14px;"><strong>The FeelLog Team</strong></p>
          <hr style="margin-top: 30px;">
          <p style="font-size: 12px; color: #aaa;">Sent by FeelLog • Please do not reply to this email</p>
        </div>
      </body>
    </html>
    """

    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=html_body,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)

async def send_otp_email(to_email: EmailStr, otp: str):
    subject = "🔐 Your OTP Code - Secure Verification"
    recipients = [to_email]

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
          <h2 style="color: #2c3e50;">🔐 OTP Verification</h2>
          <p style="font-size: 16px;">Hello,</p>
          <p style="font-size: 16px;">Your One-Time Password (OTP) is:</p>
          <h1 style="font-size: 36px; color: #2980b9; letter-spacing: 4px; text-align: center;">{otp}</h1>
          <p style="font-size: 14px; color: #555;">This OTP is valid for <strong>15 minutes</strong>. If you did not request this, please ignore this email.</p>
          <hr>
          <p style="font-size: 12px; color: #aaa;">Sent by FeelLog</p>
        </div>
      </body>
    </html>
    """

    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=html_body,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)
