import os
import subprocess
import requests
from openai import OpenAI

# ---------------- CONFIG ----------------
MAX_DIFF_CHARS = 8000
ALLOWED_EXTENSIONS = (".java", ".py", ".ts", ".js", ".go")

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

# ---------------- UTILS ----------------
def run(cmd):
    return subprocess.check_output(cmd).decode("utf-8", errors="ignore")

# ---------------- FETCH FILES ----------------
print("Fetching changed files...")

files = run(["git", "diff", "--name-only", "origin/main"]).splitlines()
files = [f for f in files if f.endswith(ALLOWED_EXTENSIONS)]

if not files:
    print("No relevant files to review.")
    exit(0)

# ---------------- REVIEW FUNCTION ----------------
def review_file(file_path):
    print(f"Reviewing {file_path}...")

    try:
        diff = run(["git", "diff", "origin/main", "--", file_path])
    except Exception as e:
        print(f"Failed to get diff for {file_path}: {e}")
        return None

    if not diff.strip():
        return None

    diff = diff[:MAX_DIFF_CHARS]

    prompt = f"""
Review ONLY the following code diff.

Rules:
- Only comment on code visible in the diff
- Do not assume anything about the rest of the file
- Do not summarize the file
- Do not mention generic issues
- If no real issue is visible, return: NO_ISSUES

Focus only on:
- bugs
- reliability issues (timeouts, retries)
- performance issues
- security issues ONLY if clearly visible

Confidence Guidelines (MANDATORY):

- 0.9 – 1.0 → Clearly visible deterministic issue in diff
- 0.75 – 0.89 → Strong signal but some assumption required
- 0.6 – 0.74 → Possible issue but uncertain context
- < 0.6 → DO NOT REPORT

Rules:
- DO NOT assign 1.0 unless the issue is explicitly visible in the diff
- Most issues should be between 0.75 and 0.95
- If unsure → lower confidence

Format STRICTLY:

Severity: Critical | High | Medium | Low
Confidence: (must follow rules above)
Issue:
Impact:
Recommendation:

Diff:
{diff}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You review code like you are responsible for production incidents."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        output = response.choices[0].message.content.strip()

        # Kill noise
        if not output or "NO_ISSUES" in output:
            return None

        return output

    except Exception as e:
        print(f"OpenAI error for {file_path}: {e}")
        return None

# ---------------- POST COMMENT ----------------
def post_comment(body):
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    res = requests.post(url, headers=headers, json={"body": body})

    if res.status_code != 201:
        print("Failed to post comment", res.status_code, res.text)

# ---------------- MAIN ----------------
print("Starting AI review...")

for file in files:
    review = review_file(file)

    if not review:
        continue

    comment = f"## 🤖 AI Review — `{file}`\n\n{review}"

    post_comment(comment)

print("Review completed.")
