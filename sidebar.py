import streamlit as st
import json
import os
from datetime import datetime
from utils.auth import authenticate_user, logout_user
from utils.config import get_config, init_session_state, update_last_activity

def render_sidebar():
    """Render the main application sidebar with authentication and navigation"""
    
    # Initialize session state
    init_session_state()
    
    with st.sidebar:
        st.title("🏢 Business Suite")
        st.markdown("---")
        
        # Authentication Section
        if not st.session_state.get('logged_in', False):
            render_login_section()
        else:
            render_authenticated_sidebar()

def render_login_section():
    """Render login section in sidebar"""
    st.subheader("🔐 Authentication")
    
    # Google Sheets Service Account Upload
    st.markdown("### 📊 Google Sheets Setup")
    uploaded_file = st.file_uploader(
        "Upload Service Account JSON",
        type=['json'],
        help="Upload your Google Sheets service account JSON file",
        key="sidebar_service_account_upload"
    )
    
    if uploaded_file is not None:
        try:
            # Read and validate the JSON file
            service_account_info = json.load(uploaded_file)
            
            # Validate required fields
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            if all(field in service_account_info for field in required_fields):
                # Store in session state
                st.session_state['service_account_info'] = service_account_info
                st.success("✅ Service account file uploaded successfully!")
                
                # Save to temporary file for use across the app
                temp_path = "temp_service_account.json"
                with open(temp_path, 'w') as f:
                    json.dump(service_account_info, f)
                
                st.session_state['service_account_path'] = temp_path
                
            else:
                st.error("❌ Invalid service account file. Missing required fields.")
                
        except json.JSONDecodeError:
            st.error("❌ Invalid JSON file format.")
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
    
    # Login Form
    st.markdown("### 👤 User Login")
    with st.form("login_form"):
        username = st.text_input("Username", key="sidebar_username")
        password = st.text_input("Password", type="password", key="sidebar_password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if authenticate_user(username, password):
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

def render_authenticated_sidebar():
    """Render sidebar for authenticated users"""
    
    # User info
    st.markdown(f"👋 Welcome, **{st.session_state.get('user_name', 'User')}**")
    st.markdown(f"📧 {st.session_state.get('user_email', 'No email')}")
    
    # Service Account Status
    if st.session_state.get('service_account_info'):
        st.success("✅ Google Sheets Connected")
        
        # Show service account email
        service_email = st.session_state['service_account_info'].get('client_email', 'Unknown')
        st.info(f"📊 Service Account: {service_email[:30]}...")
        
        # Refresh connection button
        if st.button("🔄 Refresh Connection", key="sidebar_refresh_connection"):
            # Clear cache and reconnect
            if 'gsheet_cache' in st.session_state:
                del st.session_state['gsheet_cache']
            st.success("Connection refreshed!")
            
    else:
        st.warning("⚠️ Google Sheets not connected")
        
        # Re-upload option
        st.markdown("### 📊 Connect Google Sheets")
        uploaded_file = st.file_uploader(
            "Upload Service Account JSON",
            type=['json'],
            help="Upload your Google Sheets service account JSON file",
            key="sidebar_reupload_service_account"
        )
        
        if uploaded_file is not None:
            try:
                service_account_info = json.load(uploaded_file)
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                
                if all(field in service_account_info for field in required_fields):
                    st.session_state['service_account_info'] = service_account_info
                    
                    # Save to temporary file
                    temp_path = "temp_service_account.json"
                    with open(temp_path, 'w') as f:
                        json.dump(service_account_info, f)
                    
                    st.session_state['service_account_path'] = temp_path
                    st.success("✅ Service account connected!")
                    st.rerun()
                else:
                    st.error("❌ Invalid service account file.")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    st.markdown("---")
    
    # Navigation Menu
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
        ("📞 Call Center", "9_Call_Center")
    ]
    
    current_page = st.session_state.get('current_page', 'Dashboard')
    
    for page_name, page_key in pages:
        if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
            st.session_state['current_page'] = page_key
            update_last_activity()
            st.rerun()
    
    st.markdown("---")
    
    # Quick Stats
    st.subheader("📊 Quick Stats")
    
    try:
        # Display some basic stats
        if 'gsheet_cache' in st.session_state:
            cache_info = st.session_state['gsheet_cache']
            st.metric("Cached Sheets", len(cache_info))
            
            # Show last sync time
            if cache_info:
                last_sync = max([info.get('timestamp', '') for info in cache_info.values()])
                if last_sync:
                    st.info(f"Last sync: {last_sync[:16]}")
        
        # Show session info
        login_time = st.session_state.get('login_time')
        if login_time:
            st.info(f"Session: {login_time[:16]}")
            
    except Exception as e:
        st.error(f"Error loading stats: {str(e)}")
    
    st.markdown("---")
    
    # System Actions
    st.subheader("⚙️ System")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh", key="sidebar_refresh_app"):
            # Clear all caches
            for key in list(st.session_state.keys()):
                if 'cache' in key.lower():
                    del st.session_state[key]
            st.success("App refreshed!")
            st.rerun()
    
    with col2:
        if st.button("🚪 Logout", key="sidebar_logout"):
            logout_user()
            st.rerun()
    
    # Theme Toggle
    st.markdown("---")
    theme = st.selectbox(
        "🎨 Theme",
        ["Light", "Dark", "Auto"],
        index=0 if st.session_state.get('theme', 'light') == 'light' else 1,
        key="sidebar_theme_select"
    )
    
    if theme.lower() != st.session_state.get('theme', 'light'):
        st.session_state['theme'] = theme.lower()
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; color: gray; font-size: 0.8em;'>
            Business Suite v{get_config('version', '2.0.0')}<br>
            {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
        """,
        unsafe_allow_html=True
    )

def cleanup_temp_files():
    """Clean up temporary files on app shutdown"""
    try:
        temp_files = ['temp_service_account.json']
        for file in temp_files:
            if os.path.exists(file):
                os.remove(file)
    except Exception:
        pass

# Register cleanup function
import atexit
atexit.register(cleanup_temp_files)
