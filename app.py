# ============================================================
# 🎭 Role-based Creative Chatbot + Image Studio (Integrated Pro Version)
# Author: Huiting Qiu x GPT-5
# For: Art & Advanced Big Data · Role-based AI + Visual Studio
# ============================================================

import streamlit as st
import io
import time
import base64
from dataclasses import dataclass
from typing import List, Optional
from openai import OpenAI
from PIL import Image

# ------------------------------------------------------------
# 🌈 Page Setup
# ------------------------------------------------------------
st.set_page_config(
    page_title="Role-based Creative Chatbot + Image Studio",
    page_icon="🎬",
    layout="wide"
)

# ------------------------------------------------------------
# 🎛️ Sidebar: API + Model + Role Settings
# ------------------------------------------------------------
st.sidebar.markdown("### 🔑 API & Role Settings")

api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
model = st.sidebar.selectbox(
    "Model",
    ["gpt-4.1-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
    index=0
)

role = st.sidebar.selectbox(
    "Choose a role 🎭",
    [
        "Video Director 🎬",
        "Fashion Designer 👗",
        "Storyboard Artist ✏️",
        "Graphic Designer 🎨",
        "Performer 🎭"
    ],
    index=0
)

# Role descriptions & system prompts
ROLE_DESCRIPTIONS = {
    "Video Director 🎬": {
        "desc": "Analyzes mood, camera angle, lighting.",
        "prompt": (
            "You are a professional film director. Always analyze ideas in terms of visual storytelling — "
            "use camera movement, lighting, framing, editing, and emotional tone to explain your thoughts. "
            "Describe concepts as if you are planning a film scene or visual sequence."
        )
    },
    "Fashion Designer 👗": {
        "desc": "Focuses on color harmony, texture, silhouette.",
        "prompt": (
            "You are an avant-garde fashion designer. Think in terms of form, fabric, tone, "
            "and how clothing expresses emotion, era, and identity."
        )
    },
    "Storyboard Artist ✏️": {
        "desc": "Creates composition sketches, camera layout, and timing cues.",
        "prompt": (
            "You are a storyboard artist. Visualize action beats, body language, and composition. "
            "Explain the scene framing with cinematic clarity."
        )
    },
    "Graphic Designer 🎨": {
        "desc": "Balances composition, typography, and color palette.",
        "prompt": (
            "You are a professional graphic designer. Focus on layout, composition, and how design communicates mood. "
            "Think visually and describe spatial balance and rhythm."
        )
    },
    "Performer 🎭": {
        "desc": "Analyzes emotion, posture, gesture, and audience impact.",
        "prompt": (
            "You are a stage performer and actor. Express emotional tone, gesture, and performance dynamics. "
            "Explain how to evoke empathy and rhythm in storytelling."
        )
    },
}

role_info = ROLE_DESCRIPTIONS[role]
st.sidebar.markdown(f"**Role description:** {role_info['desc']}")
with st.sidebar.expander("🧠 System prompt used for this role"):
    st.markdown(role_info["prompt"])

# ------------------------------------------------------------
# 🧠 Session States
# ------------------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "history" not in st.session_state:
    st.session_state.history = []


# ------------------------------------------------------------
# 🧩 Helpers
# ------------------------------------------------------------
def get_client():
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def generate_chat_response(prompt):
    """Generate chat response with OpenAI API."""
    client = get_client()
    if not client:
        st.error("⚠️ Please enter a valid API Key.")
        return None

    messages = [{"role": "system", "content": role_info["prompt"]}]
    for msg in st.session_state.chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt})

    resp = client.chat.completions.create(model=model, messages=messages)
    content = resp.choices[0].message.content
    return content


def b64_to_pil(b64png: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(b64png)))


# ------------------------------------------------------------
# 🎭 Main Layout
# ------------------------------------------------------------
st.markdown("# 🎭 Role-based Creative Chatbot + Image Studio")

tab_chat, tab_image = st.tabs(["💬 Chat Assistant", "🖼️ Image Studio"])

# ============================================================
# 💬 CHAT ASSISTANT
# ============================================================
with tab_chat:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"{role} — Creative Assistant")
        user_input = st.text_area(
            "Enter your question or idea:",
            placeholder="e.g. How can I shoot a dream sequence?",
            height=130
        )
        if st.button("✨ Generate Response", use_container_width=True):
            if not user_input.strip():
                st.warning("Please enter your question first.")
            else:
                response = generate_chat_response(user_input)
                if response:
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    st.session_state.chat_history.append({"role": "assistant", "content": response})

    with col2:
        st.subheader("💭 Conversation History (bubble view)")
        if len(st.session_state.chat_history) == 0:
            st.info("아직 대화가 없습니다. 질문을 한 번 해보세요!")
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f'<div style="background:#DCF8C6;padding:8px 12px;border-radius:10px;margin:6px 0;">🧑‍🎨 <b>You:</b> {msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="background:#E8E8E8;padding:8px 12px;border-radius:10px;margin:6px 0;">🤖 <b>AI:</b> {msg["content"]}</div>', unsafe_allow_html=True)
        if st.button("🗑️ Clear history"):
            st.session_state.chat_history.clear()

# ============================================================
# 🖼️ IMAGE STUDIO
# ============================================================
with tab_image:
    st.subheader("🖼️ AI Image Studio")
    st.caption("Visualize your creative idea with AI image generation.")

    colA, colB = st.columns([2, 1])

    with colA:
        prompt = st.text_area("Image Prompt", placeholder="Describe your visual idea...", height=130)
        negative = st.text_input("Negative Prompt (optional)", placeholder="e.g. blurry, text artifacts, bad lighting")
    with colB:
        size = st.selectbox("Image Size", ["1024x1024", "1344x768", "768x1344", "2048x2048"], index=0)
        n_images = st.slider("Number of Images", 1, 6, 3)
        bg_trans = st.toggle("Transparent Background", False)
        quality = st.select_slider("Quality", options=["standard", "hd"], value="standard")

    if st.button("🚀 Generate Images", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ Please enter your OpenAI API Key.")
        elif not prompt.strip():
            st.warning("Please enter a prompt.")
        else:
            client = get_client()
            with st.spinner("Generating images..."):
                try:
                    result = client.images.generate(
                        model="gpt-image-1",
                        prompt=f"{prompt}\nStyle: {role_info['prompt']}",
                        size=size,
                        n=n_images,
                        quality=quality,
                        background="transparent" if bg_trans else "white"
                    )
                    images_b64 = [d.b64_json for d in result.data]
                    st.session_state.history.insert(0, images_b64)
                    st.success("✅ Images generated successfully!")
                except Exception as e:
                    st.error(str(e))

    if st.session_state.history:
        st.markdown("### ⭐ Latest Results")
        cols = st.columns(2)
        latest = st.session_state.history[0]
        for i, b64img in enumerate(latest):
            with cols[i % 2]:
                img = b64_to_pil(b64img)
                st.image(img, use_column_width=True, caption=f"Image {i+1}")
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                st.download_button("Download", buf.getvalue(), f"image_{i+1}.png", "image/png")

# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------
st.caption("Built for Art & Advanced Big Data · Huiting Qiu · 2025")
