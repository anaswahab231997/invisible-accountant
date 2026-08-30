import asyncio
import os
import json
from hmrc_api import HMRCClient, HMRCApiError, generate_whatsapp_fraud_headers

async def main():
    print('--- Starting HMRC API Connection Test ---')
    os.environ['HMRC_BASE_URL'] = 'https://test-api.service.hmrc.gov.uk'
    
    print('\n[1/2] Generating Compliant Fraud Prevention Headers...')
    headers = generate_whatsapp_fraud_headers(real_device_id='dummy-device-id-1234')
    print(f"Generated {len(headers)} strict headers.")
    print(f"Gov-Client-Connection-Method: {headers.get('Gov-Client-Connection-Method')}")
    print(f"Gov-Client-Device-ID: {headers.get('Gov-Client-Device-ID')}")
    
    print('\n[2/2] Pinging HMRC Sandbox API (Business Details endpoint)...')
    print('Note: Because we are not passing a real OAuth token, we expect HMRC to actively reject this with a 401 error.')
    
    client = HMRCClient(access_token='fake_test_token_for_validation', fraud_headers=headers)
    
    try:
        await client.get_business_details('AA123456A')
        print('Wait, this should have failed without a real token!')
    except HMRCApiError as e:
        print('\n--- SUCCESS: RECEIVED REAL HMRC RESPONSE ---')
        print(f'HTTP Status Code: {e.status_code}')
        print(f'HMRC JSON Payload: {json.dumps(e.payload, indent=2)}')

if __name__ == '__main__':
    asyncio.run(main())
