import json

wf_path = r"c:\Hospital-AI-Automation\n8n\workflows\hospital-ai-automation-main.json"
with open(wf_path, "r", encoding="utf-8") as f:
    wf = json.load(f)

for i, node in enumerate(wf.get("nodes", [])[10:18], start=11):
    print(f"\n==========================================")
    print(f"NODE {i}: {node.get('name')} ({node.get('type')})")
    print(json.dumps(node.get("parameters", {}), indent=2))

