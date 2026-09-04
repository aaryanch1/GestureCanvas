"""
AsBots — AI Senior Medical Assistant
=====================================
A Streamlit chat application powered by the Groq API that behaves as a senior,
evidence-based medical assistant. It answers ONLY with medically-established
information relevant to the user's query — no small talk, no off-topic
content, no speculation beyond established clinical evidence.

Run with:
    streamlit run asbots.py

Before running, install dependencies:
    pip install streamlit groq python-dotenv

The Groq API key is embedded as a fallback default below AND can be
overridden via a GROQ_API_KEY environment variable or a local .env file.
"""

import os
import time
import html
from datetime import datetime

import streamlit as st
from groq import Groq

# python-dotenv is optional — the app still works without it since a
# fallback API key is hardcoded below. If it's installed, it lets you
# override the key via a local .env file without editing this script.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ─────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────

# Fallback key so the app runs even with no .env file / no env var set.
# You can still override it by setting GROQ_API_KEY in your environment
# or in a .env file placed next to this script.
DEFAULT_GROQ_API_KEY = "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"

APP_NAME = "AsBots"
APP_TAGLINE = "Senior Medical Assistant · Evidence-Based Answers Only"

AVAILABLE_MODELS = {
    "GPT-OSS 120B (Recommended — most accurate)": "openai/gpt-oss-120b",
    "GPT-OSS 20B (Fastest)": "openai/gpt-oss-20b",
    "Qwen 3.6 27B (Alternative)": "qwen/qwen3.6-27b",
}

SYSTEM_PROMPT = """You are Dr. AsBots — a senior, board-certified attending physician \
acting as a professional medical information assistant.

STRICT RULES YOU MUST ALWAYS FOLLOW:
1. Respond ONLY with medically-proven, evidence-based information (established \
clinical guidelines, peer-reviewed consensus, standard-of-care practice). Never \
speculate, guess, or present unproven/alternative claims as fact.
2. Stay strictly on-topic to the medical question asked. Do NOT add greetings, \
small talk, filler, jokes, or unrelated content. No content outside the medical \
scope of the question.
3. If the user asks something that is NOT a medical/health question, politely \
decline in one sentence and state you only handle medical queries. Do not answer \
the non-medical part.
4. Always communicate like a senior doctor speaking to a patient or colleague: \
calm, precise, professional, and structured (use short headers or bullet points \
when it aids clarity — e.g. Overview, Likely Causes, Evidence-Based Management, \
When to Seek Immediate Care).
5. Never provide a definitive individual diagnosis or a specific prescription/dose \
for the user to self-administer without clinical evaluation. Instead, explain the \
established medical understanding, standard evidence-based management options, \
and clearly state that in-person evaluation by a licensed clinician is required \
for diagnosis, prescription, or treatment changes.
6. Always flag red-flag / emergency symptoms clearly and advise immediate \
emergency care (e.g. call local emergency services) when relevant.
7. Cite the general source of consensus when useful (e.g. "per WHO/CDC/major \
clinical guidelines") without fabricating specific studies or statistics you are \
not certain of.
8. Keep answers focused and free of padding — no unnecessary disclaimers repeated \
more than once, no restating the question, no filler conclusions.

You are not a replacement for an in-person licensed physician. You provide \
established medical knowledge in a professional, senior-doctor tone."""

EMERGENCY_NOTICE = (
    "⚠️ If this is a medical emergency (e.g. chest pain, severe bleeding, "
    "difficulty breathing, stroke symptoms, loss of consciousness), "
    "**stop and call your local emergency number immediately.**"
)


# ─────────────────────────────────────────────────────────────────────────
# PAGE SETUP
# ─────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title=f"{APP_NAME} — AI Medical Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
:root {
    --primary: #17b6c4;
    --primary-dark: #0e838e;
    --bg-app: #0b1416;
    --bg-card: #141f22;
    --bg-card-alt: #17262a;
    --border: #26393d;
    --text-main: #eef6f7;
    --text-dim: #a9bcc0;
}

/* Overall app background — force dark regardless of system theme */
.stApp {
    background: linear-gradient(180deg, #0b1416 0%, #0e1b1e 100%);
    color: var(--text-main);
}
html, body, [class*="css"] {
    color: var(--text-main) !important;
}

/* Header */
.asbots-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 22px;
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
    border-radius: 14px;
    margin-bottom: 18px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.45);
}
.asbots-header h1 {
    color: #ffffff;
    font-size: 26px;
    margin: 0;
    font-weight: 700;
    letter-spacing: 0.3px;
}
.asbots-header p {
    color: #eafcfd;
    margin: 0;
    font-size: 13.5px;
}
.asbots-header .icon {
    font-size: 34px;
}

/* Emergency banner */
.emergency-banner {
    background: #2a1512;
    border: 1px solid #7a3226;
    color: #ffb3a3;
    padding: 10px 16px;
    border-radius: 10px;
    font-size: 13.5px;
    margin-bottom: 16px;
}

/* Chat message bubbles */
[data-testid="stChatMessage"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 10px 12px;
    margin-bottom: 10px;
}
[data-testid="stChatMessage"] * {
    color: var(--text-main) !important;
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span {
    color: var(--text-main) !important;
    font-size: 15.5px;
    line-height: 1.55;
}
[data-testid="stChatMessage"] strong {
    color: #ffffff !important;
}
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3,
[data-testid="stChatMessage"] h4 {
    color: var(--primary) !important;
}
[data-testid="stChatMessage"] code {
    background: #0d1719;
    color: #7fe3ec;
    padding: 2px 5px;
    border-radius: 4px;
}

/* Chat input box */
[data-testid="stChatInput"] textarea {
    background: var(--bg-card) !important;
    color: var(--text-main) !important;
    border: 1px solid var(--border) !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-dim) !important;
    opacity: 1;
}
[data-testid="stChatInput"] {
    background: var(--bg-card) !important;
    border-top: 1px solid var(--border);
}

/* Main body text / markdown outside chat bubbles */
.stMarkdown, .stMarkdown p, .stMarkdown li {
    color: var(--text-main) !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #081113;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * {
    color: var(--text-main) !important;
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown p {
    color: var(--text-main) !important;
}
section[data-testid="stSidebar"] .stButton button {
    background: var(--primary);
    color: #04191b !important;
    border: none;
    border-radius: 8px;
    font-weight: 700;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: var(--primary-dark);
    color: #ffffff !important;
}
section[data-testid="stSidebar"] .stDownloadButton button {
    background: var(--bg-card-alt);
    color: var(--text-main) !important;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-weight: 600;
}
section[data-testid="stSidebar"] .stDownloadButton button:hover {
    border-color: var(--primary);
    color: var(--primary) !important;
}

/* Selectbox / slider widgets */
[data-baseweb="select"] > div {
    background: var(--bg-card) !important;
    color: var(--text-main) !important;
    border-color: var(--border) !important;
}
[data-baseweb="popover"] li {
    background: var(--bg-card) !important;
    color: var(--text-main) !important;
}
.stSlider [data-testid="stTickBarMin"],
.stSlider [data-testid="stTickBarMax"] {
    color: var(--text-dim) !important;
}

/* Footer disclaimer */
.disclaimer-box {
    font-size: 12px;
    color: var(--text-dim);
    border-top: 1px solid var(--border);
    padding-top: 10px;
    margin-top: 18px;
    line-height: 1.5;
}
.disclaimer-box b {
    color: var(--text-main);
}

/* Copy button styling inside messages */
.copy-btn {
    font-size: 12px;
    background: var(--bg-card-alt);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 4px 12px;
    cursor: pointer;
    color: var(--primary);
    margin-top: 8px;
    font-weight: 600;
}
.copy-btn:hover {
    background: #1d3236;
    border-color: var(--primary);
}

/* Error box contrast */
[data-testid="stAlert"] {
    background: var(--bg-card) !important;
    color: var(--text-main) !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────

st.markdown(
    f"""
    <div class="asbots-header">
        <div class="icon">🩺</div>
        <div>
            <h1>{APP_NAME}</h1>
            <p>{APP_TAGLINE}</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(f'<div class="emergency-banner">{EMERGENCY_NOTICE}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Settings")

    model_label = st.selectbox("Model", list(AVAILABLE_MODELS.keys()), index=0)
    model_id = AVAILABLE_MODELS[model_label]

    temperature = st.slider(
        "Response focus (lower = stricter / more conservative)",
        min_value=0.0, max_value=1.0, value=0.2, step=0.05,
    )

    st.markdown("---")
    st.markdown("### 💬 Conversation")

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    # Build a plain-text transcript for download
    def build_transcript() -> str:
        lines = [f"{APP_NAME} — Conversation Export", f"Generated: {datetime.now():%Y-%m-%d %H:%M}", "=" * 50, ""]
        for m in st.session_state.get("messages", []):
            role = "You" if m["role"] == "user" else "Dr. AsBots"
            lines.append(f"[{role}]")
            lines.append(m["content"])
            lines.append("")
        return "\n".join(lines)

    st.download_button(
        "💾 Save full conversation (.txt)",
        data=build_transcript(),
        file_name=f"asbots_conversation_{datetime.now():%Y%m%d_%H%M}.txt",
        mime="text/plain",
        use_container_width=True,
        disabled=len(st.session_state.get("messages", [])) == 0,
    )

    st.markdown("---")
    st.markdown(
        """
        <div class="disclaimer-box">
        <b>Disclaimer:</b> AsBots provides general, evidence-based medical
        information for educational purposes only. It does not diagnose,
        prescribe, or replace an in-person licensed physician. Always consult
        a qualified healthcare provider for personal medical decisions.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []  # list[{"role": "user"/"assistant", "content": str}]


# ─────────────────────────────────────────────────────────────────────────
# GROQ CLIENT
# ─────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_client():
    # Priority: Streamlit Cloud secrets  ->  local env var / .env  ->  hardcoded fallback
    api_key = None
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY", DEFAULT_GROQ_API_KEY)
    if not api_key:
        return None
    return Groq(api_key=api_key)


client = get_client()

if client is None:
    st.error(
        "**No Groq API key configured.** Set it in Streamlit Cloud under "
        "App settings → Secrets as `GROQ_API_KEY = \"...\"`, or set a "
        "`GROQ_API_KEY` environment variable / `.env` file locally."
    )
    st.stop()


# ─────────────────────────────────────────────────────────────────────────
# RENDER EXISTING CHAT
# ─────────────────────────────────────────────────────────────────────────

def render_copy_button(text: str, key: str):
    """Small JS-based copy-to-clipboard button (no external component needed)."""
    safe_text = html.escape(text).replace("`", "&#96;").replace("\n", "&#10;")
    st.markdown(
        f"""
        <button class="copy-btn" onclick="navigator.clipboard.writeText(`{safe_text}`);
            this.innerText='✅ Copied'; setTimeout(()=>this.innerText='📋 Copy response', 1500);">
            📋 Copy response
        </button>
        """,
        unsafe_allow_html=True,
    )


for i, msg in enumerate(st.session_state.messages):
    avatar = "🧑" if msg["role"] == "user" else "🩺"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            render_copy_button(msg["content"], key=f"copy_{i}")


# ─────────────────────────────────────────────────────────────────────────
# CHAT INPUT
# ─────────────────────────────────────────────────────────────────────────

user_prompt = st.chat_input("Describe your medical question or symptom...")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_prompt)

    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    api_messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    with st.chat_message("assistant", avatar="🩺"):
        placeholder = st.empty()
        full_response = ""
        try:
            stream = client.chat.completions.create(
                model=model_id,
                messages=api_messages,
                temperature=temperature,
                max_tokens=1200,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                full_response += delta
                placeholder.markdown(full_response + "▌")
                time.sleep(0.005)
            placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"⚠️ Error contacting Groq API: {e}"
            placeholder.markdown(full_response)

        render_copy_button(full_response, key=f"copy_live_{len(st.session_state.messages)}")

    st.session_state.messages.append({"role": "assistant", "content": full_response})