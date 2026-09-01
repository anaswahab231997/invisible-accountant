Skip to main content

[ GOV.UK HMRC Developer Hub  ](https://developer.service.hmrc.gov.uk/api-
documentation)

Menu

  * [Send fraud prevention data](/guides/fraud-prevention)
  * [Documentation](/api-documentation/docs/using-the-hub)
  * [Applications](/developer/applications)
  * [Support](/developer/support)

Table of contents

  * [Send fraud prevention data](/guides/fraud-prevention/)
    * [Why you must send data](/guides/fraud-prevention/#why-you-must-send-data)
  * [What you need to send](/guides/fraud-prevention/connection-method/)
  * [Use the Test API](/guides/fraud-prevention/test-api/)
  * [Getting it right](/guides/fraud-prevention/getting-it-right/)
    * [How we check data](/guides/fraud-prevention/getting-it-right/#how-we-check-data)
    * [Check your application](/guides/fraud-prevention/getting-it-right/#check-your-application)
    * [Send data in the correct format](/guides/fraud-prevention/getting-it-right/#send-data-in-the-correct-format)
    * [Missing header data](/guides/fraud-prevention/getting-it-right/#missing-header-data)
    * [Contact us](/guides/fraud-prevention/getting-it-right/#contact-us)
  * [Change log](/guides/fraud-prevention/change-log/)
    * 

# Send fraud prevention data

Version 3.3 issued 27 January 2025  
[Check what has changed](change-log/)

## Why you must send data

We monitor transactions to help protect your customers’ confidential data from
criminals and fraudsters. To make this possible, you must send us specific
types of user audit data.

When you use some of our APIs, you have to submit HTTP fraud prevention
headers. We use the data to support prosecutions for tax and duty fraud.

! ** Warning You are required by law to submit header data for the [VAT
(MTD)](/api-documentation/docs/api/service/vat-api/1.0) and [Income Tax Self
Assessment (MTD)](/guides/income-tax-mtd-end-to-end-service-guide/) APIs. This
includes all associated APIs and endpoints. **

We work with you to help meet this specification. If after discussions with
HMRC an application continues to submit incorrect or missing data, software
providers may be fined and blocked from using HMRC APIs. Check the [Compliance
and Sanctions Guidelines
(PDF)](Fraud%20Prevention%20Header%20Data%20Compliance%20and%20Sanctions%20Guidelines.pdf).

### Privacy and security

HMRC has the right to collect audit data. We follow best practices set out by
the Information Commissioner’s Office.

Transaction monitoring is a key security approach used in the UK and globally.
Our approach follows the [National Cyber Security Centre (NCSC) and the
Cabinet Office’s recommended guidance
(PDF)](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/271268/GPG_53_Transaction_Monitoring_issue_1-1_April_2013.pdf).

For more information or to review your privacy notices, [check the data
protection impact assessment (PDF)](/api-
documentation/assets/content/documentation/3f4c263faa8231bea05c1826b7f6b81c-TxM%20DPIA%20v3%201%20Public.pdf).
You can also [check the
regulations](http://www.legislation.gov.uk/uksi/2019/360/made).

All content is available under the [Open Government Licence
v3.0](https://www.nationalarchives.gov.uk/doc/open-government-
licence/version/3/), except where otherwise stated

[© Crown copyright](https://www.nationalarchives.gov.uk/information-
management/re-using-public-sector-information/uk-government-licensing-
framework/crown-copyright/)

