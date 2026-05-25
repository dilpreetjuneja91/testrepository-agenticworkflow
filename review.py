import os
import subprocess
import requests
import json
from openai import OpenAI

# ---------------- CONFIG ----------------
MAX_DIFF_CHARS = 8000
ALLOWED_EXTENSIONS = (".java", ".py", ".ts", ".js", ".go")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY")
PR_NUMBER = os.environ.get("PR_NUMBER")

if not all([OPENAI_API_KEY, GITHUB_TOKEN, REPO, PR_NUMBER]):
    raise Exception("Missing required environment variables")

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------- UTILS ----------------
def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True).stdout.decode()

# ---------------- FETCH FILES ----------------
print("Fetching changed files...")

files = run(["git", "diff", "--name-only", "origin/main"]).splitlines()
files = [f for f in files if f.endswith(ALLOWED_EXTENSIONS)]

if not files:
    print("No relevant files.")
    exit(0)

# ---------------- AI ANALYSIS ----------------
def analyze_file(file_path):
    print(f"Analyzing {file_path}")

    diff = run(["git", "diff", "origin/main", "--", file_path])

    if not diff.strip():
        return None

    diff = diff[:MAX_DIFF_CHARS]

    prompt = f"""
You are a Principal Engineer reviewing production-critical code.

Return STRICT JSON ONLY:

{{
  "issues": [
    {{
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "type": "TIMEOUT_MISSING|RETRY_NO_BACKOFF|BLOCKING_CALL|NULL_RISK|RESOURCE_LEAK|SECURITY_RISK|OTHER",
      "issue": "...",
      "impact": "...",
      "production_risk": "...",
      "recommendation": "...",
      "confidence": 0.0-1.0,
      "blast_radius": "service-wide|request-path|edge-case",
      "fixable": true/false
    }}
  ]
}}

Rules:
- ONLY include issues that can impact production
- IGNORE style, naming, formatting
- If no real issues → return {{ "issues": [] }}
- Prefer reliability, scalability, security
- Be concise and specific
- Confidence < 0.7 → DO NOT include
- Max 3 issues per file

Common failure patterns:
- Missing timeouts → thread exhaustion
- Retry without backoff → cascading failures
- Blocking calls in async flows
- Resource leaks / unbounded memory

File: {file_path}

Diff:
{diff}
"""

    try:
        res = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are on-call and responsible for production stability."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        return json.loads(res.choices[0].message.content)

    except Exception as e:
        print(f"AI error: {e}")
        return None

# ---------------- GITHUB COMMENT ----------------
def post_comment(body):
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    res = requests.post(url, headers=headers, json={"body": body})

    if res.status_code != 201:
        print("Failed to post comment:", res.text)

# ---------------- FORMAT OUTPUT ----------------
def format_issues(file, issues):
    if not issues:
        return None

    # sort by severity + confidence
    severity_order = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}

    issues = sorted(
        issues,
        key=lambda x: (severity_order.get(x["severity"], 5), -x["confidence"])
    )

    output = f"## 🤖 AI Review — `{file}`\n\n"

    for i in issues:
        output += f"""
### {i['severity']} — {i['type']}

**Issue**  
{i['issue']}

**Impact**  
{i['impact']}

**Production Risk**  
{i['production_risk']}

**Recommendation**  
{i['recommendation']}

**Confidence**: {round(i['confidence'], 2)}  
**Blast Radius**: {i['blast_radius']}  
**Fixable**: {i['fixable']}

---
"""

    return output

# ---------------- MAIN ----------------
print("Starting AI review...")

for file in files:
    result = analyze_file(file)

    if not result or not result.get("issues"):
        continue

    issues = result["issues"]

    # final safety filter
    issues = [i for i in issues if i.get("confidence", 0) >= 0.7]

    if not issues:
        continue

    comment = format_issues(file, issues)

    if comment:
        post_comment(comment)

print("Review completed.")
