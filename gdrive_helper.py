from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "YOUR_FOLDER_ID")

def get_gdrive():
    gauth = GoogleAuth()
    # Sử dụng Service Account JSON để xác thực
    gauth.LoadServiceAccountCredentials('service_account.json')
    drive = GoogleDrive(gauth)
    return drive

def upload_file_to_gdrive(local_path, remote_name=None):
    drive = get_gdrive()
    remote_name = remote_name or os.path.basename(local_path)
    # Xoá file cũ cùng tên (nếu có)
    file_list = drive.ListFile({
        'q': f"'{GDRIVE_FOLDER_ID}' in parents and title = '{remote_name}' and trashed=false"
    }).GetList()
    for f in file_list:
        f.Delete()
    f = drive.CreateFile({'title': remote_name, 'parents': [{'id': GDRIVE_FOLDER_ID}]})
    f.SetContentFile(local_path)
    f.Upload()
    return f['id']

def download_file_from_gdrive(remote_name, local_path):
    drive = get_gdrive()
    file_list = drive.ListFile({
        'q': f"'{GDRIVE_FOLDER_ID}' in parents and title = '{remote_name}' and trashed=false"
    }).GetList()
    if not file_list:
        raise FileNotFoundError("Không tìm thấy file trên Google Drive.")
    file_list[0].GetContentFile(local_path)
