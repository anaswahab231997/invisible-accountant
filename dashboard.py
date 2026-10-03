from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import asyncpg
from db import get_connection

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def view_dashboard(request: Request):
    async with get_connection() as conn:
        # Fetch staged expenses that haven't been queued to Xero yet
        rows = await conn.fetch("""
            SELECT c.id, c.sender_id, c.timestamp as created_at, c.staging_payload as payload,
                   c.raw_message, c.media_urls
            FROM chat_sessions c
            LEFT JOIN hmrc_ledger h ON c.id = h.chat_id
            WHERE c.staging_payload IS NOT NULL AND h.id IS NULL
            ORDER BY c.timestamp DESC
        """)
        
        items = []
        for r in rows:
            payload = r['payload']
            import json
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except:
                    payload = {}
                    
            # Basic parsing of the timestamp string
            import datetime
            try:
                dt = datetime.datetime.fromisoformat(str(r['created_at']))
                created_at = dt.strftime("%Y-%m-%d %H:%M")
            except:
                created_at = str(r['created_at'])

            # Fallbacks for missing keys
            account_code = str(payload.get('account_code') or payload.get('category') or payload.get('xero_account_code') or 'N/A').strip()
            tax_code = str(payload.get('tax_code') or payload.get('tax_rate') or payload.get('xero_tax_rate') or 'N/A').strip()
            
            # Combine reasoning steps if they exist
            reasoning = payload.get('reasoning', payload.get('reasoning_steps', ''))
            if not reasoning:
                parts = []
                for k, v in payload.items():
                    if k.startswith('reasoning_step_'):
                        parts.append(str(v))
                reasoning = chr(10).join(parts)

            items.append({
                "id": r['id'],
                "sender_id": r['sender_id'],
                "created_at": created_at,
                "vendor": payload.get('vendor', 'Unknown'),
                "memo": payload.get('memo', payload.get('reasoning_step_2_nature_of_expense', '')),
                "amount": payload.get('amount', payload.get('gross_amount', 0.0)),
                "account_code": account_code,
                "tax_code": tax_code,
                "raw_message": r.get('raw_message') or 'No original message available.',
                "media_urls": r.get('media_urls', ''),
                "reasoning": reasoning or 'No AI reasoning provided.'
            })
            
    
    context = {"request": request, "items": items}
    template = templates.get_template("dashboard.html")
    html_content = template.render(context)
    return HTMLResponse(content=html_content)


@router.post("/dashboard/approve/{item_id}", response_class=HTMLResponse)
async def approve_item(request: Request, item_id: int):
    from db import confirm_and_queue_to_ledger, get_connection
    import logging
    try:
        queue_id = await confirm_and_queue_to_ledger(item_id)
        async with get_connection() as conn:
            await conn.execute("UPDATE hmrc_ledger SET status = 'APPROVED' WHERE id = $1", queue_id)
    except Exception as e:
        logging.error(f"Failed to approve {item_id}: {e}")
        
    return HTMLResponse(f"""
    <tr class="bg-green-50 transition-colors">
        <td colspan="7" class="px-6 py-4 text-sm font-medium text-green-800 text-center flex items-center justify-center space-x-2">
            <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
            <span>Approved!</span>
        </td>
    </tr>
    """)

@router.post("/dashboard/bulk-approve", response_class=HTMLResponse)
async def bulk_approve(request: Request):
    from db import confirm_and_queue_to_ledger, get_connection
    import logging
    async with get_connection() as conn:
        rows = await conn.fetch("""
            SELECT c.id 
            FROM chat_sessions c
            LEFT JOIN hmrc_ledger h ON c.id = h.chat_id
            WHERE c.staging_payload IS NOT NULL AND h.id IS NULL
        """)
        for r in rows:
            try:
                queue_id = await confirm_and_queue_to_ledger(r["id"])
                await conn.execute("UPDATE hmrc_ledger SET status = 'APPROVED' WHERE id = $1", queue_id)
            except Exception as e:
                logging.error(f"Failed to bulk-approve {r['id']}: {e}")

    # Return refreshed table
    return await view_dashboard(request)
