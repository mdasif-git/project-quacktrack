import streamlit as st

st.title("🦆 QuackTrack")
st.subheader("Personal Expense Intelligence")

st.info("Please sign in with your Google account to access your dashboard.")

# Triggers the OIDC flow defined in your secrets.toml
if st.button("Log in with Google", type="primary"):
    st.login()