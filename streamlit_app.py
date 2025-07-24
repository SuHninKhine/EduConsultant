import os
import streamlit as st
from openai import OpenAI

# Load API key from environment variable
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    st.error("❗️ OpenRouter API key not found. Please set the OPENROUTER_API_KEY environment variable.")
    st.stop()

# Initialize OpenRouter client
client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Define the system prompt for chatbot personality
SYSTEM_PROMPT = (
    "You are a friendly and knowledgeable AI assistant who gives helpful, concise and trustworthy information "
    "about working, studying, or living in Singapore. Always ask questions to better understand the user's needs."
)

# Initialize or retrieve chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "assistant",
            "content": (
                "Hello! To get started, may I know your name? "
                "What are you currently doing? And what are your plans for the future?"
            )
        },
    ]

# Configure Streamlit page
st.set_page_config(page_title="🇸🇬 SG Career & Study Bot", page_icon="🇸🇬")
st.title("🇸🇬 SG Career & Study Bot")
st.markdown("> Ask anything about education, work, or life in Singapore. The AI will help guide you step-by-step.")

# Display existing messages in chat history (except system prompt)
for msg in st.session_state.chat_history[1:]:
    if msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])
    elif msg["role"] == "user":
        st.chat_message("user").write(msg["content"])

# Accept user input
user_input = st.chat_input("Type your message here...")

def ask_ai(user_message, history):
    # Add user message
    history.append({"role": "user", "content": user_message})
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-3-70b-instruct",
            messages=history,
            max_tokens=800,
            temperature=0.3,
        )
        reply = response.choices[0].message.content
        # Add assistant response
        history.append({"role": "assistant", "content": reply})
        return reply, history
    except Exception as e:
        error_msg = f"⚠️ Error: {str(e)}"
        history.append({"role": "assistant", "content": error_msg})
        return error_msg, history

# Handle user input & update chat
if user_input:
    reply, st.session_state.chat_history = ask_ai(user_input, st.session_state.chat_history)
    st.rerun()

