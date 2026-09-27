import json, os

w = {
    "name": "Hospital AI Automation — Appointments + WhatsApp Support + Voice Calls + Reports + Feedback",
    "nodes": [],
    "connections": {},
    "active": True,
    "settings": {"executionOrder": "v1"}
}

def node(nid, name, ntype, pos, params, ver=1.1, wid=None):
    n = {"parameters": params, "id": nid, "name": name, "type": ntype, "typeVersion": ver, "position": pos}
    if wid: n["webhookId"] = wid
    w["nodes"].append(n)

def conn(src, dst, ctype="main", s_idx=0, d_idx=0):
    if src not in w["connections"]: w["connections"][src] = {}
    if ctype not in w["connections"][src]: w["connections"][src][ctype] = []
    while len(w["connections"][src][ctype]) <= s_idx:
        w["connections"][src][ctype].append([])
    w["connections"][src][ctype][s_idx].append({"node": dst, "type": ctype, "index": d_idx})

# 1. Handshake Webhook
node("wh-ver", "WhatsApp Webhook Verification (GET)", "n8n-nodes-base.webhook", [100, 100], {"httpMethod": "GET", "path": "whatsapp-webhook", "responseMode": "responseNode"}, 1.1, "whatsapp-webhook-verify")
node("code-ver", "Verify Handshake Token", "n8n-nodes-base.code", [300, 100], {"jsCode": "const q=$input.first().json.query||{}; if(q['hub.mode']==='subscribe'&&q['hub.verify_token']==($env.WA_VERIFY_TOKEN||'hospital_ai_webhook_verify_token')){ return [{json:{statusCode:200,body:q['hub.challenge']}}]; } return [{json:{statusCode:403,body:'Token mismatch'}}];"}, 2)
node("resp-ver", "Respond Handshake Challenge", "n8n-nodes-base.respondToWebhook", [500, 100], {"respondWith": "text", "responseBody": "={{ $json.body }}", "options": {"responseCode": "={{ $json.statusCode }}"}}, 1)
conn("WhatsApp Webhook Verification (GET)", "Verify Handshake Token")

# 2. Inbound WhatsApp Message Webhook & Router
node("wh-in", "WhatsApp Inbound Webhook", "n8n-nodes-base.webhook", [100, 300], {"httpMethod": "POST", "path": "whatsapp-webhook", "responseMode": "responseNode"}, 1.1, "whatsapp-webhook")
node("code-ext", "Extract Message & Classify", "n8n-nodes-base.code", [300, 300], {"jsCode": "const b=$input.first().json.body||$input.first().json; const m=b.entry?.[0]?.changes?.[0]?.value?.messages?.[0]; if(!m) return [{json:{isValid:false}}]; const f=m.from, t=m.text?.body||''; const r=t.trim().match(/^(?:rating\\s*[:=]?\\s*)?([1-5])(?:\\s*(?:\\/5|\\*|stars?))?\\s*[-:,.]?\\s*(.*)$/i); const isFb=['1','2','3','4','5'].includes(t.trim())||Boolean(r); return [{json:{isValid:true,from:f,text:t,isFeedback:isFb,rating:r?parseInt(r[1],10):(isFb?parseInt(t.trim(),10):null),comment:r?r[2]:''}}];"}, 2)
node("if-fb", "Is Feedback Rating?", "n8n-nodes-base.if", [500, 300], {"conditions": {"boolean": [{"value1": "={{ $json.isFeedback }}", "value2": True}]}}, 1)
node("req-fb", "Record Feedback in Database", "n8n-nodes-base.httpRequest", [700, 200], {"method": "POST", "url": "http://backend:8000/api/feedback", "sendBody": True, "specifyBody": "json", "jsonBody": "={\\n  \\\"rating\\\": {{ $json.rating }},\\n  \\\"comment\\\": \\\"{{ $json.comment || 'WhatsApp Feedback' }}\\\"\\n}"}, 4.1)
node("send-fb", "Send Feedback Gratitude WhatsApp", "n8n-nodes-base.httpRequest", [900, 200], {"method": "POST", "url": "https://graph.facebook.com/v19.0/={{ $env.WA_PHONE_NUMBER_ID }}/messages", "sendHeaders": True, "headerParameters": {"parameters": [{"name": "Authorization", "value": "Bearer ={{ $env.WA_ACCESS_TOKEN }}"}]}, "sendBody": True, "specifyBody": "json", "jsonBody": "={\\n  \\\"messaging_product\\\": \\\"whatsapp\\\",\\n  \\\"to\\\": \\\"{{ $json.from }}\\\",\\n  \\\"type\\\": \\\"text\\\",\\n  \\\"text\\\": { \\\"body\\\": \\\"Thank you! Your rating of {{ $json.rating }}/5 has been safely recorded.\\\" }\\n}"}, 4.1)
node("ack-wh", "Acknowledge WhatsApp Event 200 OK", "n8n-nodes-base.respondToWebhook", [1150, 300], {"respondWith": "json", "responseBody": "={\\n  \\\"status\\\": \\\"EVENT_RECEIVED\\\"\\n}"}, 1)

conn("WhatsApp Inbound Webhook", "Extract Message & Classify")
conn("Extract Message & Classify", "Is Feedback Rating?")
conn("Is Feedback Rating?", "Record Feedback in Database", "main", 0)
conn("Record Feedback in Database", "Send Feedback Gratitude WhatsApp")
conn("Send Feedback Gratitude WhatsApp", "Acknowledge WhatsApp Event 200 OK")


# 3. Patient WhatsApp AI Agent & Tools
node("ai-agent", "Patient WhatsApp AI Agent", "@n8n/n8n-nodes-langchain.agent", [700, 420], {"promptType": "define", "text": "={{ $json.text }}", "options": {"systemMessage": "You are the official Patient WhatsApp AI Agent for City Care Multispeciality Hospital. Use hospital tools to check info, slots, book/cancel appointments, check reports, request voice calls, or escalate emergencies."}}, 1.6)
conn("Is Feedback Rating?", "Patient WhatsApp AI Agent", "main", 1)

tools = [
    ("tool-info", "Tool: Get Hospital and Doctor Info", "get_hospital_doctor_info", "Retrieve hospital overview, doctors, slots, fees.", "GET", "http://backend:8000/api/doctors", None),
    ("tool-slots", "Tool: Check Doctor Booked Slots", "check_doctor_booked_slots", "Check doctor slots.", "GET", "http://backend:8000/api/doctors/{{ $fromAI(\"doctor_id\") }}/slots?slot_date={{ $fromAI(\"date\") }}", None),
    ("tool-book", "Tool: Book Appointment", "book_appointment", "Book appointment.", "POST", "http://backend:8000/api/appointments", "={\\n  \\\"doctor_id\\\": \\\"{{ $fromAI(\\\"doctor_id\\\") }}\\\",\\n  \\\"appointment_date\\\": \\\"{{ $fromAI(\\\"appointment_date\\\") }}\\\",\\n  \\\"appointment_time\\\": \\\"{{ $fromAI(\\\"appointment_time\\\") }}\\\",\\n  \\\"reason\\\": \\\"{{ $fromAI(\\\"reason\\\") }}\\\"\\n}"),
    ("tool-resched", "Tool: Reschedule Appointment", "reschedule_appointment", "Reschedule appointment.", "POST", "http://backend:8000/api/appointments/{{ $fromAI(\"appointment_id\") }}/reschedule", "={\\n  \\\"new_date\\\": \\\"{{ $fromAI(\\\"new_date\\\") }}\\\",\\n  \\\"new_time\\\": \\\"{{ $fromAI(\\\"new_time\\\") }}\\\",\\n  \\\"reason\\\": \\\"{{ $fromAI(\\\"reason\\\") }}\\\"\\n}"),
    ("tool-cancel", "Tool: Cancel Appointment", "cancel_appointment", "Cancel appointment.", "POST", "http://backend:8000/api/appointments/{{ $fromAI(\"appointment_id\") }}/cancel", "={\\n  \\\"cancelled_reason\\\": \\\"{{ $fromAI(\\\"reason\\\") }}\\\"\\n}"),
    ("tool-rep", "Tool: Check My Report Status", "check_my_report_status", "Check reports.", "GET", "http://backend:8000/api/reports", None),
    ("tool-voice", "Tool: Request AI Voice Call For This Patient", "request_ai_voice_call", "Request voice call.", "POST", "http://backend:8000/api/voice/request", "={\\n  \\\"phone\\\": \\\"{{ $fromAI(\\\"phone\\\") }}\\\",\\n  \\\"reason\\\": \\\"{{ $fromAI(\\\"reason\\\") }}\\\"\\n}"),
    ("tool-esc", "Tool: Escalate To Front Desk (Human Handoff)", "escalate_to_front_desk", "Escalate to front desk.", "POST", "http://backend:8000/api/escalations", "={\\n  \\\"reason\\\": \\\"{{ $fromAI(\\\"reason\\\") }}\\\",\\n  \\\"priority\\\": \\\"{{ $fromAI(\\\"priority\\\") }}\\\",\\n  \\\"notes\\\": \\\"{{ $fromAI(\\\"notes\\\") }}\\\"\\n}"),
]

for idx, (tid, tname, tfn, tdesc, tmethod, turl, tbody) in enumerate(tools):
    tp = {"name": tfn, "description": tdesc, "method": tmethod, "url": turl}
    if tbody: tp["sendBody"] = True; tp["specifyBody"] = "json"; tp["jsonBody"] = tbody
    node(tid, tname, "@n8n/n8n-nodes-langchain.toolHttpRequest", [600 + idx*80, 640], tp, 1.1)
    conn(tname, "Patient WhatsApp AI Agent", "ai_tool")

node("send-ai", "Send WhatsApp AI Response", "n8n-nodes-base.httpRequest", [950, 420], {"method": "POST", "url": "https://graph.facebook.com/v19.0/={{ $env.WA_PHONE_NUMBER_ID }}/messages", "sendHeaders": True, "headerParameters": {"parameters": [{"name": "Authorization", "value": "Bearer ={{ $env.WA_ACCESS_TOKEN }}"}]}, "sendBody": True, "specifyBody": "json", "jsonBody": "={\\n  \\\"messaging_product\\\": \\\"whatsapp\\\",\\n  \\\"to\\\": \\\"{{ $('Extract Message & Classify').item.json.from }}\\\",\\n  \\\"type\\\": \\\"text\\\",\\n  \\\"text\\\": { \\\"body\\\": \\\"{{ $json.output }}\\\" }\\n}"}, 4.1)

# 4. Schedules, Reports & Error Alert Workflows
node("sch-rem", "Hourly Appointment Reminders Trigger", "n8n-nodes-base.scheduleTrigger", [100, 850], {"rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}}, 1.1)
node("exec-rem", "Execute Reminders Scan & Notification", "n8n-nodes-base.httpRequest", [350, 850], {"method": "POST", "url": "http://backend:8000/api/admin/tasks/scan-reminders"}, 4.1)
conn("Hourly Appointment Reminders Trigger", "Execute Reminders Scan & Notification")

node("sch-fb", "Scheduled Feedback Scanner Trigger", "n8n-nodes-base.scheduleTrigger", [100, 1050], {"rule": {"interval": [{"field": "hours", "hoursInterval": 6}]}}, 1.1)
node("exec-fb", "Scan Completed Appointments & Send Feedback Request", "n8n-nodes-base.httpRequest", [350, 1050], {"method": "POST", "url": "http://backend:8000/api/admin/tasks/scan-feedback"}, 4.1)
conn("Scheduled Feedback Scanner Trigger", "Scan Completed Appointments & Send Feedback Request")

node("wh-rep", "Report Ready Webhook Trigger", "n8n-nodes-base.webhook", [100, 1250], {"httpMethod": "POST", "path": "report-ready-webhook"}, 1.1, "report-ready-webhook")
node("exec-rep", "Notify Ready Diagnostic Reports", "n8n-nodes-base.httpRequest", [350, 1250], {"method": "POST", "url": "http://backend:8000/api/admin/tasks/scan-reports"}, 4.1)
conn("Report Ready Webhook Trigger", "Notify Ready Diagnostic Reports")

node("err-trig", "Global Error Trigger", "n8n-nodes-base.errorTrigger", [100, 1450], {}, 1)
node("build-alert", "Build Alert Message", "n8n-nodes-base.code", [300, 1450], {"jsCode": "const err=$input.first().json; return [{json:{alertSubject:`[CRITICAL ALERT] Hospital AI Workflow Failure: ${err.node?.name||'System'}`,alertBody:`Hospital AI Failure\\nNode: ${err.node?.name}\\nError: ${err.error?.message}\\nTime: ${new Date().toISOString()}`,service_name:'n8n-engine',error_level:'CRITICAL',message:err.error?.message||'Failure',endpoint:err.node?.name||'n8n'}}];"}, 2)
node("send-email", "Send Error Alert Email", "n8n-nodes-base.emailSend", [500, 1450], {"fromEmail": "={{ $env.SMTP_SENDER || 'alerts@citycarehospital.com' }}", "toEmail": "={{ $env.ALERT_EMAIL_TO || 'admin@citycarehospital.com' }}", "subject": "={{ $json.alertSubject }}", "text": "={{ $json.alertBody }}"}, 2)
node("log-err-db", "Log Error to Database", "n8n-nodes-base.httpRequest", [700, 1450], {"method": "POST", "url": "http://backend:8000/api/admin/errors", "sendBody": True, "specifyBody": "json", "jsonBody": "={\\n  \\\"service_name\\\": \\\"{{ $json.service_name }}\\\",\\n  \\\"error_level\\\": \\\"{{ $json.error_level }}\\\",\\n  \\\"message\\\": \\\"{{ $json.message }}\\\",\\n  \\\"endpoint\\\": \\\"{{ $json.endpoint }}\\\"\\n}"}, 4.1)
conn("Global Error Trigger", "Build Alert Message")
conn("Build Alert Message", "Send Error Alert Email")
conn("Build Alert Message", "Log Error to Database")

os.makedirs("n8n/workflows", exist_ok=True)
p1 = os.path.join("n8n", "workflows", "Hospital AI Automation — Appointments + WhatsApp Support + Voice Calls + Reports + Feedback.json")
p2 = os.path.join("n8n", "workflows", "hospital-ai-automation-main.json")
with open(p1, "w", encoding="utf-8") as f: json.dump(w, f, indent=2)
with open(p2, "w", encoding="utf-8") as f: json.dump(w, f, indent=2)
print("Master workflow generated successfully!")

conn("Patient WhatsApp AI Agent", "Send WhatsApp AI Response")
conn("Send WhatsApp AI Response", "Acknowledge WhatsApp Event 200 OK")

conn("Verify Handshake Token", "Respond Handshake Challenge")
