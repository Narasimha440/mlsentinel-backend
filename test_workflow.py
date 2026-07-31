from app.integrations.github_app import create_workflow_file

workflow_content = """name: MLSentinel Test Workflow

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "MLSentinel workflow committed successfully"
"""

result = create_workflow_file(
    installation_id="149995168",
    owner="Narasimha440",
    repo="rdp",
    file_content=workflow_content,
)

print("Committed:", result.get("content", {}).get("html_url"))