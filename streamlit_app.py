import streamlit as st
from openai import OpenAI

# Load API key from Streamlit secrets
API_KEY = st.secrets.get("OPENROUTER_API_KEY")

if not API_KEY:
    st.error("❗️ OpenRouter API key not found. Please add it in your Streamlit secrets.")
    st.stop()

# Initialize OpenRouter client
client = OpenAI(api_key=API_KEY, base_url="https://openrouter.ai/api/v1")

# Streamlit page configuration
st.set_page_config(page_title="🇸🇬 SG Career & Study Bot", page_icon="🇸🇬")

st.title("🇸🇬 SG Career & Study Bot")
st.markdown("> Ask anything about education, work, or life in Singapore. The AI will help guide you step-by-step.")

# Initialize user profile and chat history in session state
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "name": None,
        "identity": None,
        "origin": None,
        "is_foreigner": None,
    }

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Step 1: Ask user for their name (only name)
if not st.session_state.user_profile["name"]:
    name_input = st.text_input("Hi! What's your name?")
    if name_input:
        st.session_state.user_profile["name"] = name_input.strip()
        st.success(f"Nice to meet you, {st.session_state.user_profile['name']}!")
        st.rerun()
    st.stop()

# Helper to build personalized system prompt dynamically
def build_system_prompt(profile):
    base_prompt = (
        "You are a friendly and knowledgeable AI assistant who gives helpful, concise, "
        "and trustworthy information about working, studying, or living in Singapore. "
        "Always ask questions to better understand the user's needs."
    )
    # Add available user info (if any) without explicit sensitive details in greeting
    additions = []
    if profile.get("identity"):
        additions.append(f"The user is a {profile['identity']}.")
    if profile.get("origin"):
        additions.append(f"The user is from {profile['origin']}.")
    if profile.get("is_foreigner") is not None:
        additions.append(
            "The user is a foreigner." if profile['is_foreigner'] == "Yes" else "The user is a Singaporean or permanent resident."
        )
    return base_prompt + " " + " ".join(additions) if additions else base_prompt

# If chat history is empty, initialize with greeting from assistant (only name)
if not st.session_state.chat_history:
    greeting = f"Hello, {st.session_state.user_profile['name']}! I am here to assist you with education, career, or life in Singapore. Feel free to ask me anything!"
    st.session_state.chat_history = [
        {"role": "system", "content": build_system_prompt(st.session_state.user_profile)},
        {"role": "assistant", "content": greeting},
    ]

# Display chat history (skip the system prompt)
for message in st.session_state.chat_history[1:]:
    if message["role"] == "assistant":
        st.chat_message("assistant").write(message["content"])
    elif message["role"] == "user":
        st.chat_message("user").write(message["content"])

# Function to append a system assistant message (for onboarding questions)
def append_assistant_message(msg):
    st.session_state.chat_history.append({"role": "assistant", "content": msg})

# Function to append user message to chat history
def append_user_message(msg):
    st.session_state.chat_history.append({"role": "user", "content": msg})

# Define onboarding questions and flow
onboarding_questions = [
    ("identity", f"{st.session_state.user_profile['name']}, please select your current status:", 
        ["Student", "Working Professional", "Visitor/Planning to come to Singapore", "Others"]),
    ("origin", f"{st.session_state.user_profile['name']}, which country are you from?", None),
    ("is_foreigner", f"{st.session_state.user_profile['name']}, are you a foreigner to Singapore?", 
        ["Yes", "No"]),
]

def onboarding_incomplete(profile):
    # Return the first unset onboarding field
    for field, _, _ in onboarding_questions:
        if profile.get(field) is None:
            return field
    return None

def ask_onboarding_question(field, question, options=None):
    if options:
        # Display options (radio/selectbox) for user to choose
        choice = st.radio(question, options, key=field, horizontal=True)
        if st.button("Submit", key=f"submit_{field}"):
            st.session_state.user_profile[field] = choice
            append_user_message(choice)
            # Update system prompt since profile changed
            system_prompt = build_system_prompt(st.session_state.user_profile)
            st.session_state.chat_history[0]["content"] = system_prompt
            st.rerun()
    else:
        # Text input for free text answers
        answer = st.text_input(question, key=field)
        if answer:
            st.session_state.user_profile[field] = answer.strip()
            append_user_message(answer.strip())
            # Update system prompt since profile changed
            system_prompt = build_system_prompt(st.session_state.user_profile)
            st.session_state.chat_history[0]["content"] = system_prompt
            st.rerun()

# Check if onboarding is incomplete and ask accordingly
next_field = onboarding_incomplete(st.session_state.user_profile)
if next_field:
    for field, question, options in onboarding_questions:
        if field == next_field:
            ask_onboarding_question(field, question, options)
    st.stop()

# Function to send user query to OpenRouter and append response
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

# Accept normal chat input once onboarding complete
user_input = st.chat_input(f"{st.session_state.user_profile['name']}, type your message here...")

if user_input:
    append_user_message(user_input)
    reply, st.session_state.chat_history = ask_ai(user_input, st.session_state.chat_history)
    st.rerun()
