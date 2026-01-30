import streamlit as st
from auth import is_authenticated, get_auth_headers, is_admin, logout_and_rerun
from api import admin_get_users, admin_add_tokens, admin_reset_password, admin_delete_user


def show_admin_tab(urls, api_base_url: str):
    st.header("🔐 Admin Dashboard")
    if not is_authenticated():
        st.warning("⚠️ Please log in to access the admin dashboard.")
        return
    if not is_admin(api_base_url):
        st.error("❌ Access Denied: Admin privileges required.")
        return
    
    st.success("✅ Admin access granted")
    st.subheader("Filter Users")
    min_tokens = st.slider(
        "Show users with at least X tokens",
        min_value=0,
        max_value=1000,
        value=0,
        step=1,
        help="Set to 0 to show all users"
    )
    users = []
    try:
        headers = get_auth_headers()
        response = admin_get_users(urls, headers, min_tokens if min_tokens > 0 else None)
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
        elif response.status_code == 401:
            logout_and_rerun()
        elif response.status_code == 403:
            st.error("❌ Access Denied: Admin privileges required.")
            return
        else:
            st.error(f"❌ Failed to fetch users: {response.text}")
            return
    except Exception as e:
        st.error(f"Error fetching users: {e}")
        return
    
    if not users:
        st.info("No users found matching the filter criteria.")
        return
    
    st.subheader(f"Users ({len(users)} found)")
    for user in users:
        user_id = user.get("id")
        email = user.get("email")
        tokens = user.get("tokens", 0)
        is_admin_user = user.get("is_admin", False)
        
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
            
            with col1:
                admin_badge = "👑 Admin" if is_admin_user else ""
                st.write(f"**{email}** {admin_badge}")
            
            with col2:
                st.write(f"**ID:** {user_id}")
            
            with col3:
                st.write(f"**Tokens:** {tokens}")
            
            with col4:
                dialog_key = f"dialog_{user_id}"
                if dialog_key not in st.session_state:
                    st.session_state[dialog_key] = False
                if st.button("⚙️ Actions", key=f"actions_btn_{user_id}", type="secondary"):
                    st.session_state[dialog_key] = not st.session_state.get(dialog_key, False)
            if st.session_state.get(dialog_key, False):
                st.markdown("---")
                with st.container():
                    st.markdown(f"### ⚙️ Actions for {email}")
                    current_user_email = st.session_state.get("user_email")
                    is_current_user = current_user_email and email == current_user_email
                    action_options = ["➕ Add Tokens", "🔑 Reset Password"]
                    if not is_current_user:
                        action_options.append("🗑️ Delete User")
                    action_key = f"action_{user_id}"
                    current_action = st.session_state.get(action_key)
                    if current_action not in action_options:
                        st.session_state[action_key] = action_options[0]
                    
                    action = st.selectbox(
                        "Select Action",
                        action_options,
                        key=action_key
                    )
                    
                    st.divider()
                    if action == "➕ Add Tokens":
                        st.subheader("Add Tokens")
                        credit_card = st.text_input(
                            "Credit Card",
                            key=f"card_{user_id}",
                            placeholder="1234-5678-9012-3456",
                            help="Simulated credit card number"
                        )
                        amount = st.number_input(
                            "Amount",
                            min_value=1,
                            value=10,
                            step=1,
                            key=f"amount_{user_id}"
                        )
                        col_btn1, col_btn2 = st.columns([1, 1])
                        with col_btn1:
                            if st.button("Add Tokens", key=f"add_{user_id}", type="primary"):
                                if not credit_card:
                                    st.error("Please enter a credit card number")
                                else:
                                    try:
                                        headers = get_auth_headers()
                                        response = admin_add_tokens(urls, user_id, headers, email, credit_card, amount)
                                        if response.status_code == 200:
                                            st.success(f"✅ Added {amount} tokens to {email}")
                                            st.session_state[dialog_key] = False
                                            st.rerun()
                                        elif response.status_code == 401:
                                            logout_and_rerun()
                                        else:
                                            st.error(f"❌ Failed: {response.json().get('detail', response.text)}")
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        with col_btn2:
                            if st.button("Cancel", key=f"cancel_add_{user_id}"):
                                st.session_state[dialog_key] = False
                    
                    elif action == "🔑 Reset Password":
                        st.subheader("Reset Password")
                        new_password = st.text_input(
                            "New Password",
                            type="password",
                            key=f"pwd_{user_id}",
                            help="Minimum 4 characters"
                        )
                        col_btn1, col_btn2 = st.columns([1, 1])
                        with col_btn1:
                            if st.button("Reset", key=f"reset_{user_id}", type="primary"):
                                if len(new_password) < 4:
                                    st.error("Password must be at least 4 characters")
                                else:
                                    try:
                                        headers = get_auth_headers()
                                        response = admin_reset_password(urls, user_id, headers, email, new_password)
                                        if response.status_code == 200:
                                            st.success(f"✅ Password reset for {email}")
                                            st.session_state[dialog_key] = False
                                            st.rerun()
                                        elif response.status_code == 401:
                                            logout_and_rerun()
                                        else:
                                            st.error(f"❌ Failed: {response.json().get('detail', response.text)}")
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        with col_btn2:
                            if st.button("Cancel", key=f"cancel_reset_{user_id}"):
                                st.session_state[dialog_key] = False
                    
                    elif action == "🗑️ Delete User":
                        st.subheader("Delete User")
                        if is_current_user:
                            st.error("❌ **You cannot delete your own account.**")
                            if st.button("Close", key=f"close_self_delete_{user_id}"):
                                st.session_state[dialog_key] = False
                        else:
                            st.warning(f"⚠️ **Are you sure you want to delete user '{email}'?**")
                            st.warning("This action cannot be undone. The user and all their trained models will be permanently deleted.")
                            col_btn1, col_btn2 = st.columns([1, 1])
                            with col_btn1:
                                if st.button("Yes, Delete", key=f"yes_{user_id}", type="primary"):
                                    try:
                                        headers = get_auth_headers()
                                        response = admin_delete_user(urls, user_id, headers)
                                        if response.status_code == 200:
                                            st.success(f"✅ User {email} and all models deleted")
                                            st.session_state[dialog_key] = False
                                            st.rerun()
                                        elif response.status_code == 401:
                                            logout_and_rerun()
                                        elif response.status_code == 403:
                                            st.error("❌ You cannot delete your own account.")
                                            st.session_state[dialog_key] = False
                                        else:
                                            st.error(f"❌ Failed: {response.json().get('detail', response.text)}")
                                            st.session_state[dialog_key] = False
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                                        st.session_state[dialog_key] = False
                            with col_btn2:
                                if st.button("Cancel", key=f"cancel_delete_{user_id}"):
                                    st.session_state[dialog_key] = False
                
                st.markdown("---")
            
            st.divider()

