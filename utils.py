#from turtle import st
import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse
from github import Github


from langchain_google_vertexai import VertexAI
from langchain_core.runnables import RunnablePassthrough
from langchain.prompts import PromptTemplate
from google.cloud import aiplatform
import json

# Initialize Vertex AI
def init_vertex_ai():
    try:
        # Load JSON from file if it exists
#        if os.path.exists("gcp-service-account.json"):
 #           with open("gcp-service-account.json", "r") as f:
  #              service_account_info = json.load(f)
                
            # Set environment variable
   #         os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-service-account.json"
            
            # Initialize Vertex AI
            aiplatform.init(
                project=service_account_info["project_id"],
                location="us-east1"
            )
            
            # Create LLM instance
            llm = VertexAI(
                model_name="gemini-1.5-pro",
                temperature=0.3,
                project=service_account_info["project_id"],
                location="us-central1"
            )
            
            return llm
#        else:
 #           print("Service account file not found.")
 #           return None
    except Exception as e:
        print(f"Error initializing Vertex AI: {str(e)}")
        return None

# GitHub API integration
class LocalGitHubLoader:
    def __init__(self, token):
        self.g = Github(token) if token else Github()
    def get_repo_commits(self,repo_name,days):
        try:
            repo = self.g.get_repo(repo_name)
            since = datetime.now() - timedelta(days=days)
            commits = list(repo.get_commits(since=since))
            commit_data = []
            for commit in commits:
                stats = commit.stats
                commit_data.append({
                    'time': commit.commit.author.date.strftime("%H:%M"),
                    'message': commit.commit.message.split("\n")[0][:50],
                    'changes': f"+{stats.additions}/-{stats.deletions}",
                    'files': len(list(commit.files)),
                    'url': commit.html_url
                })
                
            return pd.DataFrame(commit_data)
        except Exception as e:
            print(f"Error fetching commits: {str(e)}")
            return pd.DataFrame()
    
    def get_github_diff(self, url):
        """Fetch detailed diff content including line changes"""
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip("/").split("/")
            
            if (len(path_parts) < 4 or 
                "github.com" not in parsed.netloc or 
                "commit" not in path_parts):
                raise ValueError(f"Invalid GitHub commit URL format: {url}")
            
            commit_index = path_parts.index("commit") if "commit" in path_parts else -1
            if commit_index == -1 or commit_index+1 >= len(path_parts):
                raise ValueError(f"Could not find commit SHA in URL: {url}")
            
            owner = path_parts[0]
            repo = path_parts[1]
            commit_sha = path_parts[commit_index+1]
            
            repo = self.g.get_repo(f"{owner}/{repo}")
            commit = repo.get_commit(commit_sha)
            
            files = []
            for file in commit.files:
                files.append({
                    'filename': file.filename,
                    'status': file.status,
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'patch': file.patch,
                    'raw_url': file.raw_url
                })
            
            return {
                'type': 'commit',
                'sha': commit_sha,
                'message': commit.commit.message,
                'author': commit.commit.author.name,
                'date': commit.commit.author.date,
                'files': files
            }
        except Exception as e:
            print(f"Error fetching diff: {str(e)}")
            return f"Unable to fetch diff: {str(e)}"

# LangChain prompt chains
def create_analysis_chain():
    # Initialize the LLM
    llm = init_vertex_ai()
    if not llm:
        return lambda x: "AI service unavailable"
    
    prompt = PromptTemplate.from_template("""
    Analyze these GitHub commits:
    {commits} here is the detailed changes 
    
    Provide:
    1. 🏆 Key accomplishments
    2. ⏱ Estimated focus time (based on commit times) and working hours from 9 to 5 EST
    3. 🚧 Potential blockers that I faced while making this code
    4. ➡️ Recommended next steps
    
    Keep it concise with bullet points as I will use this as the guidelines while talking in today's standup.
    """)
    
    return (
        {"commits": RunnablePassthrough()} 
        | prompt 
        | llm
    )

def create_url_analysis_chain():
    # Initialize the LLM
    llm = init_vertex_ai()
    if not llm:
        return lambda x: "AI service unavailable"
    
    prompt = PromptTemplate.from_template("""
    Analyze this GitHub change:
    {diff_data}
    
    Provide detailed insights on:
    1. Code changes impact
    2. Potential risks
    3. Review priorities
    4. Related files to check
    
    Format as markdown with clear sections.
    """)
    
    return {"diff_data": RunnablePassthrough()} | prompt | llm
