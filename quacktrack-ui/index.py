import streamlit as st

# 1. Define your page objects
login_page = st.Page("login.py", title="Login", icon="🔒")
dashboard = st.Page("dashboard.py", title="Dashboard", icon="📊")
categorize = st.Page("categories.py", title="Categorize", icon="🏷️")
audit_dashboard = st.Page("llm_audit_dashboard.py", title="LLM Audit", icon="🤖")


# 2. Logic to decide which pages to show
if st.user.is_logged_in:
    # If logged in, show the actual app pages
    pg = st.navigation([dashboard, categorize, audit_dashboard])
    
    # Optional: Add a logout button to the sidebar
    if st.sidebar.button("Log out"):
        st.logout()
else:
    # If NOT logged in, ONLY show the login page
    pg = st.navigation([login_page])

# 3. Run the selected page
pg.run()