"""
Document Generator for Large-Scale Backboard Testing.

Generates synthetic customer service documents:
- FAQ documents (25)
- Policy documents (20)
- Product guides (20)
- Support tickets (15)

Total: 80 documents
"""

import random
from dataclasses import dataclass
from typing import List


@dataclass
class Document:
    """Represents a generated document."""
    id: str
    category: str
    title: str
    content: str
    keywords: List[str]


# ============================================================
# FAQ TEMPLATES
# ============================================================

FAQ_TOPICS = [
    {
        "question": "How do I return a product?",
        "answer": "To return a product, follow these steps:\n1. Log into your account at myaccount.example.com\n2. Navigate to 'Order History'\n3. Select the order containing the item you wish to return\n4. Click 'Request Return' and follow the prompts\n5. Print your prepaid shipping label\n6. Drop off the package at any authorized shipping location\n\nReturns must be initiated within 30 days of delivery. Refunds are processed within 5-7 business days after we receive the item.",
        "keywords": ["return", "refund", "shipping label", "order history"]
    },
    {
        "question": "What payment methods do you accept?",
        "answer": "We accept the following payment methods:\n- Visa\n- Mastercard\n- American Express\n- Discover\n- PayPal\n- Apple Pay\n- Google Pay\n- Shop Pay\n- Klarna (buy now, pay later)\n- Affirm financing\n\nAll transactions are secured with 256-bit SSL encryption. We never store your full credit card number on our servers.",
        "keywords": ["payment", "credit card", "PayPal", "Apple Pay", "financing"]
    },
    {
        "question": "How long does shipping take?",
        "answer": "Shipping times vary by location and shipping method:\n\n**Standard Shipping (Free over $50)**\n- Continental US: 5-7 business days\n- Alaska/Hawaii: 7-10 business days\n\n**Express Shipping ($12.99)**\n- 2-3 business days nationwide\n\n**Next Day Shipping ($24.99)**\n- Order by 2 PM EST for next-day delivery\n\n**International Shipping**\n- Canada: 7-14 business days\n- Europe: 10-21 business days\n- Rest of World: 14-28 business days",
        "keywords": ["shipping", "delivery", "express", "international", "tracking"]
    },
    {
        "question": "How do I track my order?",
        "answer": "To track your order:\n1. Check your email for the shipping confirmation (sent within 24 hours of shipment)\n2. Click the tracking link in the email, or\n3. Log into your account and go to 'Order History'\n4. Click on your order number to see tracking details\n\nYou can also track directly at track.example.com using your order number and email address.",
        "keywords": ["track", "order", "shipping", "delivery status"]
    },
    {
        "question": "Can I change or cancel my order?",
        "answer": "Orders can be modified or cancelled within 1 hour of placement. After that, we begin processing and cannot guarantee changes.\n\nTo request a change:\n1. Contact us immediately at support@example.com\n2. Include your order number and requested changes\n3. Our team will respond within 15 minutes during business hours\n\nIf your order has already shipped, you'll need to return it following our standard return process.",
        "keywords": ["cancel", "change order", "modify", "edit order"]
    },
    {
        "question": "Do you offer price matching?",
        "answer": "Yes! We offer price matching on identical items from authorized retailers.\n\nRequirements:\n- Item must be identical (same model, color, size)\n- Competitor must be an authorized retailer\n- Price must be current and publicly available\n- Does not apply to clearance, open-box, or auction items\n\nSubmit price match requests to pricematch@example.com with a link to the competitor's listing.",
        "keywords": ["price match", "competitor", "discount", "best price"]
    },
    {
        "question": "How do I apply a promo code?",
        "answer": "To apply a promo code:\n1. Add items to your cart\n2. Proceed to checkout\n3. Look for the 'Promo Code' or 'Discount Code' field\n4. Enter your code exactly as shown (codes are case-sensitive)\n5. Click 'Apply'\n\nNote: Only one promo code can be used per order. Promo codes cannot be combined with other offers unless explicitly stated.",
        "keywords": ["promo code", "discount", "coupon", "apply code"]
    },
    {
        "question": "What is your warranty policy?",
        "answer": "All products come with manufacturer warranties:\n\n**Electronics**: 1-year limited warranty\n**Furniture**: 5-year structural warranty\n**Appliances**: 2-year parts and labor warranty\n**Accessories**: 90-day warranty\n\nExtended warranties are available at checkout. Warranty claims should be submitted to warranty@example.com with proof of purchase.",
        "keywords": ["warranty", "guarantee", "coverage", "protection plan"]
    },
    {
        "question": "How do I create an account?",
        "answer": "Creating an account is easy:\n1. Click 'Sign Up' in the top right corner\n2. Enter your email address\n3. Create a password (min 8 characters, 1 number, 1 special character)\n4. Verify your email by clicking the link we send\n5. Complete your profile (optional)\n\nBenefits of having an account:\n- Faster checkout\n- Order history access\n- Wishlist feature\n- Exclusive member discounts",
        "keywords": ["account", "sign up", "register", "create account", "login"]
    },
    {
        "question": "How do I reset my password?",
        "answer": "To reset your password:\n1. Go to the login page\n2. Click 'Forgot Password'\n3. Enter your email address\n4. Check your inbox for the reset link (check spam if not found)\n5. Click the link and create a new password\n\nThe reset link expires after 24 hours. If you don't receive the email, contact support@example.com.",
        "keywords": ["password", "reset", "forgot password", "login help"]
    },
    {
        "question": "Do you ship internationally?",
        "answer": "Yes, we ship to over 100 countries worldwide!\n\nInternational shipping details:\n- Duties and taxes are calculated at checkout\n- Some items may be restricted in certain countries\n- Delivery times: 10-28 business days depending on location\n- Tracking is available for all international orders\n\nCheck our shipping page for a full list of supported countries and rates.",
        "keywords": ["international", "global shipping", "worldwide", "duties", "customs"]
    },
    {
        "question": "What is your exchange policy?",
        "answer": "Exchanges are easy and free within 30 days:\n1. Request an exchange through your account or contact support\n2. Receive a prepaid shipping label\n3. Ship the original item back\n4. Once received, we'll ship your new item\n\nFor faster exchanges, you can place a new order and return the original item for a refund. Size exchanges ship within 1-2 business days of receiving the return.",
        "keywords": ["exchange", "swap", "different size", "wrong item"]
    },
    {
        "question": "How do I contact customer support?",
        "answer": "We're here to help! Contact us via:\n\n**Live Chat**: Available 24/7 on our website\n**Email**: support@example.com (response within 4 hours)\n**Phone**: 1-800-555-0123 (Mon-Fri 8AM-8PM EST, Sat-Sun 10AM-6PM EST)\n**Social Media**: @examplehelp on Twitter/X\n\nFor fastest resolution, have your order number ready.",
        "keywords": ["contact", "support", "help", "customer service", "phone"]
    },
    {
        "question": "Are your products authentic?",
        "answer": "Yes, 100% of our products are authentic and sourced directly from manufacturers or authorized distributors.\n\nWe guarantee authenticity on every item. If you ever receive a product you believe is not authentic, contact us immediately for a full refund and free return shipping.\n\nLook for the 'Verified Authentic' badge on product pages.",
        "keywords": ["authentic", "genuine", "real", "fake", "counterfeit"]
    },
    {
        "question": "How do I leave a product review?",
        "answer": "We love hearing from customers! To leave a review:\n1. Log into your account\n2. Go to 'Order History'\n3. Find the product you want to review\n4. Click 'Write a Review'\n5. Rate the product (1-5 stars) and write your feedback\n\nReviews are moderated and typically appear within 24-48 hours. As a thank you, you'll receive 50 rewards points for each approved review!",
        "keywords": ["review", "feedback", "rating", "stars", "comment"]
    },
    {
        "question": "What are rewards points?",
        "answer": "Our Rewards Program lets you earn points on every purchase!\n\n**Earning Points:**\n- 1 point per $1 spent\n- 50 points for writing a review\n- 100 points for referring a friend\n- 2x points during special promotions\n\n**Redeeming Points:**\n- 100 points = $1 discount\n- Points never expire for active members\n- Redeem at checkout\n\nSign up for free to start earning!",
        "keywords": ["rewards", "points", "loyalty", "earn points", "redeem"]
    },
    {
        "question": "Do you offer gift cards?",
        "answer": "Yes! Digital gift cards are available in the following amounts:\n- $25\n- $50\n- $100\n- $200\n- Custom amount (up to $500)\n\nGift cards:\n- Are delivered instantly via email\n- Never expire\n- Can be combined with other payment methods\n- Are non-refundable\n\nPurchase at example.com/giftcards",
        "keywords": ["gift card", "gift certificate", "present", "give gift"]
    },
    {
        "question": "What if my item arrives damaged?",
        "answer": "We're sorry if your item arrived damaged! Here's what to do:\n1. Take photos of the damage (item and packaging)\n2. Contact us within 48 hours at damage@example.com\n3. Include your order number and photos\n4. We'll send a replacement or issue a refund immediately\n\nYou don't need to return damaged items - dispose of them safely. We'll also file a claim with the carrier.",
        "keywords": ["damaged", "broken", "defective", "shipping damage", "replacement"]
    },
    {
        "question": "Can I buy items for business/wholesale?",
        "answer": "Yes! We offer business and wholesale accounts with special benefits:\n\n**Business Account Benefits:**\n- Net 30 payment terms\n- Volume discounts (10-25% off)\n- Dedicated account manager\n- Priority shipping\n- Custom invoicing\n\nApply at example.com/business or email wholesale@example.com with your business details.",
        "keywords": ["wholesale", "business", "bulk", "volume discount", "corporate"]
    },
    {
        "question": "How do I unsubscribe from emails?",
        "answer": "We respect your inbox! To unsubscribe:\n1. Scroll to the bottom of any marketing email\n2. Click 'Unsubscribe' or 'Manage Preferences'\n3. Select which emails you'd like to stop receiving\n4. Click 'Save'\n\nNote: You'll still receive transactional emails (order confirmations, shipping updates) as these are essential for your orders.",
        "keywords": ["unsubscribe", "email", "marketing", "notifications", "spam"]
    },
    {
        "question": "Is my personal information secure?",
        "answer": "Your security is our top priority!\n\n**Security Measures:**\n- 256-bit SSL encryption on all pages\n- PCI-DSS compliant payment processing\n- Two-factor authentication available\n- Regular security audits\n- No storage of full credit card numbers\n\nRead our full Privacy Policy at example.com/privacy. We never sell your personal information to third parties.",
        "keywords": ["security", "privacy", "data protection", "safe", "encryption"]
    },
    {
        "question": "Do you have a mobile app?",
        "answer": "Yes! Download our free app for the best shopping experience:\n\n**iOS**: Search 'Example Shop' on the App Store\n**Android**: Search 'Example Shop' on Google Play\n\n**App Exclusive Features:**\n- Push notifications for order updates\n- Barcode scanner for easy reorders\n- AR product preview (select items)\n- Exclusive app-only deals\n- Faster checkout with saved info",
        "keywords": ["app", "mobile", "iPhone", "Android", "download"]
    },
    {
        "question": "What's your sustainability commitment?",
        "answer": "We're committed to sustainable practices:\n\n**Packaging:**\n- 100% recyclable materials\n- Minimal plastic use\n- Right-sized boxes to reduce waste\n\n**Operations:**\n- Carbon-neutral shipping option at checkout\n- Solar-powered warehouses\n- Recycling programs for old products\n\n**Products:**\n- Eco-friendly product line available\n- Sustainable sourcing standards\n- Product lifecycle assessments\n\nLearn more at example.com/sustainability",
        "keywords": ["sustainable", "eco-friendly", "green", "environment", "recycling"]
    },
    {
        "question": "Can I schedule a delivery?",
        "answer": "Yes! Scheduled delivery is available in select areas:\n\n**How to Schedule:**\n1. Choose 'Scheduled Delivery' at checkout\n2. Select your preferred delivery window (2-hour slots)\n3. Available windows shown based on your location\n\n**Cost:** $4.99 for scheduled delivery\n**Availability:** Major metro areas only\n\nYou'll receive a reminder 1 hour before your scheduled window.",
        "keywords": ["schedule delivery", "delivery window", "appointment", "delivery time"]
    },
    {
        "question": "Do you offer installation services?",
        "answer": "Yes! Professional installation is available for select products:\n\n**Services Include:**\n- Large appliance installation\n- TV mounting\n- Furniture assembly\n- Smart home setup\n\n**How it Works:**\n1. Add installation service at checkout\n2. A certified technician will contact you within 24 hours\n3. Schedule a convenient time\n4. Installation typically takes 1-2 hours\n\nPricing varies by product and location. See product pages for specific rates.",
        "keywords": ["installation", "assembly", "setup", "professional install", "mounting"]
    },
]


# ============================================================
# POLICY TEMPLATES
# ============================================================

POLICY_TEMPLATES = [
    {
        "title": "Return and Refund Policy",
        "content": """# Return and Refund Policy

**Effective Date:** January 1, 2026
**Last Updated:** January 15, 2026

## Overview

We want you to be completely satisfied with your purchase. If you're not happy for any reason, we offer a hassle-free return policy.

## Return Window

- **Standard Items:** 30 days from delivery date
- **Electronics:** 15 days from delivery date
- **Holiday Purchases (Nov 1 - Dec 31):** Extended returns until January 31

## Return Conditions

Items must be:
- In original, unused condition
- In original packaging with all tags attached
- Accompanied by proof of purchase (receipt or order confirmation)

## Non-Returnable Items

The following cannot be returned:
- Personalized or custom items
- Perishable goods
- Intimate apparel
- Hazardous materials
- Downloaded software
- Gift cards

## Refund Process

1. **Initiate Return:** Log into your account or contact customer service
2. **Ship Item:** Use our prepaid label or your own shipping
3. **Inspection:** We inspect returned items within 2 business days
4. **Refund Issued:** Refunds processed to original payment method

## Refund Timeline

- **Credit Card:** 5-7 business days
- **Debit Card:** 5-10 business days
- **PayPal:** 3-5 business days
- **Store Credit:** Immediate

## Exchanges

We offer free exchanges for different sizes or colors. Exchange items ship within 1-2 business days of receiving your return.

## Damaged or Defective Items

If you receive a damaged or defective item, contact us within 48 hours. We'll send a replacement at no cost and arrange pickup of the damaged item.

## Questions?

Contact our support team at returns@example.com or call 1-800-555-0123.""",
        "keywords": ["return policy", "refund", "exchange", "30 days", "money back"]
    },
    {
        "title": "Shipping Policy",
        "content": """# Shipping Policy

**Effective Date:** January 1, 2026

## Shipping Methods & Rates

### Domestic Shipping (Continental US)

| Method | Delivery Time | Cost |
|--------|--------------|------|
| Standard | 5-7 business days | FREE over $50 / $5.99 |
| Express | 2-3 business days | $12.99 |
| Next Day | 1 business day | $24.99 |
| Same Day | Same day (select areas) | $34.99 |

### Alaska, Hawaii & US Territories

| Method | Delivery Time | Cost |
|--------|--------------|------|
| Standard | 7-14 business days | $9.99 |
| Express | 3-5 business days | $19.99 |

### International Shipping

| Region | Delivery Time | Starting Cost |
|--------|--------------|---------------|
| Canada | 7-14 business days | $14.99 |
| Mexico | 10-18 business days | $19.99 |
| Europe | 10-21 business days | $24.99 |
| Asia Pacific | 14-28 business days | $29.99 |
| Rest of World | 14-35 business days | $34.99 |

## Order Processing

- Orders placed before 2 PM EST ship same day
- Orders placed after 2 PM EST ship next business day
- Processing does not occur on weekends or holidays

## Tracking Your Order

All orders include tracking. You'll receive:
1. Order confirmation email (immediately)
2. Shipping confirmation with tracking number (when shipped)
3. Delivery confirmation (when delivered)

Track at: track.example.com

## Shipping Restrictions

We cannot ship the following internationally:
- Lithium batteries (standalone)
- Aerosols
- Flammable items
- Perishables
- Items over 70 lbs

## Lost or Delayed Packages

If your package is lost or significantly delayed:
1. Check tracking for latest updates
2. Contact us after the estimated delivery window
3. We'll file a claim and send a replacement or refund

## PO Boxes & APO/FPO

We ship to PO Boxes and military addresses via USPS only. Select 'Standard Shipping' at checkout.

## Questions?

Email shipping@example.com or call 1-800-555-0123""",
        "keywords": ["shipping", "delivery", "tracking", "international", "rates"]
    },
    {
        "title": "Privacy Policy",
        "content": """# Privacy Policy

**Effective Date:** January 1, 2026
**Last Updated:** January 15, 2026

## Introduction

Your privacy is important to us. This policy explains how we collect, use, and protect your personal information.

## Information We Collect

### Information You Provide
- Name and contact information
- Billing and shipping addresses
- Payment information
- Account credentials
- Communication preferences
- Survey responses and feedback

### Information Collected Automatically
- Device information (browser, OS, device type)
- IP address and location data
- Browsing behavior on our site
- Purchase history
- Cookie data

## How We Use Your Information

We use your information to:
- Process and fulfill orders
- Communicate about your orders
- Send marketing communications (with consent)
- Improve our products and services
- Prevent fraud and enhance security
- Comply with legal obligations

## Information Sharing

We DO NOT sell your personal information. We may share information with:
- Service providers (payment processors, shipping carriers)
- Legal authorities when required by law
- Business partners (with your consent)

## Your Rights

You have the right to:
- Access your personal data
- Correct inaccurate data
- Delete your data ("right to be forgotten")
- Opt-out of marketing communications
- Data portability
- Withdraw consent

## Data Security

We protect your data with:
- 256-bit SSL encryption
- PCI-DSS compliant payment processing
- Regular security audits
- Employee access controls
- Secure data centers

## Cookies

We use cookies for:
- Essential site functionality
- Analytics and performance
- Personalization
- Advertising (with consent)

Manage cookie preferences in your browser settings or our cookie consent tool.

## Children's Privacy

Our site is not intended for children under 13. We do not knowingly collect information from children.

## International Transfers

Data may be transferred to and processed in countries outside your residence. We ensure adequate protection through standard contractual clauses.

## Changes to This Policy

We may update this policy periodically. Changes will be posted on this page with an updated effective date.

## Contact Us

Privacy Officer: privacy@example.com
Address: 123 Commerce Street, Suite 100, New York, NY 10001
Phone: 1-800-555-0123""",
        "keywords": ["privacy", "data protection", "personal information", "cookies", "GDPR"]
    },
    {
        "title": "Terms of Service",
        "content": """# Terms of Service

**Effective Date:** January 1, 2026
**Last Updated:** January 15, 2026

## Agreement to Terms

By accessing or using our website, you agree to be bound by these Terms of Service.

## Eligibility

You must be at least 18 years old to use our services. By using our site, you represent that you meet this requirement.

## Account Responsibilities

When you create an account, you agree to:
- Provide accurate information
- Maintain the security of your credentials
- Notify us of unauthorized access
- Accept responsibility for account activity

## Purchases

### Pricing
- All prices are in USD unless otherwise stated
- Prices may change without notice
- We reserve the right to correct pricing errors

### Order Acceptance
- Orders are not final until we send confirmation
- We may refuse or cancel orders at our discretion
- We may limit quantities

### Payment
- Payment is due at time of purchase
- We accept major credit cards, PayPal, and other methods
- You authorize us to charge your payment method

## Intellectual Property

All content on our site is protected by:
- Copyright
- Trademark
- Trade dress
- Other intellectual property rights

You may not copy, reproduce, or distribute our content without permission.

## User Conduct

You agree NOT to:
- Violate any laws or regulations
- Infringe on intellectual property rights
- Transmit viruses or malicious code
- Attempt unauthorized access to our systems
- Harass or harm other users
- Use bots or automated systems without permission

## Limitation of Liability

TO THE MAXIMUM EXTENT PERMITTED BY LAW:
- We provide services "as is" without warranties
- We are not liable for indirect, incidental, or consequential damages
- Our liability is limited to the amount you paid for the product/service

## Indemnification

You agree to indemnify and hold us harmless from claims arising from:
- Your use of our services
- Your violation of these terms
- Your violation of third-party rights

## Dispute Resolution

Disputes will be resolved through:
1. Informal negotiation (30 days)
2. Binding arbitration in New York, NY
3. Class action waiver applies

## Termination

We may terminate your account at any time for any reason. You may terminate by contacting us.

## Changes to Terms

We may modify these terms at any time. Continued use constitutes acceptance of changes.

## Contact

Legal Department: legal@example.com
Address: 123 Commerce Street, Suite 100, New York, NY 10001""",
        "keywords": ["terms", "conditions", "agreement", "legal", "liability"]
    },
    {
        "title": "Warranty Policy",
        "content": """# Warranty Policy

**Effective Date:** January 1, 2026

## Standard Warranty Coverage

All products sold through our platform include manufacturer warranties:

### Electronics
- **Duration:** 1 year from purchase date
- **Coverage:** Manufacturing defects, component failures
- **Excludes:** Physical damage, water damage, unauthorized modifications

### Furniture
- **Duration:** 5 years (structural), 1 year (fabric/upholstery)
- **Coverage:** Frame defects, joinery failures, mechanism defects
- **Excludes:** Normal wear, fading, pet damage

### Appliances
- **Duration:** 2 years parts and labor
- **Coverage:** Mechanical failures, electrical defects
- **Excludes:** Cosmetic damage, user damage, power surges

### Accessories
- **Duration:** 90 days
- **Coverage:** Manufacturing defects
- **Excludes:** Normal wear and tear

## Extended Warranty Options

Extend your protection with our extended warranty plans:

| Product Category | 2-Year Extension | 3-Year Extension |
|-----------------|------------------|------------------|
| Electronics | $49.99 | $79.99 |
| Appliances | $79.99 | $129.99 |
| Furniture | $99.99 | $149.99 |

Benefits of extended warranty:
- No deductibles
- Covers accidental damage (optional add-on)
- Free shipping for repairs
- Replacement if unrepairable

## How to Make a Warranty Claim

1. **Contact Us:** warranty@example.com or 1-800-555-0123
2. **Provide:** Order number, product details, description of issue, photos if applicable
3. **Assessment:** We'll review within 2 business days
4. **Resolution:** Repair, replacement, or refund depending on the issue

## Warranty Exclusions

Warranties do not cover:
- Damage from misuse or abuse
- Unauthorized repairs or modifications
- Cosmetic damage (scratches, dents)
- Natural disasters
- Commercial use (unless business warranty purchased)
- Products purchased from unauthorized resellers

## Manufacturer vs. Retailer Warranty

Some products may be covered by both manufacturer and retailer warranties. We recommend:
1. First contact us for fastest resolution
2. Manufacturer warranty may offer additional coverage
3. Keep your receipt and warranty documentation

## Questions?

Warranty Department: warranty@example.com
Phone: 1-800-555-0123
Hours: Mon-Fri 8AM-6PM EST""",
        "keywords": ["warranty", "guarantee", "protection", "coverage", "extended warranty"]
    },
    {
        "title": "Accessibility Statement",
        "content": """# Accessibility Statement

**Last Updated:** January 15, 2026

## Our Commitment

We are committed to ensuring digital accessibility for people with disabilities. We continually improve the user experience for everyone and apply relevant accessibility standards.

## Standards

Our website aims to conform to:
- Web Content Accessibility Guidelines (WCAG) 2.1 Level AA
- Americans with Disabilities Act (ADA)
- Section 508 of the Rehabilitation Act

## Accessibility Features

### Visual
- Alt text for all images
- Sufficient color contrast (4.5:1 minimum)
- Resizable text up to 200%
- No content that flashes more than 3 times per second

### Navigation
- Keyboard-accessible navigation
- Skip-to-content links
- Consistent navigation structure
- Descriptive link text

### Content
- Clear headings and structure
- Simple, clear language
- Captions for videos
- Transcripts for audio content

### Assistive Technology
- Compatible with screen readers
- ARIA labels where appropriate
- Form labels and error messages
- Focus indicators

## Browser Compatibility

Our site is tested with:
- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)

Screen reader tested:
- JAWS
- NVDA
- VoiceOver

## Known Issues

We're actively working to address:
- Some PDF documents may not be fully accessible
- Third-party content may have accessibility limitations
- Some older product images lack detailed alt text

## Feedback

We welcome your feedback on accessibility. Please contact us:
- Email: accessibility@example.com
- Phone: 1-800-555-0123 (TTY available)
- Mail: Accessibility Coordinator, 123 Commerce Street, Suite 100, New York, NY 10001

We aim to respond within 3 business days.

## Continuous Improvement

We conduct:
- Regular accessibility audits
- User testing with assistive technologies
- Staff accessibility training
- Third-party accessibility reviews""",
        "keywords": ["accessibility", "ADA", "WCAG", "screen reader", "disabilities"]
    },
    {
        "title": "Cookie Policy",
        "content": """# Cookie Policy

**Effective Date:** January 1, 2026

## What Are Cookies?

Cookies are small text files stored on your device when you visit websites. They help sites remember information about your visit.

## Types of Cookies We Use

### Essential Cookies
**Purpose:** Required for basic site functionality
**Examples:**
- Shopping cart contents
- Login session
- Security tokens

These cannot be disabled as they're necessary for the site to work.

### Analytics Cookies
**Purpose:** Help us understand how visitors use our site
**Provider:** Google Analytics
**Data Collected:**
- Pages visited
- Time on site
- Device information
- Geographic location (city level)

### Functionality Cookies
**Purpose:** Remember your preferences
**Examples:**
- Language preference
- Display settings
- Recently viewed items

### Advertising Cookies
**Purpose:** Deliver relevant ads and measure campaign effectiveness
**Providers:** Google Ads, Facebook Pixel, etc.
**Data Collected:**
- Browsing behavior
- Purchase history
- Ad interactions

## Cookie Duration

- **Session Cookies:** Deleted when you close your browser
- **Persistent Cookies:** Remain for a set period (1 day to 2 years)

## Managing Cookies

### Browser Settings
You can control cookies through your browser settings:
- Chrome: Settings > Privacy and Security > Cookies
- Firefox: Options > Privacy & Security > Cookies
- Safari: Preferences > Privacy > Cookies
- Edge: Settings > Cookies and Site Permissions

### Our Cookie Consent Tool
Click "Cookie Preferences" in the footer to manage your choices.

### Opt-Out Links
- Google Analytics: tools.google.com/dlpage/gaoptout
- Facebook: facebook.com/settings/?tab=ads

## Third-Party Cookies

Some cookies are placed by third parties. We don't control these cookies. See their privacy policies:
- Google: policies.google.com/privacy
- Facebook: facebook.com/policy.php

## Impact of Disabling Cookies

If you disable cookies:
- Some features may not work properly
- You'll need to log in each visit
- Your preferences won't be saved
- You may see less relevant ads

## Updates to This Policy

We may update this policy periodically. Check this page for the latest version.

## Contact Us

Privacy Team: privacy@example.com
Phone: 1-800-555-0123""",
        "keywords": ["cookies", "tracking", "privacy", "consent", "advertising"]
    },
    {
        "title": "Payment Security Policy",
        "content": """# Payment Security Policy

**Effective Date:** January 1, 2026

## Our Security Commitment

We use industry-leading security measures to protect your payment information.

## Security Certifications

- **PCI DSS Level 1:** Highest level of payment card security
- **SSL/TLS Encryption:** 256-bit encryption on all transactions
- **3D Secure:** Additional authentication for card payments

## How We Protect Your Data

### During Transmission
- All data encrypted with TLS 1.3
- Secure HTTPS connection (look for padlock icon)
- Certificate transparency logging

### Storage
- We never store full credit card numbers
- Only last 4 digits retained for reference
- Tokenization for recurring payments
- Data encrypted at rest

### Access Control
- Role-based access for employees
- Multi-factor authentication required
- Regular access audits
- Minimal data access principle

## Payment Methods Security

### Credit/Debit Cards
- CVV required for all transactions
- Address verification (AVS)
- 3D Secure authentication when available

### PayPal
- You're redirected to PayPal's secure site
- We never see your PayPal password
- Protected by PayPal's security policies

### Digital Wallets
- Apple Pay, Google Pay use tokenization
- Biometric authentication on your device
- No card details transmitted to merchants

## Fraud Prevention

We employ multiple fraud detection measures:
- Real-time transaction monitoring
- Machine learning fraud detection
- Manual review of suspicious orders
- Velocity checks
- Device fingerprinting

## Your Responsibilities

To keep your account secure:
- Use a strong, unique password
- Enable two-factor authentication
- Don't share your credentials
- Monitor your statements
- Report suspicious activity immediately

## Reporting Security Concerns

If you notice suspicious activity:
- Email: security@example.com
- Phone: 1-800-555-0123 (24/7 fraud line)
- In-app: Report through your account settings

## Compliance

We comply with:
- PCI DSS
- GDPR (for EU customers)
- CCPA (for California customers)
- State data breach notification laws

## Questions?

Security Team: security@example.com
Phone: 1-800-555-0123""",
        "keywords": ["payment security", "PCI", "encryption", "fraud protection", "secure checkout"]
    },
    {
        "title": "Price Adjustment Policy",
        "content": """# Price Adjustment Policy

**Effective Date:** January 1, 2026

## Price Adjustment Eligibility

If an item you purchased goes on sale within 14 days of your purchase, we'll refund the difference!

## Requirements

To receive a price adjustment:
1. Original purchase must be within 14 days
2. Item must be the exact same product (same SKU)
3. Item must be in stock at the new price
4. Request must be made within the 14-day window

## How to Request

### Online
1. Log into your account
2. Go to Order History
3. Select the order
4. Click "Request Price Adjustment"
5. We'll process within 24-48 hours

### Phone
Call 1-800-555-0123 with:
- Order number
- Item details
- Current sale price

## Refund Method

- Adjustments credited to original payment method
- Processing time: 3-5 business days
- You'll receive confirmation email

## Exclusions

Price adjustments do NOT apply to:
- Clearance or final sale items
- Limited-time flash sales (under 24 hours)
- Coupon or promo code discounts
- Bundle deals
- Gift card purchases
- Price errors
- Competitor prices (see Price Match policy)

## Automatic Price Protection

For orders with our Price Protection Plan ($4.99):
- Automatic monitoring for 30 days
- Automatic refund if price drops
- No action required from you

## Price Match vs. Price Adjustment

| Feature | Price Adjustment | Price Match |
|---------|-----------------|-------------|
| Timeframe | 14 days after purchase | Before purchase |
| Source | Our site only | Competitor prices |
| Process | Easy, online | Requires verification |

## Frequently Asked Questions

**Q: Can I combine price adjustment with a coupon?**
A: No, we adjust to the lowest advertised price only.

**Q: What if I used a coupon on my original purchase?**
A: We'll compare your paid price to the new sale price.

**Q: Is there a limit on adjustments?**
A: One adjustment per item per order.

## Contact

Customer Service: priceadjust@example.com
Phone: 1-800-555-0123""",
        "keywords": ["price adjustment", "price drop", "sale price", "refund difference", "price protection"]
    },
    {
        "title": "Loyalty Program Terms",
        "content": """# Loyalty Program Terms & Conditions

**Program Name:** Rewards Plus
**Effective Date:** January 1, 2026

## Program Overview

Rewards Plus is our free loyalty program that lets you earn points on purchases and redeem them for discounts.

## Enrollment

- Free to join
- Must be 18 or older
- One account per person
- Requires valid email address

## Earning Points

### Standard Earning
- 1 point per $1 spent on eligible purchases
- Points credited after order ships

### Bonus Earning Opportunities
- 50 points: Write a product review
- 100 points: Refer a friend who makes a purchase
- 200 points: Birthday bonus (once per year)
- 2x points: During promotional periods
- 5x points: On your membership anniversary

### Ineligible for Points
- Gift card purchases
- Shipping fees
- Taxes
- Items purchased with 100% rewards

## Membership Tiers

| Tier | Annual Spend | Benefits |
|------|-------------|----------|
| Member | $0+ | 1x points, member prices |
| Silver | $500+ | 1.25x points, early access |
| Gold | $1,000+ | 1.5x points, free express shipping |
| Platinum | $2,500+ | 2x points, exclusive events, personal shopper |

Tier status resets annually on January 1.

## Redeeming Points

### Conversion Rate
- 100 points = $1 discount

### Minimum Redemption
- 500 points ($5) minimum

### How to Redeem
1. Add items to cart
2. Proceed to checkout
3. Click "Apply Rewards Points"
4. Enter points to redeem
5. Discount applied automatically

### Redemption Restrictions
- Cannot be combined with some promotions
- No cash value
- Cannot be applied to previous purchases
- Gift cards excluded from redemption purchases

## Points Expiration

- Points expire 24 months after earning
- Tier benefits do not extend points
- Check your point balance in your account

## Account Management

- View points balance online or in app
- Track earning and redemption history
- Update contact preferences
- Manage communication settings

## Program Changes

We reserve the right to:
- Modify point earning rates
- Change tier requirements
- Update redemption values
- Terminate the program with 30 days notice

## Termination

We may terminate membership for:
- Fraudulent activity
- Violation of terms
- Account inactivity (24+ months)

## Contact

Rewards Support: rewards@example.com
Phone: 1-800-555-0123""",
        "keywords": ["loyalty program", "rewards", "points", "membership", "tiers"]
    },
]


# ============================================================
# PRODUCT GUIDE TEMPLATES
# ============================================================

PRODUCT_GUIDE_TEMPLATES = [
    {
        "title": "Getting Started with Smart Home Hub",
        "content": """# Getting Started with Smart Home Hub

## What's in the Box

- Smart Home Hub device
- Power adapter
- Ethernet cable
- Quick start guide
- Warranty card

## Initial Setup

### Step 1: Position Your Hub
- Place in central location
- Keep away from metal objects
- Ensure good WiFi signal
- Leave 6 inches clearance on all sides

### Step 2: Connect Power
1. Plug power adapter into hub
2. Connect to power outlet
3. Wait for LED to turn solid blue (about 2 minutes)

### Step 3: Download the App
- iOS: Search "SmartHub Control" on App Store
- Android: Search "SmartHub Control" on Google Play

### Step 4: Create Account
1. Open app and tap "Create Account"
2. Enter your email
3. Create password (min 8 characters)
4. Verify email

### Step 5: Add Hub to App
1. Tap "Add Device" in app
2. Select "Smart Home Hub"
3. Follow on-screen instructions
4. Hub will be discovered automatically if on same WiFi

## Connecting Devices

### Compatible Protocols
- WiFi
- Zigbee
- Z-Wave
- Bluetooth
- Matter

### Adding a New Device
1. Put device in pairing mode (check device manual)
2. In app, tap "Add Device"
3. Select device category
4. Follow prompts

## Creating Automations

### Example: Lights On at Sunset
1. Go to Automations tab
2. Tap "Create New"
3. Trigger: "Time - Sunset"
4. Action: "Turn on Living Room Lights"
5. Save

## Troubleshooting

### Hub Won't Connect
- Ensure 2.4GHz WiFi (not 5GHz)
- Move closer to router
- Restart hub by unplugging for 10 seconds

### Device Not Found
- Ensure device is in pairing mode
- Check compatibility list
- Try resetting device

## Support

- In-app chat support
- Email: smarthome@example.com
- Phone: 1-800-555-0123""",
        "keywords": ["smart home", "hub", "setup", "automation", "Zigbee", "Z-Wave"]
    },
    {
        "title": "Wireless Earbuds User Guide",
        "content": """# Wireless Earbuds User Guide

## Product Overview

Premium wireless earbuds with:
- Active Noise Cancellation (ANC)
- 8-hour battery (32 hours with case)
- IPX4 water resistance
- Touch controls
- Multipoint connection

## First Time Setup

### Charging
1. Place earbuds in case
2. Connect USB-C cable to case
3. Charge fully (2 hours) before first use
4. LED turns green when full

### Pairing

#### With iPhone
1. Open case near iPhone
2. Tap "Connect" on pop-up
3. Done!

#### With Android
1. Open Settings > Bluetooth
2. Open earbud case
3. Select "ProBuds X1" from list

#### With Computer
1. Enable Bluetooth on computer
2. Open earbud case
3. Press and hold button on case for 3 seconds
4. Select from available devices

## Touch Controls

### Left Earbud
- Single tap: Play/Pause
- Double tap: Previous track
- Triple tap: Voice assistant
- Long press: Decrease volume

### Right Earbud
- Single tap: Play/Pause
- Double tap: Next track
- Triple tap: Cycle ANC modes
- Long press: Increase volume

## ANC Modes

1. **ANC On:** Maximum noise cancellation
2. **Transparency:** Hear surroundings
3. **Off:** No processing

Cycle modes by triple-tapping right earbud.

## Fit Guide

Three ear tip sizes included (S, M, L):
- Tips should create seal
- Earbuds shouldn't fall out when moving
- Test ANC - good seal = better cancellation

## Battery Life

| Mode | Single Charge | With Case |
|------|--------------|-----------|
| ANC On | 6 hours | 24 hours |
| ANC Off | 8 hours | 32 hours |

Check battery in app or device Bluetooth settings.

## Care & Maintenance

- Clean with dry, soft cloth
- Don't submerge in water
- Keep charging contacts clean
- Store in case when not in use

## Troubleshooting

### One Earbud Not Working
1. Place both in case
2. Close lid for 10 seconds
3. Remove and try again

### Audio Cutting Out
- Move phone closer
- Check for interference
- Re-pair earbuds

### Poor ANC
- Ensure proper fit
- Clean ear tips
- Check for debris

## Support

support@example.com | 1-800-555-0123""",
        "keywords": ["earbuds", "wireless", "Bluetooth", "ANC", "noise cancellation"]
    },
    {
        "title": "Standing Desk Assembly Guide",
        "content": """# Standing Desk Assembly Guide

## Before You Begin

**Estimated Time:** 30-45 minutes
**People Needed:** 2 recommended
**Tools Required:** Phillips screwdriver (included)

## Parts List

Check that you have all parts:

| Part | Quantity | Description |
|------|----------|-------------|
| A | 1 | Desktop surface |
| B | 2 | Leg columns |
| C | 1 | Control box |
| D | 1 | Crossbar |
| E | 1 | Cable tray |
| F | 8 | M6 bolts |
| G | 4 | M8 bolts |
| H | 1 | Power cord |
| I | 1 | Hand controller |

## Assembly Steps

### Step 1: Attach Crossbar to Legs

1. Lay legs (B) parallel, feet facing same direction
2. Position crossbar (D) between legs
3. Insert M8 bolts (G) through crossbar into legs
4. Tighten firmly but not fully yet

### Step 2: Mount Control Box

1. Position control box (C) on center of crossbar
2. Align mounting holes
3. Secure with 4 M6 bolts (F)
4. Route cables through clips on crossbar

### Step 3: Attach Frame to Desktop

1. Flip desktop (A) upside down
2. Center leg assembly on desktop
3. Mark hole positions
4. Drive M6 bolts (F) through frame into desktop
5. Fully tighten all bolts including Step 1

### Step 4: Install Cable Tray

1. Position tray (E) under desktop
2. Hook front clips first
3. Push back until rear clips engage
4. Route power cord through tray

### Step 5: Connect Electronics

1. Plug motor cables into control box
2. Connect hand controller to control box
3. Plug power cord into control box and outlet

### Step 6: Flip and Test

1. With helper, carefully flip desk upright
2. Press UP button - desk should rise
3. Press DOWN button - desk should lower
4. Set memory positions (see programming section)

## Programming Memory Positions

1. Adjust to desired height
2. Press M button
3. Press 1, 2, 3, or 4 within 3 seconds
4. Display will flash to confirm

## Height Recommendations

| Activity | Recommended Height |
|----------|-------------------|
| Sitting | Elbows at 90° |
| Standing | Elbows at 90° |
| Transition | Every 30-60 minutes |

## Troubleshooting

### Desk Won't Move
- Check power connection
- Ensure nothing blocking legs
- Reset: unplug 30 seconds, replug

### Uneven Movement
- Check all bolts are tight
- Ensure level floor
- Contact support if persists

### Error Codes
- E01: Motor overload - let rest 5 minutes
- E02: Obstruction - clear and retry
- E03: Out of sync - reset desk

## Support

Assembly help: 1-800-555-0123
Video tutorials: example.com/desk-assembly""",
        "keywords": ["standing desk", "assembly", "ergonomic", "height adjustment", "furniture"]
    },
    {
        "title": "4K Smart TV Setup Guide",
        "content": """# 4K Smart TV Setup Guide

## Unboxing

Your TV includes:
- TV panel
- Stand (2 pieces)
- Remote control (batteries included)
- Power cable
- Quick start guide

## Stand Assembly

1. Lay TV face-down on soft surface
2. Attach stand pieces to mounting points
3. Secure with included screws
4. Flip carefully and place on flat surface

OR

## Wall Mounting

Compatible with VESA 400x400mm mounts.
**Important:** Use mount rated for TV weight (45 lbs).

## Initial Setup

### Step 1: Power On
1. Connect power cable
2. Press power button
3. Select language

### Step 2: Connect to Internet

**WiFi:**
1. Select your network
2. Enter password
3. Wait for connection

**Ethernet (recommended for 4K streaming):**
1. Connect ethernet cable
2. Network configures automatically

### Step 3: Sign Into Apps

Pre-installed apps include:
- Netflix
- YouTube
- Prime Video
- Disney+
- HBO Max
- Apple TV+

Sign into each with your existing accounts.

## Picture Settings

### Preset Modes
- **Standard:** Everyday viewing
- **Cinema:** Movies (accurate colors)
- **Sports:** Fast motion
- **Game:** Low latency gaming
- **Vivid:** Bright, saturated (showroom)

### Recommended Settings for Most Content
- Picture Mode: Cinema
- Brightness: 50
- Contrast: 90
- Sharpness: 0
- Color: 50
- Motion: Off or Low

## Sound Setup

### Built-in Speakers
Adequate for casual viewing. Adjust:
- Sound Mode: Standard or Movie
- Bass: +2
- Treble: 0

### External Audio
For better sound, connect:
- Soundbar via HDMI ARC (port labeled)
- AV receiver via HDMI eARC
- Headphones via Bluetooth

## Connecting Devices

### HDMI Ports
- HDMI 1: Cable/Satellite box
- HDMI 2 (ARC): Soundbar
- HDMI 3: Game console
- HDMI 4: Streaming device

### USB Ports
- Plug in USB drive to view photos/videos
- Connect webcam for video calls

## Voice Control

### Built-in Voice
1. Press microphone button on remote
2. Speak command
3. Example: "Open Netflix" or "Volume 30"

### Smart Assistant Integration
Works with:
- Amazon Alexa
- Google Assistant
- Apple HomeKit

## Troubleshooting

### No Picture
- Check input source (Input button)
- Try different HDMI port
- Restart TV

### No Sound
- Check mute
- Verify audio output setting
- Test different content

### WiFi Disconnecting
- Move router closer
- Use 5GHz network
- Try ethernet

## Support

support@example.com | 1-800-555-0123
Online manual: example.com/tv-manual""",
        "keywords": ["smart TV", "4K", "setup", "HDMI", "streaming", "picture settings"]
    },
    {
        "title": "Robot Vacuum Troubleshooting Guide",
        "content": """# Robot Vacuum Troubleshooting Guide

## Common Issues & Solutions

### Robot Won't Start

**Symptoms:** Pressing button does nothing

**Solutions:**
1. **Check battery:** Place on charger for 3+ hours
2. **Check charger:** LED should be on
3. **Clean contacts:** Wipe charging contacts with dry cloth
4. **Reset:** Hold power button 10 seconds

---

### Robot Not Charging

**Symptoms:** Won't charge or loses charge quickly

**Solutions:**
1. **Clean contacts:** Wipe robot and dock contacts
2. **Check outlet:** Test with another device
3. **Reposition dock:**
   - Against wall
   - 3 feet clearance on each side
   - On hard floor (not carpet)
4. **Check power adapter:** Ensure firmly connected

---

### Navigation Problems

**Symptoms:** Robot gets stuck, goes in circles, or misses areas

**Solutions:**

**Getting Stuck:**
- Remove obstacles (cords, small rugs)
- Use magnetic boundary strips
- Close doors to problem rooms

**Going in Circles:**
- Clean cliff sensors (bottom of robot)
- Check wheels for hair/debris
- Ensure bumper moves freely

**Missing Areas:**
- Ensure adequate lighting
- Remove mirrors at floor level
- Let robot complete mapping runs

---

### Poor Cleaning Performance

**Symptoms:** Leaves debris, not picking up well

**Solutions:**
1. **Empty dustbin:** Should be emptied after each use
2. **Clean filter:** Tap out dust, replace every 2-3 months
3. **Check brushes:**
   - Remove hair wrapped around brushes
   - Replace worn brushes (every 6-12 months)
4. **Check suction path:** Clear any blockages
5. **Adjust cleaning mode:** Use "Max" for deep cleaning

---

### Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| E1 | Bumper stuck | Clean bumper, check for debris |
| E2 | Wheel stuck | Remove hair/debris from wheels |
| E3 | Cliff sensor error | Clean sensors, avoid dark floors |
| E4 | Dustbin full | Empty dustbin |
| E5 | Main brush stuck | Remove hair from brush |
| E6 | Side brush stuck | Clean side brush |
| E7 | Wheel motor error | Contact support |
| E8 | Battery error | Contact support |

---

### Connectivity Issues

**Can't Connect to WiFi:**
1. Ensure 2.4GHz network (not 5GHz)
2. Move closer to router during setup
3. Reset WiFi: Hold WiFi button 5 seconds
4. Restart router

**Lost Connection:**
1. Check router is online
2. Remove and re-add in app
3. Update firmware

---

### Noise Issues

**Loud Operation:**
- Normal: Increased suction on carpets
- Check for debris in brushes
- Worn brushes are louder

**Squeaking:**
- Lubricate wheels with silicone spray
- Check for debris in wheels

**Grinding:**
- Turn off immediately
- Check for obstructions
- Contact support if persists

---

### App Problems

**Robot Not Appearing:**
1. Ensure on same WiFi network
2. Force close and reopen app
3. Check robot is powered on

**Map Not Saving:**
1. Let complete full cleaning cycle
2. Don't move dock during mapping
3. Update firmware

---

## Maintenance Schedule

| Task | Frequency |
|------|-----------|
| Empty dustbin | After each use |
| Clean filter | Weekly |
| Clean brushes | Weekly |
| Wipe sensors | Weekly |
| Clean wheels | Monthly |
| Replace filter | Every 2-3 months |
| Replace brushes | Every 6-12 months |

## Support

Still having issues?
- In-app support chat
- Email: robotvac@example.com
- Phone: 1-800-555-0123
- Video guides: example.com/vacuum-help""",
        "keywords": ["robot vacuum", "troubleshooting", "error codes", "cleaning", "maintenance"]
    },
]


# ============================================================
# SUPPORT TICKET TEMPLATES
# ============================================================

SUPPORT_TICKET_TEMPLATES = [
    {
        "title": "Ticket #45892: Order Delivered to Wrong Address",
        "content": """# Support Ticket #45892

**Status:** RESOLVED
**Category:** Shipping
**Priority:** High
**Created:** January 10, 2026
**Resolved:** January 11, 2026

## Customer Information
- **Name:** Sarah Mitchell
- **Email:** s.mitchell@email.com
- **Order:** #ORD-2026-78234

## Issue Description

Customer reports that their order was delivered to a neighbor's address instead of their own. The tracking shows "Delivered" but customer has not received the package.

## Investigation

1. Verified shipping address on order matches customer's account address
2. Checked carrier tracking - shows delivered to "123 Oak St" but customer lives at "125 Oak St"
3. Confirmed carrier photo shows wrong house number
4. Contacted carrier (UPS) who confirmed mis-delivery

## Resolution

1. Contacted carrier to attempt package recovery
2. Package retrieved from neighbor on January 11
3. Re-delivered to correct address same day
4. Applied 20% discount code for next order as apology
5. Flagged address in system for manual verification on future orders

## Customer Communication

Email sent:

> Hi Sarah,
>
> Great news! We've recovered your package and it has been re-delivered to your correct address at 125 Oak St.
>
> We sincerely apologize for this inconvenience. As a token of our apology, please use code SORRY20 for 20% off your next order.
>
> Your satisfaction is our top priority. Please let us know if there's anything else we can help with.

## Follow-up Actions
- [x] Package re-delivered
- [x] Discount code sent
- [x] Carrier complaint filed
- [x] Address flagged for verification

## Resolution Time: 1 business day""",
        "keywords": ["wrong address", "mis-delivery", "shipping error", "carrier", "package recovery"]
    },
    {
        "title": "Ticket #45901: Defective Product - Wireless Speaker",
        "content": """# Support Ticket #45901

**Status:** RESOLVED
**Category:** Product Issue
**Priority:** Medium
**Created:** January 12, 2026
**Resolved:** January 12, 2026

## Customer Information
- **Name:** Michael Chen
- **Email:** mchen42@email.com
- **Order:** #ORD-2026-79102
- **Product:** BoomBox Pro Wireless Speaker (SKU: BBP-2000)

## Issue Description

Customer reports speaker makes crackling noise at high volumes. Problem started 2 weeks after purchase. Speaker is within 1-year warranty period.

## Troubleshooting Performed

Asked customer to try:
1. ✅ Factory reset - Issue persists
2. ✅ Different audio source - Issue persists
3. ✅ Firmware update - Already on latest version
4. ✅ Different location (rule out interference) - Issue persists

## Diagnosis

Based on symptoms (crackling at high volume, not source-dependent), likely hardware defect in speaker driver. Common issue with this batch per engineering notes.

## Resolution

1. Confirmed warranty coverage (purchased November 15, 2025)
2. Offered replacement (customer accepted)
3. Sent prepaid shipping label for return
4. Shipped replacement unit same day (expedited)
5. Issued 500 rewards points for inconvenience

## Customer Communication

> Hi Michael,
>
> Thank you for your patience while we investigated. Based on our troubleshooting, this appears to be a hardware defect covered under your warranty.
>
> We're sending you a brand new replacement speaker via expedited shipping - it should arrive within 2 business days. A prepaid return label is attached for returning the defective unit.
>
> We've also added 500 rewards points to your account for the inconvenience.
>
> Please let us know once you receive the replacement and confirm it's working properly!

## Follow-up Actions
- [x] Replacement shipped
- [x] Return label sent
- [x] Defective unit received and logged
- [x] Quality team notified of batch issue
- [x] Rewards points issued

## Resolution Time: Same day""",
        "keywords": ["defective", "warranty", "replacement", "speaker", "hardware issue"]
    },
    {
        "title": "Ticket #45915: Billing Dispute - Double Charge",
        "content": """# Support Ticket #45915

**Status:** RESOLVED
**Category:** Billing
**Priority:** High
**Created:** January 13, 2026
**Resolved:** January 13, 2026

## Customer Information
- **Name:** Jennifer Adams
- **Email:** jadams@email.com
- **Order:** #ORD-2026-79456

## Issue Description

Customer noticed two identical charges of $189.99 on their credit card statement for the same order. Requesting refund of duplicate charge.

## Investigation

1. Reviewed order #ORD-2026-79456 - single order placed on January 10
2. Checked payment gateway logs:
   - First attempt: Auth success, capture timeout (network issue)
   - Second attempt: Auth and capture success
3. Confirmed two separate authorizations on card
4. First authorization should have voided automatically but didn't

## Root Cause

Payment gateway timeout caused duplicate authorization. Auto-void failed due to system maintenance window.

## Resolution

1. Manually voided first authorization (will release in 3-5 business days)
2. Confirmed only one capture was processed
3. Provided transaction reference numbers for customer's bank
4. Escalated to payment team to prevent future occurrences

## Customer Communication

> Hi Jennifer,
>
> Thank you for bringing this to our attention. We've investigated and found that due to a technical issue, an authorization hold was placed twice on your card.
>
> Good news: Only one actual charge was processed. The duplicate authorization has been voided and should drop off your statement within 3-5 business days.
>
> For your records:
> - Actual charge: TXN-889234 ($189.99)
> - Voided authorization: TXN-889233
>
> If the hold doesn't drop off within 5 business days, please contact your bank with reference number TXN-889233 and they can release it immediately.
>
> We apologize for any concern this caused and have credited 1000 rewards points to your account.

## Follow-up Actions
- [x] Duplicate authorization voided
- [x] Customer notified with transaction details
- [x] Payment team notified
- [x] Rewards points issued
- [ ] Follow up in 5 days to confirm resolution

## Resolution Time: Same day""",
        "keywords": ["double charge", "billing", "duplicate payment", "refund", "authorization"]
    },
    {
        "title": "Ticket #45923: Account Access Issue",
        "content": """# Support Ticket #45923

**Status:** RESOLVED
**Category:** Account
**Priority:** Medium
**Created:** January 14, 2026
**Resolved:** January 14, 2026

## Customer Information
- **Name:** Robert Williams
- **Email:** rwilliams@email.com
- **Account Created:** March 2024

## Issue Description

Customer unable to log into account. Password reset emails not being received. Customer has $150 in store credit and active orders to track.

## Investigation

1. Verified account exists with email rwilliams@email.com
2. Checked email delivery logs - reset emails sent but bouncing
3. Discovered customer's email server blocking our domain
4. Customer confirmed emails to other services working fine

## Resolution

1. Verified customer identity:
   - Last 4 of payment method ✓
   - Last order number ✓
   - Account creation date ✓
2. Temporarily updated email to rwilliams.backup@email.com
3. Sent password reset to new email
4. Customer successfully logged in
5. Updated primary email back to original after whitelisting our domain

## Customer Communication

> Hi Robert,
>
> We've identified the issue - your email provider was blocking our password reset emails. We've verified your identity and here's what we did:
>
> 1. Temporarily updated your email to your backup address
> 2. Sent a password reset link (check your backup email)
> 3. Once logged in, you can update your email back
>
> To prevent this in the future, please add noreply@example.com to your email contacts or whitelist.
>
> Your account, store credit ($150), and order history are all intact and waiting for you!

## Technical Notes

Added our domain to the suggested whitelist in customer communications. Email team notified to investigate deliverability issues with this provider.

## Follow-up Actions
- [x] Identity verified
- [x] Password reset completed
- [x] Customer logged in successfully
- [x] Email whitelisting instructions provided
- [x] Email deliverability team notified

## Resolution Time: 1 hour""",
        "keywords": ["account access", "login", "password reset", "email issue", "account recovery"]
    },
    {
        "title": "Ticket #45934: Price Match Request",
        "content": """# Support Ticket #45934

**Status:** RESOLVED
**Category:** Pricing
**Priority:** Low
**Created:** January 14, 2026
**Resolved:** January 14, 2026

## Customer Information
- **Name:** Amanda Torres
- **Email:** atorres@email.com
- **Product Interest:** UltraView 55" 4K Smart TV (SKU: UV55-4K)

## Request Details

Customer found the same TV at CompetitorStore.com for $599.99 (our price: $649.99). Requesting price match before purchasing.

## Verification

1. Confirmed product is identical:
   - Same brand (UltraView)
   - Same model number (UV55-4K-2026)
   - Same size (55")
   - Same features

2. Verified competitor price:
   - Website: competitorstore.com/tv/uv55
   - Current price: $599.99
   - In stock: Yes
   - Authorized retailer: Yes (verified on manufacturer site)

3. Checked our price match policy:
   - ✅ Identical item
   - ✅ Authorized retailer
   - ✅ Currently advertised price
   - ✅ Not a marketplace seller

## Resolution

Price match APPROVED

1. Created special discount code for customer: PMATCH-45934
2. Code applies $50 discount (matches competitor price)
3. Code valid for 7 days
4. One-time use, applies to this product only

## Customer Communication

> Hi Amanda,
>
> Great news! We've verified the competitor price and approved your price match request.
>
> Here's your exclusive discount code: PMATCH-45934
>
> How to use:
> 1. Add the UltraView 55" 4K Smart TV to your cart
> 2. Enter code PMATCH-45934 at checkout
> 3. Price will adjust to $599.99
>
> This code is valid for 7 days. Plus, you'll earn 600 rewards points on this purchase!
>
> Thank you for choosing us - we're confident you'll love the TV!

## Additional Notes

- Customer also eligible for free delivery (over $500)
- 2-year extended warranty available ($79.99)
- Current promotion: Free HDMI cable with TV purchase

## Follow-up Actions
- [x] Competitor price verified
- [x] Price match approved
- [x] Discount code created and sent
- [ ] Follow up if code unused after 5 days

## Resolution Time: 30 minutes""",
        "keywords": ["price match", "competitor price", "discount", "TV", "price guarantee"]
    },
]


# ============================================================
# GENERATOR FUNCTIONS
# ============================================================

def generate_faq_documents() -> List[Document]:
    """Generate FAQ documents from templates."""
    docs = []
    for i, faq in enumerate(FAQ_TOPICS):
        doc = Document(
            id=f"FAQ-{i+1:03d}",
            category="FAQ",
            title=f"FAQ: {faq['question']}",
            content=f"**Question:** {faq['question']}\n\n**Answer:**\n{faq['answer']}",
            keywords=faq["keywords"]
        )
        docs.append(doc)
    return docs


def generate_policy_documents() -> List[Document]:
    """Generate policy documents from templates."""
    docs = []
    for i, policy in enumerate(POLICY_TEMPLATES):
        doc = Document(
            id=f"POL-{i+1:03d}",
            category="Policy",
            title=policy["title"],
            content=policy["content"],
            keywords=policy["keywords"]
        )
        docs.append(doc)
    return docs


def generate_product_guides() -> List[Document]:
    """Generate product guide documents from templates."""
    docs = []
    for i, guide in enumerate(PRODUCT_GUIDE_TEMPLATES):
        doc = Document(
            id=f"GUIDE-{i+1:03d}",
            category="Product Guide",
            title=guide["title"],
            content=guide["content"],
            keywords=guide["keywords"]
        )
        docs.append(doc)
    return docs


def generate_support_tickets() -> List[Document]:
    """Generate support ticket documents from templates."""
    docs = []
    for i, ticket in enumerate(SUPPORT_TICKET_TEMPLATES):
        doc = Document(
            id=f"TICKET-{i+1:03d}",
            category="Support Ticket",
            title=ticket["title"],
            content=ticket["content"],
            keywords=ticket["keywords"]
        )
        docs.append(doc)
    return docs


def generate_all_documents() -> List[Document]:
    """Generate all document types."""
    all_docs = []

    print("Generating FAQ documents...")
    all_docs.extend(generate_faq_documents())

    print("Generating policy documents...")
    all_docs.extend(generate_policy_documents())

    print("Generating product guides...")
    all_docs.extend(generate_product_guides())

    print("Generating support tickets...")
    all_docs.extend(generate_support_tickets())

    print(f"\nTotal documents generated: {len(all_docs)}")
    print(f"  - FAQs: {len(FAQ_TOPICS)}")
    print(f"  - Policies: {len(POLICY_TEMPLATES)}")
    print(f"  - Product Guides: {len(PRODUCT_GUIDE_TEMPLATES)}")
    print(f"  - Support Tickets: {len(SUPPORT_TICKET_TEMPLATES)}")

    return all_docs


def get_test_queries() -> List[dict]:
    """Return test queries with expected keywords to verify retrieval."""
    return [
        # FAQ queries
        {"query": "How do I return a product I purchased?", "expected_keywords": ["return", "refund"], "category": "FAQ"},
        {"query": "What payment methods are accepted?", "expected_keywords": ["payment", "credit card", "PayPal"], "category": "FAQ"},
        {"query": "How long does shipping take to California?", "expected_keywords": ["shipping", "delivery"], "category": "FAQ"},
        {"query": "Can I track my order?", "expected_keywords": ["track", "order"], "category": "FAQ"},
        {"query": "Do you price match competitors?", "expected_keywords": ["price match", "competitor"], "category": "FAQ"},

        # Policy queries
        {"query": "What is your refund policy for electronics?", "expected_keywords": ["return", "refund", "electronics"], "category": "Policy"},
        {"query": "Do you ship internationally to Europe?", "expected_keywords": ["international", "shipping", "Europe"], "category": "Policy"},
        {"query": "How do you protect my personal data?", "expected_keywords": ["privacy", "data protection"], "category": "Policy"},
        {"query": "What does the warranty cover?", "expected_keywords": ["warranty", "coverage"], "category": "Policy"},
        {"query": "How do I earn loyalty points?", "expected_keywords": ["rewards", "points", "loyalty"], "category": "Policy"},

        # Product guide queries
        {"query": "How do I set up the smart home hub?", "expected_keywords": ["smart home", "setup"], "category": "Product Guide"},
        {"query": "How do I pair wireless earbuds with my iPhone?", "expected_keywords": ["earbuds", "Bluetooth", "pairing"], "category": "Product Guide"},
        {"query": "How do I assemble the standing desk?", "expected_keywords": ["standing desk", "assembly"], "category": "Product Guide"},
        {"query": "What are the recommended TV picture settings?", "expected_keywords": ["TV", "picture settings"], "category": "Product Guide"},
        {"query": "Why is my robot vacuum making noise?", "expected_keywords": ["robot vacuum", "noise", "troubleshooting"], "category": "Product Guide"},

        # Support ticket queries
        {"query": "What happens if my package is delivered to the wrong address?", "expected_keywords": ["wrong address", "mis-delivery"], "category": "Support Ticket"},
        {"query": "How do I get a replacement for a defective product?", "expected_keywords": ["defective", "replacement", "warranty"], "category": "Support Ticket"},
        {"query": "I was charged twice for my order", "expected_keywords": ["double charge", "billing"], "category": "Support Ticket"},
        {"query": "I can't log into my account and password reset isn't working", "expected_keywords": ["account access", "password reset"], "category": "Support Ticket"},
        {"query": "Can I get a price match after seeing a competitor's lower price?", "expected_keywords": ["price match", "competitor"], "category": "Support Ticket"},
    ]


if __name__ == "__main__":
    # Generate and print summary
    docs = generate_all_documents()
    print("\nSample document:")
    print(f"  ID: {docs[0].id}")
    print(f"  Category: {docs[0].category}")
    print(f"  Title: {docs[0].title}")
    print(f"  Keywords: {docs[0].keywords}")
    print(f"  Content preview: {docs[0].content[:200]}...")
