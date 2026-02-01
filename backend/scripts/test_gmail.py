"""
Gmail SMTP Test Script

Tests email sending via Gmail with App Password.

Prerequisites:
1. Enable 2-Factor Authentication on your Google Account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Set environment variables:
   - GMAIL_EMAIL: Your Gmail address
   - GMAIL_APP_PASSWORD: 16-character app password (no spaces)

Usage:
    GMAIL_EMAIL="your@gmail.com" GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx" python scripts/test_gmail.py

Reference: Sprint 128 Infrastructure Setup
"""
import os
import smtplib
import ssl
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def test_gmail():
    """Test Gmail SMTP email sending"""

    print("\n" + "="*60)
    print("GMAIL SMTP TEST")
    print("Sprint 128 - Team Invitation System")
    print("="*60 + "\n")

    # Get credentials from environment
    gmail_email = os.getenv("GMAIL_EMAIL", "")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "")

    # Prompt for missing credentials
    if not gmail_email:
        print("Enter your Gmail address:")
        gmail_email = input("> ").strip()

    if not gmail_app_password:
        print("\nEnter your Gmail App Password (16 chars, no spaces):")
        print("(Get it from: https://myaccount.google.com/apppasswords)")
        gmail_app_password = input("> ").strip().replace(" ", "")

    if not gmail_email or not gmail_app_password:
        print("❌ Gmail credentials required!")
        sys.exit(1)

    # Get test recipient
    test_email = os.getenv("TEST_EMAIL", "")
    if not test_email:
        print(f"\nEnter recipient email (or press Enter to send to {gmail_email}):")
        test_email = input("> ").strip() or gmail_email

    print(f"\n📧 Testing Gmail SMTP...")
    print(f"   From: {gmail_email}")
    print(f"   To: {test_email}")
    print(f"   Server: smtp.gmail.com:587")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    print("\n" + "="*60)

    # Create test email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Gmail SMTP Test - SDLC Orchestrator"
    msg["From"] = f"SDLC Orchestrator <{gmail_email}>"
    msg["To"] = test_email

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #28a745; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ padding: 20px; background: #f8f9fa; border-radius: 0 0 8px 8px; }}
            .success {{ color: #28a745; font-weight: bold; font-size: 18px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Gmail SMTP Test Successful!</h1>
            </div>
            <div class="content">
                <p class="success">Congratulations!</p>
                <p>Your Gmail SMTP configuration is working correctly.</p>

                <h3>Configuration Details:</h3>
                <ul>
                    <li><strong>Provider:</strong> Gmail SMTP</li>
                    <li><strong>Server:</strong> smtp.gmail.com:587</li>
                    <li><strong>TLS:</strong> Enabled ✅</li>
                    <li><strong>Authentication:</strong> App Password ✅</li>
                </ul>

                <p>You're ready to send team invitation emails!</p>

                <hr style="margin: 20px 0;">
                <p style="font-size: 12px; color: #6c757d;">
                    Sent by SDLC Orchestrator - Team Invitation System (Sprint 128)<br>
                    Timestamp: {datetime.now().isoformat()}
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_content, "html"))

    try:
        # Create secure connection
        context = ssl.create_default_context()

        print("\n1️⃣ Connecting to smtp.gmail.com:587...")

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            print("2️⃣ Starting TLS encryption...")
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()

            print("3️⃣ Authenticating with App Password...")
            server.login(gmail_email, gmail_app_password)

            print("4️⃣ Sending test email...")
            server.sendmail(gmail_email, test_email, msg.as_string())

        print("\n" + "="*60)
        print("✅ SUCCESS! Email sent successfully!")
        print(f"\n📬 Check your inbox: {test_email}")
        print("   (Email should arrive within 1-2 minutes)")
        print("\n💡 If email not in inbox, check spam folder")
        print("="*60 + "\n")

        # Save credentials hint
        print("📝 Add these to your .env.local file:\n")
        print(f'   GMAIL_EMAIL="{gmail_email}"')
        print(f'   GMAIL_APP_PASSWORD="{gmail_app_password}"')
        print(f'   EMAIL_FROM_ADDRESS="{gmail_email}"')
        print('   EMAIL_PROVIDER="gmail"')
        print('   EMAIL_SANDBOX_MODE=false')
        print("")

        return True

    except smtplib.SMTPAuthenticationError as e:
        print("\n" + "="*60)
        print("❌ AUTHENTICATION FAILED!")
        print("="*60)
        print(f"\nError: {str(e)}")
        print("\n🔑 Troubleshooting:")
        print("   1. Ensure 2-Factor Authentication is enabled on your Google Account")
        print("   2. Generate a NEW App Password: https://myaccount.google.com/apppasswords")
        print("   3. Use the 16-character password WITHOUT spaces")
        print("   4. Make sure you're using your full Gmail address")
        return False

    except smtplib.SMTPException as e:
        print("\n" + "="*60)
        print("❌ SMTP ERROR!")
        print("="*60)
        print(f"\nError: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check your internet connection")
        print("   2. Ensure Gmail SMTP is not blocked by firewall")
        print("   3. Try again in a few minutes")
        return False

    except Exception as e:
        print("\n" + "="*60)
        print("❌ UNEXPECTED ERROR!")
        print("="*60)
        print(f"\nError: {type(e).__name__}: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_gmail()

    if success:
        print("\n✅ Gmail SMTP test PASSED!")
        print("\nNext Steps:")
        print("  1. Update .env.local with credentials shown above")
        print("  2. Set EMAIL_SANDBOX_MODE=false to enable real emails")
        print("  3. Run integration tests")
        sys.exit(0)
    else:
        print("\n❌ Gmail SMTP test FAILED!")
        print("   Please check the troubleshooting steps above.")
        sys.exit(1)
