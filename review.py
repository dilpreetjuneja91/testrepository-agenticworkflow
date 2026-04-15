import os
import subprocess
import requests
from openai import OpenAI

# CONFIG
MAX_DIFF_CHARS = 12000

# ENV VARIABLES
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY")
PR_NUMBER = os.environ.get("PR_NUMBER")

if not OPENAI_API_KEY:
    raise Exception("OPENAI_API_KEY is missing")

if not GITHUB_TOKEN:
    raise Exception("GITHUB_TOKEN is missing")

if not PR_NUMBER:
    raise Exception("PR_NUMBER is missing")

# GET DIFF
print("Fetching git diff...")

try:
    diff = subprocess.check_output(
        ["git", "diff", "origin/main"]
    ).decode("utf-8", errors="ignore")
except Exception as e:
    raise Exception(f"Failed to get git diff: {e}")

if not diff.strip():
    print("No diff found. Exiting.")
    exit(0)

# Trim diff
diff = diff[:MAX_DIFF_CHARS]

# AI REVIEW
print("Sending diff to OpenAI...")

client = OpenAI(api_key=OPENAI_API_KEY)

prompt = f"""
You are a strict senior software architect reviewing a pull request.

Review the following code diff and provide:

- Bugs
- Performance issues
- Security concerns
- Code quality improvements

Be direct and concise.

Diff:
{diff}
"""

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "You are a strict senior engineer."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.2
)

review_text = response.choices[0].message.content

if not review_text:
    review_text = "AI returned no feedback."

# POST COMMENT TO PR
print("Posting comment to PR...")

url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

data = {
    "body": f"AI PR Review\n\n{review_text}"
}

res = requests.post(url, headers=headers, json=data)

if res.status_code != 201:
    print("Failed to post comment")
    print(res.status_code, res.text)
    exit(1)

print("PR review comment posted successfully")
