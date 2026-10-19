import base64
import streamlit as st
from PIL import ImageOps, Image
import numpy as np


def set_background(image_file):
    with open(image_file, "rb") as f:
        img_data = f.read()

    b64_encoded = base64.b64encode(img_data).decode()

    style = f"""
        <style>
        .stApp {{
            background-image:
                linear-gradient(
                    rgba(8, 10, 25, 0.35),
                    rgba(8, 10, 25, 0.35)
                ),
                url("data:image/png;base64,{b64_encoded}");

            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* Keep the chat interface readable */
        [data-testid="stChatMessage"] {{
            background-color: rgba(12, 15, 30, 0.78);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 14px;
            padding: 12px;
        }}

        /* Make regular text readable */
        .stMarkdown, .stText {{
            color: #f5f5fa;
        }}
        </style>
    """

    st.markdown(style, unsafe_allow_html=True)