
import streamlit as st
import requests
from github import Github
import os
from PIL import Image
import analysis  # Make sure analysis.py exists and defines show_analysis_page()

# Page configuration
st.set_page_config(
    page_title="DBot - GitHub Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "home"

# ======================= 🔒 GitHub Token Authentication Replaced OAuth =======================
token = st.text_input("🔐 Enter your GitHub Personal Access Token (PAT)", type="password")

if token:
    try:
        github = Github(token)
        user = github.get_user()
        st.session_state["access_token"] = token  # ✅ Save PAT in session state
        st.session_state.authenticated = True
        st.session_state.username = user.login
        st.success(f"✅ Authenticated as: {user.login}")
    except Exception as e:
        st.session_state.authenticated = False
        st.error(f"❌ Authentication failed: {e}")
else:
    st.warning("Please enter your GitHub PAT to authenticate.")

if not st.session_state.get("authenticated", False):
    st.session_state.page = "home"

def create_nav():
    primary_color = "#86BC25"
    secondary_color = "#43B02A"
    text_color = "#333"
    accent_color = "#007CB0"
    nav_height = "60px"
    nav_font_size = "1.2rem"
    cols = st.columns([1, 3, 1])

    with cols[0]:
        st.markdown(f"""
            <div style="display: flex; align-items: center; height: {nav_height};">
                <div style="font-size: 2.2rem; font-weight: 700; color: {text_color};">
                    <span>D<span style="display: inline-block; height: 14px; width: 14px; background-color: {primary_color}; border-radius: 50%; margin-left: 6px;"></span></span>
                    <span style="font-weight: 500;">Bot</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        menu_cols = st.columns(4)
        nav_style = f"""
        <style>
        div[data-testid="column"] div.stButton > button {{
            color: {primary_color};
            background-color: transparent;
            border: 2px solid {accent_color};
            width: 100%;
            font-weight: 600;
            font-size: {nav_font_size};
            margin: 0;
            padding: 0.8rem 0;
            transition: all 0.2s;
            height: {nav_height};
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        div[data-testid="column"] div.stButton > button:hover {{
            color: {text_color};
            background-color: #f0f0f0;
            border-radius: 5px;
            border-color: {accent_color};
        }}
        div[data-testid="column"] div.stButton > button.active {{
            border-bottom: 3px solid {primary_color};
        }}
        </style>
        """
        st.markdown(nav_style, unsafe_allow_html=True)

        with menu_cols[0]:
            home_btn = st.button("Home", key="home_nav", use_container_width=True)
            if home_btn:
                st.session_state.page = "home"
                st.rerun()

        with menu_cols[1]:
            features_btn = st.button("Features", key="features_nav", use_container_width=True)
            if features_btn:
                st.session_state.page = "features"
                st.rerun()

        with menu_cols[2]:
            how_it_works_btn = st.button("How It Works", key="how_it_works_nav", use_container_width=True)
            if how_it_works_btn:
                st.session_state.page = "how_it_works"
                st.rerun()

        with menu_cols[3]:
            if st.session_state.authenticated:
                analysis_btn = st.button("Analysis", key="analysis_nav", use_container_width=True)
                if analysis_btn:
                    st.session_state.page = "analysis"
                    st.rerun()

    with cols[2]:
        if st.session_state.get("authenticated", False):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"<span style='font-size: 1.1rem;'>👤 {st.session_state.username}</span>", unsafe_allow_html=True)
            with col2:
                logout_button = st.button("Logout")
                if logout_button:
                    st.session_state.clear()
                    st.rerun()
        else:
            st.warning("🔐 Not authenticated")

def display_hero():
    image = Image.open("sg-daily-stand-up.png")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image(image, use_column_width=True)
    with col2:
        st.markdown("<h1>Welcome to D-Bot</h1>", unsafe_allow_html=True)

def display_features():
    st.markdown("## 🧠 Features Coming Soon!")

def display_how_it_works():
    st.markdown("## ⚙️ How It Works Coming Soon!")

# Main app logic
create_nav()

if st.session_state.page == "home":
    display_hero()
    display_features()
    display_how_it_works()
elif st.session_state.page == "features":
    display_features()
elif st.session_state.page == "how_it_works":
    display_how_it_works()
elif st.session_state.page == "analysis":
    if st.session_state.authenticated:
        analysis.show_analysis_page()
    else:
        st.warning("Please log in to access the analysis page")
        st.session_state.page = "home"
        st.rerun()
