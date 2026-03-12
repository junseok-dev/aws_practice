# Deployment Key Setup

This document tracks the necessary keys and secrets for the AWS deployment pipeline via GitHub Actions.

## Required GitHub Secrets

| Secret Name | Source / How to Get | Default/Placeholder (If applicable) |
| :--- | :--- | :--- |
| `AWS_ACCESS_KEY_ID` | AWS IAM Console -> Users -> [Your User] -> Security Credentials -> Create access key | - |
| `AWS_SECRET_ACCESS_KEY` | Same as above (Only shown once during creation) | - |
| `EC2_HOST` | AWS EC2 Console -> Instances -> Public IPv4 address | - |
| `EC2_USERNAME` | Default for Ubuntu AMI | `ubuntu` |
| `EC2_PRIVATE_KEY` | Contents of your `.pem` file | - |
| `OPENAI_API_KEY` | [OpenAI Platform](https://platform.openai.com/api-keys) | - |
| `DJANGO_SECRET_KEY` | `backend/config/settings.py` or generate a new one | Found in `settings.py` |
| `REDIS_HOST` | Internal Docker network or EC2 IP | `redis` (within Docker) |

## Steps to populate

1. **AWS Identity**: Create an IAM user with `AmazonEC2FullAccess` (or specific permissions) and generate Access Keys.
2. **OpenAI**: Ensure you have an active API key with sufficient credits.
3. **Django**: Use a strong, unique secret key for production.
4. **GitHub**: Navigate to Repository Settings -> Secrets and variables -> Actions to add these.
