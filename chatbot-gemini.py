from google import genai
import streamlit as st

st.set_page_config(page_title="Gemini Chat")

client = genai.Client(
    api_key="AQ.Ab8RN6KmkZtpj37cM9lSrEnHetFMGtfAdZ335X6pTUc_HtLDNw"
)

st.title("🤖 Gemini 2.5 Flash Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Type your message...")

if prompt:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            ai_response = response.text
            st.markdown(ai_response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": ai_response
        }
    )

if st.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()