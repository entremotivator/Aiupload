import streamlit as st
import json
import os
from datetime import datetime
from utils.auth import authenticate_user, logout_user
from utils.config import get_config, init_session_state, update_last_activity

def show_sidebar():
    """Render the sidebar UI"""
    init_session_state()

    with st.sidebar:
        st.title("🏢 Business Suite")
        st.markdown("---")

        if not st.session_state.get('logged_in', False):
            login_section()
        else:
            authenticated_section()


def login_section():
    """Sidebar login interface with service account upload"""
    st.subheader("🔐 Login")

    st.markdown("### 📊 Google Sheets Setup")
    uploaded_file = st.file_uploader(
        "Upload Service Account JSON",
        type=['json'],
        help="Upload your Google Sheets service account JSON file",
        key="upload_service_account"
    )

    if uploaded_file:
        try:
            service_account_info = json.load(uploaded_file)
            required = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            if all(k in service_account_info for k in required):
                st.session_state['service_account_info'] = service_account_info

                path = "temp_service_account.json"
                with open(path, "w") as f:
                    json.dump(service_account_info, f)
                st.session_state['service_account_path'] = path

                st.success("✅ Service account uploaded!")
            else:
                st.error("❌ Missing fields in service account JSON.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

    st.markdown("### 👤 User Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if authenticate_user(username, password):
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")


def authenticated_section():
    """Sidebar content for authenticated users"""
    st.markdown(f"👋 Welcome, **{st.session_state.get('user_name', 'User')}**")
    st.markdown(f"📧 {st.session_state.get('user_email', 'No email')}")

    # Google Sheets Status
    if st.session_state.get('service_account_info'):
        st.success("✅ Google Sheets Connected")
        email = st.session_state['service_account_info'].get('client_email', 'Unknown')
        st.info(f"Service Email: {email}")
    else:
        st.warning("⚠️ Google Sheets not connected")

    st.markdown("---")
    st.subheader("📋 Navigation")

    pages = [
        ("🏠 Dashboard", "1_Dashboard"),
        ("📅 Calendar", "2_Calendar"),
        ("🧾 Invoices", "3_Invoices"),
        ("👥 Customers", "4_Customers"),
        ("📅 Appointments", "5_Appointments"),
        ("💰 Pricing", "6_Pricing"),
        ("💬 Super Chat", "7_Super_Chat"),
        ("📞 AI Caller", "8_AI_Caller"),
        ("📞 Call Center", "9_Call_Center"),
    ]

    current_page = st.session_state.get("current_page", "Dashboard")

    for label, key in pages:
        if st.button(label, use_container_width=True, key=f"nav_{key}"):
            st.session_state["current_page"] = key
            update_last_activity()
            st.rerun()

    st.markdown("---")
    quick_stats_section()
    st.markdown("---")
    system_section()
    st.markdown("---")
    footer_section()


def quick_stats_section():
    """Show quick metrics and session info"""
    st.subheader("📊 Quick Stats")

    try:
        if 'gsheet_cache' in st.session_state:
            cache = st.session_state['gsheet_cache']
            st.metric("Cached Sheets", len(cache))

            timestamps = [info.get('timestamp', '') for info in cache.values()]
            if timestamps:
                last_sync = max(timestamps)
                if last_sync:
                    st.info(f"Last Sync: {last_sync[:16]}")

        login_time = st.session_state.get('login_time')
        if login_time:
            st.info(f"Session started: {login_time[:16]}")
    except Exception as e:
        st.error(f"Error fetching stats: {e}")


def system_section():
    """Buttons for logout, refresh, and theme selection"""
    st.subheader("⚙️ System")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Refresh"):
            for key in list(st.session_state.keys()):
                if 'cache' in key:
                    del st.session_state[key]
            st.success("Refreshed!")
            st.rerun()

    with col2:
        if st.button("🚪 Logout"):
            logout_user()
            st.rerun()

    theme = st.selectbox(
        "🎨 Theme",
        ["Light", "Dark", "Auto"],
        index=["light", "dark", "auto"].index(st.session_state.get("theme", "light")),
        key="theme_select"
    )

    if theme.lower() != st.session_state.get("theme", "light"):
        st.session_state["theme"] = theme.lower()
        st.rerun()


def footer_section():
    """Footer with version and timestamp"""
    version = get_config("version", "2.0.0")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    st.markdown(
        f"""
        <div style='text-align:center; font-size:0.8em; color:gray;'>
        Business Suite v{version} <br>
        {now}
        </div>
        """,
        unsafe_allow_html=True
    )


# Optional: clean up temporary files
def cleanup_temp_files():
    try:
        if os.path.exists("temp_service_account.json"):
            os.remove("temp_service_account.json")
    except Exception:
        pass

import atexit
atexit.register(cleanup_temp_files)
