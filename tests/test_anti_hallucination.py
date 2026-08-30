import pytest
from unittest.mock import patch, AsyncMock
from agents import verify_expense_hallucination

@pytest.mark.asyncio
@patch('agents.client.aio.models.generate_content', new_callable=AsyncMock)
async def test_hallucination_detected(mock_generate):
    class MockResponse:
        text = '{"is_hallucinated": true, "hallucination_reason": "Fabricated", "corrected_question": "Please clarify?"}'
    mock_generate.return_value = MockResponse()
    
    result = await verify_expense_hallucination("lunch", {"vendor": "Tesco", "amount": 100.0})
    assert result["is_hallucinated"] is True
