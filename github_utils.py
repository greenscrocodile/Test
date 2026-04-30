import base64
import requests
import streamlit as st

def get_github_config():
    """Retrieve GitHub configuration from st.secrets."""
    try:
        return {
            "token": st.secrets["GITHUB_TOKEN"],
            "repo": st.secrets["GITHUB_REPO"], # format: "owner/repo"
            "branch": st.secrets.get("GITHUB_BRANCH", "main")
        }
    except Exception:
        return None

def github_request(method, path, data=None):
    config = get_github_config()
    if not config:
        return None, "GitHub secrets missing (GITHUB_TOKEN, GITHUB_REPO)"

    url = f"https://api.github.com/repos/{config['repo']}/contents/{path}"
    headers = {
        "Authorization": f"token {config['token']}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params={"ref": config["branch"]})
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, json=data)
        else:
            return None, f"Unsupported method: {method}"

        return response, None
    except Exception as e:
        return None, str(e)

def list_files_github(folder_path):
    response, error = github_request("GET", folder_path)
    if error:
        return [], error
    if response.status_code == 200:
        return response.json(), None
    elif response.status_code == 404:
        return [], None
    else:
        return [], f"GitHub Error: {response.status_code} - {response.text}"

def upload_file_github(folder_path, file_name, file_content):
    path = f"{folder_path}/{file_name}".strip("/")

    # Check if file exists to get SHA
    existing_files, _ = list_files_github(folder_path)
    sha = next((f["sha"] for f in existing_files if f["name"] == file_name), None)

    content_b64 = base64.b64encode(file_content).decode("utf-8")

    config = get_github_config()
    data = {
        "message": f"Upload {file_name} via HTS WORKS",
        "content": content_b64,
        "branch": config["branch"]
    }
    if sha:
        data["sha"] = sha

    response, error = github_request("PUT", path, data)
    if error:
        return False, error
    if response.status_code in [200, 201]:
        return True, None
    return False, f"GitHub Error: {response.status_code} - {response.text}"

def delete_file_github(folder_path, file_name):
    path = f"{folder_path}/{file_name}".strip("/")

    # Need SHA to delete
    existing_files, _ = list_files_github(folder_path)
    sha = next((f["sha"] for f in existing_files if f["name"] == file_name), None)

    if not sha:
        return False, "File not found in GitHub"

    config = get_github_config()
    data = {
        "message": f"Delete {file_name} via HTS WORKS",
        "sha": sha,
        "branch": config["branch"]
    }

    response, error = github_request("DELETE", path, data)
    if error:
        return False, error
    if response.status_code == 200:
        return True, None
    return False, f"GitHub Error: {response.status_code} - {response.text}"
