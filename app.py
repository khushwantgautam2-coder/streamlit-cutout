"""Run with: streamlit run app.py"""
import hashlib
import io
import os
from pathlib import Path
import warnings

import streamlit as st
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

os.environ.setdefault("U2NET_HOME", str(Path(__file__).parent / ".models"))
st.set_page_config(page_title="Cutout Studio", page_icon="✂️", layout="wide")


@st.cache_resource
def removal_session():
    from rembg import new_session
    return new_session("u2netp", providers=["CPUExecutionProvider"])


def read_image(data):
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        image = Image.open(io.BytesIO(data))
        if image.width * image.height > 25_000_000:
            raise ValueError("Choose an image under 25 megapixels.")
        if image.format not in {"JPEG", "PNG", "WEBP"}:
            raise ValueError("Choose a JPG, PNG or WebP image.")
        image.load()
        return ImageOps.exif_transpose(image).convert("RGBA")


def preview_image(image, color):
    """Composite only the preview; keep exported pixels transparent."""
    image = image.copy()
    image.thumbnail((1200, 1200))
    if color:
        background = Image.new("RGBA", image.size, color)
    else:
        background = Image.new("RGBA", image.size, "#ffffff")
        draw = ImageDraw.Draw(background)
        for y in range(0, image.height, 24):
            for x in range(0, image.width, 24):
                if (x // 24 + y // 24) % 2:
                    draw.rectangle((x, y, x + 23, y + 23), fill="#e8ebef")
    return Image.alpha_composite(background, image)


st.markdown("""<style>
.stApp {background:#f4f5f7;color:#202124}
.block-container {padding-top:2rem;max-width:1400px}
h1 {letter-spacing:-1.5px}
div.stButton > button[kind=primary] {background:#d8fa69;color:#202124;border:0}
div.stDownloadButton > button {background:#202124;color:white;border:0}
</style>""", unsafe_allow_html=True)
st.caption("✂ CUTOUT STUDIO")
st.title("Keep the good part.")
st.write("Remove the background from your image and download a transparent PNG.")

controls, workspace = st.columns([1, 2.4], gap="large")
with controls:
    st.subheader("Your image")
    upload = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png", "webp"])
    st.caption("Up to 20 MB. Images are processed on the machine running this app.")

if upload is None:
    st.session_state.pop("cutout", None)
    st.session_state.pop("image_key", None)
    with workspace:
        st.info("Upload an image to start your cutout.")
    st.stop()

data = upload.getvalue()
if len(data) > 20 * 1024 * 1024:
    st.error("Choose an image under 20 MB.")
    st.stop()
try:
    image = read_image(data)
except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
    st.error("This file cannot be opened. Choose a valid JPG, PNG or WebP under 25 megapixels.")
    st.stop()

image_key = hashlib.sha256(data).hexdigest()
if st.session_state.get("image_key") != image_key:
    st.session_state.image_key = image_key
    st.session_state.pop("cutout", None)

with controls:
    st.caption(f"{image.width:,} × {image.height:,} pixels")
    clicked = st.button("Remove background", type="primary", width="stretch")
    st.caption("The first run downloads a small removal model. Later runs reuse it.")
    st.divider()
    st.subheader("Preview background")
    background = st.selectbox("Background", ["Transparent", "White", "Dark", "Lime", "Custom"])
    colors = {"Transparent": None, "White": "#ffffff", "Dark": "#202124", "Lime": "#d8fa69"}
    color = st.color_picker("Preview color", "#aabfff") if background == "Custom" else colors[background]
    st.caption("Preview colors do not change your transparent PNG.")

if clicked:
    try:
        with st.spinner("Removing background… Keep this page open."):
            from rembg import remove
            cutout = remove(image, session=removal_session()).convert("RGBA")
            output = io.BytesIO()
            cutout.save(output, format="PNG")
            st.session_state.cutout = output.getvalue()
    except Exception:
        st.error("Background removal failed. Check your internet connection for the first model download, then try again or use a smaller image.")

result = st.session_state.get("cutout")
with workspace:
    before, after = st.columns(2)
    with before:
        st.subheader("Original")
        st.image(image, width="stretch")
    with after:
        st.subheader("Cutout")
        if result:
            cutout = Image.open(io.BytesIO(result)).convert("RGBA")
            st.image(preview_image(cutout, color), width="stretch")
        else:
            st.info("Click Remove background to create your cutout.")
with controls:
    if result:
        st.download_button("Download transparent PNG", result,
            file_name=f"{Path(upload.name).stem}-cutout.png", mime="image/png",
            width="stretch", on_click="ignore")
        st.success("Your cutout is ready.")
