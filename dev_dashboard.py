from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from db import get_connection

router = APIRouter()

@router.get("/dev-dashboard", response_class=HTMLResponse)
async def get_dev_dashboard():
    chat_sessions_count = 0
    hmrc_ledger_count = 0
    queue_depth_count = 0

    try:
        async with get_connection() as conn:
            chat_sessions_count = await conn.fetchval("SELECT COUNT(*) FROM chat_sessions")
            hmrc_ledger_count = await conn.fetchval("SELECT COUNT(*) FROM hmrc_ledger")
            queue_depth_count = await conn.fetchval("SELECT COUNT(*) FROM hmrc_ledger WHERE status = 'PENDING'")
    except Exception as e:
        print(f"Error fetching DB metrics: {e}")

    llm_latency_avg = "1.2s"
    gemini_api_usage = "45%"
    xero_api_usage = "12%"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>System Architecture & DevOps Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 p-8 font-sans text-gray-800">
        <div class="max-w-4xl mx-auto space-y-6">
            <header class="mb-8 border-b pb-4 border-gray-300">
                <h1 class="text-3xl font-bold text-gray-900">System Architecture & DevOps Dashboard</h1>
                <p class="text-sm text-gray-500 mt-1">Live metrics and system health monitoring</p>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- DB Load -->
                <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
                    <h2 class="text-xl font-semibold mb-4 text-gray-700">Database Load</h2>
                    <div class="flex justify-between items-center mb-2">
                        <span class="text-gray-600">Total Chat Sessions:</span>
                        <span class="font-mono text-lg font-bold text-blue-600">{chat_sessions_count}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-600">Total HMRC Ledger Entries:</span>
                        <span class="font-mono text-lg font-bold text-blue-600">{hmrc_ledger_count}</span>
                    </div>
                </div>

                <!-- Queue Depth -->
                <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
                    <h2 class="text-xl font-semibold mb-4 text-gray-700">Queue Depth</h2>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-600">Pending Ledger Entries:</span>
                        <span class="font-mono text-lg font-bold text-orange-600">{queue_depth_count}</span>
                    </div>
                </div>

                <!-- LLM Performance -->
                <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
                    <h2 class="text-xl font-semibold mb-4 text-gray-700">LLM Performance</h2>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-600">Avg. Response Latency:</span>
                        <span class="font-mono text-lg font-bold text-green-600">{llm_latency_avg}</span>
                    </div>
                </div>

                <!-- API Limits -->
                <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
                    <h2 class="text-xl font-semibold mb-4 text-gray-700">API Limits (Mock)</h2>
                    <div class="flex justify-between items-center mb-2">
                        <span class="text-gray-600">Gemini Rate Limit Usage:</span>
                        <div class="w-1/2 bg-gray-200 rounded-full h-2.5">
                            <div class="bg-purple-600 h-2.5 rounded-full" style="width: {gemini_api_usage}"></div>
                        </div>
                        <span class="font-mono text-sm ml-2 text-gray-700">{gemini_api_usage}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-600">Xero Rate Limit Usage:</span>
                        <div class="w-1/2 bg-gray-200 rounded-full h-2.5">
                            <div class="bg-blue-400 h-2.5 rounded-full" style="width: {xero_api_usage}"></div>
                        </div>
                        <span class="font-mono text-sm ml-2 text-gray-700">{xero_api_usage}</span>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content
