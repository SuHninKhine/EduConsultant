import streamlit as st
from openai import OpenAI


# Load API key from Streamlit secrets
API_KEY = st.secrets.get("OPENROUTER_API_KEY")
if not API_KEY:
    st.error("❗️ OpenRouter API key not found. Please add it in your Streamlit secrets.")
    st.stop()


client = OpenAI(api_key=API_KEY, base_url="https://openrouter.ai/api/v1")


st.set_page_config(page_title="🇸🇬 SG Career & Study Bot", page_icon="🇸🇬")
st.title("🇸🇬 SG Career & Study Bot")
st.markdown("> Ask anything about education, work, or life in Singapore. The AI will help guide you step-by-step.")


# Initialize user profile and chat history if not present
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "name": None,
        "identity": None,
        "is_foreigner": None,
    }
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# Step 1: Ask for user name once
if not st.session_state.user_profile["name"]:
    name_input = st.text_input("Hi! What's your name?")
    if name_input:
        st.session_state.user_profile["name"] = name_input.strip()
        st.success(f"Nice to meet you, {st.session_state.user_profile['name']}!")
        st.rerun()
    st.stop()


# Build system prompt based on user profile
def build_system_prompt(profile):
    base_prompt = (
        "You are a friendly and knowledgeable AI assistant who gives helpful, concise, "
        "and trustworthy information about working, studying, or living in Singapore. "
        "Always ask questions to better understand the user's needs."
    )
    additions = []
    if profile.get("identity"):
        additions.append(f"The user is a {profile['identity']}.")
    if profile.get("is_foreigner") is not None:
        additions.append(
            "The user is a foreigner." if profile['is_foreigner'] == "Yes" else "The user is a Singaporean or permanent resident."
        )
    return base_prompt + " " + " ".join(additions) if additions else base_prompt


# Onboarding questions
onboarding_questions = [
    ("identity", "Please select your current status:",
     ["Student", "Working Professional", "Visitor/Planning to come to Singapore", "Others"]),
    ("is_foreigner", "Are you a foreigner to Singapore?", ["Yes", "No"]),
]


def onboarding_incomplete(profile):
    for field, _, _ in onboarding_questions:
        if profile.get(field) is None:
            return field
    return None


def ask_onboarding_question(field, question, options=None):
    if options:
        choice = st.radio(question, options, key=field, horizontal=True)
        if st.button("Submit", key=f"submit_{field}"):
            st.session_state.user_profile[field] = choice
            st.session_state.chat_history.append({"role": "user", "content": choice})
            system_prompt = build_system_prompt(st.session_state.user_profile)
            if st.session_state.chat_history:
                st.session_state.chat_history[0]["content"] = system_prompt
            st.rerun()
    else:
        answer = st.text_input(question, key=field)
        if answer:
            st.session_state.user_profile[field] = answer.strip()
            st.session_state.chat_history.append({"role": "user", "content": answer.strip()})
            system_prompt = build_system_prompt(st.session_state.user_profile)
            if st.session_state.chat_history:
                st.session_state.chat_history[0]["content"] = system_prompt
            st.rerun()


# Run onboarding if not complete
next_field = onboarding_incomplete(st.session_state.user_profile)
if next_field:
    for field, question, options in onboarding_questions:
        if field == next_field:
            ask_onboarding_question(field, question, options)
    st.stop()


# Show intro message once after onboarding
if not st.session_state.get("intro_message_shown"):
    user_name = st.session_state.user_profile.get("name", "")
    user_identity = st.session_state.user_profile.get("identity", "")

    topics_map = {
        "Student": [
            "Universities and Polytechnic options",
            "Scholarships and Financial Aid",
            "Student Visa Requirements",
            "Part-time work while studying"
        ],
        "Working Professional": [
            "Work Permit and Employment Pass",
            "Job Market and Industries",
            "Career Development and Training",
            "Singaporean Work Culture"
        ],
        "Visitor/Planning to come to Singapore": [
            "Visa and Entry Requirements",
            "Living Costs and Housing",
            "Social and Cultural Adaptation",
            "Local Laws and Regulations"
        ],
        "Others": [
            "General Education and Career Advice",
            "Living and Working in Singapore",
            "Government Services and Support",
        ]
    }

    topics = topics_map.get(user_identity, topics_map["Others"])
    topics_str = "\n".join(f"- {topic}" for topic in topics)

    intro_message = (
        f"{user_name}, it's a great pleasure to meet you.\n\n"
        "You can ask me any questions you have—these are just suggested topics you might be interested in:\n"
        f"{topics_str}"
    )

    st.session_state.chat_history.append({"role": "assistant", "content": intro_message})
    st.session_state.intro_message_shown = True
    st.rerun()


# Initialize chat history if empty
if not st.session_state.chat_history:
    system_prompt = build_system_prompt(st.session_state.user_profile)
    greeting = f"Hello, {st.session_state.user_profile['name']}! I am here to assist you with education, career, or life in Singapore. Feel free to ask me anything!"
    st.session_state.chat_history = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": greeting},
    ]
else:
    system_prompt = build_system_prompt(st.session_state.user_profile)
    st.session_state.chat_history[0]["content"] = system_prompt


# Display chat messages (except system prompt)
for message in st.session_state.chat_history[1:]:
    if message["role"] == "assistant":
        st.chat_message("assistant").write(message["content"])
    elif message["role"] == "user":
        st.chat_message("user").write(message["content"])


# Function to ask AI and return response with follow-ups
def ask_ai(user_message, history):
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-3-70b-instruct",
            messages=history,
            max_tokens=800,
            temperature=0.3,
        )
        ai_reply = response.choices[0].message.content.strip()

        # Your custom follow-up questions
        followups = (
            "\n\n---\n"
            "🔍 *You can also ask:*\n"
            "- Would it help to discuss how this fits with what we've talked about so far?\n"
            "- Are you interested in the bigger picture or trends related to this?\n"
            "- What are you currently doing or planning next about this?"
        )

        full_reply = ai_reply + followups

        history.append({"role": "assistant", "content": full_reply})
        return full_reply, history

    except Exception as e:
        error_msg = f"⚠️ Error: {str(e)}"
        history.append({"role": "assistant", "content": error_msg})
        return error_msg, history


# User input prompt
user_input = st.chat_input("Type your message here...")


if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    with st.spinner("🤖 Thinking... just a moment"):
        reply, st.session_state.chat_history = ask_ai(user_input, st.session_state.chat_history)

    st.rerun()
