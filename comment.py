import os
import requests

repo = os.environ["GITHUB_REPOSITORY"]
pr_number = os.environ["GITHUB_REF"].split("/")[-1]
token = os.environ["GITHUB_TOKEN"]

with open("review.txt", "r") as f:
    body = f.read()

url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json"
}

requests.post(url, headers=headers, json={"body": body})
