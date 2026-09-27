import requests

"""
Create all example email templates at once

Usage:
    python create_all_templates.py
"""

import asyncio
import sys

# All templates to create
TEMPLATES = [
    {
        "name": "welcome",
        "subject": "Welcome to {{ app_name }}! 🎉",
        "html_content": """<html><body style='font-family: Arial, sans-serif;'>
<h1>Welcome, {{ user_name }}!</h1>
<p>We're excited to have you on board.</p>
<p>Your account has been created with the email: <strong>{{ email }}</strong></p>
<p><a href='{{ app_url }}/dashboard' style='background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;'>Go to Dashboard</a></p>
<p>Best regards,<br>The {{ company_name }} Team</p>
</body></html>""",
        "plain_text_content": """Welcome, {{ user_name }}!

We're excited to have you on board.

Your account has been created with the email: {{ email }}

Go to your dashboard: {{ app_url }}/dashboard

Best regards,
The {{ company_name }} Team""",
        "variables": ["user_name", "email", "app_name", "app_url", "company_name"],
    },
    {
        "name": "password_reset",
        "subject": "Reset Your {{ app_name }} Password",
        "html_content": """<html><body style='font-family: Arial, sans-serif;'>
<h2>Password Reset Request</h2>
<p>Hi {{ user_name }},</p>
<p>We received a request to reset your password. Click the button below to create a new password:</p>
<p><a href='{{ reset_link }}' style='background-color: #2196F3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;'>Reset Password</a></p>
<p>This link expires in {{ expiration_hours }} hours.</p>
<p>If you didn't request this, you can ignore this email.</p>
<p>Security tip: Never share your password with anyone.</p>
</body></html>""",
        "plain_text_content": """Password Reset Request

Hi {{ user_name }},

We received a request to reset your password.

Reset your password here: {{ reset_link }}

This link expires in {{ expiration_hours }} hours.

If you didn't request this, you can ignore this email.

Security tip: Never share your password with anyone.""",
        "variables": ["user_name", "reset_link", "expiration_hours", "app_name"],
    },
    {
        "name": "order_confirmation",
        "subject": "Order #{{ order_id }} Confirmed",
        "html_content": """<html><body style='font-family: Arial, sans-serif;'>
<h2>Order Confirmation</h2>
<p>Hi {{ customer_name }},</p>
<p>Thank you for your order! Here are your order details:</p>
<table style='width: 100%; border-collapse: collapse;'>
<tr style='background-color: #f0f0f0;'>
<th style='border: 1px solid #ddd; padding: 8px;'>Item</th>
<th style='border: 1px solid #ddd; padding: 8px;'>Quantity</th>
<th style='border: 1px solid #ddd; padding: 8px;'>Price</th>
</tr>
<tr>
<td style='border: 1px solid #ddd; padding: 8px;'>{{ item_name }}</td>
<td style='border: 1px solid #ddd; padding: 8px;'>{{ quantity }}</td>
<td style='border: 1px solid #ddd; padding: 8px;'>${{ price }}</td>
</tr>
</table>
<p><strong>Order Total: ${{ total }}</strong></p>
<p>Your order will be delivered to:</p>
<p>{{ shipping_address }}</p>
<p>Estimated delivery: {{ delivery_date }}</p>
<p>Track your order: <a href='{{ tracking_url }}'>Click here</a></p>
</body></html>""",
        "plain_text_content": """Order Confirmation

Hi {{ customer_name }},

Thank you for your order #{{ order_id }}!

Item: {{ item_name }}
Quantity: {{ quantity }}
Price: ${{ price }}

Order Total: ${{ total }}

Shipping to:
{{ shipping_address }}

Estimated delivery: {{ delivery_date }}

Track your order: {{ tracking_url }}""",
        "variables": [
            "customer_name",
            "order_id",
            "item_name",
            "quantity",
            "price",
            "total",
            "shipping_address",
            "delivery_date",
            "tracking_url",
        ],
    },
    {
        "name": "email_verification",
        "subject": "Verify Your Email Address",
        "html_content": """<html><body style='font-family: Arial, sans-serif;'>
<h2>Email Verification</h2>
<p>Hi {{ user_name }},</p>
<p>Please verify your email address to complete your registration:</p>
<p><a href='{{ verification_link }}' style='background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;'>Verify Email</a></p>
<p>Or use this code: <code style='background-color: #f0f0f0; padding: 5px 10px;'>{{ verification_code }}</code></p>
<p>This link expires in 24 hours.</p>
</body></html>""",
        "plain_text_content": """Email Verification

Hi {{ user_name }},

Please verify your email address to complete your registration.

Verification link: {{ verification_link }}

Or use this code: {{ verification_code }}

This link expires in 24 hours.""",
        "variables": ["user_name", "verification_link", "verification_code"],
    },
    {
        "name": "promotional",
        "subject": "{{ discount }}% Off - Limited Time! 🔥",
        "html_content": """<html><body style='font-family: Arial, sans-serif; background-color: #f5f5f5;'>
<div style='max-width: 600px; margin: 0 auto; background-color: white; padding: 20px;'>
<h1 style='color: #e74c3c;'>{{ discount }}% OFF SALE!</h1>
<p>Hi {{ customer_name }},</p>
<p>We're having a special sale just for you!</p>
<p style='font-size: 18px; color: #27ae60;'>Use code: <strong>{{ promo_code }}</strong></p>
<p>Get {{ discount }}% off on {{ product_category }}</p>
<p><a href='{{ shop_url }}' style='background-color: #e74c3c; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-size: 16px;'>Shop Now</a></p>
<p style='color: #7f8c8d;'>Offer expires: {{ expiration_date }}</p>
</div>
</body></html>""",
        "plain_text_content": """{{ discount }}% OFF SALE!

Hi {{ customer_name }},

We're having a special sale just for you!

Use code: {{ promo_code }}
Get {{ discount }}% off on {{ product_category }}

Shop now: {{ shop_url }}

Offer expires: {{ expiration_date }}""",
        "variables": [
            "customer_name",
            "discount",
            "promo_code",
            "product_category",
            "shop_url",
            "expiration_date",
        ],
    },
    {
        "name": "payment_received",
        "subject": "Payment Received - Invoice #{{ invoice_id }}",
        "html_content": """<html><body style='font-family: Arial, sans-serif;'>
<h2>Payment Received</h2>
<p>Hi {{ customer_name }},</p>
<p>Thank you! We have received your payment.</p>
<table style='width: 100%; margin: 20px 0;'>
<tr><td><strong>Invoice #</strong></td><td>{{ invoice_id }}</td></tr>
<tr><td><strong>Amount</strong></td><td>${{ amount }}</td></tr>
<tr><td><strong>Payment Method</strong></td><td>{{ payment_method }}</td></tr>
<tr><td><strong>Date</strong></td><td>{{ payment_date }}</td></tr>
</table>
<p>Your invoice has been marked as paid. You can view it here: <a href='{{ invoice_url }}'>Download Invoice</a></p>
<p>Thank you for your business!</p>
</body></html>""",
        "plain_text_content": """Payment Received

Hi {{ customer_name }},

Thank you! We have received your payment.

Invoice #: {{ invoice_id }}
Amount: ${{ amount }}
Payment Method: {{ payment_method }}
Date: {{ payment_date }}

View your invoice: {{ invoice_url }}

Thank you for your business!""",
        "variables": [
            "customer_name",
            "invoice_id",
            "amount",
            "payment_method",
            "payment_date",
            "invoice_url",
        ],
    },
    {
        "name": "newsletter",
        "subject": "{{ month }} Newsletter - What's New",
        "html_content": """<html><body style='font-family: Arial, sans-serif;'>
<div style='max-width: 600px; margin: 0 auto;'>
<h2>{{ company_name }} Newsletter - {{ month }}</h2>
<p>Hi {{ user_name }},</p>
<h3>Featured Article</h3>
<p><strong>{{ article_title }}</strong></p>
<p>{{ article_excerpt }}</p>
<p><a href='{{ article_url }}'>Read More →</a></p>
<h3>Quick Updates</h3>
<ul>
<li>{{ update_1 }}</li>
<li>{{ update_2 }}</li>
<li>{{ update_3 }}</li>
</ul>
<h3>Upcoming Events</h3>
<p>{{ event_name }} - {{ event_date }}</p>
<p><a href='{{ event_url }}'>Learn More</a></p>
</div>
</body></html>""",
        "plain_text_content": """{{ company_name }} Newsletter - {{ month }}

Hi {{ user_name }},

Featured Article:
{{ article_title }}
{{ article_excerpt }}
{{ article_url }}

Quick Updates:
- {{ update_1 }}
- {{ update_2 }}
- {{ update_3 }}

Upcoming Events:
{{ event_name }} - {{ event_date }}
{{ event_url }}""",
        "variables": [
            "user_name",
            "company_name",
            "month",
            "article_title",
            "article_excerpt",
            "article_url",
            "update_1",
            "update_2",
            "update_3",
            "event_name",
            "event_date",
            "event_url",
        ],
    },
    {
        "name": "account_deactivated",
        "subject": "Your {{ app_name }} Account Has Been Deactivated",
        "html_content": """<html><body style='font-family: Arial, sans-serif;'>
<h2>Account Deactivation</h2>
<p>Hi {{ user_name }},</p>
<p>Your account on {{ app_name }} has been successfully deactivated on {{ deactivation_date }}.</p>
<p>You can reactivate your account anytime by logging in with your credentials.</p>
<p>If you need any help or have questions, contact us at: {{ support_email }}</p>
<p>We'd love to have you back!</p>
</body></html>""",
        "plain_text_content": """Account Deactivation

Hi {{ user_name }},

Your account on {{ app_name }} has been successfully deactivated on {{ deactivation_date }}.

You can reactivate your account anytime by logging in.

If you need help, contact: {{ support_email }}

We'd love to have you back!""",
        "variables": ["user_name", "app_name", "deactivation_date", "support_email"],
    },
    {
        "name": "otp_code",
        "subject": "Your {{ app_name }} Verification Code",
        "html_content": """<html><body style='font-family: Arial, sans-serif; text-align: center;'>
<h2>Verification Code</h2>
<p>Hi {{ user_name }},</p>
<p>Your verification code is:</p>
<h1 style='font-size: 48px; color: #2196F3; letter-spacing: 5px;'>{{ otp_code }}</h1>
<p>This code expires in {{ expiration_minutes }} minutes.</p>
<p style='color: #7f8c8d; font-size: 12px;'>If you didn't request this code, ignore this email.</p>
</body></html>""",
        "plain_text_content": """Verification Code

Hi {{ user_name }},

Your verification code is:

{{ otp_code }}

This code expires in {{ expiration_minutes }} minutes.

If you didn't request this code, ignore this email.""",
        "variables": ["user_name", "otp_code", "expiration_minutes", "app_name"],
    },
    {
        "name": "support_response",
        "subject": "Re: {{ ticket_subject }} - Ticket #{{ ticket_id }}",
        "html_content": """<html><body style='font-family: Arial, sans-serif;'>
<h2>Support Ticket Response</h2>
<p>Hi {{ customer_name }},</p>
<p>Thank you for contacting us. We've received your ticket and wanted to provide an update:</p>
<div style='background-color: #f0f0f0; padding: 15px; border-left: 4px solid #2196F3;'>
<p><strong>Ticket #{{ ticket_id }}</strong></p>
<p>{{ support_response }}</p>
</div>
<p>If you have any follow-up questions, please reply to this email or visit your ticket:</p>
<p><a href='{{ ticket_url }}'>View Ticket</a></p>
<p>Average response time: {{ response_time }}</p>
<p>Best regards,<br>{{ support_team_name }}</p>
</body></html>""",
        "plain_text_content": """Support Ticket Response

Hi {{ customer_name }},

Thank you for contacting us. Here's an update:

Ticket #{{ ticket_id }}
Subject: {{ ticket_subject }}

{{ support_response }}

View your ticket: {{ ticket_url }}

Average response time: {{ response_time }}

Best regards,
{{ support_team_name }}""",
        "variables": [
            "customer_name",
            "ticket_id",
            "ticket_subject",
            "support_response",
            "ticket_url",
            "response_time",
            "support_team_name",
        ],
    },
    {
        "name": "contact_us_reciepient",
        "subject": "New Contact Us Submission from {{ sender_name }} on {{ website_name }}",
        "html_content": """<html><body style='font-family: Arial, sans-serif;'>
<h2>New Contact Us Submission</h2>
<p>You have received a new message from the Contact Us form:</p>
<div style='background-color: #f0f0f0; padding: 15px; border-left: 4px solid #2196F3;'>
<p><strong>Name:</strong> {{ sender_name }}</p>
<p><strong>Email:</strong> {{ sender_email }}</p>
<p><strong>Subject:</strong> {{ subject }}</p>
<p><strong>Message:</strong></p>
<p>{{ message }}</p>
</div>
<p>Please respond to the sender at your earliest convenience.</p>
</body></html>""",
        "plain_text_content": """New Contact Us Submission

Name: {{ sender_name }}
Email: {{ sender_email }}
Subject: {{ subject }}
Message: {{ message }}

Please respond to the sender at your earliest convenience.""",
        "variables": [
            "website_name",
            "sender_name",
            "sender_email",
            "subject",
            "message",
        ],
    },
]


def create_all_templates(base_url: str = "http://localhost:8000/api"):
    """Create all example templates"""

    print("\n" + "=" * 60)
    print("Creating Email Templates")
    print("=" * 60 + "\n")

    created = 0
    failed = 0

    for template in TEMPLATES:
        try:
            response = requests.post(
                f"{base_url}/templates",
                json={
                    "name": template["name"],
                    "subject": template["subject"],
                    "html_content": template.get("html_content"),
                    "plain_text_content": template.get("plain_text_content"),
                    "variables": template.get("variables"),
                },
            )
            response.raise_for_status()
            result = response.json()
            print(f"✓ Created: {template['name']}")
            print(f"  ID: {result['id']}")
            print(f"  Variables: {', '.join(template.get('variables', []))}")
            print()
            created += 1
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to create {template['name']}: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"Summary: {created} created, {failed} failed")
    print("=" * 60 + "\n")

    if created > 0:
        print("✓ All templates created successfully!")
        print("\nYou can now use these templates:")
        for template in TEMPLATES:
            print(f"  - {template['name']}")

    return created, failed


async def main():
    """Main entry point"""
    base_url = "http://localhost:8000/api"

    # Check if custom URL provided
    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    print(f"\nUsing API: {base_url}\n")

    try:
        _, failed = create_all_templates(base_url)
        sys.exit(0 if failed == 0 else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
