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
## newly added
from langchain_community.vectorstores import FAISS
import tempfile
import shutil
from langchain_community.document_loaders import GitLoader
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from langchain_google_vertexai import VertexAIEmbeddings

# Initialize Vertex AI
def init_vertex_ai():
    try:
        # Load JSON from file if it exists
        if os.path.exists("gcp-service-account.json"):
            with open("gcp-service-account.json", "r") as f:
                service_account_info = json.load(f)
                
            # Set environment variable
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-service-account.json"
            
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
        else:
            print("Service account file not found.")
            return None
    except Exception as e:
        print(f"Error initializing Vertex AI: {str(e)}")
        return None

# GitHub API integration
class LocalGitHubLoader:
    def __init__(self, token):
        self.g = Github(token) if token else Github()
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
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

    def get_relevant_context(self, repo_url, commit_sha, query, k=5):
        """Retrieve relevant code context using RAG"""
        vectorstore = self.clone_and_index_repo(repo_url, commit_sha)
        
        # print(f"Indexed {len(vectorstore.docstore._dict)} documents")  # Should show >0     
        docs = vectorstore.similarity_search(query, k=k)
        
        # Format for LLM consumption
        return "\n\n".join(
            f"File: {doc.metadata['file_path']}\n"
            f"Content:\n{doc.page_content[:2000]}..."  # Truncate
            for doc in docs
        )

    def clone_and_index_repo(self, repo_url, commit_sha):
        """Clone repo and create vector index"""
        if "github.com" in repo_url:
            repo_name = "/".join(repo_url.split("github.com/")[1].split("/")[:2])
        else:
            repo_name = repo_url  # Assume it's already in "owner/repo" format
        with tempfile.TemporaryDirectory() as temp_dir:
            clone_dir = os.path.join(temp_dir, repo_name.replace('/', '_'))
            os.makedirs(clone_dir, exist_ok=True)
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir)
        os.makedirs(clone_dir, exist_ok=True)
    # Clone repository at specific commit using proper URL format
        loader = GitLoader(
            clone_url=f"https://{self.token}@github.com/{repo_name}.git",
            repo_path=clone_dir,
            branch=commit_sha,
            file_filter=lambda file_path: not file_path.split('/')[-1].startswith('.')
        )
        
        # Load and split code
        documents = loader.load()
        if not documents:
            print(f"Warning: No documents found in repository at {repo_url} for commit {commit_sha}")
            return None 
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = splitter.split_documents(documents)
        if not splits:
            print(f"Warning: No text splits generated from documents")
            return None
        # Create vector store
        return FAISS.from_documents(splits, self.embeddings)

# LangChain prompt chains
def create_analysis_chain():
    prompt = PromptTemplate.from_template("""
    You are my personal assistant, helping prepare notes for my daily standup, to summarize what I worked on yesterday..
    
    Analyze these GitHub commits:
    {commits}
    
    Detailed changes: {diff_data}
    Repository context: {repo_context}
    
    Based on the provided commits and changes, infer the project context and provide the following information in bullet points:
    1. 🏆 Key accomplishments: Highlight the main achievements and completed tasks.
    2. ⏱ Estimated focus time: Calculate the focus time based on commit times and working hours from 9 to 5 GMT+2. If the focus time cannot be reliably estimated, provide a detailed explanation.
    3. 🚧 Potential blockers: Identify any issues or obstacles faced during the development process. This could be such a small accomplishment taking much more estimated work time than needed. If no blockers are evident, explain why and suggest ways to improve commit messages for better clarity.
    4. ➡️ Recommended next steps: Suggest the next steps to be taken based on the current progress. Include recommendations for improving commit messages and project tracking.
 
    Example Output when having the 1st push of the day at 13:00, taking much more time than needed for 4 lines of code in API integration:
    - 🏆 Key accomplishments:
      - Implemented feature X
      - Fixed bug Y
    - ⏱ Estimated focus time:
      - 4 hours of focused work between 9:00 and 13:00 
    - 🚧 Potential blockers:
      - Encountered issue with API integration 
    - ➡️ Recommended next steps:
      - Continue working on feature Z
      - Resolve API integration issue
      - Add more descriptive commit messages to improve project tracking and collaboration. Explain the *purpose* of the changes, not just *what* changed. For example, instead of "adding 9 to 5", a better message would be "Added employee working hours (9am-5pm) to the scheduling module".
 
    Keep it concise with bullet points.
    """)
    
    return RunnableParallel({
        "commits": RunnablePassthrough(),
        "diff_data": RunnablePassthrough(),
        "repo_context": RunnablePassthrough()
    }) | prompt | llm

def create_url_analysis_chain():
    # Initialize the LLM
    llm = init_vertex_ai()
    if not llm:
        return lambda x: "AI service unavailable"
    
    prompt = PromptTemplate.from_template("""
    Analyze this GitHub changes:
    {diff_data}
    That are present in the following repo: {repo_context}

    Provide detailed insights on:
    1. Code changes impact
    2. Potential risks
    3. Review priorities
    4. Related files to check
    
    Format as markdown with clear sections.
    """)
    
    return {"diff_data": RunnablePassthrough(),
        "repo_context": RunnablePassthrough()} | prompt | llm

def parseURL(url):
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    
    # More flexible URL validation
    if (len(path_parts) < 4 or 
        "github.com" not in parsed.netloc or 
        "commit" not in path_parts):
        raise ValueError(f"Invalid GitHub commit URL format: {url}")
    
    # Extract owner, repo, and commit SHA
    # Handle both:
    # https://github.com/owner/repo/commit/sha
    # https://github.com/owner/repo/blob/sha/file.py
    commit_index = path_parts.index("commit") if "commit" in path_parts else -1
    if commit_index == -1 or commit_index+1 >= len(path_parts):
        raise ValueError(f"Could not find commit SHA in URL: {url}")
    
    owner = path_parts[0]
    repo = path_parts[1]
    commit_sha = path_parts[commit_index+1]
    return owner, repo, commit_sha


