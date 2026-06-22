import os
import re
import json

# Absolute Paths
ROOT_DIR = "/Users/parth/Downloads/Projects/Elite ti/ELLITE_MAIN"
MEETING_DIR = os.path.join(ROOT_DIR, "Memory", "Conversations ", "Meeting")
CHAT_PATH = os.path.join(ROOT_DIR, "Memory", "Conversations ", "WhatsApp Chat - Nathan Ellite (amazing Cars)", "_chat.txt")
OUTPUT_DIR = os.path.join(ROOT_DIR, "website-catalog", "Client-portal")
OUTPUT_HTML_PORTAL = os.path.join(OUTPUT_DIR, "client_portal.html")
OUTPUT_HTML_PROJECT = os.path.join(ROOT_DIR, "website-catalog", "Project.html")

def sanitize_text(text):
    if not text:
        return text
    text = re.sub(r'shpss_[a-zA-Z0-9]{32}', '[REDACTED_SHOPIFY_SHARED_SECRET]', text)
    text = re.sub(r'shpat_[a-zA-Z0-9]{32}', '[REDACTED_SHOPIFY_TOKEN]', text)
    text = re.sub(r'\b[a-fA-F0-9]{32}\b', '[REDACTED_SECRET]', text)
    return text

def parse_meetings():
    meetings = []
    conversations_dir = os.path.join(ROOT_DIR, "Memory", "Conversations ")
    if not os.path.exists(conversations_dir):
        print(f"Conversations directory {conversations_dir} does not exist.")
        return meetings

    # Recursively find all txt and md files, ignoring WhatsApp folder
    file_paths = []
    for root, dirs, files in os.walk(conversations_dir):
        if "WhatsApp Chat" in root:
            continue
        for f_name in files:
            if f_name.endswith('.txt') or f_name.endswith('.md'):
                file_paths.append(os.path.join(root, f_name))
                
    file_paths.sort()

    for path in file_paths:
        f_name = os.path.relpath(path, conversations_dir)
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            continue
            
        title = lines[0].strip()
        if not title:
            title = os.path.basename(path)
            
        recording_url = ""
        purpose = ""
        takeaways = []
        topics = []
        action_items = []
        transcript = []
        
        current_section = None
        
        # Simple line-by-line parsing
        for line in lines[1:]:
            line_str = line.strip()
            if not line_str:
                continue
                
            # Detect recording link
            if "VIEW RECORDING" in line_str:
                match = re.search(r'https?://[^\s]+', line_str)
                if match:
                    recording_url = match.group(0)
                continue
                
            # Detect section headers
            if line_str in ["Meeting Purpose", "Key Takeaways", "Topics", "Action Items", "Next Steps", "Tasks", "Todo", "To-Do"]:
                current_section = line_str
                continue
                
            # Parse sections
            if current_section == "Meeting Purpose":
                purpose += line_str + " "
            elif current_section == "Key Takeaways":
                if line_str.startswith("-") or line_str.startswith("*"):
                    takeaways.append(line_str.lstrip("-* ").strip())
            elif current_section == "Topics":
                # Check if it looks like transcript start
                if ":" in line_str and not line_str.startswith("-") and not line_str.startswith("http"):
                    if re.match(r'^\d+:\d+', line_str) or re.match(r'^[a-zA-Z\s]+:', line_str):
                        current_section = "Transcript"
                else:
                    if line_str.startswith("-") or line_str.startswith("*"):
                        topics.append(line_str.lstrip("-* ").strip())
            
            # Action items / Next Steps / Tasks / Todo / To-Do
            if current_section in ["Action Items", "Next Steps", "Tasks", "Todo", "To-Do"]:
                if line_str.startswith("-") or line_str.startswith("*"):
                    item_text = line_str.lstrip("-* ").strip()
                    
                    # Parse checkbox status
                    initial_status = "pending"
                    chk_match = re.match(r'^\[([ xX])\]\s*(.*)', item_text)
                    if chk_match:
                        marker = chk_match.group(1).lower()
                        initial_status = "completed" if marker == 'x' else "pending"
                        item_text = chk_match.group(2).strip()
                    
                    watch_url = ""
                    
                    # Extract fathom link
                    watch_match = re.search(r'https://fathom.video/share/[^\s]+', item_text)
                    if watch_match:
                        watch_url = watch_match.group(0)
                        item_text = re.sub(r'-\s*WATCH.*', '', item_text).strip()
                        item_text = re.sub(r'https://fathom.video/share/[^\s]+', '', item_text).strip()
                        item_text = item_text.replace("✨", "").strip()
                        item_text = item_text.replace("@", "").strip()
                    
                    # Extract timestamp details if present
                    time_match = re.search(r'(\d+:\d+)', item_text)
                    timestamp_label = time_match.group(0) if time_match else ""
                    if timestamp_label:
                        item_text = item_text.replace(timestamp_label, "").strip()
                    
                    # Clean remaining double spaces or trailing characters
                    item_text = re.sub(r'\s+', ' ', item_text).strip()
                    
                    # Determine assignee
                    owner = "Shopifydevstudio"
                    item_lower = item_text.lower()
                    if "@nathan" in item_lower or "@nate" in item_lower or "nathan:" in item_lower or "nate:" in item_lower or item_lower.startswith("nathan") or item_lower.startswith("nate"):
                        owner = "Nathan"
                        item_text = re.sub(r'^nathan:\s*', '', item_text, flags=re.IGNORECASE)
                        item_text = re.sub(r'^nate:\s*', '', item_text, flags=re.IGNORECASE)
                        item_text = item_text.replace("@Nathan", "").replace("@Nate", "").replace("@nathan", "").replace("@nate", "").strip()
                    elif "@parth" in item_lower or "@studio" in item_lower or "@shopifydevstudio" in item_lower or "studio:" in item_lower or "parth:" in item_lower or item_lower.startswith("studio") or item_lower.startswith("parth"):
                        owner = "Shopifydevstudio"
                        item_text = re.sub(r'^studio:\s*', '', item_text, flags=re.IGNORECASE)
                        item_text = re.sub(r'^parth:\s*', '', item_text, flags=re.IGNORECASE)
                        item_text = item_text.replace("@Parth", "").replace("@Studio", "").replace("@shopifydevstudio", "").strip()
                    elif "nathan" in item_lower or "nate" in item_lower:
                        owner = "Nathan"
                    
                    item_text = re.sub(r'\s+', ' ', item_text).strip()
                    
                    action_items.append({
                        "description": item_text,
                        "owner": owner,
                        "watch_url": watch_url,
                        "timestamp": timestamp_label,
                        "initial_status": initial_status,
                        "source": f_name
                    })
                    
            # Transcript parsing
            if current_section == "Transcript":
                match = re.match(r'^(\d+:\d+)\s*-\s*([^\n:]+)', line_str)
                if match:
                    timestamp, speaker = match.groups()
                    transcript.append({
                        "timestamp": timestamp,
                        "speaker": "Nathan" if "Nathan" in speaker else "Shopifydevstudio",
                        "text": ""
                    })
                elif transcript:
                    transcript[-1]["text"] += (" " if transcript[-1]["text"] else "") + line_str
        
        # Fallback to checklist scan if action section didn't capture items
        if not action_items:
            for line_idx, line in enumerate(lines):
                line_str = line.strip()
                chk_match = re.match(r'^[-*]\s*\[([ xX])\]\s*(.*)', line_str)
                if chk_match:
                    marker = chk_match.group(1).lower()
                    initial_status = "completed" if marker == 'x' else "pending"
                    item_text = chk_match.group(2).strip()
                    
                    watch_url = ""
                    watch_match = re.search(r'https://fathom.video/share/[^\s]+', item_text)
                    if watch_match:
                        watch_url = watch_match.group(0)
                        item_text = re.sub(r'-\s*WATCH.*', '', item_text).strip()
                        item_text = re.sub(r'https://fathom.video/share/[^\s]+', '', item_text).strip()
                        item_text = item_text.replace("✨", "").strip()
                        item_text = item_text.replace("@", "").strip()
                    
                    time_match = re.search(r'(\d+:\d+)', item_text)
                    timestamp_label = time_match.group(0) if time_match else ""
                    if timestamp_label:
                        item_text = item_text.replace(timestamp_label, "").strip()
                        
                    owner = "Shopifydevstudio"
                    item_lower = item_text.lower()
                    if "@nathan" in item_lower or "@nate" in item_lower or "nathan:" in item_lower or "nate:" in item_lower or item_lower.startswith("nathan") or item_lower.startswith("nate"):
                        owner = "Nathan"
                        item_text = re.sub(r'^nathan:\s*', '', item_text, flags=re.IGNORECASE)
                        item_text = re.sub(r'^nate:\s*', '', item_text, flags=re.IGNORECASE)
                        item_text = item_text.replace("@Nathan", "").replace("@Nate", "").replace("@nathan", "").replace("@nate", "").strip()
                    elif "@parth" in item_lower or "@studio" in item_lower or "@shopifydevstudio" in item_lower or "studio:" in item_lower or "parth:" in item_lower or item_lower.startswith("studio") or item_lower.startswith("parth"):
                        owner = "Shopifydevstudio"
                        item_text = re.sub(r'^studio:\s*', '', item_text, flags=re.IGNORECASE)
                        item_text = re.sub(r'^parth:\s*', '', item_text, flags=re.IGNORECASE)
                        item_text = item_text.replace("@Parth", "").replace("@Studio", "").replace("@shopifydevstudio", "").strip()
                    elif "nathan" in item_lower or "nate" in item_lower:
                        owner = "Nathan"
                        
                    item_text = re.sub(r'\s+', ' ', item_text).strip()
                    
                    action_items.append({
                        "description": item_text,
                        "owner": owner,
                        "watch_url": watch_url,
                        "timestamp": timestamp_label,
                        "initial_status": initial_status,
                        "source": f_name
                    })

        meetings.append({
            "filename": f_name,
            "title": title,
            "recording_url": recording_url,
            "purpose": purpose.strip(),
            "takeaways": takeaways,
            "topics": topics,
            "action_items": action_items,
            "transcript": transcript
        })
    return meetings

def parse_chat():
    messages = []
    if not os.path.exists(CHAT_PATH):
        print(f"Chat file {CHAT_PATH} does not exist.")
        return messages

    pattern = re.compile(r'^\[(\d{2}/\d{2}/\d{2}),\s*([^\]]+)\]\s*([^:]+):\s*(.*)')
    
    with open(CHAT_PATH, 'r', encoding='utf-8') as f:
        current_msg = None
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            
            match = pattern.match(line_str)
            if match:
                if current_msg:
                    messages.append(current_msg)
                
                date_str, time_str, sender, text = match.groups()
                sender_clean = "Nathan" if "Nathan" in sender or "Nate" in sender else "Shopifydevstudio"
                current_msg = {
                    "date": date_str,
                    "time": time_str.replace('\u202f', ' '),
                    "sender": sender_clean,
                    "text": sanitize_text(text)
                }
            else:
                if current_msg:
                    current_msg["text"] += "\n" + sanitize_text(line_str)
        
        if current_msg:
            messages.append(current_msg)
            
    return messages[-600:]

def generate_portal():
    print("⏳ Parsing meeting logs...")
    meetings = parse_meetings()
    
    print("⏳ Parsing WhatsApp chat log...")
    chat_logs = parse_chat()
    
    # Create output directory if needed
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Elite Ti - Client Portal & Project Tracker</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        'brand-lime': '#C4F101',
                        'brand-cyan': '#00E5FF',
                        'brand-dark': '#0B0B0C',
                        'brand-card': '#141416',
                        'brand-border': '#27272A'
                    },
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                        outfit: ['Outfit', 'sans-serif']
                    }
                }
            }
        }
    </script>
    <style>
        body {
            background-color: #070708;
            color: #E4E4E7;
            -webkit-font-smoothing: antialiased;
        }
        
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #0B0B0C;
        }
        ::-webkit-scrollbar-thumb {
            background: #27272A;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #C4F101;
        }
        
        .glass-panel {
            background: rgba(20, 20, 22, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(39, 39, 42, 0.5);
        }
        
        .tab-btn.active {
            color: #C4F101;
            border-bottom-color: #C4F101;
        }
        
        .glow-lime {
            box-shadow: 0 0 20px rgba(196, 241, 1, 0.1);
        }
        .glow-cyan {
            box-shadow: 0 0 20px rgba(0, 229, 255, 0.1);
        }
        
        /* Message bubble styles */
        .msg-nathan {
            background-color: #17241A;
            border: 1px solid rgba(74, 222, 128, 0.15);
            align-self: flex-start;
        }
        .msg-studio {
            background-color: #1D1D22;
            border: 1px solid rgba(255, 255, 255, 0.05);
            align-self: flex-end;
        }
    </style>
</head>
<body class="min-h-screen flex flex-col font-sans">

    <!-- Top Glow Effects -->
    <div class="fixed top-0 left-1/4 w-96 h-96 bg-brand-lime/5 rounded-full filter blur-[100px] pointer-events-none z-0"></div>
    <div class="fixed top-0 right-1/4 w-96 h-96 bg-brand-cyan/5 rounded-full filter blur-[100px] pointer-events-none z-0"></div>

    <!-- Header -->
    <header class="border-b border-brand-border/60 bg-brand-dark/80 backdrop-blur sticky top-0 z-50 px-4 py-4 md:px-8">
        <div class="max-w-[1500px] mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
            <div class="flex items-center gap-4">
                <a href="../Photo-organising-portal/visual_audit_sheet.html" class="flex items-center gap-2 border border-brand-border hover:border-brand-lime text-[10px] font-black tracking-widest px-4 py-2 bg-brand-card hover:bg-black text-gray-300 hover:text-brand-lime transition-all uppercase rounded-sm">
                    <span>← PHOTO MANAGER PORTAL</span>
                </a>
                <div class="h-6 w-px bg-brand-border/60 hidden sm:block"></div>
                <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-brand-lime shadow-[0_0_8px_#C4F101]"></span>
                    <span class="text-[10px] font-black uppercase tracking-widest text-zinc-400">CLIENT COOPERATIVE PORTAL</span>
                </div>
            </div>
            
            <div class="flex items-center gap-4">
                <span class="text-xl font-outfit font-black tracking-tight text-white">ELITE <span class="text-brand-lime">TI</span></span>
                <span class="text-[8px] font-extrabold uppercase tracking-widest px-2 py-0.5 border border-brand-cyan/35 text-brand-cyan bg-brand-cyan/10 rounded-sm">PROJECT MANAGEMENT</span>
            </div>
        </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-grow max-w-[1500px] w-full mx-auto p-4 md:p-8 z-10 relative flex flex-col gap-6">
        
        <!-- Summary Stats Board -->
        <section class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <!-- Overall Progress -->
            <div class="glass-panel p-5 rounded-lg flex flex-col justify-between glow-lime">
                <div class="flex justify-between items-start">
                    <span class="text-[9px] font-black tracking-widest uppercase text-zinc-400">Overall Progress</span>
                    <span id="stat-progress-pct" class="text-2xl font-outfit font-black text-brand-lime">0.0%</span>
                </div>
                <div class="my-4">
                    <div class="w-full bg-black h-1.5 rounded-full overflow-hidden border border-brand-border">
                        <div id="stat-progress-bar" class="bg-brand-lime h-full w-0 transition-all duration-1000 ease-out shadow-[0_0_10px_#C4F101]"></div>
                    </div>
                </div>
                <div class="text-[8px] font-extrabold text-zinc-500 uppercase tracking-widest flex justify-between">
                    <span>Task Checklist</span>
                    <span id="stat-progress-ratio">0/0 Completed</span>
                </div>
            </div>

            <!-- Total Meetings -->
            <div class="glass-panel p-5 rounded-lg flex flex-col justify-between">
                <span class="text-[9px] font-black tracking-widest uppercase text-zinc-400">Total Sync Calls</span>
                <div class="flex items-baseline gap-2 mt-4">
                    <span id="stat-total-meetings" class="text-3xl font-outfit font-black text-white">0</span>
                    <span class="text-[10px] text-zinc-500 font-bold uppercase">Recorded Meetings</span>
                </div>
                <span id="stat-last-call" class="text-[8px] font-extrabold text-brand-cyan uppercase tracking-widest mt-2">Latest: Call on June 22</span>
            </div>

            <!-- WhatsApp Exchange Counters -->
            <div class="glass-panel p-5 rounded-lg flex flex-col justify-between">
                <span class="text-[9px] font-black tracking-widest uppercase text-zinc-400">WhatsApp Exchange</span>
                <div class="flex items-baseline gap-2 mt-4">
                    <span id="stat-total-chats" class="text-3xl font-outfit font-black text-white">0</span>
                    <span class="text-[10px] text-zinc-500 font-bold uppercase">Messages Logged</span>
                </div>
                <span class="text-[8px] font-extrabold text-zinc-500 uppercase tracking-widest mt-2">Searchable decision trail</span>
            </div>

            <!-- Quick Fathom Link -->
            <div class="glass-panel p-5 rounded-lg flex flex-col justify-between glow-cyan">
                <span class="text-[9px] font-black tracking-widest uppercase text-zinc-400 font-bold text-brand-cyan">Quick-Access Video Link</span>
                <div class="mt-4">
                    <a id="stat-recording-btn" href="#" target="_blank" class="w-full text-center block bg-brand-cyan hover:bg-brand-cyan/90 text-black text-[10px] font-black tracking-wider uppercase py-2 px-3 rounded transition-all hover:scale-[1.02]">
                        🎥 Watch Recent Meet Video
                    </a>
                </div>
                <span class="text-[8px] font-extrabold text-zinc-500 uppercase tracking-widest mt-2">Google Meet Recording</span>
            </div>
        </section>

        <!-- Navigation Tabs -->
        <section class="border-b border-brand-border/60 flex gap-6">
            <button onclick="switchTab('meetings')" id="tab-btn-meetings" class="tab-btn pb-3 text-xs font-black tracking-widest uppercase border-b-2 border-transparent transition-all active">
                📅 Sync Calls & Takeaways
            </button>
            <button onclick="switchTab('tasks')" id="tab-btn-tasks" class="tab-btn pb-3 text-xs font-black tracking-widest uppercase border-b-2 border-transparent transition-all">
                📋 Action Item Tracker
            </button>
            <button onclick="switchTab('chats')" id="tab-btn-chats" class="tab-btn pb-3 text-xs font-black tracking-widest uppercase border-b-2 border-transparent transition-all">
                💬 WhatsApp Chat Tracker
            </button>
        </section>

        <!-- Tab Section: Meetings -->
        <section id="tab-meetings" class="tab-content grid grid-cols-1 lg:grid-cols-4 gap-6">
            <!-- Left Side: Meeting List -->
            <div class="lg:col-span-1 flex flex-col gap-3">
                <span class="text-[10px] font-black tracking-widest uppercase text-zinc-500 mb-1">Select Sync Call</span>
                <div id="meetings-list-container" class="flex flex-col gap-2">
                    <!-- Dynamic meeting buttons -->
                </div>
            </div>

            <!-- Right Side: Meeting Details -->
            <div class="lg:col-span-3 flex flex-col gap-6">
                <!-- Heading -->
                <div class="glass-panel p-6 rounded-lg flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                        <h2 id="active-call-title" class="text-lg font-outfit font-black text-white uppercase tracking-tight">Call Title</h2>
                        <span id="active-call-filename" class="text-[10px] text-zinc-500 font-mono mt-1 block">Filename</span>
                    </div>
                    <a id="active-call-video" href="#" target="_blank" class="bg-brand-lime hover:bg-brand-lime/90 text-black text-[9px] font-black tracking-wider uppercase py-2.5 px-4 rounded transition-all hover:scale-[1.02] flex items-center gap-2">
                        <span>▶ VIEW FATHOM RECORDING</span>
                    </a>
                </div>

                <!-- Call Purpose & Key Takeaways -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Purpose -->
                    <div class="glass-panel p-6 rounded-lg">
                        <span class="text-[9px] font-black tracking-widest uppercase text-brand-cyan mb-3 block">Meeting Purpose</span>
                        <p id="active-call-purpose" class="text-sm text-zinc-300 leading-relaxed italic">No purpose logged.</p>
                    </div>

                    <!-- Takeaways -->
                    <div class="glass-panel p-6 rounded-lg">
                        <span class="text-[9px] font-black tracking-widest uppercase text-brand-lime mb-3 block">Key Takeaways</span>
                        <ul id="active-call-takeaways" class="text-xs text-zinc-300 flex flex-col gap-2 list-disc pl-4">
                            <!-- Injected -->
                        </ul>
                    </div>
                </div>

                <!-- Topics Details -->
                <div class="glass-panel p-6 rounded-lg">
                    <span class="text-[9px] font-black tracking-widest uppercase text-zinc-400 mb-4 block">Topics & Discussions</span>
                    <div id="active-call-topics" class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <!-- Injected -->
                    </div>
                </div>

                <!-- Meeting Transcript -->
                <div class="glass-panel p-6 rounded-lg flex flex-col gap-4">
                    <div class="flex justify-between items-center border-b border-brand-border/40 pb-3">
                        <span class="text-[9px] font-black tracking-widest uppercase text-zinc-400">Searchable Transcript</span>
                        <div class="max-w-xs w-full">
                            <input type="text" id="transcript-search" oninput="handleTranscriptSearch()" placeholder="FILTER TRANSCRIPT..." class="w-full bg-zinc-950 border border-brand-border text-white text-[10px] p-2 outline-none focus:border-brand-lime transition-all rounded shadow-inner uppercase">
                        </div>
                    </div>
                    
                    <div id="active-call-transcript" class="flex flex-col gap-3 max-h-[400px] overflow-y-auto pr-2">
                        <!-- Dialogue timeline items -->
                    </div>
                </div>
            </div>
        </section>

        <!-- Tab Section: Task Tracker -->
        <section id="tab-tasks" class="tab-content hidden flex flex-col gap-6">
            <!-- Task Stats Dashboard -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="glass-panel p-4 rounded-lg flex flex-col justify-between">
                    <span class="text-[9px] font-black tracking-widest uppercase text-zinc-400">Total Tasks</span>
                    <span id="board-total-tasks" class="text-2xl font-outfit font-black text-white mt-2">0</span>
                </div>
                <div class="glass-panel p-4 rounded-lg flex flex-col justify-between border-l-2 border-brand-lime">
                    <span class="text-[9px] font-black tracking-widest uppercase text-brand-lime">Completed</span>
                    <span id="board-completed-tasks" class="text-2xl font-outfit font-black text-brand-lime mt-2">0</span>
                </div>
                <div class="glass-panel p-4 rounded-lg flex flex-col justify-between border-l-2 border-amber-500">
                    <span class="text-[9px] font-black tracking-widest uppercase text-amber-500">Yet to be Done</span>
                    <span id="board-pending-tasks" class="text-2xl font-outfit font-black text-amber-500 mt-2">0</span>
                </div>
                <div class="glass-panel p-4 rounded-lg flex flex-col justify-between border-l-2 border-brand-cyan">
                    <span class="text-[9px] font-black tracking-widest uppercase text-brand-cyan">Nate's Pending</span>
                    <span id="board-nathan-pending" class="text-2xl font-outfit font-black text-brand-cyan mt-2">0</span>
                </div>
            </div>

            <!-- Board Controls & Search -->
            <div class="glass-panel p-4 rounded-lg flex flex-col md:flex-row justify-between items-center gap-4">
                <div class="flex flex-wrap gap-2">
                    <button onclick="setTaskFilter('all')" id="task-filter-all" class="bg-brand-lime text-black font-extrabold text-[9px] uppercase tracking-wider py-2 px-4 rounded border border-brand-lime">Show All</button>
                    <button onclick="setTaskFilter('Nathan')" id="task-filter-nathan" class="bg-zinc-950 hover:bg-zinc-900 border border-brand-border text-zinc-400 font-extrabold text-[9px] uppercase tracking-wider py-2 px-4 rounded transition-all">Nate's Tasks</button>
                    <button onclick="setTaskFilter('Shopifydevstudio')" id="task-filter-studio" class="bg-zinc-950 hover:bg-zinc-900 border border-brand-border text-zinc-400 font-extrabold text-[9px] uppercase tracking-wider py-2 px-4 rounded transition-all">Studio Tasks</button>
                </div>
                
                <div class="flex items-center gap-4 w-full md:w-auto">
                    <div class="relative w-full md:w-64">
                        <input type="text" id="task-search" oninput="renderTasks()" placeholder="SEARCH TASKS..." class="w-full bg-zinc-950 border border-brand-border text-white text-[10px] p-2 outline-none focus:border-brand-lime transition-all rounded uppercase shadow-inner">
                    </div>
                </div>
            </div>

            <!-- Two-Column Kanban Layout -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Column 1: Yet to be Done -->
                <div class="flex flex-col gap-4">
                    <div class="flex justify-between items-center border-b border-brand-border pb-2">
                        <div class="flex items-center gap-2">
                            <span class="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_8px_#F59E0B]"></span>
                            <h3 class="text-sm font-outfit font-black tracking-tight text-white uppercase">YET TO BE DONE</h3>
                        </div>
                        <span id="pending-count-badge" class="bg-amber-500/10 text-amber-500 border border-amber-500/20 text-[9px] font-black px-2 py-0.5 rounded">0 Tasks</span>
                    </div>
                    
                    <div id="pending-tasks-list" class="flex flex-col gap-3 min-h-[300px]">
                        <!-- Dynamic pending task cards -->
                    </div>
                </div>

                <!-- Column 2: Completed -->
                <div class="flex flex-col gap-4">
                    <div class="flex justify-between items-center border-b border-brand-border pb-2">
                        <div class="flex items-center gap-2">
                            <span class="w-2 h-2 rounded-full bg-brand-lime shadow-[0_0_8px_#C4F101]"></span>
                            <h3 class="text-sm font-outfit font-black tracking-tight text-white uppercase">COMPLETED TASKS</h3>
                        </div>
                        <span id="completed-count-badge" class="bg-brand-lime/10 text-brand-lime border border-brand-lime/20 text-[9px] font-black px-2 py-0.5 rounded">0 Tasks</span>
                    </div>
                    
                    <div id="completed-tasks-list" class="flex flex-col gap-3 min-h-[300px]">
                        <!-- Dynamic completed task cards -->
                    </div>
                </div>
            </div>
        </section>

        <!-- Tab Section: WhatsApp Chat logs -->
        <section id="tab-chats" class="tab-content hidden grid grid-cols-1 lg:grid-cols-4 gap-6">
            <!-- Left Panel: Chat Meta -->
            <div class="lg:col-span-1 glass-panel p-5 rounded-lg flex flex-col gap-4 h-fit">
                <div class="border-b border-brand-border/40 pb-3">
                    <h3 class="text-sm font-outfit font-black text-white uppercase tracking-tight">WhatsApp Track</h3>
                    <span class="text-[9px] text-zinc-500 font-extrabold uppercase mt-1 block">Nathan Ellite &lt;&gt; Studio</span>
                </div>
                <p class="text-xs text-zinc-400 leading-relaxed">
                    This timeline tracks historical chat statements from the WhatsApp backup file, helping quickly resolve past design agreements, duplicate queries, and instructions.
                </p>
                <div class="flex flex-col gap-2">
                    <span class="text-[9px] font-black tracking-widest uppercase text-zinc-500">Fast Filters</span>
                    <button onclick="filterChatBySender('all')" id="chat-filter-all" class="bg-brand-lime text-black font-extrabold text-[9px] uppercase tracking-wider py-2 px-3 rounded text-left border border-brand-lime">Show All Messages</button>
                    <button onclick="filterChatBySender('Nathan')" id="chat-filter-nathan" class="bg-zinc-950 hover:bg-zinc-900 border border-brand-border text-zinc-400 font-extrabold text-[9px] uppercase tracking-wider py-2 px-3 rounded text-left transition-all">Filter by Nathan</button>
                    <button onclick="filterChatBySender('Shopifydevstudio')" id="chat-filter-studio" class="bg-zinc-950 hover:bg-zinc-900 border border-brand-border text-zinc-400 font-extrabold text-[9px] uppercase tracking-wider py-2 px-3 rounded text-left transition-all">Filter by Studio</button>
                </div>
            </div>

            <!-- Right Panel: Chat List -->
            <div class="lg:col-span-3 glass-panel rounded-lg flex flex-col h-[650px] overflow-hidden">
                <!-- Search -->
                <div class="p-4 border-b border-brand-border/40 flex justify-between items-center bg-black/20">
                    <span class="text-[10px] font-black tracking-widest text-zinc-400 uppercase">Search Chat Statements</span>
                    <div class="max-w-xs w-full">
                        <input type="text" id="chat-search" oninput="handleChatSearch()" placeholder="FILTER LOGS..." class="w-full bg-zinc-950 border border-brand-border text-white text-[10px] p-2.5 outline-none focus:border-brand-lime transition-all rounded shadow-inner uppercase">
                    </div>
                </div>

                <!-- Chat Feed -->
                <div id="chat-feed-container" class="flex-grow p-6 overflow-y-auto flex flex-col gap-4 bg-zinc-950/20">
                    <!-- Injected chat bubbles -->
                </div>
            </div>
        </section>
        
    </main>

    <!-- Footer -->
    <footer class="p-8 border-t border-brand-border bg-brand-dark flex flex-col md:flex-row justify-between items-center gap-4 text-[9px] font-extrabold text-zinc-500 uppercase tracking-widest mt-10">
        <div>&copy; 2026 ELITE TI PORTFOLIO MANAGEMENT</div>
        <div class="flex gap-4">
            <span class="text-brand-lime">PORTAL STATUS: STABLE ONLINE</span>
        </div>
        <div>SHOPIFYDEVSTUDIO &copy; CLIENT PORTAL MANAGEMENT</div>
    </footer>

    <!-- JSON DATA INJECTION -->
    <script>
        const meetingsData = %MEETINGS_DATA%;
        const chatLogsData = %CHAT_DATA%;
        
        let activeMeetingIndex = 0;
        let activeTab = 'meetings';
        let currentTaskFilter = 'all';
        let currentChatFilter = 'all';
        
        // Switch tab views
        function switchTab(tabName) {
            activeTab = tabName;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.add('hidden'));
            
            document.getElementById(`tab-btn-${tabName}`).classList.add('active');
            document.getElementById(`tab-${tabName}`).classList.remove('hidden');
        }

        // Initialize meeting buttons and content
        function initMeetings() {
            const btnContainer = document.getElementById('meetings-list-container');
            btnContainer.innerHTML = '';
            
            meetingsData.forEach((meet, index) => {
                const active = index === activeMeetingIndex;
                const btn = document.createElement('button');
                btn.onclick = () => selectMeeting(index);
                btn.className = `w-full text-left p-4 rounded border transition-all flex flex-col gap-1 ${active ? 'bg-brand-lime/10 border-brand-lime text-brand-lime glow-lime' : 'bg-brand-card/40 border-brand-border hover:border-zinc-700 text-zinc-400'}`;
                btn.innerHTML = `
                    <span class="text-[10px] font-black uppercase tracking-wider ${active ? 'text-brand-lime' : 'text-white'}">${meet.title}</span>
                    <span class="text-[8px] font-mono tracking-wide text-zinc-500 mt-1">${meet.filename}</span>
                `;
                btnContainer.appendChild(btn);
            });
            
            renderActiveMeeting();
        }

        function selectMeeting(index) {
            activeMeetingIndex = index;
            initMeetings();
        }

        function renderActiveMeeting() {
            const meet = meetingsData[activeMeetingIndex];
            if (!meet) return;
            
            document.getElementById('active-call-title').textContent = meet.title;
            document.getElementById('active-call-filename').textContent = meet.filename;
            
            // Video link
            const videoBtn = document.getElementById('active-call-video');
            if (meet.recording_url) {
                videoBtn.href = meet.recording_url;
                videoBtn.classList.remove('opacity-50', 'pointer-events-none');
            } else {
                videoBtn.href = '#';
                videoBtn.classList.add('opacity-50', 'pointer-events-none');
            }
            
            // Purpose
            document.getElementById('active-call-purpose').textContent = meet.purpose || 'No purpose logged.';
            
            // Takeaways
            const takeawaysList = document.getElementById('active-call-takeaways');
            takeawaysList.innerHTML = '';
            if (meet.takeaways && meet.takeaways.length > 0) {
                meet.takeaways.forEach(tk => {
                    const li = document.createElement('li');
                    li.className = "py-0.5";
                    li.textContent = tk;
                    takeawaysList.appendChild(li);
                });
            } else {
                takeawaysList.innerHTML = '<li class="italic text-zinc-500 list-none">No takeaways logged.</li>';
            }
            
            // Topics
            const topicsGrid = document.getElementById('active-call-topics');
            topicsGrid.innerHTML = '';
            if (meet.topics && meet.topics.length > 0) {
                meet.topics.forEach(tp => {
                    const el = document.createElement('div');
                    el.className = "bg-black/30 border border-brand-border/40 p-3 rounded-md text-[11px] font-semibold text-zinc-300 uppercase tracking-wide flex items-center gap-2";
                    el.innerHTML = `<span class="w-1.5 h-1.5 bg-brand-cyan rounded-full"></span> <span>${tp}</span>`;
                    topicsGrid.appendChild(el);
                });
            } else {
                topicsGrid.innerHTML = '<p class="italic text-zinc-500 text-[11px]">No topics logged.</p>';
            }
            
            // Transcript
            renderTranscript(meet.transcript);
        }

        function renderTranscript(items) {
            const container = document.getElementById('active-call-transcript');
            container.innerHTML = '';
            
            if (!items || items.length === 0) {
                container.innerHTML = '<p class="italic text-zinc-500 text-xs py-4 uppercase text-center tracking-widest font-black">No transcript logged for this call.</p>';
                return;
            }
            
            items.forEach(tr => {
                const isNathan = tr.speaker === 'Nathan';
                const item = document.createElement('div');
                item.className = `flex flex-col gap-1 p-3.5 rounded border max-w-2xl ${isNathan ? 'bg-[#17241A]/50 border-green-500/20 mr-auto' : 'bg-[#1D1D22]/60 border-zinc-800 ml-auto'}`;
                
                const initials = isNathan ? 'NB' : 'SD';
                const avatarBg = isNathan ? 'bg-green-700 text-white font-bold' : 'bg-brand-lime text-black font-extrabold';
                
                item.innerHTML = `
                    <div class="flex items-center gap-2 mb-1.5 border-b border-brand-border/20 pb-1 w-full justify-between">
                        <div class="flex items-center gap-2">
                            <span class="w-5 h-5 rounded-full flex items-center justify-center text-[9px] ${avatarBg}">${initials}</span>
                            <span class="text-[9px] font-black uppercase text-zinc-300 tracking-wider">${tr.speaker === 'Nathan' ? 'Nathan Benoit' : 'Shopifydevstudio'}</span>
                        </div>
                        <span class="text-[9px] font-mono text-zinc-500 font-bold">${tr.timestamp}</span>
                    </div>
                    <p class="text-xs text-zinc-300 leading-relaxed font-medium">${tr.text}</p>
                `;
                container.appendChild(item);
            });
        }

        function handleTranscriptSearch() {
            const q = document.getElementById('transcript-search').value.toLowerCase();
            const meet = meetingsData[activeMeetingIndex];
            if (!meet || !meet.transcript) return;
            
            const filtered = meet.transcript.filter(tr => tr.text.toLowerCase().includes(q) || tr.speaker.toLowerCase().includes(q));
            renderTranscript(filtered);
        }

        // Action Items state manager
        function getTaskStateKey(desc) {
            return `elite_ti_task_` + desc.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
        }

        function toggleTaskStatus(chk, desc) {
            const key = getTaskStateKey(desc);
            localStorage.setItem(key, chk.checked ? 'completed' : 'pending');
            
            renderTasks();
            updateGlobalStats();
        }

        function setTaskFilter(filter) {
            currentTaskFilter = filter;
            document.querySelectorAll('#tab-tasks button').forEach(b => {
                b.className = "bg-zinc-950 hover:bg-zinc-900 border border-brand-border text-zinc-400 font-extrabold text-[9px] uppercase tracking-wider py-2 px-4 rounded transition-all";
            });
            
            const activeId = filter === 'all' ? 'task-filter-all' : (filter === 'Nathan' ? 'task-filter-nathan' : 'task-filter-studio');
            document.getElementById(activeId).className = "bg-brand-lime text-black font-extrabold text-[9px] uppercase tracking-wider py-2 px-4 rounded border border-brand-lime";
            
            renderTasks();
        }

        function renderTasks() {
            const pendingList = document.getElementById('pending-tasks-list');
            const completedList = document.getElementById('completed-tasks-list');
            
            pendingList.innerHTML = '';
            completedList.innerHTML = '';
            
            const allTasks = [];
            meetingsData.forEach(meet => {
                if (meet.action_items) {
                    meet.action_items.forEach(task => {
                        allTasks.push(task);
                    });
                }
            });
            
            const searchQuery = document.getElementById('task-search').value.toLowerCase();
            let filteredTasks = allTasks;
            if (searchQuery) {
                filteredTasks = filteredTasks.filter(t => 
                    t.description.toLowerCase().includes(searchQuery) || 
                    t.owner.toLowerCase().includes(searchQuery) ||
                    t.source.toLowerCase().includes(searchQuery)
                );
            }
            
            filteredTasks = filteredTasks.filter(t => currentTaskFilter === 'all' || t.owner === currentTaskFilter);
            
            let pendingCount = 0;
            let completedCount = 0;
            let nathanPendingCount = 0;
            
            filteredTasks.forEach(task => {
                const key = getTaskStateKey(task.description);
                let isCompleted = task.initial_status === 'completed';
                const userOverride = localStorage.getItem(key);
                if (userOverride !== null) {
                    isCompleted = userOverride === 'completed';
                }
                
                if (isCompleted) {
                    completedCount++;
                } else {
                    pendingCount++;
                    if (task.owner === 'Nathan') {
                        nathanPendingCount++;
                    }
                }
                
                const card = document.createElement('div');
                card.className = `glass-panel p-4 rounded-lg flex flex-col gap-3 transition-all duration-300 hover:scale-[1.01] ${isCompleted ? 'opacity-65 hover:opacity-90 border-brand-lime/20 bg-brand-lime/[0.01]' : 'hover:border-zinc-600'}`;
                
                const badgeClass = task.owner === 'Nathan' ? 'border-brand-cyan/30 text-brand-cyan bg-brand-cyan/5' : 'border-brand-lime/30 text-brand-lime bg-brand-lime/5';
                const ownerHtml = `<span class="border px-2 py-0.5 font-black uppercase rounded text-[9px] tracking-wide ${badgeClass}">${task.owner === 'Nathan' ? 'Nathan' : 'Studio'}</span>`;
                
                const clipHtml = task.watch_url ? `
                    <a href="${task.watch_url}" target="_blank" class="text-brand-cyan hover:underline flex items-center gap-1">
                        <span>🎥 WATCH CLIP</span>
                    </a>
                ` : '';
                
                card.innerHTML = `
                    <div class="flex justify-between items-start gap-4">
                        <label class="flex items-start gap-3 cursor-pointer select-none flex-grow">
                            <input type="checkbox" onchange="toggleTaskStatus(this, '${task.description.replace(/'/g, "\\'")}')" ${isCompleted ? 'checked' : ''} class="mt-0.5 w-4 h-4 accent-brand-lime border-brand-border rounded cursor-pointer flex-shrink-0">
                            <span class="text-xs text-zinc-200 font-medium leading-relaxed ${isCompleted ? 'line-through text-zinc-500' : ''}">${task.description}</span>
                        </label>
                        <div class="flex-shrink-0">${ownerHtml}</div>
                    </div>
                    <div class="flex justify-between items-center border-t border-brand-border/40 pt-2 text-[8px] font-extrabold text-zinc-500 uppercase tracking-widest">
                        <div class="flex items-center gap-1.5 flex-grow mr-2 overflow-hidden">
                            <span>📂</span>
                            <span class="hover:text-zinc-300 transition-all font-mono truncate text-[8px] max-w-[200px]" title="${task.source}">${task.source}</span>
                        </div>
                        <div class="flex-shrink-0">${clipHtml}</div>
                    </div>
                `;
                
                if (isCompleted) {
                    completedList.appendChild(card);
                } else {
                    pendingList.appendChild(card);
                }
            });
            
            if (pendingCount === 0) {
                pendingList.innerHTML = `<div class="glass-panel p-8 text-center text-zinc-500 text-[10px] font-black uppercase tracking-widest rounded-lg border border-dashed border-brand-border">No Pending Tasks</div>`;
            }
            if (completedCount === 0) {
                completedList.innerHTML = `<div class="glass-panel p-8 text-center text-zinc-500 text-[10px] font-black uppercase tracking-widest rounded-lg border border-dashed border-brand-border">No Completed Tasks</div>`;
            }
            
            document.getElementById('pending-count-badge').textContent = `${pendingCount} Tasks`;
            document.getElementById('completed-count-badge').textContent = `${completedCount} Tasks`;
            
            document.getElementById('board-total-tasks').textContent = filteredTasks.length;
            document.getElementById('board-completed-tasks').textContent = completedCount;
            document.getElementById('board-pending-tasks').textContent = pendingCount;
            document.getElementById('board-nathan-pending').textContent = nathanPendingCount;
        }

        // WhatsApp Chat tab
        function filterChatBySender(sender) {
            currentChatFilter = sender;
            document.querySelectorAll('#tab-chats button').forEach(b => {
                b.className = "bg-zinc-950 hover:bg-zinc-900 border border-brand-border text-zinc-400 font-extrabold text-[9px] uppercase tracking-wider py-2 px-3 rounded text-left transition-all";
            });
            
            const activeId = sender === 'all' ? 'chat-filter-all' : (sender === 'Nathan' ? 'chat-filter-nathan' : 'chat-filter-studio');
            document.getElementById(activeId).className = "bg-brand-lime text-black font-extrabold text-[9px] uppercase tracking-wider py-2 px-3 rounded text-left border border-brand-lime";
            
            renderChatFeed();
        }

        function renderChatFeed(feed = chatLogsData) {
            const container = document.getElementById('chat-feed-container');
            container.innerHTML = '';
            
            const filtered = feed.filter(m => currentChatFilter === 'all' || m.sender === currentChatFilter);
            
            if (filtered.length === 0) {
                container.innerHTML = '<p class="italic text-zinc-500 text-xs py-10 uppercase text-center tracking-widest font-black">No Messages Found.</p>';
                return;
            }
            
            filtered.forEach(m => {
                const isNathan = m.sender === 'Nathan';
                const wrapper = document.createElement('div');
                wrapper.className = `flex w-full ${isNathan ? 'justify-start' : 'justify-end'}`;
                
                const initials = isNathan ? 'NB' : 'SD';
                const bubbleClass = isNathan ? 'msg-nathan rounded-tr-lg rounded-br-lg rounded-bl-lg' : 'msg-studio rounded-tl-lg rounded-bl-lg rounded-br-lg';
                
                wrapper.innerHTML = `
                    <div class="flex gap-2 max-w-xl items-start ${isNathan ? 'flex-row' : 'flex-row-reverse'}">
                        <span class="w-6 h-6 rounded-full flex items-center justify-center text-[9px] flex-shrink-0 ${isNathan ? 'bg-green-700 text-white font-bold' : 'bg-brand-lime text-black font-extrabold'}">${initials}</span>
                        <div class="flex flex-col gap-1 p-3.5 shadow-md ${bubbleClass}">
                            <div class="flex justify-between items-center gap-6 border-b border-white/[0.04] pb-1 mb-1">
                                <span class="text-[9px] font-black uppercase text-zinc-400 tracking-wider">${isNathan ? 'Nathan Benoit' : 'Shopifydevstudio'}</span>
                                <span class="text-[8px] text-zinc-500 font-mono font-bold">${m.date} ${m.time}</span>
                            </div>
                            <p class="text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed">${m.text}</p>
                        </div>
                    </div>
                `;
                container.appendChild(wrapper);
            });
            
            setTimeout(() => container.scrollTop = container.scrollHeight, 100);
        }

        function handleChatSearch() {
            const q = document.getElementById('chat-search').value.toLowerCase();
            const filtered = chatLogsData.filter(m => m.text.toLowerCase().includes(q) || m.sender.toLowerCase().includes(q));
            renderChatFeed(filtered);
        }

        // Global stats calculator
        function updateGlobalStats() {
            const allTasks = [];
            meetingsData.forEach(meet => {
                if (meet.action_items) {
                    meet.action_items.forEach(task => {
                        allTasks.push(task);
                    });
                }
            });
            
            const total = allTasks.length;
            let completed = 0;
            allTasks.forEach(t => {
                const key = getTaskStateKey(t.description);
                let isCompleted = t.initial_status === 'completed';
                const userOverride = localStorage.getItem(key);
                if (userOverride !== null) {
                    isCompleted = userOverride === 'completed';
                }
                if (isCompleted) {
                    completed++;
                }
            });
            
            const pct = total > 0 ? ((completed / total) * 100).toFixed(1) : '0.0';
            
            document.getElementById('stat-progress-pct').textContent = `${pct}%`;
            document.getElementById('stat-progress-bar').style.width = `${pct}%`;
            document.getElementById('stat-progress-ratio').textContent = `${completed}/${total} Completed`;
            
            document.getElementById('stat-total-meetings').textContent = meetingsData.length;
            document.getElementById('stat-total-chats').textContent = chatLogsData.length;
            
            const recent = meetingsData[0];
            const recentBtn = document.getElementById('stat-recording-btn');
            if (recent && recent.recording_url) {
                recentBtn.href = recent.recording_url;
                recentBtn.classList.remove('opacity-50', 'pointer-events-none');
            } else {
                recentBtn.href = '#';
                recentBtn.classList.add('opacity-50', 'pointer-events-none');
            }
        }

        // Initialize portal
        function init() {
            initMeetings();
            renderTasks();
            renderChatFeed();
            updateGlobalStats();
        }

        init();
    </script>
</body>
</html>
"""
    
    # Inject JSON blocks
    serialized_meetings = json.dumps(meetings, ensure_ascii=False)
    serialized_chats = json.dumps(chat_logs, ensure_ascii=False)
    
    html_content_portal = html_template.replace("%MEETINGS_DATA%", serialized_meetings).replace("%CHAT_DATA%", serialized_chats)
    html_content_project = html_content_portal.replace("../Photo-organising-portal/visual_audit_sheet.html", "Photo-organising-portal/visual_audit_sheet.html")
    
    with open(OUTPUT_HTML_PORTAL, 'w', encoding='utf-8') as f:
        f.write(html_content_portal)
        
    with open(OUTPUT_HTML_PROJECT, 'w', encoding='utf-8') as f:
        f.write(html_content_project)
        
    print(f"🎉 Success! Client Progress Portal generated at {OUTPUT_HTML_PORTAL} and {OUTPUT_HTML_PROJECT}")

if __name__ == '__main__':
    generate_portal()
