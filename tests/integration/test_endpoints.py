import pytest
from unittest.mock import patch, AsyncMock
import json
import hmac
import hashlib

@pytest.mark.integration
def test_webhook_whatsapp_unauthorized(test_client):
    response = test_client.post("/webhook/whatsapp", json={
        "sender_id": "12345",
        "message": "Hello",
        "turn_count": 1
    })
    assert response.status_code == 403
    assert "Invalid signature" in response.json()["detail"]

@pytest.mark.integration
@patch("main.create_chat_session", new_callable=AsyncMock)
@patch("main.get_recent_intakes_by_sender", new_callable=AsyncMock)
@patch("main.process_expense_message", new_callable=AsyncMock)
@patch("main.verify_expense_hallucination", new_callable=AsyncMock)
def test_webhook_whatsapp_authorized(mock_verify, mock_process, mock_get_recent, mock_create_chat, test_client):
    mock_create_chat.return_value = 1
    mock_process.return_value = {"vendor": "Train", "amount": 40.0, "category": "Travel", "is_ambiguous": False}
    mock_verify.return_value = {"is_hallucinated": False}
    
    payload = {
        "sender_id": "1234567890",
        "message": "I bought a train ticket for 40",
        "turn_count": 1
    }
    raw_body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(
        "dummy_secret".encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    headers = {
        "X-Hub-Signature-256": f"sha256=" + signature,
        "Content-Type": "application/json"
    }
    
    response = test_client.post("/webhook/whatsapp", content=raw_body, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "chat_id" in response.json()

@pytest.mark.integration
@patch("main.get_all_hmrc_queue", new_callable=AsyncMock)
def test_queue_pagination(mock_get_all, test_client):
    def mock_get(limit=100, offset=0):
        records = [
            {"id": i, "vendor": f"Vendor{i}", "amount": 100.0 + i, "category": "Travel costs", "status": "PENDING"}
            for i in range(10)
        ]
        return records[offset:offset+limit]
    
    mock_get_all.side_effect = mock_get

    response = test_client.get("/queue?limit=5&offset=0", headers={"X-API-Key": "super-secret-key"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["queue"]) == 5
    assert data["queue"][0]["vendor"] == "Vendor0"
    assert data["queue"][1]["vendor"] == "Vendor1"
    
    response2 = test_client.get("/queue?limit=2&offset=5", headers={"X-API-Key": "super-secret-key"})
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["queue"]) == 2
    assert data2["queue"][0]["vendor"] == "Vendor5"
