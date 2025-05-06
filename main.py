import streamlit as st
import requests
from github import Github
import os
from PIL import Image
import analysis

# Load environment variables
# load_dotenv()

# Configuration
GITHUB_CLIENT_ID = "Ov23li7VLjufh99QANN9"
GITHUB_CLIENT_SECRET = "1a1a346a1c8bcb35d5a3e8920e05b59f50df05c8"
# REDIRECT_URI = "https://standup-bot-1095165959029.us-central1.run.app/" 
REDIRECT_URI = "http://localhost:8501/" 
github_auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=read:user user:email"

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

# OAuth URL setup
github_auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=read:user user:email"

# Function to handle GitHub OAuth
def handle_github_auth():        
    # Handle OAuth code
    query_params = st.query_params
    code = query_params.get("code")
    
    if code:
        with st.spinner("Authenticating with GitHub..."):
            # Exchange code for access token
            token_url = "https://github.com/login/oauth/access_token"
            headers = {"Accept": "application/json"}
            data = {
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": REDIRECT_URI
            }
            
            try:
                response = requests.post(token_url, headers=headers, data=data, verify=False)
                if response.status_code == 200:
                    access_token = response.json().get("access_token")
                    if access_token:
                        st.session_state["access_token"] = access_token
                        st.session_state.authenticated = True
                        
                        # Verify token works
                        user_resp = requests.get(
                            "https://api.github.com/user",
                            headers={"Authorization": f"Bearer {access_token}"},
                            verify=False
                        )
                        if user_resp.status_code == 200:
                            user_data = user_resp.json()
                            st.session_state["username"] = user_data.get("login")
                            st.query_params.clear()  # Clean URL
                        else:
                            st.error("Failed to fetch user data")
                            st.session_state.authenticated = False
                            if "access_token" in st.session_state:
                                del st.session_state["access_token"]
                else:
                    st.error(f"Token exchange failed: {response.text}")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")

# Function to create the navigation bar
def create_nav():
    primary_color = "#86BC25"  # Deloitte Green
    secondary_color = "#43B02A" # Green 4
    text_color = "#333"
    accent_color = "#007CB0" # Accessible blue

    nav_height = "60px" # Increased height
    nav_font_size = "1.2rem" # Increased font size
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
        nav_style = """
       <style>
        div[data-testid="column"] div.stButton > button {
            color: {primary_color};
            background-color: transparent;
            border: 2px solid {accent_color};
            width: 100%;
            font-weight: 600;
            font-size: {nav_font_size};
            margin: 0;
            padding: 0.8rem 0; /* Adjusted padding for increased height */
            transition: all 0.2s;
            height: {nav_height}; /* Match nav height */
            display: flex;
            justify-content: center;
            align-items: center;
        }
        div[data-testid="column"] div.stButton > button:hover {
            color: {text_color};
            background-color: #f0f0f0;
            border-radius: 5px;
            border-color: {accent_color}; 
        }
        div[data-testid="column"] div.stButton > button.active {
            border-bottom: 3px solid {primary_color};
        }
        </style>
        """
        st.markdown(nav_style, unsafe_allow_html=True)
        
        with menu_cols[0]:
            st.markdown(f"""
                <style>
                div[data-testid="column"]:nth-child(1) div.stButton > button {{
                    background-color: transparent; 
                    border: 2px solid {primary_color};
                }}
                div[data-testid="column"]:nth-child(1) div.stButton > button:hover {{
                    background-color: {text_color};
                    color: {primary_color};
                }}
                </style>
            """, unsafe_allow_html=True)
            home_btn = st.button("Home", key="home_nav", use_container_width=True)
            if home_btn:
                st.session_state.page = "home"
                st.rerun()
                
        with menu_cols[1]:
            st.markdown(f"""
                <style>
                div[data-testid="column"]:nth-child(2) div.stButton > button {{
                   background-color: transparent;
                   border: 2px solid {primary_color};
                }}
                div[data-testid="column"]:nth-child(2) div.stButton > button:hover {{
                    background-color: {text_color};
                    color: {secondary_color};
                }}
                </style>
            """, unsafe_allow_html=True)
            features_btn = st.button("Features", key="features_nav", use_container_width=True)
            if features_btn:
                st.session_state.page = "features"
                st.rerun()
                
        with menu_cols[2]:
            st.markdown(f"""
                <style>
                div[data-testid="column"]:nth-child(3) div.stButton > button {{
                    background-color: transparent;
                    border: 2px solid {primary_color};
                }}
                div[data-testid="column"]:nth-child(3) div.stButton > button:hover {{
                    background-color: {text_color};
                    color: {secondary_color};
                }}
                </style>
            """, unsafe_allow_html=True)
            how_it_works_btn = st.button("How It Works", key="how_it_works_nav", use_container_width=True)
            if how_it_works_btn:
                st.session_state.page = "how_it_works"
                st.rerun()
                
        with menu_cols[3]:
            st.markdown(f"""
                    <style>
                    div[data-testid="column"]:nth-child(4) div.stButton > button {{
                          background-color: transparent;
                          border: 2px solid {primary_color};
                    }}
                    div[data-testid="column"]:nth-child(4) div.stButton > button:hover {{
                       background-color: {text_color};
                       color: {secondary_color};
                    }}
                    </style>
                """, unsafe_allow_html=True)
            if st.session_state.authenticated:
                analysis_btn = st.button("Analysis", key="analysis_nav", use_container_width=True)
                if analysis_btn:
                    st.session_state.page = "analysis"
                    st.rerun()
    
    with cols[2]:
        st.markdown(f"""
                    <style>
                    .stButton>button {{
                        width: 100%;
                        height: {nav_height};
                        font-size: {nav_font_size};
                        color: {text_color};
                        background-color: {primary_color};
                        border: none;
                        border-radius: 6px;
                    }}
                    .stButton>button:hover {{
                        color: {accent_color};
                        background-color: {text_color};
                        border: 1px solid {accent_color};
                    }}
                    </style>
                """, unsafe_allow_html=True)
        if st.session_state.get("authenticated", False):
           col1, col2 = st.columns([2, 1])
           with col1:
            st.markdown(f"<span style='font-size: 1.1rem;'>👤 {st.session_state.username}</span>", unsafe_allow_html=True)
           with col2:
            logout_button = st.button("Logout")
            if logout_button:
                st.session_state.clear()
                st.rerun()
            st.markdown("""
                <style>
                .stButton>button {
                    width: 101%;
                    height: {nav_height}; /* Match nav height */
                    font-size: {nav_font_size}; /* Increased font size */
                }
                </style>
            """, unsafe_allow_html=True)
            
        else:
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-end;">
                <a href="{github_auth_url}" target="_self" style="text-decoration: none;">
                    <button style="padding: 8px 16px; background-color: #24292e; color: white; border: none; border-radius: 6px; font-size: 0.9rem; cursor: pointer; display: flex; align-items: center; gap: 8px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                        </svg>
                        Login
                    </button>
                </a>
            </div>
            """, unsafe_allow_html=True)

# Function to display hero section
def display_hero():
    image = Image.open("sg-daily-stand-up.png") # Replace "your_image.png" with the actual path to your image

    col1, col2 = st.columns([1, 1]) # Adjust the ratio [image_width, text_width]

    with col1:
        st.image(image, use_column_width=True)

    with col2:
        st.markdown("""
        <div style="padding: 2rem 1rem;">
            <h1 style="font-size: 3rem; font-weight: 700; margin-bottom: 1rem;">
                <span style="position: relative; display: inline-block;">
                    D<span style="position: absolute; bottom: 0.2rem; right: -0.4rem; height: 10px; width: 10px; background-color: #22c55e; border-radius: 50%; box-shadow: 0 0 4px rgba(34,197,94,0.4);"></span>
                </span>
                <span style="font-weight: 500;">Bot</span>
            </h1>
            <p style="font-size: 1.15rem; color:#63666A ; margin-bottom: 2rem; max-width: 500px;">
               Elevate your daily stand-up reporting with the insightful assistance of D-Bot. It intelligently structures your reflections on yesterday's endeavors, clarifies your focus for today, and highlights critical dependencies or obstacles requiring attention.
            </p>
            <p style="font-size: 1.15rem; color: #000000; margin-bottom: 2rem; max-width: 500px;">
                     Ready to experience the power of D-Bot ?
            </p>
            <a href="#how-it-works" style="text-decoration: none;">
                <button style="padding: 0.75rem 2rem; background-color: #26890D; color: white; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; box-shadow: 0 4px 6px rgba(79, 70, 229, 0.2); transition: all 0.2s;">
                    Let's Start
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

# Function to display features section
def display_features():
    st.markdown("""
    <div id="features" style="padding: 4rem 1rem;">
        <h2 style="text-align: center; font-size: 2.5rem; font-weight: 700; margin-bottom: 3rem; color: #1e293b;">
            Intelligent Features
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background-color: white; padding: 2rem; border-radius: 1rem; height: 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.05); transition: transform 0.3s ease, box-shadow 0.3s ease;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem; color: #4f46e5;">📝</div>
            <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.75rem; color: #111827;">Standup Meeting Notes</h3>
            <p style="color: #6b7280; font-size: 1rem;">Keep track of your daily standup meetings, what was done, and what's planned.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background-color: white; padding: 2rem; border-radius: 1rem; height: 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.05); transition: transform 0.3s ease, box-shadow 0.3s ease;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem; color: #4f46e5;">🔍</div>
            <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.75rem; color: #111827;">Security Analysis</h3>
            <p style="color: #6b7280; font-size: 1rem;">Detect security vulnerabilities and receive guidance to fix potential issues.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background-color: white; padding: 2rem; border-radius: 1rem; height: 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.05); transition: transform 0.3s ease, box-shadow 0.3s ease;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem; color: #4f46e5;">🧠</div>
            <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.75rem; color: #111827;">Code Quality</h3>
            <p style="color: #6b7280; font-size: 1rem;">Get insights on code quality, complexity and maintainability with actionable tips.</p>
        </div>
        """, unsafe_allow_html=True)

# Function to display how it works section
def display_how_it_works():
    st.markdown("""
    <div id="how-it-works" style="padding: 4rem 1rem;">
        <h2 style="text-align: center; font-size: 2.5rem; font-weight: 700; margin-bottom: 3rem; color: #1e293b;">
            How It Works
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background-color: #f9fafb; padding: 2rem; border-radius: 1rem; position: relative; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); height: 100%;">
        <div style="font-size: 1.2rem; font-weight: bold; background-color: #26890D; color: white; padding: 0.9rem 1rem; border-radius: 999px; position: absolute; top: -18px; left: 50%; transform: translateX(-50%);">1</div>
            <h3 style="font-size: 1.3rem; font-weight: 600; margin-top: 1rem; margin-bottom: 1rem; color: #111827;">Connect Your Codebase</h3>
            <p style="font-size: 0.95rem; color: #6b7280; margin-bottom: 1.5rem;">Simply connect your repository or upload your code files to get started.</p>
        """, unsafe_allow_html=True)
        
        if not st.session_state.authenticated:
            st.markdown(f"""
            <div style="margin-top: 1rem;">
                <a href="{github_auth_url}" target="_self" style="text-decoration: none;">
                    <button style="padding: 10px 20px; background-color: #24292e; color: white; border: none; border-radius: 6px; cursor: pointer; display: inline-flex; align-items: center; gap: 8px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                        </svg>
                        Login with GitHub
                    </button>
                </a>
            </div>
            """, unsafe_allow_html=True)        
        else:
            st.markdown("""
            <div style="margin-top: 1rem;">
                <button style="padding: 10px 20px; background-color: #26890D; color: white; border: none; border-radius: 6px; cursor: pointer;">
                    ✓ Connected
                </button>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background-color: #f9fafb; padding: 2rem; border-radius: 1rem; position: relative; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); height: 100%;">
<div style="font-size: 1.2rem; font-weight: bold; background-color: #26890D; color: white; padding: 0.9rem 1rem; border-radius: 999px; position: absolute; top: -18px; left: 50%; transform: translateX(-50%);">2</div>
            <h3 style="font-size: 1.3rem; font-weight: 600; margin-top: 1rem; margin-bottom: 1rem; color: #111827;">AI Analysis</h3>
            <p style="font-size: 0.95rem; color: #6b7280;">Our engine reads and understands your code structure and intent, analyzing patterns and potential issues.</p>
            <div style="margin-top: 1.5rem;">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="1 4 1 10 7 10"></polyline>
                    <polyline points="23 20 23 14 17 14"></polyline>
                    <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
                </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background-color: #f9fafb; padding: 2rem; border-radius: 1rem; position: relative; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); height: 100%;">
        <div style="font-size: 1.2rem; font-weight: bold; background-color: #26890D; color: white; padding: 0.9rem 1rem; border-radius: 999px; position: absolute; top: -18px; left: 50%; transform: translateX(-50%);">3</div>
            <h3 style="font-size: 1.3rem; font-weight: 600; margin-top: 1rem; margin-bottom: 1rem; color: #111827;">Receive Insights</h3>
            <p style="font-size: 0.95rem; color: #6b7280;">Get detailed analysis with performance metrics, security issues, and quality insights for your standups.</p>
            <div style="margin-top: 1.5rem;">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)
st.markdown(
        """
        <style>
        body {
            background: linear-gradient(to bottom, #FFFFFF, #DDEFE8); /* White DDEFE8 Light Green */
            background-attachment: fixed; /* Optional: keeps the gradient fixed during scrolling */
        }
        .stApp { /* This targets the main app container */
            background-color: transparent; /* Make the default Streamlit background transparent */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
# Main app flow
handle_github_auth()
create_nav()
if st.session_state.page == "home":
    display_hero()
    display_features()
    display_how_it_works()
elif st.session_state.page == "features":
    st.markdown("<div style='padding-top: 2rem;'></div>", unsafe_allow_html=True)
    display_features()
elif st.session_state.page == "how_it_works":
    st.markdown("<div style='padding-top: 2rem;'></div>", unsafe_allow_html=True)
    display_how_it_works()
elif st.session_state.page == "chatbot":
    if st.session_state.authenticated:
        chatbot.show_chatbot_page()
    else:
        st.warning("Please log in to access the analysis page")
        st.session_state.page = "home"
        st.rerun()
elif st.session_state.page == "analysis":
    if st.session_state.authenticated:
        analysis.show_analysis_page()
    else:
        st.warning("Please log in to access the analysis page")
        st.session_state.page = "home"
        st.rerun()
