import re

with open('landing_page.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_script = """
        // Chat Demo Logic
        function submitDemo() {
            const inp = document.getElementById('demoInput');
            const val = inp.value.trim();
            if(!val) return;
            inp.value = ''; inp.disabled = true;
            
            const chat = document.getElementById('chatBody');
            chat.innerHTML += `<div class="msg-user px-3 py-2 text-[15px] self-end max-w-[85%] mb-2">${val}</div>`;
            chat.scrollTop = chat.scrollHeight;

            const typingId = 'typing-' + Date.now();
            setTimeout(() => {
                chat.innerHTML += `<div id="${typingId}" class="msg-ai px-4 py-2 self-start text-slate flex gap-1 items-center max-w-[85%] mb-2">
                    <span class="w-1.5 h-1.5 bg-slate rounded-full animate-bounce"></span>
                    <span class="w-1.5 h-1.5 bg-slate rounded-full animate-bounce" style="animation-delay: 0.1s"></span>
                    <span class="w-1.5 h-1.5 bg-slate rounded-full animate-bounce" style="animation-delay: 0.2s"></span>
                </div>`;
                chat.scrollTop = chat.scrollHeight;
            }, 400);

            setTimeout(() => {
                document.getElementById(typingId).remove();
                const amounts = val.match(/[\\d\\.]+/);
                const amount = amounts ? `£${amounts[0]}` : 'that expense';

                chat.innerHTML += `<div class="msg-ai px-3 py-2 text-[15px] shadow-sm max-w-[85%] mb-2">
                    <div class="font-medium text-emerald-700 mb-1 flex items-center gap-1"><i data-lucide="check-circle-2" class="w-4 h-4"></i> Vaulted & Categorised</div>
                    I've logged ${amount} under <strong>Business Travel</strong> based on HMRC rules. You're all set!
                </div>`;
                lucide.createIcons();
                chat.scrollTop = chat.scrollHeight;
                inp.disabled = false; inp.focus();
            }, 2000);
        }
"""

new_script = """
        // Real-Time Inference WebSockets & API
        const session_id = "demo_web_" + Math.random().toString(36).substring(7);
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        let ws;
        
        function connectWebSocket() {
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/${session_id}`);
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'INTAKE_UPDATE') {
                    const typingIndicator = document.getElementById('typing-indicator');
                    if (typingIndicator) typingIndicator.remove();
                    
                    const chat = document.getElementById('chatBody');
                    const inp = document.getElementById('demoInput');
                    const res = data.result;
                    
                    let html = '';
                    if (res.status === 'CONFIRMED') {
                        html = `<div class="msg-ai px-3 py-2 text-[15px] shadow-sm max-w-[85%] mb-2">
                            <div class="font-medium text-emerald-700 mb-1 flex items-center gap-1"><i data-lucide="lock" class="w-4 h-4"></i> Locked & Sent</div>
                            All set! I've officially locked this into your tax ledger and it's queued for HMRC.
                        </div>`;
                    } else if (res.is_ambiguous) {
                        html = `<div class="msg-ai px-3 py-2 text-[15px] shadow-sm max-w-[85%] mb-2">${res.auditor_question || "Could you clarify that?"}</div>`;
                    } else if (res.amount) {
                        html = `<div class="msg-ai px-3 py-2 text-[15px] shadow-sm max-w-[85%] mb-2">
                            <div class="font-medium text-emerald-700 mb-1 flex items-center gap-1"><i data-lucide="check-circle-2" class="w-4 h-4"></i> Vaulted & Categorised</div>
                            I've logged £${res.amount.toFixed(2)} at ${res.vendor || "the vendor"} under <strong>${res.category || "General"}</strong>. Reply 'proceed' to lock it.
                        </div>`;
                    } else {
                        html = `<div class="msg-ai px-3 py-2 text-[15px] shadow-sm max-w-[85%] mb-2">I couldn't process that. Try sending an expense like '£5 for coffee'.</div>`;
                    }
                    
                    chat.innerHTML += html;
                    lucide.createIcons();
                    chat.scrollTop = chat.scrollHeight;
                    inp.disabled = false; inp.focus();
                }
            };
            
            ws.onclose = function(e) {
                setTimeout(connectWebSocket, 1000);
            };
        }
        
        connectWebSocket();

        async function submitDemo() {
            const inp = document.getElementById('demoInput');
            const val = inp.value.trim();
            if(!val) return;
            inp.value = ''; inp.disabled = true;
            
            const chat = document.getElementById('chatBody');
            chat.innerHTML += `<div class="msg-user px-3 py-2 text-[15px] self-end max-w-[85%] mb-2">${val}</div>`;
            chat.scrollTop = chat.scrollHeight;

            chat.innerHTML += `<div id="typing-indicator" class="msg-ai px-4 py-2 self-start text-slate flex gap-1 items-center max-w-[85%] mb-2">
                <span class="w-1.5 h-1.5 bg-slate rounded-full animate-bounce"></span>
                <span class="w-1.5 h-1.5 bg-slate rounded-full animate-bounce" style="animation-delay: 0.1s"></span>
                <span class="w-1.5 h-1.5 bg-slate rounded-full animate-bounce" style="animation-delay: 0.2s"></span>
            </div>`;
            chat.scrollTop = chat.scrollHeight;

            // Send actual request to the backend AI
            try {
                await fetch('/api/simulate_whatsapp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        sender_id: session_id,
                        message: val,
                        turn_count: 1
                    })
                });
            } catch (err) {
                console.error(err);
                document.getElementById('typing-indicator').remove();
                chat.innerHTML += `<div class="msg-ai px-3 py-2 text-[15px] shadow-sm max-w-[85%] mb-2 text-red-600">Connection error. Please try again.</div>`;
                inp.disabled = false;
            }
        }
"""

# Regex replacement to handle whitespace differences safely
content = re.sub(r'// Chat Demo Logic.*?function submitDemo\(\).*?inp\.disabled = false; inp\.focus\(\);\s*\}, 2000\);\s*\}', new_script, content, flags=re.DOTALL)

with open('landing_page.html', 'w', encoding='utf-8') as f:
    f.write(content)
