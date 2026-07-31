import time
import jwt
import requests
import os
from dotenv import load_dotenv
import base64

load_dotenv()

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

    return jwt.encode(payload, GITHUB_PRIVATE_KEY, algorithm="RS256")

def get_installation_access_token(installation_id: str) -> str:
    app_jwt = generate_app_jwt()
    response = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
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

def create_or_update_file(installation_id: str, owner: str, repo: str, path: str, file_content: str, commit_message: str) -> dict:
    token = get_installation_access_token(installation_id)

    encoded_content = base64.b64encode(file_content.encode()).decode()


    existing = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/content/{path}",
        headers={"Authorization": f"Beaere {token}", "Accept": "application/vnd.github+json"},
    )

    payload = {"message": commit_message, "content": encoded_content}

    if existing.status_code == 200:
        payload["sha"] = existing.json()["sha"]

    response = requests.put(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json=payload,
    )

    response.raise_for_status()
    return response.json()

def create_repo_secret(installation_id: str, owner: str, repo: str, secret_name: str, secret_value: str) -> None:
    from nacl import encoding, public

    token = get_installation_access_token(installation_id)

    key_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    key_response.raise_for_status()
    key_data = key_response.json()

    public_key = public.PublicKey(key_data["key"].encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    encrypted_b64 = base64.b64encode(encrypted).decode("utf-8")

    response = requests.put(
        f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={"encrypted_value": encrypted_b64, "key_id": key_data["key_id"]},
    )

    response.raise_for_status()