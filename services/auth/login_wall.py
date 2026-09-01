import streamlit as st
from services.persistence.exercise_repository import get_or_create_user

def render_login_wall():
    if st.session_state.get("user_id") is not None:
        return True

    #title start
    col1, col2 = st.columns([0.15, 0.85], vertical_alignment="center")
    with col1:
        st.image(r"C:/Users/Gopal Kaushik/Downloads/gym.png", width=60)
    with col2:
        st.title("AI REAL-TIME GYM TRAINER")
    #title end


    st.markdown("### Welcome! Please enter a user name to start.")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Name (unique)", placeholder="unique name e.g. Gopal")
        submit_button = st.form_submit_button("Start Session", use_container_width=True)
        
        if submit_button:
            if not username:
               st.error("Name cannot be empty.")
               return False
            
            user = get_or_create_user(username)

            st.session_state["username"]= user["username"]
            st.session_state["user_id"] = user["id"]
    
            st.rerun()

    return False 