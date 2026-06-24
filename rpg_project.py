#Importing necessary libraries
from google import genai
import streamlit as st
import random

#Page configuration
st.set_page_config(page_title="AI RPG Adventure", page_icon="🗡️")

#importing API 
client = genai.Client(
    api_key="AQ.Ab8RN6Lj4r1Wb3uk74n2cLAC7oohcWVgT4Ga5kyMPngZ3kGNeQ"
)

#Main siebar codes (BG)
GENRES = ["Fantasy", "Sci-Fi", "Horror", "Mystery"]

LENGTH_OPTIONS = {
    "Short (3-4 turns)": (3, 4),
    "Medium (6-8 turns)": (6, 8),
    "Long (10-12 turns)": (10, 12),
    "Extra Long (13-19 turns)": (13, 19),
}

if "story" not in st.session_state:
    st.session_state.story = []
if "started" not in st.session_state:
    st.session_state.started = False
if "turn" not in st.session_state:
    st.session_state.turn = 0
if "max_turns" not in st.session_state:
    st.session_state.max_turns = 6
if "choices" not in st.session_state:
    st.session_state.choices = []

st.sidebar.title("Adventure Setup")
hero_name = st.sidebar.text_input("Your hero's name", value="Aria")
genre = st.sidebar.selectbox("Genre", GENRES)

st.title("🗡️ AI-Narrated RPG Adventure")


def build_prompt(action=None):
    story_so_far = "\n\n".join(st.session_state.story)

    is_final_turn = (st.session_state.turn + 1) >= st.session_state.max_turns

    prompt = f"""You are a game master narrating a {genre} adventure for a hero named {hero_name}.
Keep the overall plot heading toward the same fixed ending no matter what the player chooses.
Only vary descriptions, tone, and small details based on the player's action.
Write 2-4 sentences of vivid narration for this turn only. Do not repeat earlier events.

This is turn {st.session_state.turn + 1} of {st.session_state.max_turns}.

Story so far:
{story_so_far if story_so_far else "(The story is just beginning.)"}
"""

    if action:
        prompt += f"\nThe player's action: {action}\n"

    if is_final_turn:
        prompt += "\nWrap up the story with a satisfying ending in this turn. Do not include any choices."
    else:
        prompt += """
After your narration, on new lines, give exactly 3 short choices for what the hero does next, formatted exactly like this:
CHOICES:
1. <choice one>
2. <choice two>
3. <choice three>
"""

    return prompt


def generate_next(action=None):
    prompt = build_prompt(action)

    with st.spinner("The story unfolds..."):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

    text = response.text

    if "CHOICES:" in text:
        narration, choices_block = text.split("CHOICES:", 1)

        choices = []
        for line in choices_block.strip().split("\n"):
            line = line.strip()
            if line and line[0].isdigit():
                choice_text = line.split(".", 1)[-1].strip()
                if choice_text:
                    choices.append(choice_text)

        st.session_state.choices = choices[:3]
    else:
        narration = text
        st.session_state.choices = []

    st.session_state.story.append(narration.strip())
    st.session_state.turn += 1


def start_adventure(length_label):
    min_turns, max_turns = LENGTH_OPTIONS[length_label]
    st.session_state.max_turns = random.randint(min_turns, max_turns)
    st.session_state.started = True
    generate_next()


if not st.session_state.started:
    st.write(f"A **{genre}** adventure awaits **{hero_name}**. Choose how long your story should be:")

    cols = st.columns(len(LENGTH_OPTIONS))

    for col, label in zip(cols, LENGTH_OPTIONS):
        with col:
            if st.button(label):
                start_adventure(label)
                st.rerun()

else:
    for paragraph in st.session_state.story:
        st.markdown(paragraph)
        st.divider()

    if st.session_state.turn < st.session_state.max_turns:
        if st.session_state.choices:
            st.write("What does your hero do?")

            for choice in st.session_state.choices:
                if st.button(choice, key=f"choice_{st.session_state.turn}_{choice}"):
                    generate_next(choice)
                    st.rerun()
        else:
            # Fallback in case the model didn't return parseable choices
            action = st.text_input("What does your hero do?", key=f"action_{st.session_state.turn}")
            if st.button("Take Action") and action:
                generate_next(action)
                st.rerun()
    else:
        st.success("The End.")

        if st.button("Start a New Adventure"):
            st.session_state.story = []
            st.session_state.started = False
            st.session_state.turn = 0
            st.session_state.choices = []
            st.rerun()