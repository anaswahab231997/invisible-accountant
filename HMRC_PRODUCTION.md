# HMRC Production Requirements

## Required Production APIs
The following APIs are required for the production environment:
- Business Details API
- Obligations API
- Self Employment Business API
- Individuals Calculations API
- Property Business API

## Sandbox APIs
**DO NOT** include the following Sandbox APIs in production:
- Test Support 1.0
- Create Test User 1.0
- Test Fraud Prevention 1.0

## Infrastructure Requirements
- **Hosting**: The backend server MUST be hosted using a Static Egress IP (e.g., AWS Elastic IP) to comply with the Developer Hub IP Allow List requirements.
