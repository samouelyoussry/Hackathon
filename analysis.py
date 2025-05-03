import cron_descriptor
import streamlit as st
import requests
import pandas as pd
import os
import json
from google.cloud.scheduler_v1.services.cloud_scheduler import CloudSchedulerClient  # ✅ correct
from google.cloud.scheduler_v1.types import Job, HttpTarget, HttpMethod   # ✅ required types
#from google.cloud.scheduler_v1.types import Job, HttpTarget  
from datetime import datetime, timedelta
from cron_descriptor import FormatException, get_description
from utils import LocalGitHubLoader, create_analysis_chain, create_url_analysis_chain
from cron_descriptor import get_description

def show_analysis_page():
    st.title("📊 GitHub Repository Analysis")
    
    # ✅ Updated to support GitHub PAT instead of OAuth
    token = st.session_state.get("access_token")
    if token:
        token = st.session_state["access_token"]
        
        # Fetch repositories with improved error handling
        repos = fetch_repositories(token)
        
        if repos:
            with st.container():
                st.subheader("Select Repository")
                
                repo_names = [repo["full_name"] for repo in repos]
                selected_repo = st.selectbox("Choose a repository to analyze:", repo_names)
                
                tab1, tab2, tab3 = st.tabs(["Commit Analysis", "Code Quality", "Security Audit"])
                
                with tab1:
                    show_commit_analysis(selected_repo, token)
                    
                with tab2:
                    st.info("Code quality analysis will be available in the next release.")
                    placeholder = st.empty()
                    placeholder.markdown("""
                    <div style="padding: 2rem; text-align: center; border: 1px dashed #ccc; border-radius: 8px; margin: 1rem 0;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M16 18l2-2-2-2"></path>
                            <path d="M8 18l-2-2 2-2"></path>
                            <path d="M10 12l4 0"></path>
                            <rect x="3" y="5" width="18" height="14" rx="2"></rect>
                        </svg>
                        <p style="margin-top: 1rem; color: #666;">Code quality metrics will be displayed here</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with tab3:
                    st.info("Security audit will be available in the next release.")
                    placeholder = st.empty()
                    placeholder.markdown("""
                    <div style="padding: 2rem; text-align: center; border: 1px dashed #ccc; border-radius: 8px; margin: 1rem 0;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                        </svg>
                        <p style="margin-top: 1rem; color: #666;">Security audit results will be displayed here</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No repositories found or there was an error fetching them.")
    else:
        st.warning("Please log in with GitHub first to access this feature.")

def fetch_repositories(token):
    st.session_state["repos_loading"] = True
    
    try:
        with st.spinner("Fetching your repositories..."):
            # Create a session with SSL verification disabled for development
            repos_session = requests.Session()
            repos_session.verify = False
            headers = {"Authorization": f"Bearer {token}"}
            
            repos_resp = repos_session.get(
                "https://api.github.com/user/repos",
                headers=headers,
                params={"per_page": 100}
            )
            
            if repos_resp.status_code == 200:
                repos = repos_resp.json()
                st.session_state["repos_loading"] = False
                return repos
            else:
                st.error(f"Failed to fetch repositories: {repos_resp.status_code} - {repos_resp.text}")
                st.session_state["repos_loading"] = False
                return []
    except Exception as e:
        st.error(f"Error connecting to GitHub: {str(e)}")
        st.session_state["repos_loading"] = False
        return []

def show_commit_analysis(repo_name, token):
    with st.form("analyze_form"):
        st.markdown("**Configure your analysis**")
        col1, col2 = st.columns(2)
        with col1:
            cron_expression = st.text_input(
                "Schedule (Cron Expression):",
                placeholder="e.g., * * * * * or 0 9 * * MON-FRI",
                help="Specify the schedule using Cron syntax. "
                     "Refer to online resources for Cron expression help."
            )
            if cron_expression:
                try:
                    description = cron_descriptor.get_description(cron_expression)

                    st.info(f"Schedule Description: {description}")
                except FormatException as e: 
                    st.error(f"Invalid Cron expression: {e}. Please check the syntax.")
        
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
            generate_report(repo_name, token, days)
           ###call to method 
         # Create Scheduler Job
            create_scheduler_job(
            repo=repo_name,
            token=token,
            cron_expr=cron_expression,
            days=days
    )
            ####


def create_scheduler_job(repo, token, cron_expr, days):
    client = CloudSchedulerClient()
    parent = "projects/your-project-id/locations/your-region"

    job = {
        "http_target": {
            "uri": "https://standup-bot-1095165959029.us-central1.run.app",
            "http_method": HttpMethod.POST,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "repo": repo,
                "token": token,
                "days": days
            }).encode()
        },
        "schedule": cron_expr,
        "time_zone": "Etc/UTC"
    }

    response = client.create_job(request={"parent": parent, "job": job})
    return response

def generate_report(repo_name, token, days):
    try:
        with st.spinner("Fetching commits..."):
            # Initialize GitHub loader and fetch commits
            loader = LocalGitHubLoader(token)
            commits_df = loader.get_repo_commits(repo_name, days)

            if commits_df.empty:
                st.info("No commits found in the selected time period.")
                return

            # Create tabs
            tab1, tab2, tab3 = st.tabs(["📝 Commit Summary", "📊 Overview Analysis", "🔎 Detailed Analysis"])

            with tab1:
                st.subheader("📝 Commit Summary")
                # Style the DataFrame
                st.dataframe(
                    commits_df,
                    column_config={
                        "time": st.column_config.TextColumn("Time"),
                        "message": st.column_config.TextColumn("Message"),
                        "changes": st.column_config.TextColumn("Changes"),
                        "files": st.column_config.NumberColumn("Files"),
                        "url": st.column_config.LinkColumn("Link")
                    },
                    use_container_width=True,
                    hide_index=True
                )

            with tab2:
                st.subheader("📊 Overview Analysis")
                with st.spinner("AI is analyzing your commits..."):
                    # Get analysis of all commits
                    analysis_response = create_analysis_chain().invoke({
                        "commits": commits_df.to_markdown(),
                        "diff_data": ""
                    })
                    st.markdown(getattr(analysis_response, 'content', str(analysis_response)))

            with tab3:
                st.subheader("🔎 Detailed Analysis")
                if not commits_df.empty:
                    commit_options = commits_df['message'].tolist()
                    commit_urls = commits_df['url'].tolist()
                    selected_commit_message = st.selectbox("Select a commit to analyze:", [""] + commit_options)
                    if selected_commit_message:
                            selected_index = commit_options.index(selected_commit_message)
                            selected_url = commit_urls[selected_index]
                            with st.spinner(f"AI is fetching details for: {selected_commit_message}"):
                                try:
                                    diff_data = loader.get_github_diff(selected_url)
                                    url_response = create_url_analysis_chain().invoke(str(diff_data))
                                    st.markdown(getattr(url_response, 'content', str(url_response)))
                                except Exception as e:
                                    st.warning(f"Could not fetch detailed commit data: {str(e)}")
                                    st.markdown("Detailed analysis unavailable for this commit.")
                    elif not selected_commit_message:
                        st.info("Please select a commit from the list before clicking 'Generate Analysis Report'.")

    except ImportError as e:
        st.error(f"Missing dependencies: {e}. Try installing them via pip.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
