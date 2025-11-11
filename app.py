import io
import os
import time
import base64
from dataclasses import dataclass, asdict
from typing import List, Optional

import streamlit as st
from PIL import Image
from openai import OpenAI

# -----------------------------
# App Meta
# -----------------------------
st.set_page_config(
    page_title="Role-based Creative Chatbot + Image Studio",
    page_icon="🎭",
    layout="wide"
)

# -----------------------------
# Sidebar: API & Role Settings
# -----------------------------
with st.sidebar:
    st.markdown("### 🔑 API & Role Settings")
    api_key = st.text_input("Enter your OpenAI API Key:", type="password", help="Required for image generation.")
    role = st.selectbox(
        "Choose a role:",
        [
            "Video Director",
            "Fashion Consultant",
            "Dance Coach",
            "Performing Arts Critic",
            "Graphic Designer",
            "Storyboard Artist"
        ],
        index=0
    )
    st.markdown(
        "You visualize stories and direct how they are brought to life on screen."
        if role == "Video Director" else
        "You guide aesthetics and craft compelling visuals."
    )

# Prepare OpenAI client (lazy)
def get_client(_key: str) -> Optional[OpenAI]:
    if not _key:
        return None
    try:
        return OpenAI(api_key=_key)
    except Exception:
        return None

# -----------------------------
# Session State for Image History
# -----------------------------
@dataclass
class GenParams:
    prompt: str
    negative_prompt: str
    style: str
    size: str
    n_images: int
    seed: Optional[int]
    bg_transparent: bool
    quality: str

@dataclass
class GenResult:
    timestamp: float
    params: GenParams
    images_b64: List[str]  # base64 PNGs

if "history" not in st.session_state:
    st.session_state.history: List[GenResult] = []

# -----------------------------
# Helpers
# -----------------------------
SIZES = {
    "Square (1024x1024)": "1024x1024",
    "Landscape (1344x768)": "1344x768",
    "Portrait (768x1344)": "768x1344",
    "Large Square (2048x2048)": "2048x2048"
}

STYLE_HINTS = {
    "Cinematic": "cinematic lighting, shallow depth of field, filmic color grading, dramatic composition",
    "Concept Art": "highly detailed concept art, artstation quality, mood painting, volumetric light",
    "Poster Graphic": "bold poster design, vector-like clarity, balanced negative space, strong typography placeholders",
    "Watercolor": "soft watercolor texture, natural paper grain, gentle bleeding edges",
    "3D Render": "physically-based rendering, soft studio lighting, subsurface scattering",
    "Anime": "clean line art, cel shading, expressive character styling"
}

def style_prompt(role_name: str, base: str, style_key: str) -> str:
    style = STYLE_HINTS.get(style_key, "")
    role_instructions = {
        "Video Director": "Compose shots like a storyboard frame; emphasize emotion, blocking, and lighting motivation.",
        "Fashion Consultant": "Focus on outfit silhouette, fabric texture, and color harmony; editorial styling.",
        "Dance Coach": "Capture dynamic body lines, rhythm, and motion arcs; sense of stage lighting.",
        "Performing Arts Critic": "Emphasize atmosphere, dramaturgy, and audience perspective.",
        "Graphic Designer": "Prioritize layout balance, iconic shapes, and color contrast; print-friendly.",
        "Storyboard Artist": "Clear framing, character poses, arrows for motion; readable beat."
    }.get(role_name, "")
    parts = [base]
    if style:
        parts.append(style)
    if role_instructions:
        parts.append(role_instructions)
    return ", ".join([p for p in parts if p])

def b64_to_pil(b64png: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(b64png)))

def download_button_for_image(img: Image.Image, filename: str):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    st.download_button("Download PNG", data=buf.getvalue(), file_name=filename, mime="image/png")

# -----------------------------
# Header
# -----------------------------
st.markdown("# 🎭 Role-based Creative Chatbot + Image Studio")
tabs = st.tabs(["💬 Chat Assistant", "🖼️ Image Studio"])

# -----------------------------
# Tab 1: (Placeholder) Chat Assistant
# -----------------------------
with tabs[0]:
    st.subheader(f"🎬 {role} — Creative Chat Assistant")
    st.caption("Ask role-specific questions. (This demo focuses on the Image Studio below.)")
    user_q = st.text_area("Enter your question or idea:", height=120, placeholder="e.g. How can I make my short film emotionally powerful?")
    if st.button("✨ Generate Response", use_container_width=True):
        if not api_key:
            st.warning("Please enter your OpenAI API Key in the sidebar.")
        else:
            # Simple guidance response (no tool-calling to keep example focused)
            st.write(f"As a **{role}**, here are three actionable ideas to start:")
            st.markdown(
                "- Define a clear emotional arc with 3 turning points.\n"
                "- Use visual motifs (color, framing) to echo character psychology.\n"
                "- Design sound transitions that carry emotion across cuts."
            )

# -----------------------------
# Tab 2: Image Studio (Main)
# -----------------------------
with tabs[1]:
    st.subheader("🖼️ Image Studio")
    st.caption("Design and visualize ideas with AI. Choose style, size, and generate multiple variations.")

    colA, colB = st.columns([2, 1], vertical_alignment="top")
    with colA:
        base_prompt = st.text_area(
            "Prompt",
            placeholder="Describe the image you want. Include subject, setting, mood, lighting, colors…",
            height=140
        )
        negative_prompt = st.text_input(
            "Negative Prompt (optional)",
            placeholder="blurry, low quality, distorted anatomy, text artifacts"
        )

    with colB:
        style = st.selectbox("Style Preset", list(STYLE_HINTS.keys()), index=0)
        size_label = st.selectbox("Image Size", list(SIZES.keys()), index=0)
        n_images = st.slider("Variations", min_value=1, max_value=8, value=4, help="Number of images to generate")
        seed_opt = st.text_input("Seed (optional, integer)", value="", help="Leave blank for random")
        bg_transparent = st.toggle("Transparent Background (PNG)", value=False)
        quality = st.select_slider("Quality", options=["standard", "hd"], value="standard")
        seed_val = None
        if seed_opt.strip():
            try:
                seed_val = int(seed_opt.strip())
            except ValueError:
                st.warning("Seed must be an integer. Ignoring.")

    # Generate
    run = st.button("🚀 Generate Images", use_container_width=True, type="primary")

    # Guard
    if run:
        if not api_key:
            st.error("Please enter your OpenAI API Key in the sidebar.")
        elif not base_prompt.strip():
            st.error("Please enter a prompt.")
        else:
            client = get_client(api_key)
            if not client:
                st.error("Invalid API Key or client initialization failed.")
            else:
                final_prompt = style_prompt(role, base_prompt.strip(), style)
                if negative_prompt.strip():
                    final_prompt += f". Avoid: {negative_prompt.strip()}."

                st.info("Generating images…")
                try:
                    # OpenAI Images API: gpt-image-1
                    # Docs: https://platform.openai.com/docs/guides/images
                    gen = client.images.generate(
                        model="gpt-image-1",
                        prompt=final_prompt,
                        size=SIZES[size_label],
                        n=n_images,
                        background="transparent" if bg_transparent else "white",
                        quality=quality,
                        seed=seed_val
                    )
                    images_b64 = [d.b64_json for d in gen.data]
                    # Save to history
                    params = GenParams(
                        prompt=base_prompt.strip(),
                        negative_prompt=negative_prompt.strip(),
                        style=style,
                        size=SIZES[size_label],
                        n_images=n_images,
                        seed=seed_val,
                        bg_transparent=bg_transparent,
                        quality=quality
                    )
                    st.session_state.history.insert(0, GenResult(time.time(), params, images_b64))
                    st.success("Done! See results below.")
                except Exception as e:
                    st.exception(e)

    # Results (latest run)
    if st.session_state.history:
        latest: GenResult = st.session_state.history[0]
        st.markdown("### ⭐ Latest Results")
        meta1, meta2, meta3 = st.columns([2, 2, 2])
        with meta1:
            st.write("**Style:**", latest.params.style)
            st.write("**Size:**", latest.params.size)
        with meta2:
            st.write("**Variations:**", latest.params.n_images)
            st.write("**Quality:**", latest.params.quality)
        with meta3:
            st.write("**Seed:**", latest.params.seed if latest.params.seed is not None else "random")
            st.write("**Background:**", "Transparent" if latest.params.bg_transparent else "White")

        # Gallery
        cols = st.columns(2, vertical_alignment="top")
        for i, b64img in enumerate(latest.images_b64, start=1):
            pil_img = b64_to_pil(b64img)
            with cols[(i - 1) % 2]:
                st.image(pil_img, use_column_width=True, caption=f"Variation {i}")
                filename = f"image_{int(latest.timestamp)}_{i}.png"
                download_button_for_image(pil_img, filename)

        st.divider()

        # History Accordion
        with st.expander("🗂️ Generation History"):
            for idx, item in enumerate(st.session_state.history):
                with st.container(border=True):
                    st.markdown(f"**Run #{len(st.session_state.history) - idx}** – {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item.timestamp))}")
                    st.caption(
                        f"Prompt: {item.params.prompt}\n\n"
                        f"Negative: {item.params.negative_prompt or '(none)'}\n"
                        f"Style: {item.params.style} | Size: {item.params.size} | N: {item.params.n_images} | "
                        f"Seed: {item.params.seed if item.params.seed is not None else 'random'} | "
                        f"BG: {'Transparent' if item.params.bg_transparent else 'White'} | "
                        f"Quality: {item.params.quality}"
                    )
                    cols_h = st.columns(4)
                    for j, b64img in enumerate(item.images_b64, start=1):
                        pil_img = b64_to_pil(b64img)
                        with cols_h[(j - 1) % 4]:
                            st.image(pil_img, use_column_width=True, caption=f"#{j}")
    else:
        st.info("No images yet. Enter a prompt and click **Generate Images**.")

# -----------------------------
# Footer
# -----------------------------
st.caption("Built for Arts & Advanced Big Data · Role-based Chatbot + Image Studio")
