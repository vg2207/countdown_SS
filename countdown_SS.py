import base64
import io
import time
import wave

import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from streamlit_extras.stylable_container import stylable_container
from streamlit_option_menu import option_menu

st.set_page_config(layout="wide")

FREQ = 150          # base frequency (Hz)
DURATION = 0.9      # base beep length (seconds)
SAMPLE_RATE = 44100

# ---------------------------------------------------------------- styles
st.markdown(
    """
    <style>
    .big-font, .big-font-red {
        font-size: 200px !important;
        text-align: center;
        line-height: 1.1;
        margin: 0;
    }
    .big-font-red { color: #fb4c4c; }
    .dots {
        display: flex;
        justify-content: center;
        gap: 80px;
        margin-top: 20px;
    }
    .dot {
        height: 200px;
        width: 200px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-grey   { background-color: #bbb; }
    .dot-red    { background-color: #fb4c4c; }
    .dot-yellow { background-color: yellow; }
    .dot-green  { background-color: green; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------- sound
# Placeholder that holds the (invisible) audio player. It lives in the sidebar
# so it doesn't push the main layout around.
beep_slot = st.sidebar.empty()


@st.cache_data
def make_wav_b64(freq: float, duration: float) -> str:
    """Build a sine-wave WAV file and return it base64-encoded."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)  # seconds, not ms
    wave_data = 0.3 * np.sin(2 * np.pi * freq * t)

    # short fade in/out to avoid clicking
    fade = int(SAMPLE_RATE * 0.01)
    env = np.ones(n)
    env[:fade] = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)

    pcm = (wave_data * env * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.tobytes())
    return base64.b64encode(buf.getvalue()).decode()


def play_beep(freq: float = FREQ, duration: float = DURATION):
    """Play a beep. Every call renders a brand-new player (unique comment),
    so the browser autoplays it even if the sound is identical to the last."""
    st.session_state["beep_n"] = st.session_state.get("beep_n", 0) + 1
    b64 = make_wav_b64(freq, duration)
    html = (
        f'<audio autoplay><source src="data:audio/wav;base64,{b64}" '
        f'type="audio/wav"></audio><!-- beep {st.session_state["beep_n"]} -->'
    )
    with beep_slot:
        components.html(html, height=0)


# --------------------------------------------------------------- helpers
def show(slot, text, dots=None, red=False):
    """Draw the big text (and optional 3 dots) into one placeholder."""
    cls = "big-font-red" if red else "big-font"
    html = f'<p class="{cls}">{text}</p>'
    if dots:
        html += '<div class="dots">'
        html += "".join(f'<span class="dot dot-{c}"></span>' for c in dots)
        html += "</div>"
    slot.markdown(html, unsafe_allow_html=True)


def fmt(sec):
    return "{:02d}:{:02d}".format(*divmod(sec, 60))


def run_countdown(slot, seconds, frame_fn):
    """Call frame_fn(remaining) once per second, without clock drift."""
    start = time.monotonic()
    for i, remaining in enumerate(range(seconds, 0, -1)):
        frame_fn(remaining)
        time.sleep(max(0, start + (i + 1) - time.monotonic()))


def blue_button(key, label):
    with stylable_container(
        key, css_styles="button {background-color: #0349b3; color: white;}"
    ):
        return st.button(label, type="secondary", use_container_width=True, key=key + "_btn")


def grey_button(key, label):
    with stylable_container(
        key, css_styles="button {background-color: #86a3be; color: white;}"
    ):
        return st.button(label, type="secondary", use_container_width=True, key=key + "_btn")


# --------------------------------------------------------------- sidebar
with st.sidebar:
    selected_main_menu = option_menu(
        menu_title=None,
        options=["Presentation", "Q&A"],
        icons=["display", "question-circle"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical",
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "nav-link": {"--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#0349b3"},
        },
    )

# NOTE: In Streamlit, clicking *any* button interrupts the running script and
# reruns it. So pressing "Reset" automatically stops a running timer – no extra
# logic needed; the page just comes back to its idle state.

# ---------------------------------------------------------- Presentation
if selected_main_menu == "Presentation":
    col_1, col_2 = st.columns(2)
    with col_1:
        start_clicked = blue_button("pres_start", "Start")
    with col_2:
        grey_button("pres_reset", "Reset")

    display = st.empty()

    if start_clicked:
        # --- READY ? 3 2 1 GO !
        show(display, "READY ?")
        time.sleep(1)

        def intro_frame(n):
            show(display, n)
            play_beep(FREQ * 3, DURATION)

        run_countdown(display, 3, intro_frame)

        show(display, "GO !")
        play_beep(FREQ * 4, DURATION * 2)
        time.sleep(2)

        # --- 10 minute main timer
        def main_frame(remaining):
            if remaining >= 180:
                dots = ["green", "grey", "grey"]
            elif remaining > 60:
                dots = ["grey", "yellow", "grey"]
            else:
                dots = ["grey", "grey", "red"]

            show(display, fmt(remaining), dots, red=remaining <= 5)

            if remaining in (180, 60):
                play_beep(FREQ * 3, DURATION)
            elif remaining <= 5:
                play_beep(FREQ * 2, DURATION)

        run_countdown(display, 6 * 60, main_frame)

        show(display, "TIME IS UP !")
        play_beep(FREQ * 4, DURATION * 2)
        time.sleep(2)

# ------------------------------------------------------------------- Q&A
else:
    col_10, col_20 = st.columns(2)
    with col_10:
        answer_clicked = blue_button("qa_answer", "Question & Answer")
    with col_20:
        grey_button("qa_reset", "Reset")

    display = st.empty()

    if answer_clicked:

        def a_frame(remaining):
            show(display, fmt(remaining), red=remaining <= 3)
            if remaining <= 3:
                play_beep(FREQ, DURATION)

        run_countdown(display, 3 * 60, a_frame)

        show(display, "TIME IS UP !")
        play_beep(FREQ * 4, DURATION * 2)
        time.sleep(2)
