# from turtle import st
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
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.runnables import RunnableParallel

def init_vertex_ai():
    try:
        # Credentials are automatically handled in GCP environments
        project_id = os.environ.get("GCP_PROJECT_ID", "nse-gcp-ema-tt-37ab4-sbx-1")

        aiplatform.init(
            project=project_id,
            location="us-east1"
        )

        llm = VertexAI(
            model_name="gemini-1.5-pro",
            temperature=0.3,
            project=project_id,
            location="us-central1"
        )
        return llm
    except Exception as e:
        print(f"Error initializing Vertex AI: {str(e)}")
        return None
    
llm = init_vertex_ai()
if not llm:
    print("Warning: AI service unavailable. Some features may not work.")
# GitHub API integration


class LocalGitHubLoader:
    def __init__(self, token):
        self.g = Github(token) if token else Github()
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
 
    def get_repo_commits(self, repo_name, days, branch="main"):
        try:
            repo = self.g.get_repo(repo_name)
            since = datetime.now() - timedelta(days=days)
            commits = list(repo.get_commits(since=since, sha=branch))
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
        """Get detailed changes for a specific commit using GitHub API"""
        owner, repo, commit_sha = self.parseURL(url)
        
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip("/").split("/")

            if (len(path_parts) < 4 or
                "github.com" not in parsed.netloc or
                    "commit" not in path_parts):
                raise ValueError(f"Invalid GitHub commit URL format: {url}")

            commit_index = path_parts.index(
                "commit") if "commit" in path_parts else -1
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
            print(f"Error getting GitHub diff: {e}")
            return None

    def get_relevant_context(self, repo_url, commit_sha, query, k=10):
        """Retrieve relevant code context using RAG with enhanced access"""
        if "github.com" in repo_url:
            repo_name = "/".join(repo_url.split("github.com/")[1].split("/")[:2])
        else:
            repo_name = repo_url
        
        try:
            # Get repository structure using GitHub API
            repo = self.g.get_repo(repo_name)
            
            # Get all files in this commit for context
            commit = repo.get_commit(commit_sha)
            files_list = [f"{file.filename} ({file.status}: +{file.additions}/-{file.deletions})" 
                        for file in commit.files]
            
            repo_structure = f"Repository: {repo_name}\n"
            repo_structure += f"Commit: {commit_sha}\n"
            repo_structure += f"Files changed in this commit:\n- " + "\n- ".join(files_list)
            
            # Get vectorstore for semantic search
            vectorstore = self.clone_and_index_repo(repo_url, commit_sha)
            
            if not vectorstore:
                return f"Repository Structure:\n{repo_structure}\n\n" + "No code files found for indexing."
            
            # Get relevant documents
            docs = vectorstore.similarity_search(query, k=k)
            
            # Format with less truncation
            doc_content = "\n\n".join(
                f"File: {doc.metadata['file_path']}\n"
                f"Content:\n{doc.page_content[:5000]}..."  # Increased character limit
                for doc in docs
            )
            
            # Combine structure and document content
            return f"Repository Structure:\n{repo_structure}\n\n" + doc_content
            
        except Exception as e:
            print(f"Error retrieving repository context: {e}")
            return f"Error retrieving context: {str(e)}"

    def clone_and_index_repo(self, repo_url, commit_sha):
        """Get repository content using GitHub API instead of cloning"""
        if "github.com" in repo_url:
            repo_name = "/".join(repo_url.split("github.com/")[1].split("/")[:2])
        else:
            repo_name = repo_url  # Assume it's already in "owner/repo" format
        
        # Use GitHub API to get repository content
        repo = self.g.get_repo(repo_name)
        documents = []
        
        # Get file list at this commit
        files = repo.get_commit(commit_sha).files
        
        for file in files:
            try:
                # Skip files that don't meet our criteria (simplified filter)
                if file.filename.startswith('.'):
                    continue
                    
                # Get file content directly from GitHub API
                content = repo.get_contents(file.filename, ref=commit_sha)
                if content:
                    # Create document for vector store
                    documents.append(Document(
                        page_content=content.decoded_content.decode('utf-8'),
                        metadata={"file_path": file.filename}
                    ))
            except Exception as e:
                print(f"Error getting content for {file.filename}: {e}")
        
        # Split documents and create vector store
        if not documents:
            print(f"No documents found in repository {repo_name} at commit {commit_sha}")
            return None
            
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = splitter.split_documents(documents)
    
        # Create vector store
        return FAISS.from_documents(splits, self.embeddings)
    def parseURL(self, url):
        """Parse GitHub URL safely"""
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")
        
        # More flexible URL validation
        if (len(path_parts) < 4 or 
            "github.com" not in parsed.netloc or 
            "commit" not in path_parts):
            raise ValueError(f"Invalid GitHub commit URL format: {url}")
        
        # Extract owner, repo, and commit SHA
        commit_index = path_parts.index("commit") if "commit" in path_parts else -1
        if commit_index == -1 or commit_index+1 >= len(path_parts):
            raise ValueError(f"Could not find commit SHA in URL: {url}")
        
        owner = path_parts[0]
        repo = path_parts[1]
        commit_sha = path_parts[commit_index+1]
        return owner, repo, commit_sha

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
    if not llm:
        llm = init_vertex_ai()
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

def parseURL(self, url):
    """Parse GitHub URL safely"""
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    
    # More flexible URL validation
    if (len(path_parts) < 4 or 
        "github.com" not in parsed.netloc or 
        "commit" not in path_parts):
        raise ValueError(f"Invalid GitHub commit URL format: {url}")
    
    # Extract owner, repo, and commit SHA
    commit_index = path_parts.index("commit") if "commit" in path_parts else -1
    if commit_index == -1 or commit_index+1 >= len(path_parts):
        raise ValueError(f"Could not find commit SHA in URL: {url}")
    
    owner = path_parts[0]
    repo = path_parts[1]
    commit_sha = path_parts[commit_index+1]
    return owner, repo, commit_sha


