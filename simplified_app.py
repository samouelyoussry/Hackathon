import streamlit as st
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time

# Page configuration
st.set_page_config(
    page_title="DBot - GitHub Assistant", 
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "Ov23li7VLjufh99QANN9")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "1a1a346a1c8bcb35d5a3e8920e05b59f50df05c8")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8501/")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "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")

# OAuth URL setup
github_auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=read:user user:email repo"

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "home"
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "repos" not in st.session_state:
    st.session_state.repos = []
if "selected_repo" not in st.session_state:
    st.session_state.selected_repo = None
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

# Handle GitHub OAuth flow
def handle_github_auth():
    # Check for direct token
    if not st.session_state.get("access_token") and GITHUB_TOKEN:
        st.session_state["access_token"] = GITHUB_TOKEN
        st.session_state.authenticated = True
        
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
                            # Fetch repos after successful auth
                            fetch_user_repos(access_token)
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

# Helper function to fetch user repositories
def fetch_user_repos(token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        repos_resp = requests.get(
            "https://api.github.com/user/repos",
            headers=headers,
            params={"per_page": 100, "sort": "updated"},
            verify=False
        )
        
        if repos_resp.status_code == 200:
            repos = repos_resp.json()
            st.session_state.repos = repos
            return repos
        else:
            st.error(f"Failed to fetch repositories: {repos_resp.status_code}")
            return []
    except Exception as e:
        st.error(f"Error connecting to GitHub: {str(e)}")
        return []

# Helper function to fetch repository commits
def fetch_repo_commits(repo_name, token, days=1):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        commits_resp = requests.get(
            f"https://api.github.com/repos/{repo_name}/commits",
            headers=headers,
            params={"since": since_date},
            verify=False
        )
        
        if commits_resp.status_code == 200:
            commits = commits_resp.json()
            
            # Extract required commit info
            commit_data = []
            for commit in commits:
                # Get detailed commit info with file changes
                detailed_commit_resp = requests.get(
                    commit["url"],
                    headers=headers,
                    verify=False
                )
                
                if detailed_commit_resp.status_code == 200:
                    detailed_commit = detailed_commit_resp.json()
                    
                    # Format date
                    commit_date = datetime.strptime(
                        detailed_commit["commit"]["author"]["date"], 
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
                    
                    commit_data.append({
                        'time': commit_date.strftime("%H:%M"),
                        'date': commit_date.strftime("%Y-%m-%d"),
                        'message': detailed_commit["commit"]["message"].split("\n")[0][:50],
                        'changes': f"+{detailed_commit.get('stats', {}).get('additions', 0)}/-{detailed_commit.get('stats', {}).get('deletions', 0)}",
                        'files': len(detailed_commit.get("files", [])),
                        'url': detailed_commit["html_url"]
                    })
            
            return pd.DataFrame(commit_data)
        else:
            st.error(f"Failed to fetch commits: {commits_resp.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching commits: {str(e)}")
        return pd.DataFrame()

# CSS for animations and smooth transitions
st.markdown("""
<style>
    /* Global animations */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideInUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    /* Hero section animations */
    .hero-content {
        animation: fadeIn 0.9s ease-out;
    }
    
    .hero-title {
        animation: slideInUp 0.8s ease-out;
    }
    
    .hero-description {
        animation: slideInUp 1s ease-out;
    }
    
    .hero-cta {
        animation: slideInUp 1.2s ease-out;
    }
    
    /* Feature card hover animation */
    .feature-card {
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.1);
    }
    
    /* Smooth transitions for all elements */
    * {
        transition: all 0.2s ease;
    }
    
    /* Button animations */
    button, .button {
        transition: background-color 0.3s, transform 0.2s, box-shadow 0.3s;
    }
    
    button:hover, .button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Nav menu with highlight effect */
    .nav-item {
        position: relative;
        padding: 0.5rem 0;
    }
    
    .nav-item:after {
        content: "";
        position: absolute;
        left: 0;
        bottom: 0;
        width: 0%;
        height: 2px;
        background-color: #4f46e5;
        transition: width 0.3s ease;
    }
    
    .nav-item:hover:after, .nav-item.active:after {
        width: 100%;
    }
    
    /* Card hover effects */
    .card-hover {
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .card-hover:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.08);
    }
    
    /* Logo animation */
    .logo-pulse {
        animation: pulse 2s infinite;
    }
            
    .stAppToolbar.st-emotion-cache-15ecox0.e4hpqof2{
            display: none;
    }       
    
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.4);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(79, 70, 229, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(79, 70, 229, 0);
        }
    }
    
    /* Smooth scrolling */
    html {
        scroll-behavior: smooth;
    }
    </style>
""", unsafe_allow_html=True)

# Function to create the navigation bar
def create_nav():
    cols = st.columns([1, 3, 1])
    
    with cols[0]:
        # Create a state key to track if logo was clicked
        if "logo_clicked" not in st.session_state:
            st.session_state.logo_clicked = False
            
        # Using a custom HTML element with click handler that sets a query param
        # and pure CSS styling for the icon
        logo_html = """
        <div>
            <a href="?home=true" style="text-decoration: none; cursor: pointer;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #333; display: flex; align-items: center;">
                    <span style="position: relative;">
                        D<span style="position: absolute; bottom: 0px; right: -5px; height: 8px; width: 8px; background-color: #22c55e; border-radius: 50%; margin-left: 2px; animation: pulse 2s infinite;"></span>
                    </span>
                    <span style="font-weight: 500; margin-left: 3px;">Bot</span>
                </div>
            </a>
            <style>
                @keyframes pulse {
                    0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
                    70% { box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
                    100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
                }
            </style>
        </div>
        """
        st.markdown(logo_html, unsafe_allow_html=True)
        
        # Check for the home param in URL
        query_params = st.query_params
        if query_params.get("home") == "true":
            # Clear the param and navigate to home
            query_params.clear()
            st.session_state.page = "home"
            st.rerun()
    
    with cols[1]:
        menu_cols = st.columns(3)
        nav_style = """
        <style>
        div[data-testid="column"] div.stButton > button {
            background-color: transparent;
            color: #4f46e5;
            border: none;
            width: 100%;
            font-weight: 500;
            font-size: 0.9rem;
            margin: 0;
            padding: 0.5rem 0;
            transition: all 0.2s;
        }
        div[data-testid="column"] div.stButton > button:hover {
            color: #1a1a1a;
            background-color: #f0f0f0;
            border-radius: 5px;
        }
        div[data-testid="column"] div.stButton > button.active {
            border-bottom: 2px solid #4f46e5;
        }
        </style>
        """
        st.markdown(nav_style, unsafe_allow_html=True)
        
        with menu_cols[0]:
            # Removed Home button
            st.markdown("", unsafe_allow_html=True)
                
        with menu_cols[1]:
            how_it_works_btn = st.button("How It Works", key="how_it_works_nav", use_container_width=True)
            if how_it_works_btn:
                st.session_state.page = "how_it_works"
                st.rerun()
                
        with menu_cols[2]:
            if st.session_state.authenticated:
                analysis_btn = st.button("Analysis", key="analysis_nav", use_container_width=True)
                if analysis_btn:
                    st.session_state.page = "analysis"
                    st.rerun()
    
    with cols[2]:
        if st.session_state.authenticated:
            if "username" in st.session_state:
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; align-items: center; gap: 10px;">
                    <span style="color: #4b5563;">👤 {st.session_state.username}</span>
                    <button style="padding: 5px 10px; background-color: #f3f4f6; border: none; border-radius: 4px; color: #4b5563; font-size: 0.8rem; cursor: pointer;" onclick="window.location.href='/logout'">Logout</button>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-end;">
                <a href="{github_auth_url}" target="_self" style="text-decoration: none;">
                    <button style="padding: 8px 16px; background-color: #24292e; color: white; border: none; border-radius: 6px; font-size: 0.9rem; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: transform 0.2s ease, box-shadow 0.2s ease;">
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
    st.markdown("""
    <div class="hero-content" style="text-align: center; padding: 4rem 1rem;">
        <h1 class="hero-title" style="font-size: 3.5rem; font-weight: 700; margin-bottom: 1rem;">
            <span style="position: relative; display: inline-block;">
                D<span style="position: absolute; bottom: 0.2rem; right: -0.4rem; height: 10px; width: 10px; background-color: #22c55e; border-radius: 50%; box-shadow: 0 0 4px rgba(34,197,94,0.4);"></span>
            </span>
            <span style="font-weight: 500;">Bot</span>
        </h1>
        <p class="hero-description" style="font-size: 1.25rem; color: #6b7280; margin-bottom: 2rem; max-width: 600px; margin-left: auto; margin-right: auto;">
            Your silent coding partner. Get smarter suggestions, faster workflows, and better code quality insights.
        </p>
        <a href="#features" class="hero-cta" style="text-decoration: none;">
            <button style="padding: 0.75rem 2rem; background-color: #4f46e5; color: white; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; box-shadow: 0 4px 6px rgba(79, 70, 229, 0.2); transition: all 0.2s;">
                Explore Features
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

# Function to display features section
def display_features():
    st.markdown("""
    <div id="features" style="padding: 4rem 1rem; background-color: #f9fafb; scroll-margin-top: 80px;">
        <h2 style="text-align: center; font-size: 2.5rem; font-weight: 700; margin-bottom: 3rem; color: #1e293b;">
            Intelligent Features
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card" style="background-color: white; padding: 2rem; border-radius: 1rem; height: 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="font-size: 2.5rem; margin-bottom: 1rem; color: #4f46e5;">📝</div>
            <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.75rem; color: #111827;">Standup Meeting Notes</h3>
            <p style="color: #6b7280; font-size: 1rem;">Keep track of your daily standup meetings, what was done, and what's planned.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card" style="background-color: white; padding: 2rem; border-radius: 1rem; height: 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="font-size: 2.5rem; margin-bottom: 1rem; color: #4f46e5;">🔍</div>
            <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.75rem; color: #111827;">Security Analysis</h3>
            <p style="color: #6b7280; font-size: 1rem;">Detect security vulnerabilities and receive guidance to fix potential issues.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card" style="background-color: white; padding: 2rem; border-radius: 1rem; height: 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="font-size: 2.5rem; margin-bottom: 1rem; color: #4f46e5;">🧠</div>
            <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.75rem; color: #111827;">Code Quality</h3>
            <p style="color: #6b7280; font-size: 1rem;">Get insights on code quality, complexity and maintainability with actionable tips.</p>
        </div>
        """, unsafe_allow_html=True)

# Function to display how it works section
def display_how_it_works():
    st.markdown("""
    <div id="how-it-works" style="padding: 4rem 1rem; scroll-margin-top: 80px;">
        <h2 style="text-align: center; font-size: 2.5rem; font-weight: 700; margin-bottom: 3rem; color: #1e293b;">
            How It Works
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card-hover" style="background-color: #f9fafb; padding: 2rem; border-radius: 1rem; position: relative; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); height: 100%;">
            <div style="font-size: 0.9rem; font-weight: bold; background-color: #4f46e5; color: white; padding: 0.3rem 0.75rem; border-radius: 999px; position: absolute; top: -12px; left: 50%; transform: translateX(-50%);">01</div>
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
                <button style="padding: 10px 20px; background-color: #22c55e; color: white; border: none; border-radius: 6px; cursor: pointer;">
                    ✓ Connected
                </button>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card-hover" style="background-color: #f9fafb; padding: 2rem; border-radius: 1rem; position: relative; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); height: 100%;">
            <div style="font-size: 0.9rem; font-weight: bold; background-color: #4f46e5; color: white; padding: 0.3rem 0.75rem; border-radius: 999px; position: absolute; top: -12px; left: 50%; transform: translateX(-50%);">02</div>
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
        <div class="card-hover" style="background-color: #f9fafb; padding: 2rem; border-radius: 1rem; position: relative; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); height: 100%;">
            <div style="font-size: 0.9rem; font-weight: bold; background-color: #4f46e5; color: white; padding: 0.3rem 0.75rem; border-radius: 999px; position: absolute; top: -12px; left: 50%; transform: translateX(-50%);">03</div>
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

# Analysis placeholder
def generate_standup_notes(commits_df):
    """Generate standup notes from commit data"""
    if commits_df.empty:
        return "No commits found in the selected time period."
    
    # Extract commit times to estimate focus time
    try:
        times = sorted([datetime.strptime(t, "%H:%M").time() for t in commits_df['time'].unique()])
        if times:
            time_range = f"{times[0].strftime('%H:%M')} - {times[-1].strftime('%H:%M')}"
        else:
            time_range = "No time data available"
    except:
        time_range = "Unable to determine time range"
    
    # Count code changes
    total_files = commits_df['files'].sum() if 'files' in commits_df else 0
    
    # Extract additions and deletions
    additions = 0
    deletions = 0
    for change in commits_df['changes']:
        if isinstance(change, str) and '+' in change and '/-' in change:
            try:
                parts = change.split('/-')
                add_part = parts[0].strip('+')
                del_part = parts[1]
                
                additions += int(add_part)
                deletions += int(del_part)
            except:
                pass
    
    # Generate key accomplishments based on commit messages
    accomplishments = []
    for msg in commits_df['message'].unique():
        if msg not in accomplishments:
            accomplishments.append(msg)
    
    # Format the standup notes
    notes = f"""
    ## 🏆 Key accomplishments
    """
    
    for i, acc in enumerate(accomplishments[:5]):  # Limit to 5 accomplishments
        notes += f"* {acc}\n"
    
    notes += f"""
    ## ⏱ Estimated focus time
    * Working hours: {time_range}
    * Files changed: {total_files}
    * Code changes: +{additions}/-{deletions}
    
    ## 🚧 Potential blockers
    * Integration issues may need to be addressed
    * Code reviews pending for recent changes
    
    ## ➡️ Recommended next steps
    * Write tests for new changes
    * Document the implemented features
    * Share updates with the team
    """
    
    return notes

def generate_code_insights(commits_df):
    """Generate code insights based on commit data"""
    if commits_df.empty:
        return "No commits found to analyze."
    
    # Calculate average changes per commit
    avg_files = commits_df['files'].mean() if 'files' in commits_df else 0
    
    # Extract most modified files (if available)
    most_modified = "Not available in the current data"
    
    # Calculate commit frequency
    try:
        dates = commits_df['date'].unique() if 'date' in commits_df else []
        frequency = len(commits_df) / len(dates) if dates else 0
        frequency_text = f"{frequency:.1f} commits per day"
    except:
        frequency_text = "Unable to determine frequency"
    
    # Format the insights
    insights = f"""
    ## Code changes impact
    * Average files changed per commit: {avg_files:.1f}
    * Commit frequency: {frequency_text}
    * Most commits on: {', '.join(commits_df['date'].unique()[:3]) if 'date' in commits_df else 'Not available'}
    
    ## Potential areas of focus
    * Files with frequent changes may need refactoring
    * Consider creating unit tests for modified components
    * Documentation should be updated for changed functionality
    
    ## Code quality recommendations
    * Review changes with high line count (+50 lines)
    * Consider breaking down large commits into smaller ones
    * Ensure consistent coding style and naming conventions
    """
    
    return insights

def display_analysis():
    st.markdown("""
    <style>
    .ai-header {
        background: linear-gradient(90deg, #4f46e5, #7b68ee);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .github-card {
        border: 1px solid #e1e4e8;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        background-color: white;
    }
    .repo-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid #4f46e5;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .repo-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .analysis-section {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-top: 20px;
    }
    .ai-badge {
        background-color: #4f46e5;
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="ai-header">
        <h1>📊 GitHub Repository Analysis</h1>
        <p>Powered by AI to help you prepare for daily standups and gain code insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.authenticated:
        # Check if we have the token and refresh repos if needed
        if st.session_state.access_token and (not st.session_state.repos or len(st.session_state.repos) == 0):
            with st.spinner("Fetching your repositories..."):
                fetch_user_repos(st.session_state.access_token)
        
        if st.session_state.repos and len(st.session_state.repos) > 0:
            st.markdown('<div class="github-card">', unsafe_allow_html=True)
            
            # Repository selection with improved UI
            repo_options = [repo["full_name"] for repo in st.session_state.repos]
            
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_repo = st.selectbox(
                    "📂 Choose a repository to analyze",
                    repo_options,
                    index=0 if repo_options else None,
                    format_func=lambda x: x.split('/')[-1] if x else "Select a repository"
                )
            
            with col2:
                refresh_btn = st.button("🔄 Refresh Repos", use_container_width=True)
                if refresh_btn:
                    with st.spinner("Refreshing repositories..."):
                        fetch_user_repos(st.session_state.access_token)
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            if selected_repo:
                st.session_state.selected_repo = selected_repo
                
                with st.form("analyze_form"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write("📊 Configure your analysis:")
                    
                    with col2:
                        days = st.number_input(
                            "Days to analyze:",
                            min_value=1,
                            max_value=30,
                            value=1,
                            help="Number of days of commit history to analyze"
                        )
                    
                    submitted = st.form_submit_button("Generate Analysis Report", use_container_width=True)
                    
                    if submitted:
                        with st.spinner("Fetching and analyzing your commits..."):
                            # Fetch commit data
                            commits_df = fetch_repo_commits(selected_repo, st.session_state.access_token, days)
                            
                            if not commits_df.empty:
                                st.session_state.analysis_results = {
                                    "commits_df": commits_df,
                                    "standup_notes": generate_standup_notes(commits_df),
                                    "code_insights": generate_code_insights(commits_df),
                                    "days": days
                                }
                                st.success("Analysis completed!")
                            else:
                                st.warning(f"No commits found in the last {days} day(s) for this repository.")
                
                # Display analysis results if available
                if st.session_state.analysis_results and st.session_state.selected_repo == selected_repo:
                    st.markdown("""
                    <div class="analysis-section">
                        <div class="ai-badge">AI-Generated</div>
                        <h2>📝 Standup Meeting Notes</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display commit data
                    with st.expander("View Commit Data", expanded=True):
                        st.dataframe(
                            st.session_state.analysis_results["commits_df"],
                            column_config={
                                "time": st.column_config.TextColumn("Time"),
                                "date": st.column_config.TextColumn("Date"),
                                "message": st.column_config.TextColumn("Message"),
                                "changes": st.column_config.TextColumn("Changes"),
                                "files": st.column_config.NumberColumn("Files"),
                                "url": st.column_config.LinkColumn("Link")
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    # Display AI analysis with enhanced UI - single column professional layout
                    st.markdown("""
                    <style>
                    .dashboard-container {
                        display: grid;
                        grid-template-columns: 1fr;
                        gap: 24px;
                    }
                    .analysis-card {
                        background-color: white;
                        border-radius: 12px;
                        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
                        overflow: hidden;
                    }
                    .card-header {
                        padding: 16px 20px;
                        border-bottom: 1px solid #e5e7eb;
                        background: linear-gradient(90deg, #4f46e5, #6366f1);
                        color: white;
                    }
                    .card-content {
                        padding: 20px;
                    }
                    .stat-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 16px;
                        margin-bottom: 20px;
                    }
                    .stat-card {
                        background-color: #f9fafb;
                        border-radius: 8px;
                        padding: 16px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        text-align: center;
                    }
                    .stat-value {
                        font-size: 1.5rem;
                        font-weight: 700;
                        color: #4f46e5;
                    }
                    .info-panel {
                        background-color: #f9fafb;
                        border-radius: 8px;
                        padding: 16px;
                        margin-bottom: 16px;
                    }
                    .info-panel-header {
                        display: flex;
                        align-items: center;
                        margin-bottom: 12px;
                    }
                    .info-panel-icon {
                        width: 28px;
                        height: 28px;
                        background-color: #4f46e5;
                        color: white;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-right: 12px;
                    }
                    .timeline-item {
                        padding: 12px 0;
                        border-bottom: 1px solid #e5e7eb;
                        display: flex;
                    }
                    .timeline-bullet {
                        width: 12px;
                        height: 12px;
                        border-radius: 50%;
                        margin-right: 12px;
                        margin-top: 4px;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Start of analysis dashboard
                    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
                    
                    # Overview card with key metrics
                    st.markdown("""
                    <div class="analysis-card">
                        <div class="card-header">
                            <h2 style="margin: 0; font-size: 1.25rem;">Repository Analysis Overview</h2>
                        </div>
                        <div class="card-content">
                            <div class="ai-badge" style="margin-bottom: 16px;">AI-Generated</div>
                    """, unsafe_allow_html=True)
                    
                    # Extract key metrics from data
                    notes = st.session_state.analysis_results["standup_notes"]
                    insights = st.session_state.analysis_results["code_insights"]
                    
                    # Parse and extract key metrics
                    working_hours = "N/A"
                    files_changed = "0"
                    code_changes = "+0/-0"
                    
                    for line in notes.split('\n'):
                        if "Working hours:" in line:
                            working_hours = line.split(":")[-1].strip()
                        elif "Files changed:" in line:
                            files_changed = line.split(":")[-1].strip()
                        elif "Code changes:" in line:
                            code_changes = line.split(":")[-1].strip()
                    
                    # Extract more metrics from insights
                    avg_files = "0"
                    frequency = "0"
                    
                    for line in insights.split('\n'):
                        if "Average files changed per commit:" in line:
                            avg_files = line.split(":")[-1].strip()
                        elif "Commit frequency:" in line:
                            frequency = line.split(":")[-1].strip()
                    
                    # Display metrics grid
                    st.markdown(f"""
                    <div class="stat-grid">
                        <div class="stat-card">
                            <div class="stat-value">{working_hours}</div>
                            <div class="stat-label">Working Hours</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{files_changed}</div>
                            <div class="stat-label">Files Changed</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{code_changes.replace('+', '<span style="color: #22c55e;">+').replace('/-', '</span>/<span style="color: #ef4444;">-') + '</span>'}</div>
                            <div class="stat-label">Code Changes (Add/Del)</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{avg_files}</div>
                            <div class="stat-label">Avg Files/Commit</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{frequency}</div>
                            <div class="stat-label">Commit Frequency</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Close the overview card
                    st.markdown('</div></div>', unsafe_allow_html=True)
                    
                    # Key accomplishments card
                    st.markdown("""
                    <div class="analysis-card">
                        <div class="card-header">
                            <h2 style="margin: 0; font-size: 1.25rem;">🏆 Key Accomplishments</h2>
                        </div>
                        <div class="card-content">
                    """, unsafe_allow_html=True)
                    
                    # Parse and extract accomplishments
                    accomplishments = []
                    for section in notes.split("##"):
                        if "🏆 Key accomplishments" in section:
                            for line in section.split("\n"):
                                if line.strip().startswith("*"):
                                    accomplishments.append(line.strip()[1:].strip())
                    
                    if accomplishments:
                        for i, acc in enumerate(accomplishments):
                            color = ["#4f46e5", "#8b5cf6", "#ec4899", "#f97316", "#eab308"][i % 5]  # Different colors for variety
                            st.markdown(f"""
                            <div class="timeline-item">
                                <div class="timeline-bullet" style="background-color: {color};"></div>
                                <div>{acc}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown('<p>No accomplishments found in the selected time period.</p>', unsafe_allow_html=True)
                    
                    # Close accomplishments card
                    st.markdown('</div></div>', unsafe_allow_html=True)
                    
                    # Create a 2-column layout for the next two sections
                    st.markdown('<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px;">', unsafe_allow_html=True)
                    
                    # Potential blockers card
                    st.markdown("""
                    <div class="analysis-card">
                        <div class="card-header" style="background: linear-gradient(90deg, #dc2626, #ef4444);">
                            <h2 style="margin: 0; font-size: 1.25rem;">🚧 Potential Blockers</h2>
                        </div>
                        <div class="card-content">
                    """, unsafe_allow_html=True)
                    
                    # Parse and extract blockers
                    blockers = []
                    for section in notes.split("##"):
                        if "🚧 Potential blockers" in section:
                            for line in section.split("\n"):
                                if line.strip().startswith("*"):
                                    blockers.append(line.strip()[1:].strip())
                    
                    if blockers:
                        for blocker in blockers:
                            st.markdown(f"""
                            <div class="timeline-item">
                                <div class="timeline-bullet" style="background-color: #dc2626;"></div>
                                <div>{blocker}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown('<p>No blockers identified in the selected time period.</p>', unsafe_allow_html=True)
                    
                    # Close blockers card
                    st.markdown('</div></div>', unsafe_allow_html=True)
                    
                    # Recommended next steps card
                    st.markdown("""
                    <div class="analysis-card">
                        <div class="card-header" style="background: linear-gradient(90deg, #22c55e, #10b981);">
                            <h2 style="margin: 0; font-size: 1.25rem;">➡️ Recommended Next Steps</h2>
                        </div>
                        <div class="card-content">
                    """, unsafe_allow_html=True)
                    
                    # Parse and extract next steps
                    next_steps = []
                    for section in notes.split("##"):
                        if "➡️ Recommended next steps" in section:
                            for line in section.split("\n"):
                                if line.strip().startswith("*"):
                                    next_steps.append(line.strip()[1:].strip())
                    
                    if next_steps:
                        for step in next_steps:
                            st.markdown(f"""
                            <div class="timeline-item">
                                <div class="timeline-bullet" style="background-color: #22c55e;"></div>
                                <div>{step}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown('<p>No next steps suggested for the selected time period.</p>', unsafe_allow_html=True)
                    
                    # Close next steps card
                    st.markdown('</div></div>', unsafe_allow_html=True)
                    
                    # Close the 2-column layout
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Code quality insights
                    st.markdown("""
                    <div class="analysis-card" style="margin-top: 24px;">
                        <div class="card-header" style="background: linear-gradient(90deg, #3b82f6, #60a5fa);">
                            <h2 style="margin: 0; font-size: 1.25rem;">🔎 Code Quality Insights</h2>
                        </div>
                        <div class="card-content">
                    """, unsafe_allow_html=True)
                    
                    # Parse and extract code quality recommendations
                    code_quality = []
                    for section in insights.split("##"):
                        if "Code quality recommendations" in section:
                            for line in section.split("\n"):
                                if line.strip().startswith("*"):
                                    code_quality.append(line.strip()[1:].strip())
                    
                    # Parse and extract focus areas
                    focus_areas = []
                    for section in insights.split("##"):
                        if "Potential areas of focus" in section:
                            for line in section.split("\n"):
                                if line.strip().startswith("*"):
                                    focus_areas.append(line.strip()[1:].strip())
                    
                    # Display code quality and focus areas in 2 columns
                    st.markdown('<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">', unsafe_allow_html=True)
                    
                    # Code quality column
                    st.markdown('<div>', unsafe_allow_html=True)
                    st.markdown('<h3 style="font-size: 1.1rem; margin-bottom: 16px; color: #3b82f6;">✅ Quality Recommendations</h3>', unsafe_allow_html=True)
                    
                    if code_quality:
                        for rec in code_quality:
                            st.markdown(f"""
                            <div class="timeline-item">
                                <div class="timeline-bullet" style="background-color: #3b82f6;"></div>
                                <div>{rec}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown('<p>No code quality recommendations available.</p>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Focus areas column
                    st.markdown('<div>', unsafe_allow_html=True)
                    st.markdown('<h3 style="font-size: 1.1rem; margin-bottom: 16px; color: #f97316;">🔍 Focus Areas</h3>', unsafe_allow_html=True)
                    
                    if focus_areas:
                        for area in focus_areas:
                            st.markdown(f"""
                            <div class="timeline-item">
                                <div class="timeline-bullet" style="background-color: #f97316;"></div>
                                <div>{area}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown('<p>No focus areas identified.</p>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Close the 2-column layout
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Close code quality card
                    st.markdown('</div></div>', unsafe_allow_html=True)
                    
                    # Close the dashboard container
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Export options
                    st.markdown("""
                    <div class="analysis-card" style="margin-top: 24px;">
                        <div class="card-header" style="background: linear-gradient(90deg, #6b7280, #9ca3af);">
                            <h2 style="margin: 0; font-size: 1.25rem;">📥 Export Options</h2>
                        </div>
                        <div class="card-content">
                            <p style="margin-bottom: 16px;">Download your analysis reports in Markdown format</p>
                    """, unsafe_allow_html=True)
                    
                    export_col1, export_col2 = st.columns(2)
                    with export_col1:
                        st.download_button(
                            "📄 Export Standup Notes",
                            st.session_state.analysis_results["standup_notes"],
                            file_name=f"standup_notes_{selected_repo.split('/')[-1]}_{datetime.now().strftime('%Y%m%d')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    with export_col2:
                        st.download_button(
                            "📊 Export Code Insights",
                            st.session_state.analysis_results["code_insights"],
                            file_name=f"code_insights_{selected_repo.split('/')[-1]}_{datetime.now().strftime('%Y%m%d')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                        
                    st.markdown('</div></div>', unsafe_allow_html=True)
        else:
            st.info("No repositories found. Make sure you've granted access to your repositories.")
    else:
        st.markdown("""
        <div class="github-card">
            <h2>Authentication Required</h2>
            <p>Please log in with GitHub to analyze your repositories and generate standup notes.</p>
            <a href="{github_auth_url}" target="_self" style="text-decoration: none;">
                <button style="padding: 10px 20px; background-color: #24292e; color: white; border: none; border-radius: 6px; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; margin-top: 10px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                    </svg>
                    Login with GitHub
                </button>
            </a>
        </div>
        """.format(github_auth_url=github_auth_url), unsafe_allow_html=True)

# Process any pending GitHub authentication
handle_github_auth()

# Main app flow
create_nav()

if st.session_state.page == "home":
    display_hero()
    display_features()
    display_how_it_works()
elif st.session_state.page == "how_it_works":
    display_how_it_works()
elif st.session_state.page == "analysis":
    display_analysis()

# Add some additional UI polish with a footer
st.markdown("""
<footer style="margin-top: 4rem; padding: 2rem 0; border-top: 1px solid #e5e7eb; text-align: center;">
    <p style="color: #6b7280; font-size: 0.875rem;">© 2025 DBot. All rights reserved.</p>
</footer>
""", unsafe_allow_html=True)