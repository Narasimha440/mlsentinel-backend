import time
import jwt
import requests
import os
import base64

from dotenv import load_dotenv

load_dotenv()


GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")

_raw_key = os.getenv("GITHUB_APP_PRIVATE_KEY", "")
GITHUB_PRIVATE_KEY = _raw_key.replace("\\n", "\n")






def generate_app_jwt() -> str:
    now = int(time.time())

    payload = {
        "iat": now - 60,
        "exp": now + (9 * 60),
        "iss": str(GITHUB_APP_ID),
    }

    return jwt.encode(
        payload,
        GITHUB_PRIVATE_KEY,
        algorithm="RS256",
    )






def get_installation_access_token(
    installation_id: str,
) -> str:

    app_jwt = generate_app_jwt()

    response = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()["token"]






def list_repos_for_installation(
    installation_id: str,
) -> list:

    token = get_installation_access_token(
        installation_id
    )

    response = requests.get(
        "https://api.github.com/installation/repositories",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()["repositories"]






def create_workflow_file(
    installation_id: str,
    owner: str,
    repo: str,
    file_content: str,
) -> dict:

    token = get_installation_access_token(
        installation_id
    )

    encoded_content = base64.b64encode(
        file_content.encode("utf-8")
    ).decode("utf-8")

    response = requests.put(
        f"https://api.github.com/repos/{owner}/{repo}/contents/.github/workflows/mlsentinel.yml",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        json={
            "message": "Add MLSentinel automated monitoring workflow",
            "content": encoded_content,
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()






def create_or_update_file(
    installation_id: str,
    owner: str,
    repo: str,
    path: str,
    file_content: str,
    commit_message: str,
) -> dict:

    token = get_installation_access_token(
        installation_id
    )

    encoded_content = base64.b64encode(
        file_content.encode("utf-8")
    ).decode("utf-8")

    
    
    
    

    file_url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/contents/{path}"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    
    
    

    existing = requests.get(
        file_url,
        headers=headers,
        timeout=30,
    )

    payload = {
        "message": commit_message,
        "content": encoded_content,
    }

    
    
    

    if existing.status_code == 200:

        existing_data = existing.json()

        sha = existing_data.get("sha")

        if not sha:
            raise RuntimeError(
                f"GitHub returned the existing file "
                f"but no SHA was found for: {path}"
            )

        payload["sha"] = sha

    
    
    

    elif existing.status_code == 404:

        
        pass

    
    
    

    else:

        print(
            "\n========== GITHUB GET FILE ERROR =========="
        )

        print("Status:", existing.status_code)
        print("Repository:", f"{owner}/{repo}")
        print("Path:", path)
        print("Response:", existing.text)

        print(
            "===========================================\n"
        )

        existing.raise_for_status()

    
    
    

    response = requests.put(
        file_url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    
    
    

    if not response.ok:

        print(
            "\n========== GITHUB PUT FILE ERROR =========="
        )

        print("Status:", response.status_code)
        print("Repository:", f"{owner}/{repo}")
        print("Path:", path)
        print("Response:", response.text)

        print(
            "Has SHA:",
            "sha" in payload,
        )

        print(
            "Content length:",
            len(payload.get("content", "")),
        )

        print(
            "===========================================\n"
        )

    response.raise_for_status()

    return response.json()






def create_repo_secret(
    installation_id: str,
    owner: str,
    repo: str,
    secret_name: str,
    secret_value: str,
) -> None:

    from nacl import encoding, public

    token = get_installation_access_token(
        installation_id
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    
    
    

    key_response = requests.get(
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/actions/secrets/public-key",
        headers=headers,
        timeout=30,
    )

    key_response.raise_for_status()

    key_data = key_response.json()

    
    
    

    public_key = public.PublicKey(
        key_data["key"].encode("utf-8"),
        encoding.Base64Encoder(),
    )

    sealed_box = public.SealedBox(public_key)

    encrypted = sealed_box.encrypt(
        secret_value.encode("utf-8")
    )

    encrypted_b64 = base64.b64encode(
        encrypted
    ).decode("utf-8")

    
    
    

    response = requests.put(
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/actions/secrets/{secret_name}",
        headers=headers,
        json={
            "encrypted_value": encrypted_b64,
            "key_id": key_data["key_id"],
        },
        timeout=30,
    )

    response.raise_for_status()