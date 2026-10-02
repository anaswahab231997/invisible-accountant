# HMRC OFFICIAL GUIDELINES
**Source:** HMRC Developer Hub (API Documentation)
**Last Updated:** 2026-09-26

## 1. Fraud Prevention Headers (OTHER_VIA_SERVER)
When connecting to HMRC APIs, you must include specific "Fraud Prevention Headers" to verify the legitimacy of the request and provide technical metadata about the device/environment. For headless or server-side architectures, the appropriate connection method is `OTHER_VIA_SERVER`.

**Key Requirements for `OTHER_VIA_SERVER`:**
- **Identifiers:** You must supply the correct headers that inform HMRC this is a server-side application acting as a gateway, not a web or desktop client.
- **Strict Spelling & Case:** Headers must be exactly spelled (e.g., `Gov-Client-Device-ID`, not `Id`) and properly formatted (e.g., timestamps must include milliseconds).
- **Mandatory Nature:** If the full set of required headers for `OTHER_VIA_SERVER` is missing or malformed, the API request will be rejected.
- **Reference:** Developers must validate their architecture against the [HMRC Fraud Prevention documentation](https://developer.service.hmrc.gov.uk/api-documentation/docs/fraud-prevention) and can use linting tools to catch formatting errors.

## 2. MTD ITSA API JSON Payload Schemas and Rules
The definitive source for payload schemas is the [HMRC API Catalogue](https://developer.service.hmrc.gov.uk/api-catalogue).

**Integration Rules:**
- **Content Negotiation (Versioning):** You must specify the API version via the `Accept` header. Example: `Accept: application/vnd.hmrc.3.0+json`. Using the wrong version leads to `406 Not Acceptable` or `404 Not Found`. Endpoint versions vary across the ecosystem.
- **Headers and Bodies:** 
  - `Content-Type: application/json` must ONLY be used for requests with a body (`POST`, `PUT`, `PATCH`). 
  - *Gotcha:* Do not include `Content-Type` on bodyless `GET` requests, as this may trigger a `403 Bad Request` from HMRC's edge servers.
- **Schemas by Category:**
  - *Business Details (MTD):* Manage business information and accounting periods.
  - *Obligations (MTD):* Retrieve tax periods and deadlines.
  - *Individual Calculations (MTD):* Trigger and retrieve self-assessment calculations.
  - *BSAS (Business Source Adjustable Summary):* Handle adjustments to income sources.
- **Best Practice:** Do not rely on third-party tutorials. Always refer to the official HMRC API Reference for the specific endpoint version you are targeting.

## 3. Sandbox Testing Requirements & Missing-Data Protocols
The HMRC Sandbox (`https://test-api.service.hmrc.gov.uk`) isolates testing from production data.

**Sandbox Requirements:**
- **Registration:** Register your application on the HMRC Developer Hub to get your Client ID and Client Secret. Subscribe to specific APIs (e.g., MTD Income Tax).
- **Test Users:** Real tax credentials will not work. You must create "test users" (individuals, organisations, agents) via the Developer Hub's test user endpoints to simulate specific scenarios (e.g., Self Assessment enrollment).
- **Fraud Headers:** Even in the sandbox, Fraud Prevention headers are strictly required.

**Missing-Data Protocols & Error Handling:**
- **404 Not Found:** Often indicates data is legitimately missing or hasn't been processed yet (e.g., nightly reconciliation for Self Assessment).
- **Graceful Failure:** The software must not crash on a 404. It should present a user-friendly "Data is currently unavailable" message.
- **Validation Errors:** Validate locally. HMRC APIs will return explicit validation errors if mandatory fields are incorrect. Maintain a mapping of HMRC error codes (e.g., `AGENT_NOT_SUBSCRIBED`, `INVALID_REQUEST`).

## 4. Authentication (OAuth 2.0) Guidelines
HMRC uses OAuth 2.0 Authorization Code Flow to secure APIs.

**Implementation Steps:**
1. **Authorize:** Redirect the user to HMRC's Government Gateway with your `client_id`, requested `scopes`, and `redirect_uri` (which must match the one registered in the Developer Hub).
2. **Grant Access:** The user logs in and grants permission.
3. **Exchange Code:** HMRC redirects back to your site with an authorization code. Exchange this code for an `access_token` and `refresh_token` via a server-to-server POST.
4. **Token Renewal:** Use the `refresh_token` to maintain access when the time-limited `access_token` expires.

**Key Gotchas:**
- **Scopes:** Request exact scopes (e.g., `write:self-assessment`). You will only get access to scopes your application is subscribed to in the Developer Hub.
- **Subscriptions:** Even with a valid token, you will receive `403 Forbidden` if your app is not explicitly subscribed to the target API in the Developer Hub.
- **Secret Management:** Use environment variables for the `client_secret`. Never hardcode it.
- **State Tokens:** Use a single-use state token during OAuth to prevent CSRF attacks.
