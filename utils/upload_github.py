# utils/upload_github.py
from github import Github, GithubException
import os

def upload_file_to_github(local_file_path, repo_name, remote_path, commit_message, github_token=None):
    """
    Upload 1 file lên GitHub.
    """
    if github_token is None:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("Thiếu GitHub token!")

    g = Github(github_token)
    repo = g.get_repo(repo_name)
    with open(local_file_path, "rb") as f:
        content = f.read()
    try:
        contents = repo.get_contents(remote_path)
        repo.update_file(contents.path, commit_message, content, contents.sha)
        print(f"✅ Đã cập nhật file {remote_path} lên GitHub.")
    except GithubException as e:
        if e.status == 404:
            # File chưa tồn tại
            repo.create_file(remote_path, commit_message, content)
            print(f"✅ Đã upload mới file {remote_path} lên GitHub.")
        else:
            print(f"❌ Lỗi upload file lên GitHub: {e}")
            raise

if __name__ == "__main__":
    # Demo test
    upload_file_to_github(
        local_file_path="xsmb.csv",
        repo_name="anhtuluke79/3mien",
        remote_path="xsmb.csv",
        commit_message="Cập nhật kết quả XSMB mới nhất",
        github_token=None  # hoặc để None để tự lấy từ biến môi trường GITHUB_TOKEN
    )
