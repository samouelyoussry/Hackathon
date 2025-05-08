from urllib.parse import urlencode
import streamlit as st
import requests
from github import Github
import os
from PIL import Image
import analysis

# ========== CONFIGURATION ==========
# MUST be first Streamlit command
st.set_page_config(page_title="DBot - GitHub Assistant",
                   page_icon="🤖",
                   layout="wide",
                   initial_sidebar_state="collapsed")

# Official Deloitte Color Scheme
PRIMARY_COLOR = "#86BC25"  # Deloitte Green
SECONDARY_COLOR = "#43B02A"  # Deloitte Green 2
ACCENT_COLOR = "#007CB0"  # Deloitte Blue
DARK_GREEN = "#1E5631"  # Dark Deloitte Green
LIGHT_GREEN = "#DDEBC8"  # Light Deloitte Green
WHITE = "#FFFFFF"
DARK_GRAY = "#333333"
LIGHT_GRAY = "#F5F5F5"

# Background gradient using Deloitte colors
BACKGROUND_GRADIENT = f"linear-gradient(135deg, {WHITE} 0%, {LIGHT_GREEN} 100%)"
CARD_BACKGROUND = f"rgba({WHITE}, 0.95)"
TEXT_COLOR = DARK_GRAY
SECONDARY_TEXT = "#4a5568"

# GitHub Configuration
GITHUB_CLIENT_ID = "Ov23li7VLjufh99QANN9"
GITHUB_CLIENT_SECRET = "1a1a346a1c8bcb35d5a3e8920e05b59f50df05c8"
REDIRECT_URI = "https://standup-bot-1095165959029.us-central1.run.app/"

# ========== SESSION STATE ==========
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "home"
if "github_token" not in st.session_state:
    st.session_state.github_token = None
if "username" not in st.session_state:
    st.session_state.username = None

# ========== FUNCTION DEFINITIONS ==========


def authenticate_with_token(token):
    """Authenticates with GitHub using a provided personal access token."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        user_resp = requests.get("https://api.github.com/user",
                                 headers=headers,
                                 verify=False)
        user_resp.raise_for_status()
        user_data = user_resp.json()
        st.session_state.update({
            "github_token": token,
            "authenticated": True,
            "username": user_data.get("login"),
            "access_token": token
        })
        st.success("✅ Successfully authenticated with GitHub!")
        st.rerun()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Authentication failed: {e}")
        st.session_state.update({
            "authenticated": False,
            "github_token": None,
            "username": None
        })
        return False


def show_login_form():
    """Displays a form for the user to enter their GitHub token."""
    with st.form("github_token_form"):
        st.markdown("### GitHub Authentication")
        token = st.text_input(
            "Enter your GitHub Personal Access Token:",
            type="password",
            help="Create a token with repo access at https://github.com/settings/tokens"
        )

        submitted = st.form_submit_button(
            "Authenticate", type="primary", use_container_width=True)
        if submitted and token:
            authenticate_with_token(token)


def display_hero():
    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        st.markdown(f"""
        <div style="padding: 2rem 1rem;">
            <h1 style="font-size: 3.5rem; font-weight: 800; margin-bottom: 1.5rem; line-height: 1.2;">
                <span style="color: {PRIMARY_COLOR};"></span>
            </h1>
            <p style="font-size: 1.25rem; color: {SECONDARY_TEXT}; margin-bottom: 2rem; max-width: 500px; line-height: 1.6;">
               AI-powered standup reports that analyze your GitHub activity to create insightful daily updates.
            </p>
            <div style="display: flex; gap: 1rem; margin-top: 2.5rem;">
                <a class="primary-btn" href='#how-it-works'" style="padding: 0.85rem 2.25rem; border-radius: 8px; font-size: 1.05rem; cursor: pointer;">
                    Get Started
                </a>
                <a class="secondary-btn" href='#features' style="padding: 0.85rem 2.25rem; border-radius: 8px; font-size: 1.05rem; cursor: pointer;">
                    Learn More
                </a>
            </div>
        </div>
        """,
                    unsafe_allow_html=True)

    with col2:
        try:
            image = Image.open("sg-daily-stand-up.png")
            st.image(image, use_container_width=True)
        except:
            st.image(
                "https://images.unsplash.com/photo-1579389083078-4e7018379f7e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1470&q=80",
                use_column_width=True)


def display_features():
    st.markdown(f"""
    <div id="features" style="padding: 5rem 1rem;">
        <h2 style="text-align: center; font-size: 2.75rem; margin-bottom: 1rem;">
            Powerful Features
        </h2>
        <p style="text-align: center; font-size: 1.15rem; color: {SECONDARY_TEXT}; max-width: 700px; margin: 0 auto 3rem auto;">
            Everything you need to streamline your development workflow
        </p>
    </div>
    """,
                unsafe_allow_html=True)

    features = [{
        "icon": "📊",
        "title": "Standup Analytics",
        "description":
        "Automatically generate insightful standup reports from your GitHub activity",
        "color": PRIMARY_COLOR
    }, {
        "icon": "🔒",
        "title": "Security Scan",
        "description":
        "Identify vulnerabilities and get actionable security recommendations",
        "color": ACCENT_COLOR
    }, {
        "icon": "🧩",
        "title": "Code Quality",
        "description":
        "Get detailed metrics on code maintainability and technical debt",
        "color": SECONDARY_COLOR
    }]

    cols = st.columns(3, gap="large")
    for i, feature in enumerate(features):
        with cols[i]:
            st.markdown(f"""
            <div class="feature-card" style="padding: 2.5rem 2rem; height: 100%;">
                <div style="font-size: 2.5rem; margin-bottom: 1.5rem; color: {feature['color']};">{feature['icon']}</div>
                <h3 style="font-size: 1.5rem; margin-bottom: 1rem;">{feature['title']}</h3>
                <p style="color: {SECONDARY_TEXT}; font-size: 1.05rem; line-height: 1.6;">{feature['description']}</p>
            </div>
            """,
                        unsafe_allow_html=True)


def display_how_it_works():
    st.markdown(f"""
    <div id="how-it-works" style="padding: 5rem 1rem;">
        <h2 style="text-align: center; font-size: 2.75rem; margin-bottom: 1rem;">
            How It Works
        </h2>
        <p style="text-align: center; font-size: 1.15rem; color: {SECONDARY_TEXT}; max-width: 700px; margin: 0 auto 3rem auto;">
            Get started in just 3 simple steps
        </p>
    </div>
    """,
                unsafe_allow_html=True)

    steps = [{
        "number": "1",
        "title": "Connect Your Repo",
        "description": "Authenticate with GitHub to connect your repositories",
        "icon": "🔗"
    }, {
        "number": "2",
        "title": "AI Analysis",
        "description": "Our engine analyzes your code and activity patterns",
        "icon": "🤖"
    }, {
        "number": "3",
        "title": "Get Insights",
        "description": "Receive actionable reports for your standups",
        "icon": "📈"
    }]

    cols = st.columns(3, gap="large")
    for i, step in enumerate(steps):
        with cols[i]:
            st.markdown(f"""
            <div style="position: relative; text-align: center; margin-bottom: 2rem;">
                <div style="background-color: {PRIMARY_COLOR}; color: white; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: bold; margin: 0 auto 1.5rem auto;">
                    {step['number']}
                </div>
                <div class="feature-card" style="padding: 2rem; height: 100%;">
                    <div style="font-size: 2.5rem; margin-bottom: 1rem; color: {PRIMARY_COLOR};">{step['icon']}</div>
                    <h3 style="font-size: 1.4rem; margin-bottom: 1rem;">{step['title']}</h3>
                    <p style="color: {SECONDARY_TEXT}; font-size: 1.05rem; line-height: 1.6;">{step['description']}</p>
                </div>
            </div>
            """,
                        unsafe_allow_html=True)

            if i == 0 and not st.session_state.authenticated:
                show_login_form()


def create_nav():
    nav_height = "80px"

    st.markdown(f"""
    <style>
    .navbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 2rem;
        height: {nav_height};
    }}

    .nav-logo {{
        font-size: 2rem;
        font-weight: 700;
        color: {DARK_GREEN};
    }}

    .nav-logo span {{
        color: {PRIMARY_COLOR};
    }}

    .nav-buttons {{
        display: flex;
        gap: 1rem;
    }}

    .nav-user {{
        display: flex;
        align-items: center;
        gap: 1rem;
    }}

    /* Navigation button hover styles */
    div[data-testid="stHorizontalBlock"] div[data-testid="column"] div.stButton > button {{
        transition: all 0.3s !important;
        border-radius: 8px !important;
        background-color: transparent !important;
        border: 2px solid {PRIMARY_COLOR} !important;
        color: {PRIMARY_COLOR} !important;

    }}

    div[data-testid="stHorizontalBlock"] div[data-testid="column"] div.stButton > button:hover {{
        background-color: {PRIMARY_COLOR} !important;
        color: {DARK_GREEN} !important;
        border-color: {PRIMARY_COLOR} !important;

    }}
    </style>
    """,
                unsafe_allow_html=True)

    cols = st.columns([1, 3, 1])

    with cols[0]:
        st.markdown(f"""
        <div class="navbar">
             <div class="nav-logo" >
            <h1 style="font-size: 3.5rem; font-weight: 800; margin-bottom: 1.5rem; line-height: 1.2; color: {DARK_GREEN};">
                <span style="position: relative; color:{DARK_GREEN}">
                    D<span style="position: absolute; bottom: 1rem; right: -0.1rem; height: 12px; width: 12px; background-color: {PRIMARY_COLOR}; border-radius: 50%;"></span>
                </span>
                <span style="color: {PRIMARY_COLOR}; position: absolute">Bot</span>
            </h1>
            </div>

        """,
                    unsafe_allow_html=True)

    with cols[1]:
        st.markdown("""
        <style>

        /* On hover: turn text green */
        button[data-testid="stBaseButton-secondary"]:hover {
            color:white;
            background:green;
        }
        </style>
        """,
                    unsafe_allow_html=True)

        menu_cols = st.columns(4)
        pages = [("Home", "home"), ("Features", "features"),
                 ("How It Works", "how_it_works"),
                 ("Analysis",
                  "analysis") if st.session_state.authenticated else None]

        for i, (label, page) in enumerate(filter(None, pages)):
            with menu_cols[i]:
                if st.button(label,
                             key=f"{page}_nav",
                             use_container_width=True):
                    st.session_state.page = page
                    st.rerun()

    with cols[2]:
        if st.session_state.get("authenticated"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(
                    f"<div class='nav-user'><span style='font-size: 1.1rem; margin-top: 18px;'>👤 {st.session_state.username}</span></div>",
                    unsafe_allow_html=True)
            with col2:
                st.markdown("""
                <style>
                .logout-btn {
                    margin-left: -10px; /* Adjust this value to move the button left */
                }
                </style>
                """,
                            unsafe_allow_html=True)
            if st.button("Logout", key="logout_btn"):
                st.session_state.clear()
                st.rerun()
        else:
            st.warning("🔑 Please log in with GitHub")
            # add authenticate


# ========== GLOBAL STYLES ==========
st.markdown(f"""
<style>
    /* Base styles */
    html {{
        scroll-behavior: smooth;
        font-family: 'Arial', sans-serif;
    }}

    /* Custom scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: {LIGHT_GRAY};
    }}
    ::-webkit-scrollbar-thumb {{
        background: {PRIMARY_COLOR};
        border-radius: 4px;
    }}

    /* Streamlit overrides */
    .stApp {{
        background: {BACKGROUND_GRADIENT};
    }}

    /* Input focus style */
    div[data-baseweb="input"] input:focus,
    div[data-baseweb="input"]:focus-within {{
        border-color: {PRIMARY_COLOR} !important;
        box-shadow: 0 0 0 1px {PRIMARY_COLOR} !important;
        outline: none !important;
    }}

    h1, h2, h3, h4 {{
        color: {DARK_GREEN} !important;
        font-weight: 700 !important;
    }}

    /* Buttons */
    .stButton>button {{
        border: none !important;
        transition: all 0.3s ease !important;
    }}

    .primary-btn {{
        background-color: {PRIMARY_COLOR} !important;
        color: white !important;
        font-weight: 600 !important;
    }}

    .primary-btn:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(134,188,37,0.3) !important;
    }}

    .secondary-btn {{
        background-color: {WHITE} !important;
        color: {PRIMARY_COLOR} !important;
        border: 2px solid {PRIMARY_COLOR} !important;
        font-weight: 600 !important;
    }}

    /* Cards */
    .feature-card {{
        transition: all 0.3s ease;
        border-radius: 12px;
        border: 1px solid rgba(0,1,0,0.1) !important;
        background: {CARD_BACKGROUND};
    }}

    .feature-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important;
    }}

    /* Navbar */
    [data-testid="stHeader"] {{
        background-color: {WHITE} !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
    }}

    /* Responsive adjustments */
    @media (max-width: 768px) {{
        .hero-columns {{
            flex-direction: column-reverse;
        }}
    }}
</style>
""",
            unsafe_allow_html=True)

# ========== MAIN APP FLOW ==========
create_nav()

if st.session_state.page == "home":
    display_hero()
    display_features()
    display_how_it_works()
elif st.session_state.page == "features":
    st.markdown("<div style='padding-top: 2rem;'></div>",
                unsafe_allow_html=True)
    display_features()
elif st.session_state.page == "how_it_works":
    st.markdown("<div style='padding-top: 2rem;'></div>",
                unsafe_allow_html=True)
    display_how_it_works()
elif st.session_state.page == "analysis":
    if st.session_state.authenticated:
        analysis.show_analysis_page()
    else:
        st.warning("Please log in to access the analysis page")
        show_login_form()
        st.session_state.page = "home"
        st.rerun()
