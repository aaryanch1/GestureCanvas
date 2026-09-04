"""
Rule-Based Chatbot — Streamlit UI
Run with: streamlit run chatbot_app.py
"""

import streamlit as st
import random
from datetime import datetime

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="ChatBot",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------------------------
# CUSTOM CSS — clean, professional chat UI
# ----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Overall app background */
    .stApp {
        background: linear-gradient(180deg, #f7f8fc 0%, #eef1f8 100%);
    }

    /* Header */
    .chat-header {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    .chat-header h1 {
        font-size: 1.8rem;
        margin-bottom: 0.1rem;
        color: #1f2430;
    }
    .chat-header p {
        color: #6b7280;
        font-size: 0.95rem;
    }

    /* Chat bubbles */
    .user-bubble {
        background: #4f46e5;
        color: white;
        padding: 10px 16px;
        border-radius: 18px 18px 4px 18px;
        max-width: 75%;
        margin: 6px 0 6px auto;
        text-align: right;
        box-shadow: 0 2px 6px rgba(79,70,229,0.25);
    }
    .bot-bubble {
        background: white;
        color: #1f2430;
        padding: 10px 16px;
        border-radius: 18px 18px 18px 4px;
        max-width: 75%;
        margin: 6px auto 6px 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        border: 1px solid #eceef3;
    }
    .bubble-row {
        display: flex;
        flex-direction: column;
    }
    .timestamp {
        font-size: 0.7rem;
        color: #9ca3af;
        margin: 0 4px 10px 4px;
    }

    /* Sidebar tweaks */
    section[data-testid="stSidebar"] {
        background: #1f2430;
    }
    section[data-testid="stSidebar"] * {
        color: #e5e7eb !important;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 10px;
        border: none;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# CHATBOT LOGIC (same rule-based engine, wrapped for Streamlit)
# ----------------------------------------------------------------------------
BOT_NAME = "DevBot"

EXIT_COMMANDS = {"exit", "quit", "bye", "goodbye", "see you", "stop"}

KNOWLEDGE_BASE = {
    "greeting": {
        "keywords": ["hi", "hello", "hey", "greetings", "good morning", "good evening"],
        "responses": [
            f"Hello! I'm {BOT_NAME}. How can I help you today?",
            "Hi there! What's on your mind?",
            "Hey! Good to see you."
        ]
    },
    "how_are_you": {
        "keywords": ["how are you", "how's it going", "how do you do"],
        "responses": [
            "I'm just lines of code, but I'm running smoothly! How about you?",
            "Doing great, thanks for asking!"
        ]
    },
    "name": {
        "keywords": ["your name", "who are you"],
        "responses": [f"I'm {BOT_NAME}, your friendly rule-based chatbot."]
    },
    "thanks": {
        "keywords": ["thank you", "thanks", "appreciate it"],
        "responses": ["You're welcome!", "Anytime!", "Glad I could help."]
    },
    "help": {
        "keywords": ["help", "what can you do", "options"],
        "responses": [
            "I can chat about greetings, how you're doing, my name, "
            "or just have small talk. Type 'exit' anytime to leave."
        ]
    },
    "weather": {
        "keywords": ["weather", "raining", "sunny", "temperature"],
        "responses": ["I can't check live weather, but I hope it's nice where you are!"]
    }
}

FALLBACK_RESPONSES = [
    "I'm not sure I understand. Could you rephrase that?",
    "Hmm, I don't have an answer for that yet.",
    "Interesting — I don't know how to respond to that. Try 'help' for options."
]


def sanitize_input(text: str) -> str:
    text = text.strip().lower()
    text = "".join(ch for ch in text if ch.isalnum() or ch.isspace())
    return text


def is_exit_command(text: str) -> bool:
    return any(cmd in text for cmd in EXIT_COMMANDS)


def get_response(user_input: str) -> str:
    cleaned = sanitize_input(user_input)
    if not cleaned:
        return "You didn't say anything — try typing a message!"

    if is_exit_command(cleaned):
        return "Goodbye! Have a great day. (Refresh the page to start a new session.)"

    for data in KNOWLEDGE_BASE.values():
        for keyword in data["keywords"]:
            if keyword in cleaned:
                return random.choice(data["responses"])

    return random.choice(FALLBACK_RESPONSES)


# ----------------------------------------------------------------------------
# SESSION STATE
# ----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_ended" not in st.session_state:
    st.session_state.chat_ended = False


# ----------------------------------------------------------------------------
# SIDEBAR — controls, info, export
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Controls")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_ended = False
        st.rerun()

    st.markdown("---")
    st.markdown("## 📚 Try asking about")
    st.markdown(
        "- Greetings (*hi, hello*)\n"
        "- **how are you**\n"
        "- **your name**\n"
        "- **help**\n"
        "- **weather**\n"
        "- **thanks**"
    )

    st.markdown("---")
    st.markdown("## 💾 Export")

    # Build a plain-text transcript for download
    transcript_lines = []
    for m in st.session_state.messages:
        speaker = "You" if m["role"] == "user" else BOT_NAME
        transcript_lines.append(f"[{m['time']}] {speaker}: {m['text']}")
    transcript_text = "\n".join(transcript_lines)

    st.download_button(
        label="⬇️ Download Chat (.txt)",
        data=transcript_text,
        file_name=f"chat_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.markdown("---")
    st.caption("Type `exit`, `quit`, or `bye` in the chat to end the session.")


# ----------------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="chat-header">
        <h1>💬 {BOT_NAME}</h1>
        <p>A simple rule-based chatbot — ask a question below</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------------------------------------------------------
# CHAT HISTORY DISPLAY
# ----------------------------------------------------------------------------
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(
            f"""
            <div class="bubble-row">
                <div class="user-bubble">{msg['text']}</div>
                <div class="timestamp" style="text-align:right;">{msg['time']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="bubble-row">
                <div class="bot-bubble">{msg['text']}</div>
                <div class="timestamp">{BOT_NAME} · {msg['time']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        # Copy-to-clipboard: st.code() renders a built-in copy icon
        with st.expander("📋 Copy this response", expanded=False):
            st.code(msg["text"], language=None)

# ----------------------------------------------------------------------------
# INPUT LOOP (Streamlit-native chat input)
# ----------------------------------------------------------------------------
if not st.session_state.chat_ended:
    user_input = st.chat_input("Type your message here...")

    if user_input:
        now = datetime.now().strftime("%H:%M")

        # Add user message
        st.session_state.messages.append({
            "role": "user", "text": user_input, "time": now
        })

        cleaned = sanitize_input(user_input)

        # Exit strategy
        if is_exit_command(cleaned):
            st.session_state.messages.append({
                "role": "bot",
                "text": "Goodbye! Have a great day. 👋 (Click 'Clear Chat' to start over.)",
                "time": datetime.now().strftime("%H:%M")
            })
            st.session_state.chat_ended = True
        else:
            response = get_response(user_input)
            st.session_state.messages.append({
                "role": "bot", "text": response, "time": datetime.now().strftime("%H:%M")
            })

        st.rerun()
else:
    st.info("💬 Session ended. Click **Clear Chat** in the sidebar to start a new conversation.")