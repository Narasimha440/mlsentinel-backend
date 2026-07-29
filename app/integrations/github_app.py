import time
import jwt
import requests
import os

GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
_raw_key = os.getenv("GITHUB_APP_PRIVATE_KEY", "")
GITHUB_PRIVATE_KEY = _raw_key.replace("\\n", "\n")

def generate_app_jwt() -> str:
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + (9 * 60),
        "iss": str(GITHUB_APP_ID)
    }

    return jwt.encode(payload,GITHUB_PRIVATE_KEY, algorithm="RS256")

def get_installation_access_token(installation_id: str) -> str:
    app_jwt = generate_app_jwt()
    response = requests.post(
        f"https://api.github.com/app/installation/{installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
        },
    )

    response.raise_for_status()
    return response.json()["token"]

def list_repos_for_installation(installation_id: str) -> list:
    token = get_installation_access_token(installation_id)
    response = requests.get(
        "https://api.github.com/installation/repositories",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    response.raise_for_status()
    return response.json()["repositories"]

def create_workflow_file(installation_id: str, owner: str, repo: str, file_content: str) -> dict:
    token = get_installation_access_token(installation_id)
    import base64


    encoded_content = base64.b64encode(file_content.encode()).decode()

    response = requests.put(
        f"https://api.github.com/repos/{owner}/{repo}/contents/.github/workflows/mlsentinel.yml",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={
            "message": "Add MLSentinel automated monitoring workflow",
            "content": encoded_content,
        },
    )

    response.raise_for_status()
    return response.json()