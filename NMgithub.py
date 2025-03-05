#!/usr/bin/env python3

import os
import git
from git import Repo
import time
import getpass

# Function to initialize the repo if it doesn't exist
def init_repo(repo_dir):
    # Check if the repository directory does not exist
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)  # Create the repository directory if it doesn't exist

    try:
        repo = Repo(repo_dir)  # Attempt to create a Repo object for the given directory
        if not repo.bare:  # If the repository is not bare (a bare repo has no working tree)
            print(f"Repository already initialized at {repo_dir}")  # Inform the user that the repo is already initialized
        else:
            print("Initializing repository")  # If repo is bare, initialize it
            repo = Repo.init(repo_dir)  # Initialize the repo as a bare repo (no working tree)
    except git.exc.InvalidGitRepositoryError:  # Exception handling for invalid repository error
        print("Initializing repository")  # Inform user that the repo is being initialized
        repo = Repo.init(repo_dir)  # Initialize a new repo if the given path isn't a valid repo
    return repo  # Return the initialized or existing repo object

# Function to create an initial commit
def create_initial_commit(repo):
    # If no commits exist in the repository, we need to create one
    if not repo.head.commit:  # Check if the repository has any commits
        # Create a new empty file to commit if no files exist
        with open(os.path.join(repo.working_tree_dir, 'README.md'), 'w') as f:  # Create a README file
            f.write("# Initial Commit\n")  # Write initial content in the README file
        repo.index.add(['README.md'])  # Add the README file to the git index (staging area)
        repo.index.commit("Initial commit")  # Create the initial commit
        print("Initial commit created.")  # Inform the user that the initial commit has been created

# Function to commit changes to the repository
def commit_changes(repo, commit_message):
    repo.git.add(A=True)  # Adds all modified files in the repo to the staging area
    repo.index.commit(commit_message)  # Commit the staged changes with the provided commit message
    print("Changes committed successfully.")  # Inform the user that changes were committed

# Function to push changes to GitHub
def push_changes(repo, branch='main', username=None, token=None, github_url=None):
    origin = repo.remotes.origin  # Access the origin remote of the repository
    # Using HTTPS with the username and personal access token for authentication
    origin.set_url(f"https://{username}:{token}@{github_url.replace('https://', '')}")  # Set the URL for the remote with credentials
    
    # Check if the branch exists locally, if not, create it
    if branch not in repo.heads:  # Check if the branch doesn't exist locally
        print(f"Branch '{branch}' does not exist locally. Creating it now.")  # Inform the user that a new branch is being created
        repo.git.checkout("-b", branch)  # Create and switch to the new branch
    
    # Push the branch and set upstream if it's the first push
    repo.git.push("--set-upstream", "origin", branch)  # Push the local branch to the origin repository and set the upstream
    print(f"Changes pushed to the '{branch}' branch of GitHub.")  # Inform the user that the changes were pushed

# Function to compare and push only modified files
def push_modified_files(repo, branch='main', username=None, token=None, github_url=None):
    # Pull changes from GitHub to check for modifications
    origin = repo.remotes.origin  # Access the origin remote
    origin.fetch()  # Fetch the latest changes from the remote repository to check for modifications

    # Compare modified files in local repo with the ones in GitHub
    for item in repo.index.diff(None):  # Get uncommitted changes by checking the difference between the index and working directory
        if item.a_path:  # If the item has a path (i.e., it's a file)
            print(f"Modified file: {item.a_path}")  # Inform the user that a file has been modified
            repo.git.add(item.a_path)  # Stage the modified file for commit

    # Commit and push if there are any changes
    if repo.index.diff(None):  # Check if there are any uncommitted changes
        repo.index.commit("Pushed modified files")  # Commit the changes with a specific commit message
        push_changes(repo, branch, username, token, github_url)  # Push the changes to the remote repository
    else:
        print("No changes detected to push.")  # Inform the user if there were no changes to push

def main():
    repo_dir = "/home/netman/GITREPO"  # Local repository path
    github_url = "https://github.com/AravindhGoutham/NetMAN.git"  # GitHub repo URL
    username = "AravindhGoutham"  #GitHub username
    token = getpass.getpass("Enter your GitHub personal access token (hidden): ")
    branch = "main"

    # Initialize the repository
    repo = init_repo(repo_dir)  # Initialize or get the repository at the given path

    # Check if remote exists, if not, add the GitHub repository
    if not repo.remotes:  # Check if no remotes exist in the repository
        print(f"Adding remote GitHub repository: {github_url}")  # Inform the user that the remote is being added
        repo.create_remote('origin', github_url)  # Add the GitHub repository as a remote named 'origin'

    # Create the initial commit if no commits exist
    create_initial_commit(repo)  # Create the initial commit if the repository is empty

    # Commit all files and push them
    commit_changes(repo, "Initial commit or update")  # Commit all changes with a message
    push_changes(repo, branch, username, token, github_url)  # Push the committed changes to GitHub

    # Optionally, check for modified files and push only those
    push_modified_files(repo, branch, username, token, github_url)  # Check and push only modified files to GitHub

if __name__ == "__main__":
    main()






