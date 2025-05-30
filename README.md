# ScamVanguard 🛡️

**Protect yourself from scams with AI-powered analysis**

ScamVanguard is a free, serverless service that helps non-technical users (especially seniors) identify potential scams in emails, text messages, and other communications. Simply forward suspicious content to our service and receive an quick SAFE/SCAM verdict with a clear explanation.

## Features

- **Multi-Channel Support**: Analyze suspicious content via email or SMS/MMS
- **AI-Powered Detection**: Uses OpenAI GPT-4 for intelligent scam detection
- **Simple Interface**: Easy-to-understand responses with emoji indicators
- **Privacy-First**: No user data stored beyond 24 hours
- **Free Service**: Up to 500 requests per day
- **Instant Results**: Responses typically within 2 minutes

## How to Use

### Email Analysis
Forward suspicious emails to: **scan@scamvanguard.com**

### SMS/MMS Analysis
Text suspicious messages to: **1-833-SCAM-STOP** (1-833-722-6786)

### Response Format
You'll receive a response with:
- ✅ **SAFE**: Content appears legitimate
- 🚨 **SCAM**: High likelihood of scam
- ⚠️ **UNSURE**: Unable to determine - exercise caution

Each verdict includes a brief explanation (under 120 characters) to help you understand the reasoning.

## Architecture

ScamVanguard is built on AWS using a completely serverless architecture:

```
User → Email/SMS → AWS SES/Twilio → Lambda → SQS → Lambda → GPT-4 → Response
                                        ↓
                                       S3 (temporary storage)
```

### Key Components

- **AWS SES**: Receives and processes incoming emails
- **Twilio**: Handles SMS/MMS messaging
- **AWS Lambda**: Serverless compute for email parsing and classification
- **Amazon SQS**: Message queuing for reliable processing
- **Amazon S3**: Temporary storage for attachments (auto-deleted after 24h)
- **OpenAI GPT-4**: AI model for scam detection
- **AWS Secrets Manager**: Secure API key storage

## Deployment

### Prerequisites
