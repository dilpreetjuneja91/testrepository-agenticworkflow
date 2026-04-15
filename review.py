import os
import subprocess
import requests
from openai import OpenAI

# CONFIG
MAX_DIFF_CHARS = 8000
ALLOWED_EXTENSIONS = (".java", ".py", ".ts", ".js", ".go")

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

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------
# GET DIFF PER FILE
# ---------------------------
print("Fetching changed files...")

files = subprocess.check_output(
    ["git", "diff", "--name-only", "origin/main"]
).decode().splitlines()

files = [f for f in files if f.endswith(ALLOWED_EXTENSIONS)]

if not files:
    print("No relevant files to review.")
    exit(0)

# ---------------------------
# FUNCTION: REVIEW FILE
# ---------------------------
def review_file(file_path):
    print(f"Reviewing {file_path}...")

    try:
        diff = subprocess.check_output(
            ["git", "diff", "origin/main", "--", file_path]
        ).decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Failed to get diff for {file_path}: {e}")
        return None

    if not diff.strip():
        return None

    diff = diff[:MAX_DIFF_CHARS]

    prompt = f"""
You are a Principal Software Engineer conducting a rigorous code review.

Focus ONLY on high-value issues.

Review priorities:
- Correctness (bugs, edge cases)
- Performance & scalability
- Reliability (timeouts, retries, failures)
- Security risks
- Architecture & design issues

Rules:
- No generic comments
- No praise
- Only actionable issues

Format:
Severity: Critical | High | Medium | Low
Issue:
Impact:
Recommendation:

Also include:
- Missed Production Risks

File: {file_path}

Diff:
{diff}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You review code like you are on-call for production incidents."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"OpenAI error for {file_path}: {e}")
        return None

# ---------------------------
# POST COMMENT
# ---------------------------
def post_comment(body):
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    res = requests.post(url, headers=headers, json={"body": body})

    if res.status_code != 201:
        print("Failed to post comment", res.status_code, res.text)

# ---------------------------
# MAIN LOOP
# ---------------------------
print("Starting AI review...")

for file in files:
    review = review_file(file)

    if not review or len(review.strip()) < 20:
        continue

    comment = f"## 🤖 AI Review — `{file}`\n\n{review}"

    post_comment(comment)

print("Review completed.")
