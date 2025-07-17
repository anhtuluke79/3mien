# utils/upload_github.py
from github import Github
import os

def upload_file_to_github(local_file_path, repo_name, remote_path, commit_message, github_token):
    """
    Upload 1 file lên GitHub.
    - local_file_path: Đường dẫn file local (vd: xsmb.csv)
    - repo_name: Tên repo (vd: 'anhtuluke79/3mien')
    - remote_path: Đường dẫn trong repo (vd: 'xsmb.csv')
    - commit_message: Message cho commit
    - github_token: Personal access token của bạn
    """
    g = Github(github_token)
    repo = g.get_repo(repo_name)
    with open(local_file_path, "rb") as f:
        content = f.read()
    try:
        # Nếu file đã tồn tại thì update
        contents = repo.get_contents(remote_path)
        repo.update_file(contents.path, commit_message, content, contents.sha)
        print(f"✅ Đã cập nhật file {remote_path} lên GitHub.")
    except Exception:
        # Nếu file chưa tồn tại thì tạo mới
        repo.create_file(remote_path, commit_message, content)
        print(f"✅ Đã upload mới file {remote_path} lên GitHub.")
