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

# Tutorials

## on this page

  * Before you start in-page link
  * Accessing an open endpoint in-page link

  * Accessing an application-restricted endpoint in-page link
  * Accessing a user-restricted endpoint in-page link

* * *

## Before you start

These tutorials use the sandbox environment for all base URLs.

All code examples are written in Java and use:

  * the [Apache HttpClient (opens in a new tab)](http://hc.apache.org/) library for accessing HTTP resources 
  * the [Apache Oltu (opens in a new tab)](http://oltu.apache.org/) library for our [OAuth 2.0](/api-documentation/docs/authorisation/user-restricted-endpoints#user-restricted) client 

You can find more code samples in our public GitHub repositories. We provide
examples in:

  * [C# (opens in a new tab)](https://github.com/hmrc/api-example-dotnet-client)
  * [Java (opens in a new tab)](https://github.com/hmrc/api-example-java-client)
  * [Node.js (opens in a new tab)](https://github.com/hmrc/api-example-nodejs-client)

Most of our APIs follow standard HTTP verbs and use a RESTful interface. You
can read more about these online.

These tutorials use a simple Hello World API that exposes 3 endpoints:

Endpoints exposed by Hello World API Method | Path | Authorisation | Message  
---|---|---|---  
`GET` | `/hello/world` | None | `Hello World!`  
`GET` | `/hello/application` | Application (OAuth 2.0 `access_token`) | `Hello Application!`  
`GET` | `/hello/user` | User (OAuth 2.0 `access_token`) | `Hello User!`  
  
## Accessing an open endpoint

In this example, you'll access the Hello World API ‘Hello World’ endpoint.

This endpoint is unrestricted, so you can access it without an
[OAuth2.0](/api-documentation/docs/authorisation/user-restricted-endpoints)
`access_token`.

### Issue a GET request

Send a GET request to:  
https://test-api.service.hmrc.gov.uk/hello/world.

    
    
    // construct the GET request for our Hello World endpoint
    HttpClient client = HttpClientBuilder.create().build();
    HttpGet request = new HttpGet("https://test-api.service.hmrc.gov.uk/hello/world");
    request.addHeader("Accept", "application/vnd.hmrc.1.0+json");
    
    // execute the request
    HttpResponse response = client.execute(request);
    
    // extract the HTTP status code and response body
    int statusCode = response.getStatusLine().getStatusCode();
    String responseBody = EntityUtils.toString(response.getEntity());
    

## Accessing an application-restricted endpoint

In this example, you will request an OAuth 2.0 `access_token` and use it to
call the Hello Application endpoint of the Hello World API.

[Register with the Developer Hub](/developer/registration) and create a
sandbox application. You will need your application's `client_id` and
`client_secret`.

You must test your application in the sandbox environment before requesting
production credentials.

For details on how to request an OAuth 2.0 `access_token`, see the [
authorisation section](/api-documentation/docs/authorisation/application-
restricted-endpoints).

### 1\. Request an OAuth 2.0 access token with the required scope

    
    
    // extract the authorization code from the request querystring
    OAuthAuthzResponse response =
    OAuthAuthzResponse.oauthCodeAuthzResponse(httpServletRequest);
    String authorizationCode = response.getCode();
    
    // create OAuth 2.0 Client using Apache HTTP Client
    OAuthClient oAuthClient = new OAuthClient(new URLConnectionClient());
    
    // construct OAuth 2.0 Token request for the authorization code
    OAuthClientRequest request = OAuthClientRequest
    .tokenLocation("https://test-api.service.hmrc.gov.uk/oauth/token")
    .setGrantType(GrantType.CLIENT_CREDENTIALS)
    .setClientId(clientId)
    .setClientSecret(clientSecret)
    .buildBodyMessage();
    
    // request the token via the OAuth 2.0 client
    OAuthJSONAccessTokenResponse response = oAuthClient.accessToken(request);
    
    // extract the data from the response
    String accessToken = response.getAccessToken();
    String grantedScope = response.getScope();
    Long expiresIn = response.getExpiresIn();
    

  

### 2\. Issue a GET request

Send a GET request to:  
https://test-api.service.hmrc.gov.uk/hello/application.  
Include your newly issued `access_token` in the `Authorization` header with
the type `Bearer`.

    
    
    // construct the GET request for our Hello User endpoint
    HttpClient client = HttpClientBuilder.create().build();
    HttpGet request = new HttpGet("https://test-api.service.hmrc.gov.uk/hello/application");
    request.addHeader("Accept", "application/vnd.hmrc.1.0+json");
    request.addHeader("Authorization", "Bearer "+accessToken);
    
    // execute the request
    HttpResponse response = client.execute(request);
    
    // extract the HTTP status code and response body
    int statusCode = response.getStatusLine().getStatusCode();
    String responseBody = EntityUtils.toString(response.getEntity());
    

  

This should give you a "Hello Application" response.

## Accessing a user-restricted endpoint

Before you begin, you must [ register as a developer with
HMRC](/developer/registration) and create an application. You will need your
application’s `client_id` and `client_secret` for either the production or
testing environment.

In this example, you will request an OAuth 2.0 `access_token` and use it to
call the Hello World API’s Hello User endpoint.

For more information about requesting, refreshing or revoking an OAuth 2.0
`access_token`, see the [authorisation](/api-
documentation/docs/authorisation/user-restricted-endpoints) section.

### 1\. Request an OAuth 2.0 authorisation code with the required scope

    
    
    // replace with your application's client_id and client_secret
    String clientId = "YOUR-CLIENT-ID";
    String clientSecret = "YOUR-CLIENT-SECRET";
    String scope = "hello";
    String redirectUri = "https://www.example.com/redirect";
    
    // construct the OAuth 2.0 Authorize request
    OAuthClientRequest request = OAuthClientRequest
    .authorizationLocation("https://test-api.service.hmrc.gov.uk/oauth/authorize")
    .setResponseType("code")
    .setClientId(clientId)
    .setScope(scope)
    .setRedirectURI(redirectUri)
    .buildQueryMessage();
    
    // redirect to the given location
    httpServletResponse.sendRedirect(request.getLocationUri());
    

  

You are redirected to the HMRC login screen. After you enter your credentials,
you will be asked to allow your application to access the requested scope.

Once you grant the requested authority, we redirect you back to your
application through the redirect URI. The redirect includes an authorisation
code as a querystring parameter.

You can then exchange this authorisation code for an [OAuth 2.0](/api-
documentation/docs/authorisation/user-restricted-endpoints) `access_token` and
a `refresh_token`.

### 2\. Exchange the OAuth 2.0 authorisation code for an access token

    
    
    // extract the authorization code from the request querystring
    OAuthAuthzResponse response =
    OAuthAuthzResponse.oauthCodeAuthzResponse(httpServletRequest);
    String authorizationCode = response.getCode();
    
    // create OAuth 2.0 Client using Apache HTTP Client
    OAuthClient oAuthClient = new OAuthClient(new URLConnectionClient());
    
    // construct OAuth 2.0 Token request for the authorization code
    OAuthClientRequest request = OAuthClientRequest
    .tokenLocation("https://test-api.service.hmrc.gov.uk/oauth/token")
    .setGrantType(GrantType.AUTHORIZATION_CODE)
    .setClientId(clientId)
    .setClientSecret(clientSecret)
    .setRedirectURI(redirectUri)
    .setCode(authorizationCode)
    .buildBodyMessage();
    
    // request the token via the OAuth 2.0 client
    OAuthJSONAccessTokenResponse response = oAuthClient.accessToken(request);
    
    // extract the data from the response
    String accessToken = response.getAccessToken();
    String refreshToken = response.getRefreshToken();
    String grantedScope = response.getScope();
    Long expiresIn = response.getExpiresIn();
    

  

### 3\. Issue a GET request

Send a GET request to:  
https://test-api.service.hmrc.gov.uk/hello/user.  
Include your new `access_token` in the `Authorization` header with the type
`Bearer`.

    
    
    // construct the GET request for our Hello User endpoint
    HttpClient client = HttpClientBuilder.create().build();
    HttpGet request = new HttpGet("https://test-api.service.hmrc.gov.uk/hello/user");
    request.addHeader("Accept", "application/vnd.hmrc.1.0+json");
    request.addHeader("Authorization", "Bearer "+accessToken);
    
    // execute the request
    HttpResponse response = client.execute(request);
    
    // extract the HTTP status code and response body
    int statusCode = response.getStatusLine().getStatusCode();
    String responseBody = EntityUtils.toString(response.getEntity());
    

  

This will return a “Hello User!” response. The exact message may differ
depending on whether you used your testing or production `client_id` and
`client_secret` when you began the [OAuth 2.0](/api-
documentation/docs/authorisation/user-restricted-endpoints) flow.

### 4\. Refresh an expired OAuth 2.0 `access_token`

This exchanges a `refresh_token` for a new `access_token` (and a new
`refresh_token`).

    
    
    // replace with your application's client_id and client_secret
    String clientId = "YOUR-CLIENT-ID";
    String clientSecret = "YOUR-CLIENT-SECRET";
    
    // create OAuth 2.0 Client using Apache HTTP Client
    OAuthClient oAuthClient = new OAuthClient(new URLConnectionClient());
    
    // construct OAuth 2.0 Token request for the authorization code
    OAuthClientRequest request = OAuthClientRequest
    .tokenLocation("https://test-api.service.hmrc.gov.uk/oauth/token")
    .setGrantType(GrantType.REFRESH_TOKEN)
    .setClientId(clientId)
    .setClientSecret(clientSecret)
    .setRefreshToken(refreshToken)
    .buildBodyMessage();
    
    // request the token via the OAuth 2.0 client
    OAuthJSONAccessTokenResponse response = oAuthClient.accessToken(request);
    
    // extract the data from the response
    String accessToken = response.getAccessToken();
    String refreshToken = response.getRefreshToken();
    Long expiresIn = response.getExpiresIn();
    

  

You should now be ready to start integrating with [our APIs](/api-
documentation/docs/api).

[ Is this page not working properly? ](/devhub-support/report-technical-
problem?service=api-documentation-frontend?referrerUrl=%2Fapi-
documentation%2Fdocs%2Ftutorials)

## Support links

  * [ Cookies ](https://www.tax.service.gov.uk/api-documentation/docs/help/cookies)
  * [ Accessibility statement ](https://www.tax.service.gov.uk/accessibility-statement/hmrc-developer-hub?referrerUrl=%2Fapi-documentation%2Fdocs%2Ftutorials)
  * [ Privacy Policy ](https://www.tax.service.gov.uk/api-documentation/docs/help/privacy)
  * [ Terms and conditions ](https://www.tax.service.gov.uk/api-documentation/docs/help/terms-and-conditions)
  * [ Help using GOV.UK ](https://www.gov.uk/help)

All content is available under the [Open Government Licence
v3.0](https://www.nationalarchives.gov.uk/doc/open-government-
licence/version/3/), except where otherwise stated

[ © Crown copyright ](https://www.nationalarchives.gov.uk/information-
management/re-using-public-sector-information/uk-government-licensing-
framework/crown-copyright/)

