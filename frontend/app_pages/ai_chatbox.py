"""AI Chatbox page."""

import streamlit as st

from styles import render_title

render_title(
    "AI Chatbox",
    subtitle="Ask questions about clone runs, configuration, and troubleshooting.",
)

if "ai_chat_messages" not in st.session_state:
    st.session_state.ai_chat_messages = []

for message in st.session_state.ai_chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about clone automation…"):
    st.session_state.ai_chat_messages.append({"role": "user", "content": prompt})
    st.session_state.ai_chat_messages.append(
        {
            "role": "assistant",
            "content": (
                "AI responses are not connected yet. "
                "This page is ready for chat integration."
            ),
        }
    )
    st.rerun()
