import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from requests.exceptions import HTTPError

from app.db.session import get_db
from app.models.github_installation import GithubInstallation
from app.models.ml_model import MLModel
from app.models.project import Project
from app.models.api_key import APIKey
from app.auth.firebase import verify_firebase_token
from app.integrations.github_app import (
    list_repos_for_installation,
    create_or_update_file,
    create_repo_secret,
    get_installation_access_token,
)

router = APIRouter()


@router.get("/github/status")
def github_status(db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    installation = db.query(GithubInstallation).filter(GithubInstallation.firebase_uid == user["uid"]).first()
    if not installation:
        return {"connected": False}

    try:
        get_installation_access_token(installation.installation_id)
        return {"connected": True}
    except HTTPError as e:
        if e.response is not None and e.response.status_code in (404, 401):
            db.delete(installation)
            db.commit()
            return {"connected": False}
    return {"connected": True}


class InstallationCallback(BaseModel):
    installation_id: str
    account_login: str


@router.post("/github/callback")
def github_callback(req: InstallationCallback, db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    existing = db.query(GithubInstallation).filter(GithubInstallation.firebase_uid == user["uid"]).first()
    if existing:
        existing.installation_id = req.installation_id
        existing.account_login = req.account_login
    else:
        existing = GithubInstallation(
            firebase_uid=user["uid"],
            installation_id=req.installation_id,
            account_login=req.account_login,
        )
        db.add(existing)
    db.commit()
    return {"success": True}


@router.get("/github/repos")
def get_repos(db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    installation = db.query(GithubInstallation).filter(GithubInstallation.firebase_uid == user["uid"]).first()
    if not installation:
        raise HTTPException(status_code=400, detail="GitHub not connected yet")

    try:
        repos = list_repos_for_installation(installation.installation_id)
    except HTTPError as e:
        if e.response is not None and e.response.status_code in (404, 401):
            db.delete(installation)
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="Your Github connection is no longer valid. Please reconnect.",
            )
        raise HTTPException(status_code=502, detail="Failed to reack Github. Please try again")


    return {"repos": [{"full_name": r["full_name"], "name": r["name"], "owner": r["owner"]["login"]} for r in repos]}


class SetupWorkflowRequest(BaseModel):
    model_id: int
    owner: str
    repo: str
    frequency_cron: str


@router.post("/github/setup-workflow")
def setup_workflow(req: SetupWorkflowRequest, db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    """
    Sets up automated monitoring for a repo:
    1. Stores the API key as an encrypted GitHub Secret (never in plain text)
    2. Commits an evaluation script that loads the key via python-dotenv
    3. Commits a .env.example for local dev reference
    4. Commits the workflow that writes a real .env at runtime and runs the script
    """
    installation = db.query(GithubInstallation).filter(GithubInstallation.firebase_uid == user["uid"]).first()
    if not installation:
        raise HTTPException(status_code=400, detail="GitHub not connected yet")

    model = db.query(MLModel).filter(MLModel.id == req.model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    project = db.query(Project).filter(Project.id == model.project_id).first()

    key_entry = db.query(APIKey).filter(APIKey.firebase_uid == user["uid"], APIKey.label == "GitHub Actions").first()
    if not key_entry:
        new_key = "mls_" + secrets.token_hex(24)
        key_entry = APIKey(key=new_key, firebase_uid=user["uid"], label="GitHub Actions")
        db.add(key_entry)
        db.commit()
        db.refresh(key_entry)

    # 1. Store the API key as an encrypted GitHub Actions Secret
    create_repo_secret(installation.installation_id, req.owner, req.repo, "MLSENTINEL_API_KEY", key_entry.key)

    # 2. Commit the evaluation script
    eval_script = f"""from mlsentinal import MLDoc
from dotenv import load_dotenv
import os

load_dotenv()

monitor = MLDoc(os.environ["MLSENTINEL_API_KEY"])

# TODO: replace this block with your real model evaluation code.
# e.g.:
#   import joblib
#   model = joblib.load("model.pkl")
#   y_pred = model.predict(X_test)
#   from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
#   metrics = {{
#       "accuracy": accuracy_score(y_test, y_pred),
#       "precision": precision_score(y_test, y_pred),
#       "recall": recall_score(y_test, y_pred),
#       "f1_score": f1_score(y_test, y_pred),
#   }}

metrics = {{"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0}}

response = monitor.doc_report(
    project="{project.name}",
    model="{model.name}",
    metrics=metrics,
)
print(response)
"""

    create_or_update_file(
        installation.installation_id, req.owner, req.repo,
        "mlsentinel_eval.py", eval_script,
        "Add MLSentinel evaluation script",
    )

    # 3. Commit a safe .env.example
    env_example = "MLSENTINEL_API_KEY=your_api_key_here\n"
    create_or_update_file(
        installation.installation_id, req.owner, req.repo,
        ".env.example", env_example,
        "Add .env.example for MLSentinel",
    )

    # 4. Commit the workflow itself
    workflow_yaml = f"""name: MLSentinel Scheduled Check

on:
  schedule:
    - cron: '{req.frequency_cron}'
  workflow_dispatch:

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install mlsentinel python-dotenv

      - name: Create .env file
        run: echo "MLSENTINEL_API_KEY=${{{{ secrets.MLSENTINEL_API_KEY }}}}" > .env

      - name: Run MLSentinel evaluation
        run: python mlsentinel_eval.py
"""

    result = create_or_update_file(
        installation.installation_id, req.owner, req.repo,
        ".github/workflows/mlsentinel.yml", workflow_yaml,
        "Add MLSentinel automated monitoring workflow",
    )

    return {"success": True, "commit_url": result.get("content", {}).get("html_url")}