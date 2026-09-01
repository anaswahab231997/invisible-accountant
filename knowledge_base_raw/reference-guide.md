Skip to main content

[ GOV.UK ](https://www.gov.uk)

[ HMRC Developer Hub ](/api-documentation) Menu

  * [ Getting started ](/api-documentation/docs/using-the-hub)
  * [ **API documentation** ](/api-documentation/docs/api)
  * [ Applications ](/developer/applications)
  * [ Support ](/devhub-support)
  * [ Service availability ](https://api-platform-status.production.tax.service.gov.uk/)

Your [feedback (opens in new
tab)](https://zwgy80l7.optimalworkshop.com/questions/26g46322) will help us to
improve this service.

  1. [Home](/api-documentation)
  2. [Documentation](/api-documentation/docs/using-the-hub)

  * [ Register ](/developer/registration)
  * [ Sign in ](/developer/login)

  * [Getting started](/api-documentation/docs/using-the-hub)
  * [Application naming guidelines](/api-documentation/docs/name-guidelines)
  * [API statuses](/api-documentation/docs/api-statuses)
  * [Reference guide](/api-documentation/docs/reference-guide)
  * [Development practices](/api-documentation/docs/development-practices)
  * [Send fraud prevention data](/guides/fraud-prevention)
  * [Authorisation](/api-documentation/docs/authorisation)
  * [Tutorials](/api-documentation/docs/tutorials)
  * [Testing in the sandbox](/api-documentation/docs/testing)
  * [Terms of use](/api-documentation/docs/terms-of-use)

# Reference guide

## on this page

  * API access in-page link
  * Browser support for OAuth 2.0 in-page link
  * Coding in the open in-page link
  * Common data types in-page link
  * Cross-origin resource sharing (CORS) in-page link
  * Errors in-page link
  * HTTP redirection in-page link

  * IP allow list in-page link
  * Rate limiting in-page link
  * Redirect URIs in-page link
  * Scopes in-page link
  * Send fraud prevention data in-page link
  * TLS standards in-page link
  * Versioning in-page link

  

Read the reference guide for actions you need to take to make sure your
application integrates with HMRC.

See the [development practices](/api-documentation/docs/development-practices)
for how to avoid your application failing without warning when HMRC make
changes.

* * *

## API access

The base URL for sandbox APIs is:

    
    
    https://test-api.service.hmrc.gov.uk

  

The base URL for production APIs is:

    
    
    https://api.service.hmrc.gov.uk

## Browser support for OAuth 2.0

The OAuth 2.0 [authorisation](/api-documentation/docs/authorisation/user-
restricted-endpoints) journey is designed to work with most modern browsers as
per the list specified on [ Designing for different browsers and
devices](https://www.gov.uk/service-manual/technology/designing-for-different-
browsers-and-devices#browsers-to-test-in), including mobile devices and
tablets.

If you are using the Microsoft Web Browser Control embedded browser for the
authorisation journey, be aware that by default this will operate in IE7
compatibility mode which we do not formally support. For details of one way to
handle this, see [ Controlling WebBrowser Control Compatibility (opens in a
new tab) ](https://blogs.msdn.microsoft.com/patricka/2015/01/12/controlling-
webbrowser-control-compatibility/).

## Coding in the open

The HMRC Developer Hub, the underlying API Platform and some of the APIs are
coded in the open, as per the [ GOV.UK Digital Service Standard (opens in a
new tab)](https://www.gov.uk/service-manual/service-standard/make-all-new-
source-code-open).

The source code is available at [ https://github.com/hmrc (opens in a new
tab)](https://github.com/hmrc). For more details, please [contact
us](/developer/support).

## Common data types

Our APIs use consistent formats for common data types. We use ISO standards
including:

  * [ISO 8601 (opens in a new tab)](http://www.iso.org/iso/iso8601)
  * [ISO 4217 (opens in a new tab)](http://www.iso.org/iso/home/standards/currency_codes.htm)

Some examples of common data types include:

Examples of common data types Type | Example | Description  
---|---|---  
`date` | `2015-09-08` | Dates will be represented in the format YYYY-MM-DD.  
`timestamp` | `2015-09-08T01:55:28+00:00` | Timestamps will be represented in the format YYYY-MM-DDThh:mm:ss±hh:mm.  
`money` | `123.45` | Unless expressly documented, money will be represented with two decimal places and GBP currency.  
`NINO` | `QQ123456A` | A National Insurance number is made up of 2 letters, 6 numbers and a letter (A, B, C, or D).  
  
## Cross-origin resource sharing (CORS)

The API Platform does not support [cross-origin resource sharing (CORS) (opens
in a new tab)](https://fetch.spec.whatwg.org/#http-cors-protocol). It is
therefore not possible to call our APIs from client-side code within a web
browser, for example using Ajax.

## Errors

Errors during the [authorisation process](/api-
documentation/docs/authorisation/user-restricted-endpoints) use the format
specified in the OAuth 2.0 RFC.

Errors from APIs have a 4xx or 5xx HTTP status code and a consistently formed
JSON or XML body, including:

Name | Type | Description  
---|---|---  
`code` | `string` | A machine-readable error code. This is unique for each error scenario.  
`message` | `string` | A human-readable explanation for the error.  
  
There might be other error-specific information (such as a list of fields that
are in error). For example:

    
    
    {
      "code" : "ACCOUNT_SUSPENDEDSA-100201",
      "message" : "Account is temporarily suspended",
      "reactivationTimestamp" : 1431448640718
    }
    

  

Multiple errors can also be returned in a single field called errors. For
example:

    
    
    {
      "code": "BAD_REQUEST",
      "message": "Bad request",
      "errors": [
        {
          "code": "MISSING_FIELD",
          "message": "This field is required",
          "path": "/firstName"
        },
        {
          "code": "INVALID_DATE",
          "message": "Date is invalid",
          "path": "/dateOfBirth"
        }
      ]
    }
    

  

Here is an example error response in XML format

    
    
    <error>
      <code>ACCOUNT_SUSPENDEDSA-100201</code>
      <message>Account is temporarily suspended</message>
      <reactivationTimestamp>1431448640718</reactivationTimestamp>
    </error>
    

  

These error responses are common across all APIs:

### 401 (Unauthorized)

Scenario | Code  
---|---  
No OAuth token supplied for user-restricted or application-restricted endpoint | `MISSING_CREDENTIALS`  
Invalid OAuth token supplied for user-restricted or application-restricted endpoint (including expired token) | `INVALID_CREDENTIALS`  
Other issue with authentication of the supplied OAuth token | `UNAUTHORIZED`  
User-restricted API is being accessed with a server token | `INCORRECT_ACCESS_TOKEN_TYPE`  
  
### 403 (Forbidden)

Scenario | Code  
---|---  
Request done with HTTP | `HTTPS_REQUIRED`  
The OAuth token's application is not subscribed to the API | `RESOURCE_FORBIDDEN`  
The scope of the OAuth token is not sufficient to access the API | `INVALID_SCOPE`  
Supplied OAuth token not authorised to access data for given tax identifier(s) | `FORBIDDEN`  
  
### 404 (Not Found)

Scenario | Code  
---|---  
No endpoint could be found in the API for the request path | `MATCHING_RESOURCE_NOT_FOUND`  
  
### 405 (Method Not Allowed)

Scenario | Code  
---|---  
Request method is not GET, PUT, POST, PATCH, DELETE or OPTIONS | `METHOD_NOT_ALLOWED`  
  
### 406 (Not Acceptable)

Scenario | Code  
---|---  
Missing or invalid Accept header | `ACCEPT_HEADER_INVALID`  
  
### 429 (Too Many Requests)

Scenario | Code  
---|---  
The application has reached its maximum rate limit in-page link | `MESSAGE_THROTTLED_OUT`  
  
### 500 (Internal Server Error)

Scenario | Code  
---|---  
Internal server error | `INTERNAL_SERVER_ERROR`  
  
### 501 (Not Implemented)

Scenario | Code  
---|---  
API not implemented/deployed | `NOT_IMPLEMENTED`  
  
### 503 (Service Unavailable)

Scenario | Code  
---|---  
Service unavailable | `SERVER_ERROR`  
Scheduled maintenance | `SCHEDULED_MAINTENANCE`  
  
### 504 (Gateway Timeout)

Scenario | Code  
---|---  
Request timed out | `GATEWAY_TIMEOUT`  
  
## Send fraud prevention data

You must help us protect our users’ confidential data by sending us particular
types of user audit data which we will record. Check [what you need to
send](/guides/fraud-prevention).

It is mandatory to provide header data for the [VAT (MTD) API](/api-
documentation/docs/api/service/vat-api/1.0).

Soon, you'll need to send user audit data in fraud prevention headers for all
of our APIs. We recommend designing this into your applications now.

## HTTP redirection

Our API Platform uses HTTP redirection if endpoints move permanently or
temporarily.

Redirection responses have a **Location** header with the endpoint's new URI.

## IP allow list

The IP allow list is a security feature that lets you control which IP
addresses are allowed to make API requests to HMRC.

The IP allow list is optional and is only suitable if you have a static set of
IP addresses where your software is hosted.

If you have dynamic IP addresses, consider switching to static IP addresses to
use the IP allow list.

The IP allow list limits access to HMRC services to approved IP addresses
associated with your application.

### Allowed IP addresses

We allow IP address ranges represented in CIDR notation, made up of an IP
address and a netmask:

`<IP Address>/<netmask>`

Which looks like:

`1.1.1.1/24`

The netmask identifies how large the network is:

  * 1.1.1.1/32 allows access from only one IP address, for example 1.1.1.1
  * 1.1.1.1/24 allows access from 254 IP addresses, for example 1.1.1.1 to 1.1.1.254

Use /32 if you are unsure about CIDR notation but know the individual IP
addresses your traffic comes from.

The largest netmask we allow is /24.

### Adding IP addresses to the allow list

You will need a sandbox or production application to use the IP allow list.

When you set up a sandbox or production application, decide which IP addresses
are allowed to make API requests to HMRC and add to the IP allow list.

It is important that you check the IP addresses you want to use are correct
before making the IP allow list active.

While the allow list is active, only approved IP addresses associated with
your application can make API requests to HMRC.

## Rate limiting

We limit the number of requests each application can make. This protects our
service against excessive use and Denial-of-Service attacks, and also
encourages you to use our APIs efficiently.

We set limits based on anticipated loads and peaks. Our standard limit is 3
requests per second per application.

If you reach this limit you’ll get a response with an HTTP status of `429`
(Too Many Requests). If a 429 response is received we recommend that your code
should stop making additional API requests for a short period of time before
retrying.

Our rate limits are designed to encourage real-time interactions. As such we
advise software developers to avoid batching requests if they wish to avoid
being rate limited.

If you continually hit this rate limit, [contact us](/developer/support) to
discuss your application design and whether it’s appropriate to raise your
rate limit.

## Redirect URIs

We use redirect URIs to send the user back to your application after
successful (or unsuccessful) authorisation, prior to your application
accessing [user-restricted endpoints](/api-
documentation/docs/authorisation/user-restricted-endpoints).

You must specify one or more redirect URIs when you create your application,
and also specify one redirect URI when you send your user to our authorisation
endpoint.

To protect your application from phishing attacks, the redirect URI you use
for authorisation (in your call to `/oauth/authorize`) must match one of those
you specified when you created your application.

Also, you must use the same redirect URI when exchanging your authorisation
code for an access token (in your call to `/oauth/token`) that you used for
authorisation (in your call to `/oauth/authorize`).

You can specify a maximum of five redirect URIs.

### Examples

Examples of valid (and invalid) redirect URIs are:

Redirect Uris Redirect URI | Comments  
---|---  
`https://www.example.com/auth-redirect` | **Valid** \- when creating your application, you can use the full redirect URI or a partial URI, for example:   
  
`https://www.example.com/auth-redirect`  
  
`https://www.example.com`  
  
When calling our authorisation endpoint, your redirect URI must be percent-
encoded, for example:  
  
`https%3A%2F%2Fwww.example.com%2Fauth-redirect`  
`https://www.example.com:8080/auth-redirect` | **Valid** \- includes a port number  
`http://www.example.com:8080/auth-redirect` | **Invalid** \- uses HTTP, not HTTPS (HTTP is OK for installed applications - see example below)  
`/auth-redirect` | **Invalid** \- is a relative URI, not an absolute URI  
`https://203.0.113.11/auth-redirect` | **Invalid** \- uses an IP address, not a DNS name  
`https://www.example.com:8080/auth-redirect?some_parameter=some_value` | **Valid** \- includes a query component  
`https://www.example.com:8080/auth-redirect#some_fragment` | **Invalid** \- includes a fragment component  
`http://localhost:8080` | **Valid** \- as explained in [OAuth 2.0 for installed applications](/api-documentation/docs/authorisation/user-restricted-endpoints#installed-applications)  
`urn:ietf:wg:oauth:2.0:oob` | **Valid** \- as explained in [OAuth 2.0 for installed applications](/api-documentation/docs/authorisation/user-restricted-endpoints#installed-applications)  
`urn:ietf:wg:oauth:2.0:oob:auto` | **Valid** \- as explained in [OAuth 2.0 for installed applications](/api-documentation/docs/authorisation/user-restricted-endpoints#installed-applications)  
  
## Scopes

When your application needs to access API endpoints on behalf of a user, the
Developer Hub uses the [OAuth 2.0](/api-documentation/docs/authorisation/user-
restricted-endpoints#user-restricted) framework to grant and manage such an
authority.

This authority is granted in terms of OAuth 2.0 'scopes'. Each 'scope' relates
to one or more endpoints.

When your application requests an OAuth 2.0 `Bearer` token, it must specify
the scope(s) which the token should be granted for.

These are translated to human-readable descriptions that are shown to the user
before they grant authority. This makes sure the user understands and gives
access to your application.

The scope for each user-restricted endpoint is defined in the [API
documentation](/api-documentation/docs/api).

For details about OAuth 2.0 and scopes, see [authorisation](/api-
documentation/docs/authorisation/user-restricted-endpoints).

## TLS standards

HMRC APIs are only accessible over Transport Layer Security (TLS). For
example, URLs that begin with https://.

Applications must support TLS 1.2 or higher to avoid known weaknesses in
previous versions.

## Using the Accept header for versioning

You choose the version of the API you want to use by sending an `Accept`
header with a media type of:

    
    
    application/vnd.hmrc.[version]+[content-type]

  

For example:

    
    
    application/vnd.hmrc.1.0+json

  

#### How version changes affect your Accept header

  * We make backwards‑compatible changes within the same version, so you do not need to update your Accept header.
  * When we release a backwards‑incompatible change, we create a new version of the API. You must update your Accept header or the API will still remain on the same version.

Learn more about [API version statuses](/api-documentation/docs/api-statuses).

[ Is this page not working properly? ](/devhub-support/report-technical-
problem?service=api-documentation-frontend?referrerUrl=%2Fapi-
documentation%2Fdocs%2Freference-guide)

## Support links

  * [ Cookies ](https://www.tax.service.gov.uk/api-documentation/docs/help/cookies)
  * [ Accessibility statement ](https://www.tax.service.gov.uk/accessibility-statement/hmrc-developer-hub?referrerUrl=%2Fapi-documentation%2Fdocs%2Freference-guide)
  * [ Privacy Policy ](https://www.tax.service.gov.uk/api-documentation/docs/help/privacy)
  * [ Terms and conditions ](https://www.tax.service.gov.uk/api-documentation/docs/help/terms-and-conditions)
  * [ Help using GOV.UK ](https://www.gov.uk/help)

All content is available under the [Open Government Licence
v3.0](https://www.nationalarchives.gov.uk/doc/open-government-
licence/version/3/), except where otherwise stated

[ © Crown copyright ](https://www.nationalarchives.gov.uk/information-
management/re-using-public-sector-information/uk-government-licensing-
framework/crown-copyright/)

