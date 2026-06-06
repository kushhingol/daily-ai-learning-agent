#!/usr/bin/env python3
"""Generate and optionally email a daily AI learning plan."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import smtplib
import urllib.error
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HISTORY_PATH = ROOT / "learning_history.json"
OUT_DIR = ROOT / "dist"
ENV_PATH = ROOT / ".env"


@dataclass(frozen=True)
class Topic:
    name: str
    category: str
    hook: str
    overview: str
    terms: list[tuple[str, str]]
    steps: list[str]
    use_cases: list[str]
    resource_name: str
    resource_url: str
    exercise_title: str
    exercise_intro: str
    starter_code: str
    success_criteria: list[str]
    stretch: str
    subtasks: list[tuple[str, str]]
    practice_steps: list[tuple[str, str, str]] | None = None
    expected_output: str = ""


TOPICS: list[Topic] = [
    Topic(
        name="HNSW Indexes for Vector Search",
        category="vector databases",
        hook="Fast vector search is the retrieval layer behind many useful RAG systems.",
        overview="HNSW is an approximate nearest-neighbor index that stores vectors in a layered graph so similar items can be found quickly without scanning every vector.",
        terms=[
            ("Embedding", "A list of numbers that represents the meaning of text, images, or other data."),
            ("Nearest neighbor", "The stored vector most similar to a query vector."),
            ("Approximate search", "A faster search that may trade perfect accuracy for very close results."),
            ("Recall", "How often the search returns the truly relevant matches."),
        ],
        steps=[
            "Represent each item as an embedding vector.",
            "Connect nearby vectors into a graph.",
            "Create sparse upper layers and denser lower layers.",
            "Start searching from the top layer to move quickly toward the right region.",
            "Refine at lower layers until the top matches are found.",
        ],
        use_cases=[
            "Retrieving the most relevant document chunks for a RAG chatbot.",
            "Finding similar products in ecommerce search.",
            "Searching image, audio, or support-ticket collections by meaning.",
        ],
        resource_name="Pinecone: Hierarchical Navigable Small Worlds",
        resource_url="https://www.pinecone.io/learn/hnsw/",
        exercise_title="Build a tiny semantic search demo",
        exercise_intro="Compare brute-force cosine search with the interface you would use for an indexed ANN search.",
        starter_code="""documents = [
    "How to reset my password",
    "Refund policy for annual plans",
    "Troubleshooting failed payments",
    "How vector databases power RAG",
    "Setting up two-factor authentication",
]

query = "I cannot pay with my card"

doc_vectors = embed(documents)
query_vector = embed([query])[0]

scores = []
for doc, vec in zip(documents, doc_vectors):
    score = cosine_similarity(query_vector, vec)
    scores.append((score, doc))

print(sorted(scores, reverse=True)[:3])

# Stretch path:
# index = HNSWIndex()
# index.add(doc_vectors)
# print(index.search(query_vector, k=3))
""",
        success_criteria=[
            "Your script returns the top 3 most similar documents for a query.",
            "You can explain why brute-force search slows down as vectors grow.",
            "You can describe why HNSW is fast but approximate.",
        ],
        stretch="Scale the dataset to 1,000+ documents and compare query time for brute force versus indexed search.",
        subtasks=[
            ("5 mins", "Create sample text data."),
            ("10 mins", "Generate real or mocked embeddings."),
            ("10 mins", "Implement brute-force cosine similarity."),
            ("10 mins", "Wrap the search behind an ANN-style index interface."),
            ("5 mins", "Compare returned results and timing."),
        ],
    ),
    Topic(
        name="Temperature in LLM Decoding",
        category="LLMs",
        hook="Controlling randomness is one of the simplest ways to make LLM outputs more reliable or more creative.",
        overview="Temperature changes how sharply a language model samples from possible next tokens, affecting determinism, variety, and risk of off-track output.",
        terms=[
            ("Logit", "A raw model score for a possible next token."),
            ("Sampling", "Choosing the next token from a probability distribution."),
            ("Determinism", "Getting the same or nearly same output for repeated runs."),
            ("Diversity", "How varied the generated text can be."),
        ],
        steps=[
            "The model scores possible next tokens.",
            "Scores are converted into probabilities.",
            "Temperature rescales the probability distribution.",
            "Low temperature concentrates probability on top choices.",
            "High temperature spreads probability across more choices.",
        ],
        use_cases=[
            "Low-temperature extraction of structured fields.",
            "Medium-temperature drafting for emails or explanations.",
            "Higher-temperature brainstorming for names, ideas, or variants.",
        ],
        resource_name="OpenAI text generation guide",
        resource_url="https://platform.openai.com/docs/guides/text-generation",
        exercise_title="Compare output stability at different temperatures",
        exercise_intro="Run the same prompt several times with low, medium, and high temperature settings.",
        starter_code="""prompt = "Explain gradient descent to a product manager in 3 sentences."

for temperature in [0.0, 0.4, 0.9]:
    print(f"\\nTemperature: {temperature}")
    for run in range(3):
        response = call_llm(prompt=prompt, temperature=temperature)
        print(f"- {response}")
""",
        success_criteria=[
            "You have three outputs for each temperature setting.",
            "You can identify which setting is most stable.",
            "You can choose a temperature for extraction, tutoring, and brainstorming tasks.",
        ],
        stretch="Add a simple scoring rubric for factuality, variety, and usefulness.",
        subtasks=[
            ("5 mins", "Pick one reusable prompt."),
            ("10 mins", "Run it multiple times at low temperature."),
            ("10 mins", "Repeat at medium and high temperature."),
            ("10 mins", "Compare stability and wording diversity."),
            ("5 mins", "Write your rule of thumb."),
        ],
    ),
    Topic(
        name="Train, Validation, and Test Splits",
        category="ML fundamentals",
        hook="Clean evaluation starts with separating data used for learning from data used for honest measurement.",
        overview="Dataset splits prevent you from judging a model on examples it has already learned from, giving a more realistic estimate of future performance.",
        terms=[
            ("Training set", "Examples the model uses to learn parameters."),
            ("Validation set", "Examples used to tune choices like features or hyperparameters."),
            ("Test set", "Held-out examples used for final evaluation."),
            ("Data leakage", "Accidentally letting future or answer-like information into training."),
        ],
        steps=[
            "Collect and clean the dataset.",
            "Split examples before model training.",
            "Train only on the training split.",
            "Tune choices using validation performance.",
            "Report final performance once on the test split.",
        ],
        use_cases=[
            "Evaluating churn prediction before deployment.",
            "Comparing classification models fairly.",
            "Preventing over-optimistic metrics in time-series forecasting.",
        ],
        resource_name="Google Machine Learning Crash Course: Training and Test Sets",
        resource_url="https://developers.google.com/machine-learning/crash-course/training-and-test-sets/splitting-data",
        exercise_title="Split a small dataset and evaluate honestly",
        exercise_intro="Create train, validation, and test sets, then compare validation and test metrics.",
        starter_code="""from sklearn.model_selection import train_test_split

X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

model.fit(X_train, y_train)
print("validation:", score(model, X_val, y_val))
print("test:", score(model, X_test, y_test))
""",
        success_criteria=[
            "You can state what each split is used for.",
            "Your model never trains on validation or test examples.",
            "You report a final metric from the test set.",
        ],
        stretch="Try a time-based split and explain when random splitting is unsafe.",
        subtasks=[
            ("5 mins", "Choose a toy classification dataset."),
            ("10 mins", "Create train, validation, and test splits."),
            ("10 mins", "Train a baseline model."),
            ("10 mins", "Tune one choice using validation data."),
            ("5 mins", "Evaluate once on the test set."),
        ],
    ),
]


def load_history() -> list[dict[str, Any]]:
    if not HISTORY_PATH.exists():
        return []
    return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))


def load_dotenv() -> None:
    if not ENV_PATH.exists():
        return
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def save_history(history: list[dict[str, Any]]) -> None:
    HISTORY_PATH.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")


def topic_from_dict(data: dict[str, Any]) -> Topic:
    return Topic(
        name=str(data["name"]),
        category=str(data["category"]),
        hook=str(data["hook"]),
        overview=str(data["overview"]),
        terms=[(str(item["term"]), str(item["definition"])) for item in data["terms"]],
        steps=[str(item) for item in data["steps"]],
        use_cases=[str(item) for item in data["use_cases"]],
        resource_name=str(data["resource_name"]),
        resource_url=str(data["resource_url"]),
        exercise_title=str(data["exercise_title"]),
        exercise_intro=str(data["exercise_intro"]),
        starter_code=str(data["starter_code"]),
        success_criteria=[str(item) for item in data["success_criteria"]],
        stretch=str(data["stretch"]),
        subtasks=[(str(item["duration"]), str(item["task"])) for item in data["subtasks"]],
        practice_steps=[
            (str(item["title"]), str(item["duration"]), str(item["instructions"]))
            for item in data.get("practice_steps", [])
        ],
        expected_output=str(data.get("expected_output", "")),
    )


def lesson_schema() -> dict[str, Any]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "name",
            "category",
            "hook",
            "overview",
            "terms",
            "steps",
            "use_cases",
            "resource_name",
            "resource_url",
            "exercise_title",
            "exercise_intro",
            "starter_code",
            "practice_steps",
            "subtasks",
            "success_criteria",
            "expected_output",
            "stretch",
        ],
        "properties": {
            "name": {"type": "string"},
            "category": {"type": "string"},
            "hook": {"type": "string"},
            "overview": {"type": "string"},
            "terms": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["term", "definition"],
                    "properties": {
                        "term": {"type": "string"},
                        "definition": {"type": "string"},
                    },
                },
            },
            "steps": string_array,
            "use_cases": string_array,
            "resource_name": {"type": "string"},
            "resource_url": {"type": "string"},
            "exercise_title": {"type": "string"},
            "exercise_intro": {"type": "string"},
            "starter_code": {"type": "string"},
            "practice_steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["title", "duration", "instructions"],
                    "properties": {
                        "title": {"type": "string"},
                        "duration": {"type": "string"},
                        "instructions": {"type": "string"},
                    },
                },
            },
            "subtasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["duration", "task"],
                    "properties": {
                        "duration": {"type": "string"},
                        "task": {"type": "string"},
                    },
                },
            },
            "success_criteria": string_array,
            "expected_output": {"type": "string"},
            "stretch": {"type": "string"},
        },
    }


def extract_response_text(payload: dict[str, Any]) -> str:
    if payload.get("output_text"):
        return str(payload["output_text"])
    chunks: list[str] = []
    for output in payload.get("output", []):
        for content in output.get("content", []):
            if content.get("type") in {"output_text", "text"} and "text" in content:
                chunks.append(str(content["text"]))
    return "".join(chunks)


def recent_history_for_prompt(history: list[dict[str, Any]], today: dt.date) -> list[dict[str, str]]:
    cutoff = today - dt.timedelta(days=30)
    recent = []
    for item in history:
        item_date = dt.date.fromisoformat(item["date"])
        if item_date >= cutoff:
            recent.append(
                {
                    "date": item["date"],
                    "topic": item["topic"],
                    "category": item.get("category", ""),
                }
            )
    return recent[-30:]


def generate_topic_with_openai(history: list[dict[str, Any]], today: dt.date) -> Topic | None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is not set. Using local fallback topic.")
        return None

    model = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
    categories = [
        "ML fundamentals",
        "LLMs",
        "computer vision",
        "NLP",
        "MLOps",
        "AI ethics",
        "vector databases",
        "agents",
        "fine-tuning",
        "RAG",
        "skills and tools",
        "embeddings",
    ]
    prompt = {
        "date": today.isoformat(),
        "recent_lessons": recent_history_for_prompt(history, today),
        "rotation_categories": categories,
        "requirements": [
            "Pick one focused, learnable AI concept for a 60-minute lesson.",
            "Do not repeat any topic from recent_lessons.",
            "Prefer a category that has not appeared recently.",
            "Make the practical section detailed, concrete, and beginner-friendly.",
            "The practical exercise must fit in 40 minutes and include step-by-step instructions.",
            "Use concise language; the final email should stay under about 3 minutes of reading.",
            "Use a real, reputable resource URL for deeper reading.",
            "Starter code can be Python, pseudocode, SQL, YAML, or shell depending on the topic.",
        ],
    }
    body = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": (
                    "You are an AI learning coach. Generate one daily lesson as strict JSON. "
                    "The lesson should be practical, accurate, and scoped for a motivated learner."
                ),
            },
            {"role": "user", "content": json.dumps(prompt, indent=2)},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "daily_ai_lesson",
                "strict": True,
                "schema": lesson_schema(),
            }
        },
        "max_output_tokens": 3500,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        output_text = extract_response_text(payload)
        return topic_from_dict(json.loads(output_text))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
        print(f"OpenAI lesson generation failed. Using local fallback topic. Error: {exc}")
        print(f"OpenAI lesson generation failed. Using local fallback topic. Error: {exc}")
        return None


def pick_topic(history: list[dict[str, Any]], today: dt.date) -> Topic:
    recent_cutoff = today - dt.timedelta(days=30)
    recent_names = {
        item["topic"]
        for item in history
        if dt.date.fromisoformat(item["date"]) >= recent_cutoff
    }
    for topic in TOPICS:
        if topic.name not in recent_names:
            return topic
    return TOPICS[len(history) % len(TOPICS)]


def md_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def practice_steps_for(topic: Topic) -> list[tuple[str, str, str]]:
    if topic.practice_steps:
        return topic.practice_steps
    return [
        (
            task,
            duration,
            "Complete this sub-task carefully, then write down what changed and what you observed before moving on.",
        )
        for duration, task in topic.subtasks
    ]


def render_markdown(topic: Topic, today: dt.date) -> tuple[str, str]:
    display_date = f"{today.strftime('%B')} {today.day}, {today.year}"
    subject = f"🧠 AI Today: {topic.name} — {display_date}"

    subject = f"\U0001f9e0 AI Today: {topic.name} - {display_date}"
    terms = "\n".join(f"- **{term}:** {definition}" for term, definition in topic.terms)
    steps = "\n".join(f"{i}. {step}" for i, step in enumerate(topic.steps, 1))
    subtasks = "\n".join(f"- **{duration}:** {task}" for duration, task in topic.subtasks)
    practice_steps = "\n\n".join(
        f"{i}. **{title} ({duration})**\n   {instructions}"
        for i, (title, duration, instructions) in enumerate(practice_steps_for(topic), 1)
    )
    expected_output = topic.expected_output or "A small working artifact plus short notes on what you learned."

    body = f"""Hi,

Today's concept helps you build stronger AI systems one practical layer at a time.
In 60 minutes, you'll learn the idea, then turn it into a small working exercise.

## Topic

**{topic.name}** — {topic.hook}

## Reading Block: 20 mins

**Concept overview**
{topic.overview}

**Key terms**
{terms}

**How it works**
{steps}

**Real-world use cases**
{md_list(topic.use_cases)}

**Go deeper**
[{topic.resource_name}]({topic.resource_url})

## Practical Block: 40 mins

**Exercise**
{topic.exercise_title}

{topic.exercise_intro}

**Starter scaffold**

```python
{topic.starter_code.rstrip()}
```

**Step-by-step process**
{practice_steps}

**Time breakdown**
{subtasks}

**You're done when**
{md_list(topic.success_criteria)}

**Expected output**
{expected_output}

**Stretch challenge**
{topic.stretch}

See you tomorrow at 9am with a new topic.
"""
    body = body.replace("\u00e2\u20ac\u201d", "-")
    return subject, body


def html_list(items: list[str]) -> str:
    return "\n".join(f"<li>{html.escape(item)}</li>" for item in items)


def html_ordered_list(items: list[str]) -> str:
    return "\n".join(f"<li>{html.escape(item)}</li>" for item in items)


def render_html(topic: Topic, today: dt.date) -> str:
    display_date = f"{today.strftime('%B')} {today.day}, {today.year}"
    terms = "\n".join(
        f"<li><strong>{html.escape(term)}</strong><span>{html.escape(definition)}</span></li>"
        for term, definition in topic.terms
    )
    subtasks = "\n".join(
        f"<tr><td style=\"padding:6px 10px 6px 0; font-weight:700; color:#9a5b00; white-space:nowrap;\">{html.escape(duration)}</td><td style=\"padding:6px 0;\">{html.escape(task)}</td></tr>"
        for duration, task in topic.subtasks
    )
    practice_steps = "\n".join(
        f"""
        <div style="background:#ffffff; border:1px solid #f1d28c; border-radius:8px; padding:14px 15px; margin:0 0 12px;">
          <div style="font-size:13px; line-height:18px; color:#9a5b00; font-weight:800;">Step {i} - {html.escape(duration)}</div>
          <h4 style="margin:4px 0 7px; color:#172033; font-size:15px; line-height:21px;">{html.escape(title)}</h4>
          <p style="margin:0; color:#344154; font-size:14px; line-height:22px;">{html.escape(instructions)}</p>
        </div>
        """
        for i, (title, duration, instructions) in enumerate(practice_steps_for(topic), 1)
    )
    expected_output = topic.expected_output or "A small working artifact plus short notes on what you learned."
    code = html.escape(topic.starter_code.rstrip())

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI Today: {html.escape(topic.name)}</title>
  </head>
  <body style="margin:0; padding:0; background:#eef2f7; color:#172033;">
    <div style="display:none; max-height:0; overflow:hidden; opacity:0;">
      {html.escape(topic.hook)}
    </div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#eef2f7; margin:0; padding:28px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:720px; background:#ffffff; border:1px solid #d9e2ef; border-radius:14px; overflow:hidden; font-family:Arial, Helvetica, sans-serif;">
            <tr>
              <td style="background:#152238; padding:28px 30px 26px;">
                <div style="font-size:13px; line-height:18px; color:#9fc5ff; font-weight:700; text-transform:uppercase; letter-spacing:.08em;">Daily AI Learning Coach</div>
                <h1 style="margin:10px 0 8px; color:#ffffff; font-size:28px; line-height:36px; font-weight:800;">{html.escape(topic.name)}</h1>
                <p style="margin:0; color:#dbeafe; font-size:16px; line-height:24px;">{html.escape(topic.hook)}</p>
                <div style="margin-top:18px;">
                  <span style="display:inline-block; background:#f6c85f; color:#152238; border-radius:999px; padding:7px 12px; font-size:13px; font-weight:700;">60 min plan</span>
                  <span style="display:inline-block; background:#27496d; color:#ffffff; border-radius:999px; padding:7px 12px; font-size:13px; font-weight:700; margin-left:6px;">{html.escape(topic.category)}</span>
                  <span style="display:inline-block; background:#27496d; color:#ffffff; border-radius:999px; padding:7px 12px; font-size:13px; font-weight:700; margin-left:6px;">{html.escape(display_date)}</span>
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:26px 30px 8px;">
                <p style="margin:0 0 8px; font-size:16px; line-height:25px; color:#263244;">Today's concept helps you build stronger AI systems one practical layer at a time.</p>
                <p style="margin:0; font-size:16px; line-height:25px; color:#263244;">In 60 minutes, learn the idea, then turn it into a small working exercise.</p>
              </td>
            </tr>
            <tr>
              <td style="padding:18px 30px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                  <tr>
                    <td style="background:#f8fafc; border:1px solid #e1e8f2; border-radius:10px; padding:22px;">
                      <div style="font-size:13px; color:#3f6ea9; font-weight:800; text-transform:uppercase; letter-spacing:.08em;">Reading Block - 20 mins</div>
                      <h2 style="margin:8px 0 10px; font-size:21px; line-height:28px; color:#172033;">Concept Overview</h2>
                      <p style="margin:0 0 18px; font-size:15px; line-height:24px; color:#344154;">{html.escape(topic.overview)}</p>

                      <h3 style="margin:0 0 10px; font-size:16px; line-height:22px; color:#172033;">Key terms</h3>
                      <ul style="margin:0 0 18px; padding-left:20px; color:#344154; font-size:15px; line-height:24px;">{terms}</ul>

                      <h3 style="margin:0 0 10px; font-size:16px; line-height:22px; color:#172033;">How it works</h3>
                      <ol style="margin:0 0 18px; padding-left:20px; color:#344154; font-size:15px; line-height:24px;">{html_ordered_list(topic.steps)}</ol>

                      <h3 style="margin:0 0 10px; font-size:16px; line-height:22px; color:#172033;">Real-world use cases</h3>
                      <ul style="margin:0 0 18px; padding-left:20px; color:#344154; font-size:15px; line-height:24px;">{html_list(topic.use_cases)}</ul>

                      <a href="{html.escape(topic.resource_url)}" style="display:inline-block; background:#2563eb; color:#ffffff; text-decoration:none; border-radius:8px; padding:11px 15px; font-size:14px; font-weight:700;">Read deeper</a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:0 30px 24px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                  <tr>
                    <td style="background:#fffaf0; border:1px solid #f1d28c; border-radius:10px; padding:22px;">
                      <div style="font-size:13px; color:#9a5b00; font-weight:800; text-transform:uppercase; letter-spacing:.08em;">Practical Block - 40 mins</div>
                      <h2 style="margin:8px 0 10px; font-size:21px; line-height:28px; color:#172033;">{html.escape(topic.exercise_title)}</h2>
                      <p style="margin:0 0 16px; font-size:15px; line-height:24px; color:#344154;">{html.escape(topic.exercise_intro)}</p>

                      <pre style="margin:0 0 18px; padding:16px; background:#111827; color:#e5e7eb; border-radius:8px; overflow-x:auto; white-space:pre-wrap; font-family:Consolas, 'Courier New', monospace; font-size:13px; line-height:20px;">{code}</pre>

                      <h3 style="margin:0 0 10px; font-size:16px; line-height:22px; color:#172033;">Step-by-step process</h3>
                      {practice_steps}

                      <h3 style="margin:0 0 10px; font-size:16px; line-height:22px; color:#172033;">Time breakdown</h3>
                      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:0 0 18px; border-collapse:collapse; font-size:14px; line-height:21px; color:#344154;">
                        {subtasks}
                      </table>

                      <h3 style="margin:0 0 10px; font-size:16px; line-height:22px; color:#172033;">You're done when</h3>
                      <ul style="margin:0 0 18px; padding-left:20px; color:#344154; font-size:15px; line-height:24px;">{html_list(topic.success_criteria)}</ul>

                      <div style="background:#ffffff; border-left:4px solid #2563eb; padding:12px 14px; border-radius:6px; color:#344154; font-size:15px; line-height:23px; margin:0 0 12px;">
                        <strong style="color:#172033;">Expected output:</strong> {html.escape(expected_output)}
                      </div>

                      <div style="background:#ffffff; border-left:4px solid #f6c85f; padding:12px 14px; border-radius:6px; color:#344154; font-size:15px; line-height:23px;">
                        <strong style="color:#172033;">Stretch challenge:</strong> {html.escape(topic.stretch)}
                      </div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:18px 30px 26px; background:#f8fafc; border-top:1px solid #e1e8f2; color:#5c6b7e; font-size:14px; line-height:22px;">
                See you tomorrow at 9am with a new topic.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def send_email(subject: str, body: str, topic: Topic, today: dt.date) -> bool:
    required = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "MAIL_FROM", "MAIL_TO"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print(f"Email not sent. Missing environment variables: {', '.join(missing)}")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ["MAIL_FROM"]
    msg["To"] = os.environ["MAIL_TO"]
    msg.set_content(body)
    msg.add_alternative(render_html(topic, today), subtype="html")

    host = os.environ["SMTP_HOST"]
    port = int(os.environ["SMTP_PORT"])
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        smtp.send_message(msg)
    print(f"Email sent to {os.environ['MAIL_TO']}")
    return True


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send email when SMTP settings are present.")
    parser.add_argument("--date", help="Override date as YYYY-MM-DD.")
    args = parser.parse_args()

    today = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    history = load_history()
    generated_by = "openai"
    topic = generate_topic_with_openai(history, today)
    if topic is None:
        generated_by = "fallback"
        topic = pick_topic(history, today)
    subject, body = render_markdown(topic, today)

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "daily-email.md").write_text(f"# {subject}\n\n{body}", encoding="utf-8")
    (OUT_DIR / "daily-email.html").write_text(render_html(topic, today), encoding="utf-8")

    sent = send_email(subject, body, topic, today) if args.send else False
    history.append(
        {
            "date": today.isoformat(),
            "topic": topic.name,
            "category": topic.category,
            "sent": sent,
            "generated_by": generated_by,
            "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
    )
    save_history(history)

    print(subject)
    print(f"Topic: {topic.name}")
    print(f"Generated by: {generated_by}")
    print(f"Output: {OUT_DIR / 'daily-email.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
