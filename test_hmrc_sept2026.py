import asyncio
import os
import unittest
from unittest.mock import patch, MagicMock
import httpx
from hmrc_api import HMRCClient, generate_whatsapp_fraud_headers, HMRCApiError

class TestHMRCSeptember2026Release(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_nino = "AA123456A"
        self.mock_income_source_id = "XAIS12345678901"
        self.mock_tax_year = "2026-27"
        self.fraud_headers = await generate_whatsapp_fraud_headers(real_device_id="test-device-123")

    async def test_fraud_prevention_headers_other_via_server(self):
        """Verify headers conform to HMRC OTHER_VIA_SERVER specification."""
        self.assertEqual(self.fraud_headers.get("Gov-Client-Connection-Method"), "OTHER_VIA_SERVER")
        self.assertEqual(self.fraud_headers.get("Gov-Vendor-Product-Name"), "InvisibleAccountant")
        self.assertIn("InvisibleAccountantClient=1.0.0", self.fraud_headers.get("Gov-Vendor-Version", ""))
        self.assertTrue(bool(self.fraud_headers.get("Gov-Vendor-Public-IP")))
        self.assertTrue(bool(self.fraud_headers.get("Gov-Client-Public-IP")))
        self.assertTrue(bool(self.fraud_headers.get("Gov-Client-Device-ID")))
        print("[PASS] HMRC Fraud Prevention Headers (OTHER_VIA_SERVER) validated.")

    async def test_get_itsa_penalties_simulation(self):
        """Verify get_itsa_penalties falls back gracefully to clean status in simulation mode."""
        client = HMRCClient(access_token=None, fraud_headers=self.fraud_headers)
        result = await client.get_itsa_penalties(self.mock_nino)

        self.assertTrue(result.get("simulated"))
        self.assertEqual(result.get("nino"), self.mock_nino)
        self.assertEqual(result.get("penaltyPointsTotal"), 0)
        self.assertEqual(result.get("financialPenaltiesTotal"), 0.0)
        self.assertFalse(result.get("dunningLock"))
        self.assertEqual(result.get("status"), "CLEAN")
        print("[PASS] Self Assessment Accounts v4 get_itsa_penalties simulation verified.")

    async def test_get_itsa_penalties_endpoint_routing(self):
        """Verify endpoint and request construction for live Self Assessment Accounts v4."""
        mock_response = {
            "penaltyPointsTotal": 0,
            "financialPenaltiesTotal": 0.00,
            "dunningLock": False,
            "penalties": []
        }

        with patch("httpx.AsyncClient.request") as mock_request:
            mock_resp_obj = MagicMock()
            mock_resp_obj.status_code = 200
            mock_resp_obj.json.return_value = mock_response
            mock_request.return_value = mock_resp_obj

            client = HMRCClient(access_token="valid_bearer_token", fraud_headers=self.fraud_headers)
            res = await client.get_itsa_penalties(self.mock_nino)

            self.assertEqual(res, mock_response)
            mock_request.assert_called_once()
            args, kwargs = mock_request.call_args
            self.assertEqual(args[0], "GET")
            self.assertIn(f"/individuals/business/accounts/penalties/{self.mock_nino}", args[1])
            self.assertIn("Authorization", kwargs["headers"])
            self.assertEqual(kwargs["headers"]["Authorization"], "Bearer valid_bearer_token")
            self.assertEqual(kwargs["headers"]["Gov-Client-Connection-Method"], "OTHER_VIA_SERVER")
            print("[PASS] Self Assessment Accounts v4 get_itsa_penalties routing and authorization verified.")

    async def test_submit_annual_adjustments_class4_ni(self):
        """Verify Self Employment v5 adjustments object supports adjustmentToProfitsForClass4."""
        adjustments_payload = {
            "includedNonTaxableProfits": 0.00,
            "basisAdjustment": 0.00,
            "overlapReliefUsed": 0.00,
            "accountingAdjustment": 0.00,
            "averagingAdjustment": 0.00,
            "outstandingBusinessIncome": 0.00,
            "balancingChargeOther": 0.00,
            "goodsAndServicesOwnUse": 0.00,
            "adjustmentToProfitsForClass4": 250.00  # New September 15, 2026 HMRC field
        }

        # 1. Simulation mode check
        client = HMRCClient(access_token=None, fraud_headers=self.fraud_headers)
        sim_res = await client.submit_annual_adjustments(
            self.mock_nino, self.mock_income_source_id, self.mock_tax_year, adjustments_payload
        )
        self.assertTrue(sim_res.get("simulated"))
        self.assertEqual(sim_res["adjustments"]["adjustmentToProfitsForClass4"], 250.00)

        # 2. Mocked live request check
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_resp_obj = MagicMock()
            mock_resp_obj.status_code = 200
            mock_resp_obj.json.return_value = {"status": "SUCCESS", "submissionId": "SUB-12345"}
            mock_request.return_value = mock_resp_obj

            live_client = HMRCClient(access_token="valid_bearer_token", fraud_headers=self.fraud_headers)
            live_res = await live_client.submit_annual_adjustments(
                self.mock_nino, self.mock_income_source_id, self.mock_tax_year, adjustments_payload
            )

            self.assertEqual(live_res.get("status"), "SUCCESS")
            args, kwargs = mock_request.call_args
            self.assertEqual(args[0], "POST")
            self.assertIn(f"/income-tax/ni/{self.mock_nino}/self-employments/{self.mock_income_source_id}/annual-submissions/{self.mock_tax_year}", args[1])
            self.assertIn('"adjustmentToProfitsForClass4": 250.0', kwargs["content"])
            print("[PASS] Self Employment Business v5 adjustmentToProfitsForClass4 payload validated.")

    def test_deprecation_audit(self):
        """Ensure no deprecated API endpoints (Capital Gains v2, Reliefs v2) exist in hmrc_api.py."""
        with open("hmrc_api.py", "r", encoding="utf-8") as f:
            code = f.read()

        deprecated_patterns = [
            "capital-gains",
            "capital_gains",
            "/reliefs",
            "reliefs-api"
        ]
        for pat in deprecated_patterns:
            self.assertNotIn(pat, code.lower(), f"Found deprecated API pattern in hmrc_api.py: {pat}")
        print("[PASS] Deprecation audit passed: Zero references to retired APIs.")

if __name__ == "__main__":
    unittest.main()
