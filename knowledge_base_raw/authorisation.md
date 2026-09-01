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

# Authorisation

## On this page

  * Introduction
  * [Credentials](/api-documentation/docs/authorisation/credentials)
  * [Open access endpoints](/api-documentation/docs/authorisation/open-access-endpoints)
  * [Application-restricted endpoints](/api-documentation/docs/authorisation/application-restricted-endpoints)
  * [User-restricted endpoints](/api-documentation/docs/authorisation/user-restricted-endpoints)
  * [2-step verification](/api-documentation/docs/authorisation/two-step-verification)

* * *

## Introduction

Our APIs use three types of endpoints. Each type has its own access level,
authorisation token and authorisation process. The type you use depends on the
data the endpoint provides.

## Endpoint types and tokens

Use the table to identify the correct token for each endpoint access type.

Endpoint types and their required tokens Endpoint access level | Required authorisation token  
---|---  
[Open access](/api-documentation/docs/authorisation/open-access-endpoints) | No token  
[Application-restricted](/api-documentation/docs/authorisation/application-restricted-endpoints) |  OAuth 2.0 `access_token`  
Generated using [OAuth 2.0 Client Credentials
Grant](https://oauth.net/2/grant-types/client-credentials/)  
  
Using `server_token` is now deprecated.  
[User-restricted](/api-documentation/docs/authorisation/user-restricted-endpoints) |  OAuth 2.0 `access_token`  
Generated using [OAuth 2.0 Authorization Code
Grant](https://oauth.net/2/grant-types/authorization-code/)  
  
  * [ Next : Credentials ](/api-documentation/docs/authorisation/credentials "Navigate to next part")

[ Is this page not working properly? ](/devhub-support/report-technical-
problem?service=api-documentation-frontend?referrerUrl=%2Fapi-
documentation%2Fdocs%2Fauthorisation)

## Support links

  * [ Cookies ](https://www.tax.service.gov.uk/api-documentation/docs/help/cookies)
  * [ Accessibility statement ](https://www.tax.service.gov.uk/accessibility-statement/hmrc-developer-hub?referrerUrl=%2Fapi-documentation%2Fdocs%2Fauthorisation)
  * [ Privacy Policy ](https://www.tax.service.gov.uk/api-documentation/docs/help/privacy)
  * [ Terms and conditions ](https://www.tax.service.gov.uk/api-documentation/docs/help/terms-and-conditions)
  * [ Help using GOV.UK ](https://www.gov.uk/help)

All content is available under the [Open Government Licence
v3.0](https://www.nationalarchives.gov.uk/doc/open-government-
licence/version/3/), except where otherwise stated

[ © Crown copyright ](https://www.nationalarchives.gov.uk/information-
management/re-using-public-sector-information/uk-government-licensing-
framework/crown-copyright/)

