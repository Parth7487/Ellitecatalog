# update_checks.py
# Local helper CLI to quickly modify validation statuses and push them to Vercel/GitHub live website-catalog

import json
import sys
import subprocess

STATE_FILE = 'checks_state.json'

def load_state():
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def print_help():
    print("""
ETi Progress Validation CLI Updater
===================================
Commands:
  python3 update_checks.py list                             - Show all punch-list items and statuses
  python3 update_checks.py update <ID> <status> <notes>     - Update status and comments for an item
  python3 update_checks.py deploy                           - Git commit and push updates to Vercel

Statuses:
  "Passed by ETi", "Ready for ETi Review", "In Progress", "Not Started", "Blocked — Owner Decision Required"
""")

def list_items():
    state = load_state()
    print("\n--- Validation Tracker Status List ---")
    for key, data in sorted(state.items()):
        status = data.get('status', 'Not Started')
        notes = data.get('notes', '')
        print(f"[{key}] Status: {status}")
        if notes:
            print(f"      Notes: {notes[:80]}...")
    print("--------------------------------------")

def update_item(item_id, status, notes=None):
    state = load_state()
    
    valid_statuses = [
        "Passed by ETi", 
        "Ready for ETi Review", 
        "In Progress", 
        "Not Started", 
        "Blocked — Owner Decision Required"
    ]
    
    # Fuzzy match status standardizations
    status_lower = status.lower()
    matched_status = None
    for vs in valid_statuses:
        if status_lower in vs.lower() or vs.lower() in status_lower:
            matched_status = vs
            break
            
    if not matched_status:
        print(f"❌ Error: Invalid status '{status}'. Must be one of: {valid_statuses}")
        return

    if item_id not in state:
        state[item_id] = {}
        
    state[item_id]['status'] = matched_status
    if notes:
        state[item_id]['notes'] = notes
        
    save_state(state)
    print(f"✅ Successfully updated [{item_id}] to status: '{matched_status}'")

def deploy():
    print("Publishing progress updates to live client preview (Vercel)...")
    try:
        subprocess.run(["git", "add", STATE_FILE], check=True)
        subprocess.run(["git", "commit", "-m", "Sync validation status tracker state"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🚀 Successfully published live! Deployed at https://shopifydevstudioellitecatalog.vercel.app/checks.html")
    except Exception as e:
        print(f"❌ Deploy failed: {e}")

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] == 'help':
        print_help()
    elif args[0] == 'list':
        list_items()
    elif args[0] == 'update':
        if len(args) < 3:
            print("❌ Error: Missing arguments. Usage: python3 update_checks.py update <ID> <status> [notes]")
        else:
            item_id = args[1]
            status = args[2]
            notes = args[3] if len(args) > 3 else None
            update_item(item_id, status, notes)
    elif args[0] == 'deploy':
        deploy()
    else:
        print_help()
