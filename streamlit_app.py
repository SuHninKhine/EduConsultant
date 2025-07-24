import streamlit as st
from openai import OpenAI

# Load API key from Streamlit secrets
API_KEY = st.secrets.get("OPENROUTER_API_KEY")

if not API_KEY:
    st.error("❗️ OpenRouter API key not found. Please add it in your Streamlit secrets.")
    st.stop()

# Initialize OpenRouter client
client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Define chatbot system prompt
SYSTEM_PROMPT = (
    "You are a friendly and knowledgeable AI assistant who gives helpful, concise, "
    "and trustworthy information about working, studying, or living in Singapore. "
    "Always ask questions to better understand the user's needs."
)

# Initialize or retrieve chat history in session state
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

# Streamlit page configuration
st.set_page_config(page_title="🇸🇬 SG Career & Study Bot", page_icon="🇸🇬")

st.title("🇸🇬 SG Career & Study Bot")
st.markdown("> Ask anything about education, work, or life in Singapore. The AI will help guide you step-by-step.")

# Display previous chat messages (except the system prompt)
for message in st.session_state.chat_history[1:]:
    if message["role"] == "assistant":
        st.chat_message("assistant").write(message["content"])
    elif message["role"] == "user":
        st.chat_message("user").write(message["content"])

# Function to send user query to OpenRouter
def ask_ai(user_message, history):
    history.append({"role": "user", "content": user_message})
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-3-70b-instruct",
            messages=history,
            max_tokens=800,
            temperature=0.3,
        )
        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        return reply, history
    except Exception as e:
        error_msg = f"⚠️ Error: {str(e)}"
        history.append({"role": "assistant", "content": error_msg})
        return error_msg, history

# Accept user input
user_input = st.chat_input("Type your message here...")

if user_input:
    reply, st.session_state.chat_history = ask_ai(user_input, st.session_state.chat_history)
    # Refresh the app to display the updated chat
    st.rerun()
