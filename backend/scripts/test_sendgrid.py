"""
SendGrid Email Service Test Script

Tests email sending via SendGrid API to verify configuration.

Usage:
    SENDGRID_API_KEY="SG.xxx" python scripts/test_sendgrid.py

Reference: Sprint 128 Infrastructure Setup
"""
import os
import sys
import requests
from datetime import datetime


def test_sendgrid():
    """Test SendGrid email sending"""

    # Get API key from environment
    api_key = os.getenv("SENDGRID_API_KEY")

    if not api_key:
        print("❌ SENDGRID_API_KEY environment variable not set!")
        print("\nUsage:")
        print('  SENDGRID_API_KEY="SG.xxx" python scripts/test_sendgrid.py')
        sys.exit(1)

    # Get test email (default to user input)
    test_email = os.getenv("TEST_EMAIL")

    if not test_email:
        print("Enter your email address to receive test email:")
        test_email = input("> ")

    if not test_email or "@" not in test_email:
        print("❌ Invalid email address!")
        sys.exit(1)

    print(f"\n📧 Sending test email to: {test_email}")
    print(f"🔑 Using API key: {api_key[:20]}...")
    print(f"⏰ Timestamp: {datetime.utcnow().isoformat()}")
    print("\n" + "="*60)

    # Prepare email payload
    payload = {
        "personalizations": [
            {
                "to": [{"email": test_email}],
                "subject": "SendGrid Test - SDLC Orchestrator"
            }
        ],
        "from": {
            "email": os.getenv("SENDGRID_FROM_EMAIL", "noreply@sdlc-orchestrator.com"),
            "name": os.getenv("SENDGRID_FROM_NAME", "SDLC Orchestrator")
        },
        "content": [
            {
                "type": "text/html",
                "value": """
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { background: #0066cc; color: white; padding: 20px; text-align: center; }
                        .content { padding: 20px; background: #f8f9fa; }
                        .success { color: #28a745; font-weight: bold; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>✅ SendGrid Test Successful!</h1>
                        </div>
                        <div class="content">
                            <p class="success">Congratulations!</p>
                            <p>If you're reading this email, your SendGrid integration is working correctly.</p>
                            <p><strong>Configuration Details:</strong></p>
                            <ul>
                                <li>API Key: Configured ✅</li>
                                <li>Sender Email: Verified ✅</li>
                                <li>Email Delivery: Successful ✅</li>
                            </ul>
                            <p>You're ready to send team invitation emails!</p>
                            <hr>
                            <p style="font-size: 12px; color: #6c757d;">
                                Sent by SDLC Orchestrator - Team Invitation System (Sprint 128)<br>
                                Timestamp: """ + datetime.utcnow().isoformat() + """
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                """
            }
        ]
    }

    # Send email via SendGrid API
    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=10
        )

        print(f"\n📨 SendGrid API Response:")
        print(f"  Status Code: {response.status_code}")

        if response.status_code == 202:
            print(f"  Status: ✅ Accepted")
            print(f"\n🎉 SUCCESS! Email sent successfully!")
            print(f"\n📬 Check your inbox: {test_email}")
            print(f"   (Email should arrive within 1-2 minutes)")
            print(f"\n💡 If email not in inbox, check spam folder")
            return True

        else:
            print(f"  Status: ❌ Failed")
            print(f"  Response: {response.text}")

            # Parse error details
            if response.text:
                try:
                    error_data = response.json()
                    print(f"\n❌ SendGrid Error Details:")
                    for error in error_data.get("errors", []):
                        print(f"  - {error.get('message', 'Unknown error')}")
                except:
                    pass

            # Common error codes
            if response.status_code == 401:
                print(f"\n🔑 Error: Invalid API Key")
                print(f"   - Check SENDGRID_API_KEY is correct")
                print(f"   - Ensure API key has 'Mail Send' permissions")

            elif response.status_code == 403:
                print(f"\n🚫 Error: Sender Email Not Verified")
                print(f"   - Go to SendGrid → Settings → Sender Authentication")
                print(f"   - Verify sender email: {payload['from']['email']}")

            elif response.status_code == 400:
                print(f"\n⚠️ Error: Bad Request")
                print(f"   - Check email format is valid")
                print(f"   - Verify payload structure")

            return False

    except requests.RequestException as e:
        print(f"\n❌ Network Error: {str(e)}")
        print(f"   - Check internet connection")
        print(f"   - Verify SendGrid API endpoint is accessible")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SENDGRID EMAIL SERVICE TEST")
    print("Sprint 128 - Team Invitation System")
    print("="*60)

    success = test_sendgrid()

    print("\n" + "="*60)

    if success:
        print("✅ TEST PASSED - SendGrid configuration is correct!")
        print("\nNext Steps:")
        print("  1. ✅ SendGrid setup complete")
        print("  2. ⏭️  Continue to Redis setup")
        print("  3. ⏭️  Run integration tests")
        sys.exit(0)
    else:
        print("❌ TEST FAILED - Please fix SendGrid configuration")
        print("\nTroubleshooting:")
        print("  - Review SENDGRID-SETUP-GUIDE.md")
        print("  - Check SendGrid dashboard for errors")
        print("  - Verify sender email is verified")
        sys.exit(1)
