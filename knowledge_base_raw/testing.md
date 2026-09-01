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

# Testing in the sandbox

## On this page

  * Getting started
  * [Test users, test data and stateful behaviour](/api-documentation/docs/testing/test-users-test-data-stateful-behaviour)

* * *

## Getting started

Use our sandbox environment to test your application against our RESTful APIs
before going live. This environment does not support our XML APIs which must
be tested as explained in the [Basic guide for software
developers](https://www.gov.uk/government/publications/basic-guide-for-
software-developers).

### 1\. Add an application

[Add a sandbox
application](https://developer.service.hmrc.gov.uk/developer/applications/add/sandbox)
to use for testing.

Sandbox applications follow a defined lifecycle to ensure only active
applications are retained. You will receive an email before your application
is deleted.

  * Sandbox applications are automatically deleted if they do not make an API call within 30 days of creation.
  * Applications that have previously made API calls but then remain inactive for 6 months will also be deleted.

### 2\. Subscribe to APIs

You must subscribe to APIs before your application can access them. Subscribe
on the manage API subscriptions page.

### 3\. Get sandbox credentials

Get these from the manage credentials page. They are only valid for the
sandbox environment.

### 4\. Configure your application for sandbox

Configure your application to make authorisation and API calls to sandbox
endpoints using your sandbox credentials and the base URL `https://test-
api.service.hmrc.gov.uk`.

### 5\. Create test users and other test data

To test [user-restricted endpoints](/api-
documentation/docs/authorisation/user-restricted-endpoints), you need to
create [test users and potentially other test data](/api-
documentation/docs/testing/test-users-test-data-stateful-behaviour).

### 6\. Test the authorisation process

If you’re testing [user-restricted endpoints](/api-
documentation/docs/authorisation/user-restricted-endpoints), trigger the
authorisation process from your application:

  * Sign in with the credentials for the test user you created. Note that sandbox doesn’t include 2-step verification or identity checks.
  * Complete the journey by granting authority to your application.
  * We will return control back to your application, which should then obtain an OAuth token for use in subsequent API calls.

Remember to test failure cases by selecting “Do not grant authority” after
signing in.

### 7\. Test API calls

Use your application to make calls to our sandbox APIs.

Remember to test the error scenarios mentioned in the API documentation.

  * [ Next : Test users, test data and stateful behaviour ](/api-documentation/docs/testing/test-users-test-data-stateful-behaviour "Navigate to next part")

[ Is this page not working properly? ](/devhub-support/report-technical-
problem?service=api-documentation-frontend?referrerUrl=%2Fapi-
documentation%2Fdocs%2Ftesting)

## Support links

  * [ Cookies ](https://www.tax.service.gov.uk/api-documentation/docs/help/cookies)
  * [ Accessibility statement ](https://www.tax.service.gov.uk/accessibility-statement/hmrc-developer-hub?referrerUrl=%2Fapi-documentation%2Fdocs%2Ftesting)
  * [ Privacy Policy ](https://www.tax.service.gov.uk/api-documentation/docs/help/privacy)
  * [ Terms and conditions ](https://www.tax.service.gov.uk/api-documentation/docs/help/terms-and-conditions)
  * [ Help using GOV.UK ](https://www.gov.uk/help)

All content is available under the [Open Government Licence
v3.0](https://www.nationalarchives.gov.uk/doc/open-government-
licence/version/3/), except where otherwise stated

[ © Crown copyright ](https://www.nationalarchives.gov.uk/information-
management/re-using-public-sector-information/uk-government-licensing-
framework/crown-copyright/)

