import json
import os

wf_path = r"c:\Hospital-AI-Automation\n8n\workflows\hospital-ai-automation-main.json"
with open(wf_path, "r", encoding="utf-8") as f:
    wf = json.load(f)

print(f"=== Workflow: {wf.get('name')} ===")
print(f"Total Nodes: {len(wf.get('nodes', []))}")
nodes = wf.get("nodes", [])
for i, n in enumerate(nodes):
    print(f"\nNode {i+1}: '{n.get('name')}' | Type: {n.get('type')} | ID: {n.get('id')}")
    params = n.get("parameters", {})
    for k, v in params.items():
        val_str = str(v)
        if len(val_str) > 120:
            val_str = val_str[:120] + "..."
        print(f"   - {k}: {val_str}")

print("\n=== Connections ===")
connections = wf.get("connections", {})
for src, dests in connections.items():
    print(f"Source: {src}")
    for conn_type, outputs in dests.items():
        for out_idx, target_list in enumerate(outputs):
            targets = [f"{t.get('node')}(type={t.get('type')})" for t in target_list]
            print(f"   [{conn_type} output {out_idx}] -> {', '.join(targets)}")
