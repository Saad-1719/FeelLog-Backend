from email.message import EmailMessage
import aiosmtplib
from app.core.config import EMAIL, APP_PASSWORD, PORT

async def send_otp_email(to_email: str, otp: str):
    message = EmailMessage()
    message["From"] = f"FeelLog {EMAIL}"
    message["To"] = to_email
    message["Subject"] = "🔐 Your OTP Code - Secure Verification"

    # Plain text (fallback)
    message.set_content(f"Your OTP code is: {otp}\nThis code will expire in 15 minutes.")

    # HTML version
    html_content = f"""
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
    message.add_alternative(html_content, subtype='html')

    await aiosmtplib.send(
        message,
        hostname="smtp.gmail.com",
        port=PORT,
        start_tls=True,
        username=EMAIL,
        password=APP_PASSWORD
    )
