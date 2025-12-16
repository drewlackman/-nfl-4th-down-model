import streamlit as st
from nfl4th.model import evaluate

st.set_page_config(page_title="NFL 4th Down Model", layout="centered")
st.title("NFL 4th Down Decision Helper")

yard_line = st.slider("Yard line (1 = own, 99 = opp)", min_value=1, max_value=99, value=50)
yards_to_go = st.number_input("Yards to go", min_value=0.1, value=2.5, step=0.1)
show_wp = st.checkbox("Show win prob view", value=True)

override_p = st.slider("Override p(convert)?", 0.0, 1.0, value=0.59, step=0.01)
use_override_p = st.checkbox("Use override above", value=False)

if st.button("Evaluate"):
    result = evaluate(
        yard_line,
        yards_to_go,
        override_p_convert=override_p if use_override_p else None,
    )
    st.json(result if show_wp else {k: result[k] for k in ("yard_line","yards_to_go","recommendation")})
