import streamlit as st
import os
from datetime import datetime
from utils.config import get_config, init_session_state, update_last_activity
from utils.auth import logout_user

def show_sidebar():
    """Render the sidebar UI after login"""
    init_session_state()

    with st.sidebar:
        st.title("🏢 Business Suite")
        st.markdown(f"👋 Welcome, **{st.session_state.get('user_name', 'User')}**")
        st.markdown(f"📧 {st.session_state.get('user_email', 'No email')}")
        st.markdown("---")

        navigation_menu()
        st.markdown("---")
        quick_stats_section()
        st.markdown("---")
        system_controls()
        st.markdown("---")
        footer_section()


def navigation_menu():
    """Sidebar navigation buttons"""
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

    for label, key in pages:
        if st.button(label, use_container_width=True, key=f"nav_{key}"):
            st.session_state["current_page"] = key
            update_last_activity()
            st.rerun()


def quick_stats_section():
    """Quick metrics and session info"""
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


def system_controls():
    """Refresh, logout, and theme selection"""
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
    """Display version and timestamp"""
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

