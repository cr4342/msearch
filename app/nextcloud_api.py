from webdav3.client import Client

# 配置 WebDAV 客户端
options = {
    'webdav_hostname': 'https://your-nextcloud-domain.com',
    'webdav_login': 'your_username',
    'webdav_password': 'your_password'
}

client = Client(options)

# 1. 上传文件
def upload_file(local_path, remote_path):
    try:
        client.upload_sync(remote_path, local_path)
        print(f"File {local_path} uploaded to {remote_path}")
    except Exception as e:
        print(f"Error uploading file: {e}")

# 2. 下载文件
def download_file(remote_path, local_path):
    try:
        client.download_sync(remote_path, local_path)
        print(f"File {remote_path} downloaded to {local_path}")
    except Exception as e:
        print(f"Error downloading file: {e}")

# 3. 删除文件
def delete_file(remote_path):
    try:
        client.clean(remote_path)
        print(f"File {remote_path} deleted")
    except Exception as e:
        print(f"Error deleting file: {e}")

# 4. 列出目录内容
def list_directory(remote_path):
    try:
        files = client.list(remote_path)
        print(f"Contents of {remote_path}:")
        for file in files:
            print(file)
    except Exception as e:
        print(f"Error listing directory: {e}")

# 示例调用
if __name__ == "__main__":
    local_file_path = 'local_file.txt'
    remote_file_path = '/remote_directory/local_file.txt'

    # 上传文件
    upload_file(local_file_path, remote_file_path)

    # 下载文件
    download_file(remote_file_path, 'downloaded_file.txt')

    # 列出目录内容
    list_directory('/remote_directory/')

    # 删除文件
    delete_file(remote_file_path)