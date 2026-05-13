import streamlit as st
import requests
import os
from datetime import datetime

# ─── Config ──────────────────────────────────────────────────────────────────

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="TailorTalk — Drive AI",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Styling ─────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

/* Hide default streamlit bits */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* App background */
.stApp {
    background: linear-gradient(135deg, #0a0a0f 0%, #111827 50%, #0d1117 100%);
    min-height: 100vh;
}

/* ── Hero header ── */
.hero-header {
    text-align: center;
    padding: 2rem 1rem 1rem;
    margin-bottom: 1.5rem;
}
.hero-header .logo {
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(135deg, #6ee7f7 0%, #a78bfa 50%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-header .tagline {
    color: #64748b;
    font-family: 'DM Mono', monospace;
    font-size: 0.85rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 0.3rem;
}

/* ── Chat container ── */
.chat-wrapper {
    max-width: 860px;
    margin: 0 auto;
}

/* ── Message bubbles ── */
.msg-user {
    display: flex;
    justify-content: flex-end;
    margin: 0.75rem 0;
}
.msg-user .bubble {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    padding: 0.75rem 1.1rem;
    border-radius: 18px 18px 4px 18px;
    max-width: 70%;
    font-size: 0.95rem;
    line-height: 1.5;
    box-shadow: 0 4px 20px rgba(99,102,241,0.35);
}

.msg-assistant {
    display: flex;
    justify-content: flex-start;
    margin: 0.75rem 0;
    align-items: flex-start;
    gap: 0.6rem;
}
.msg-assistant .avatar {
    width: 34px;
    height: 34px;
    background: linear-gradient(135deg, #6ee7f7, #a78bfa);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    box-shadow: 0 0 12px rgba(110,231,247,0.3);
}
.msg-assistant .bubble {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    color: #e2e8f0;
    padding: 0.75rem 1.1rem;
    border-radius: 4px 18px 18px 18px;
    max-width: 75%;
    font-size: 0.95rem;
    line-height: 1.6;
    backdrop-filter: blur(10px);
}

/* ── File cards ── */
.files-section {
    margin-top: 1rem;
    padding: 0.85rem 1.1rem;
    background: rgba(99,102,241,0.06);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 12px;
    max-width: 75%;
    margin-left: 52px;
}
.files-section .files-header {
    color: #a78bfa;
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
    font-weight: 500;
}
.file-card {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 0.7rem;
    margin: 0.3rem 0;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    text-decoration: none;
    transition: all 0.2s ease;
    cursor: pointer;
}
.file-card:hover {
    background: rgba(99,102,241,0.12);
    border-color: rgba(99,102,241,0.4);
    transform: translateX(2px);
}
.file-card .file-icon { font-size: 1.1rem; }
.file-card .file-info { flex: 1; min-width: 0; }
.file-card .file-name {
    color: #e2e8f0;
    font-size: 0.88rem;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.file-card .file-meta {
    color: #64748b;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    margin-top: 1px;
}
.file-card .file-badge {
    background: rgba(99,102,241,0.2);
    color: #a78bfa;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    padding: 2px 6px;
    border-radius: 4px;
    white-space: nowrap;
    border: 1px solid rgba(99,102,241,0.3);
}

/* ── Input area ── */
.input-area {
    position: sticky;
    bottom: 0;
    background: linear-gradient(to top, #0a0a0f 80%, transparent);
    padding: 1rem 0 0.5rem;
    margin-top: 1rem;
}

/* Streamlit input override */
.stTextInput input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.7rem 1rem !important;
    transition: border-color 0.2s;
}
.stTextInput input:focus {
    border-color: rgba(99,102,241,0.6) !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important;
}

/* Button */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.4rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.35) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.5) !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(0,0,0,0.4) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] * {
    color: #94a3b8 !important;
}

/* Divider */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* Spinner */
.stSpinner > div { border-top-color: #6366f1 !important; }

/* Suggestion chips */
.chip-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.5rem 0 1rem; }
.chip {
    background: rgba(99,102,241,0.1);
    border: 1px solid rgba(99,102,241,0.25);
    color: #a78bfa;
    padding: 0.3rem 0.75rem;
    border-radius: 20px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.15s;
    font-family: 'DM Mono', monospace;
}
.chip:hover {
    background: rgba(99,102,241,0.2);
    border-color: rgba(99,102,241,0.5);
}
</style>
""", unsafe_allow_html=True)


# ─── Helper functions ─────────────────────────────────────────────────────────

def get_file_icon(mime_type: str) -> str:
    icons = {
        "application/pdf": "📄",
        "application/vnd.google-apps.document": "📝",
        "application/vnd.google-apps.spreadsheet": "📊",
        "application/vnd.google-apps.presentation": "📑",
        "image/jpeg": "🖼️",
        "image/png": "🖼️",
        "text/plain": "📃",
        "text/csv": "📋",
        "application/vnd.google-apps.folder": "📁",
    }
    return icons.get(mime_type, "📎")


def format_date(iso_string: str) -> str:
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return iso_string[:10]


def send_message(user_msg: str) -> dict:
    try:
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[:-1]  # exclude the message just added
        ]
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"message": user_msg, "history": history},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {
            "response": "⚠️ Cannot connect to the backend server. Please ensure it's running at `" + BACKEND_URL + "`.",
            "files": [],
        }
    except Exception as e:
        return {"response": f"⚠️ Error: {str(e)}", "files": []}


def render_file_cards(files: list):
    if not files:
        return
    html = '<div class="files-section">'
    html += f'<div class="files-header">📂 {len(files)} file{"s" if len(files) != 1 else ""} found</div>'
    for f in files:
        icon = get_file_icon(f.get("mimeType", ""))
        name = f.get("name", "Untitled")
        ftype = f.get("friendlyType", "File")
        date = format_date(f.get("modifiedTime", ""))
        link = f.get("webViewLink", "#")
        meta = f"{ftype} · Modified {date}" if date else ftype
        html += f"""
        <a class="file-card" href="{link}" target="_blank">
            <span class="file-icon">{icon}</span>
            <div class="file-info">
                <div class="file-name">{name}</div>
                <div class="file-meta">{meta}</div>
            </div>
            <span class="file-badge">Open ↗</span>
        </a>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ─── Session State ────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_input" not in st.session_state:
    st.session_state.pending_input = ""


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🗂️ TailorTalk")
    st.markdown("**Google Drive AI Assistant**")
    st.markdown("---")

    st.markdown("**Search Capabilities**")
    st.markdown("""
- 🔍 Search by file name
- 📁 Filter by file type
- 📝 Search inside content
- 📅 Filter by date
- 🔗 Combined queries
    """)

    st.markdown("---")
    st.markdown("**Try asking:**")
    examples = [
        "Show me all PDF files",
        "Find spreadsheets about budget",
        "Any images uploaded this week?",
        "Search for files containing 'invoice'",
        "List all Google Docs",
        "Find files modified after May 2025",
    ]
    for ex in examples:
        st.markdown(f"• *{ex}*")

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_input = ""
        st.rerun()

    # Backend health
    st.markdown("---")
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if r.status_code == 200:
            st.success("Backend: Connected ✓")
        else:
            st.error("Backend: Error")
    except Exception:
        st.error("Backend: Offline")


# ─── Main UI ─────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero-header">
    <div class="logo">🗂️ TailorTalk</div>
    <div class="tagline">AI-Powered Google Drive Discovery</div>
</div>
""", unsafe_allow_html=True)

# Quick-start chips (only show when chat is empty)
if not st.session_state.messages:
    st.markdown('<div class="chip-row">', unsafe_allow_html=True)
    chip_suggestions = [
        "Show all PDFs",
        "Find budget sheets",
        "Search for images",
        "Docs from this month",
        "Files about marketing",
    ]
    cols = st.columns(len(chip_suggestions))
    for i, suggestion in enumerate(chip_suggestions):
        with cols[i]:
            if st.button(suggestion, key=f"chip_{i}"):
                st.session_state.pending_input = suggestion
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; color:#475569; font-family:'DM Mono',monospace; font-size:0.8rem; margin: 3rem 0 2rem;">
        Ask me anything about your Google Drive files →
    </div>
    """, unsafe_allow_html=True)

# ─── Chat history ─────────────────────────────────────────────────────────────

chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="msg-user">
                <div class="bubble">{msg["content"]}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="msg-assistant">
                <div class="avatar">✦</div>
                <div class="bubble">{msg["content"]}</div>
            </div>""", unsafe_allow_html=True)
            if msg.get("files"):
                render_file_cards(msg["files"])


# ─── Input ────────────────────────────────────────────────────────────────────

st.markdown("---")
col1, col2 = st.columns([6, 1])

with col1:
    default_val = st.session_state.pending_input
    user_input = st.text_input(
        label="Message",
        value=default_val,
        placeholder="Ask about your Drive files… e.g. 'Find all PDFs about Q4 reports'",
        label_visibility="collapsed",
        key="chat_input",
    )

with col2:
    send_clicked = st.button("Send ➤", use_container_width=True)

# Handle pending input from chips
if st.session_state.pending_input and st.session_state.pending_input != user_input:
    user_input = st.session_state.pending_input

# Process message
if (send_clicked or st.session_state.get("_enter_pressed")) and user_input.strip():
    st.session_state.pending_input = ""
    user_text = user_input.strip()

    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_text})

    # Get agent response
    with st.spinner("Searching your Drive…"):
        result = send_message(user_text)

    # Add assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["response"],
        "files": result.get("files", []),
    })

    st.rerun()

# Keyboard shortcut hint
st.markdown(
    '<div style="text-align:right;color:#334155;font-size:0.72rem;font-family:\'DM Mono\',monospace;margin-top:0.3rem;">'
    "Click Send or press the button to search"
    "</div>",
    unsafe_allow_html=True,
)
