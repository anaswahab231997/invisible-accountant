import pytest
import respx
import httpx
from hmrc_api import HMRCClient, HMRCApiError
import os

pytestmark = pytest.mark.asyncio

@respx.mock
async def test_hmrc_successful_submission():
    client = HMRCClient(access_token="mock_token")
    
    # Mock the specific sandbox endpoint
    endpoint = "https://test-api.service.hmrc.gov.uk/income-tax/ni/AA123456A/self-employments/XAIS12345678901/periods"
    
    route = respx.post(endpoint).mock(return_value=httpx.Response(200, json={"message": "Success"}))
    
    response = await client.submit_periodic_update(
        nino="AA123456A",
        income_source_id="XAIS12345678901",
        amount=150.50,
        period_start="2023-04-06",
        period_end="2024-04-05"
    )
    
    assert response == {"message": "Success"}
    assert route.called
    
    # Verify strict HMRC headers
    request = route.calls.last.request
    assert request.headers["Accept"] == "application/vnd.hmrc.1.0+json"
    assert request.headers["Authorization"] == "Bearer mock_token"
    
    # Verify strict payload
    payload = request.content.decode()
    assert '"amount":150.5' in payload or '"amount": 150.5' in payload
    assert "2023-04-06" in payload

@respx.mock
async def test_hmrc_429_rate_limit_retry():
    client = HMRCClient(access_token="mock_token", max_retries=1)
    
    endpoint = "https://test-api.service.hmrc.gov.uk/income-tax/ni/AA123456A/self-employments/XAIS12345678901/periods"
    
    # First call returns 429, second returns 200
    route = respx.post(endpoint).mock(
        side_effect=[
            httpx.Response(429, json={"code": "MATCHING_RESOURCE_NOT_FOUND"}),
            httpx.Response(200, json={"message": "Success"})
        ]
    )
    
    response = await client.submit_periodic_update("AA123456A", "XAIS12345678901", 150.50, "2023-04-06", "2024-04-05")
    
    assert response == {"message": "Success"}
    assert route.call_count == 2  # Proves the retry logic worked

@respx.mock
async def test_hmrc_429_rate_limit_failure():
    client = HMRCClient(access_token="mock_token", max_retries=1)
    endpoint = "https://test-api.service.hmrc.gov.uk/income-tax/ni/AA123456A/self-employments/XAIS12345678901/periods"
    
    # Returns 429 twice (exceeding max_retries=1)
    route = respx.post(endpoint).mock(return_value=httpx.Response(429, json={"error": "Too Many"}))
    
    with pytest.raises(HMRCApiError) as exc:
        await client.submit_periodic_update("AA123456A", "XAIS12345678901", 150.50, "2023-04-06", "2024-04-05")
    
    assert exc.value.status_code == 429
    assert route.call_count == 2

async def test_hmrc_graceful_fallback():
    # When no token is provided, it simulates success without making network calls
    client = HMRCClient(access_token=None)
    response = await client.submit_periodic_update(
        nino="AA123456A",
        income_source_id="X1",
        amount=100.0,
        period_start="2023-04-06",
        period_end="2024-04-05"
    )
    assert response["simulated"] is True
