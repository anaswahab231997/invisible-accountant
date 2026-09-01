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

# Development practices

  * Why you only need 1 HMRC Developer Hub application in-page link
  * How to avoid your application failing without warning in-page link
  * HMRC changes that will affect your application in-page link
  * [AI guidelines for developers](https://www.gov.uk/guidance/guidelines-for-using-generative-artificial-intelligence-if-youre-a-software-developer)

  

The HMRC API Platform uses DevOps practices, iterative development, continuous
integration, continuous testing and continuous delivery to make hundreds of
small changes to the production environment each year.

Follow the development practices to make sure your application is not affected
by the changes we make.

* * *

## Why you only need 1 HMRC Developer Hub application

HMRC Developer Hub is for software developers who write software that
integrates with HMRC APIs.

If you are developing software that uses HMRC APIs, you only need 1 Developer
Hub production application.

[The name of your production application should be the same as your
organisation](/api-documentation/docs/name-guidelines).

You don’t need to create applications for each of your customers.

Your customers’ traffic is isolated through OAuth tokens and does not need
isolating through multiple application registrations.

Back to top in-page link

* * *

## How to avoid your application failing without warning

You should avoid unintentionally tightly coupling your application to HMRC.

Tight coupling means a set of systems are dependent on one another. Making a
change in a tightly coupled setup requires changes to both systems.

Loose coupling reduces dependencies and ensures non-breaking changes have no
impact on your application.

### HTTPS certificates can change

The HMRC API Platform’s HTTPS certificates can change. This includes the leaf
certificate, intermediary certificates and the root certificate.

! ** Warning If you import any HMRC specific certificates into your keystore
or load balancer, then your application may fail to connect when certificate
changes occur. **

Use a global root CA keystore and do not pin HMRC specific certificates

### IP addresses can change

You might need to configure your network so your software can access our API
Platform and token generation. If your software is installed on end user
devices, they might also need to configure their own network.

We have fixed domain names, but cannot provide static IP addresses, so you
need to configure your network access in your proxy, not your firewall.

Configure your proxy to allow full access to the following domains, including
HTTP `GET`, `POST`, `PUT` and `DELETE`.

For testing in sandbox:

  * `test-api.service.hmrc.gov.uk`
  * `test-www.tax.service.gov.uk`

For production use:

  * `api.service.hmrc.gov.uk`
  * `www.tax.service.gov.uk`

### OAuth flow can change

We do not support software that automatically drives the web interfaces of the
OAuth grant flow.

We regularly make changes to the OAuth grant flow and any changes could break
automated logins. We will not advise you of any OAuth changes in advance.

### Cross-origin resource sharing (CORS)

The HMRC API Platform does not support [cross-origin resource sharing
(CORS).](https://fetch.spec.whatwg.org/#http-cors-protocol) It is not possible
to call our APIs from client-side code within a web browser, for example using
Ajax.

Back to top in-page link

* * *

## HMRC changes that will affect your application

A breaking change is a change to the HMRC API platform that requires you to
make changes to your software, so it continues to work.

We try to avoid breaking changes, but sometimes they need to be made.

Breaking changes can be:

  * API specific (for example retiring a stable version of an API)
  * platform wide (for example retiring support for insecure TLS versions and cipher suites)

You will receive 6 months notice before breaking changes are made in
production.

Where possible breaking changes will be published to the sandbox environment
first before production.

You will have time to test any changes in the sandbox environment before
changes are made in production.

If you have an automated test pack, we recommend you run your tests weekly
against sandbox.

See the [reference guide](/api-documentation/docs/reference-guide) for actions
you need to take to make sure your application integrates with HMRC.

Back to top in-page link

[ Is this page not working properly? ](/devhub-support/report-technical-
problem?service=api-documentation-frontend?referrerUrl=%2Fapi-
documentation%2Fdocs%2Fdevelopment-practices)

## Support links

  * [ Cookies ](https://www.tax.service.gov.uk/api-documentation/docs/help/cookies)
  * [ Accessibility statement ](https://www.tax.service.gov.uk/accessibility-statement/hmrc-developer-hub?referrerUrl=%2Fapi-documentation%2Fdocs%2Fdevelopment-practices)
  * [ Privacy Policy ](https://www.tax.service.gov.uk/api-documentation/docs/help/privacy)
  * [ Terms and conditions ](https://www.tax.service.gov.uk/api-documentation/docs/help/terms-and-conditions)
  * [ Help using GOV.UK ](https://www.gov.uk/help)

All content is available under the [Open Government Licence
v3.0](https://www.nationalarchives.gov.uk/doc/open-government-
licence/version/3/), except where otherwise stated

[ © Crown copyright ](https://www.nationalarchives.gov.uk/information-
management/re-using-public-sector-information/uk-government-licensing-
framework/crown-copyright/)

