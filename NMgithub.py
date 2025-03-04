#!/usr/bin/env python3

import os
import git
from git import Repo
import time
import getpass

# Function to initialize the repo if it doesn't exist
def init_repo(repo_dir):
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)
    try:
        repo = Repo(repo_dir)
        if not repo.bare:
            print(f"Repository already initialized at {repo_dir}")
        else:
            print("Initializing repository")
            repo = Repo.init(repo_dir)
    except git.exc.InvalidGitRepositoryError:
        print("Initializing repository")
        repo = Repo.init(repo_dir)
    return repo

# Function to create an initial commit
def create_initial_commit(repo):
    # If no commits exist in the repository, we need to create one
    if not repo.head.commit:
        # Create a new empty file to commit if no files exist
        with open(os.path.join(repo.working_tree_dir, 'README.md'), 'w') as f:
            f.write("# Initial Commit\n")
        repo.index.add(['README.md'])
        repo.index.commit("Initial commit")
        print("Initial commit created.")

# Function to commit changes to the repository
def commit_changes(repo, commit_message):
    repo.git.add(A=True)  # Adds all modified files
    repo.index.commit(commit_message)
    print("Changes committed successfully.")

# Function to push changes to GitHub
def push_changes(repo, branch='main', username=None, token=None, github_url=None):
    origin = repo.remotes.origin
    # Using HTTPS with the username and personal access token for authentication
    origin.set_url(f"https://{username}:{token}@{github_url.replace('https://', '')}")
    
    # Push the branch and set upstream if it's the first push
    if branch not in repo.heads:
        repo.git.push("--set-upstream", "origin", branch)
    else:
        origin.push(refspec=f"{branch}:{branch}")
    print(f"Changes pushed to the '{branch}' branch of GitHub.")

# Function to compare and push only modified files
def push_modified_files(repo, branch='main', username=None, token=None, github_url=None):
    # Pull changes from GitHub to check for modifications
    origin = repo.remotes.origin
    origin.fetch()

    # Compare modified files in local repo with the ones in GitHub
    for item in repo.index.diff(None):  # Get uncommitted changes
        if item.a_path:  # Check if file has changes
            print(f"Modified file: {item.a_path}")
            repo.git.add(item.a_path)

    # Commit and push if there are any changes
    if repo.index.diff(None):
        repo.index.commit("Pushed modified files")
        push_changes(repo, branch, username, token, github_url)
    else:
        print("No changes detected to push.")

# Main function to execute the tasks
def main():
    repo_dir = "/home/netman/GITREPO"  # Local repository path
    github_url = "https://github.com/AravindhGoutham/Aravindh.git"  # GitHub repo URL
    username = "AravindhGoutham"  # Your GitHub username
    token = getpass.getpass("Enter your GitHub personal access token (hidden): ")  # Ask for token securely
    branch = "main"  # Specify the branch, default is 'main'

    # Initialize the repository
    repo = init_repo(repo_dir)

    # Check if remote exists, if not, add the GitHub repository
    if not repo.remotes:
        print(f"Adding remote GitHub repository: {github_url}")
        repo.create_remote('origin', github_url)

    # Create the initial commit if no commits exist
    create_initial_commit(repo)

    # Commit all files and push them
    commit_changes(repo, "Initial commit or update")
    push_changes(repo, branch, username, token, github_url)

    # Optionally, check for modified files and push only those
    push_modified_files(repo, branch, username, token, github_url)

if __name__ == "__main__":
    main()

