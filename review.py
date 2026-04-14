import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

with open("diff.txt", "r") as f:
    diff = f.read()

# ⚠️ IMPORTANT: trim large diffs
diff = diff[:12000]

prompt = f"""
You are a senior software architect reviewing a pull request.

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
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}]
)

review = response.choices[0].message.content

with open("review.txt", "w") as f:
    f.write(review)
