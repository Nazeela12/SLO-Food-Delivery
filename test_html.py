import streamlit as st

st.title("HTML TEST")

st.markdown(
    "<h1 style='color:red;'>THIS SHOULD BE RED</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<div style='background:black;color:white;padding:20px;'>"
    "THIS SHOULD HAVE A BLACK BOX"
    "</div>",
    unsafe_allow_html=True
)