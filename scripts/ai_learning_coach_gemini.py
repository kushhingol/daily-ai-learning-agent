#!/usr/bin/env python3
"""Generate and optionally email a daily AI learning plan as HTML."""

from __future__ import annotations

import argparse
import html
import datetime as dt
import json
import os
import smtplib
import random
import urllib.error
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any
from time import sleep


ROOT = Path(__file__).resolve().parents[1]
HISTORY_PATH = ROOT / "learning_history.json"
OUT_DIR = ROOT / "dist"
ENV_PATH = ROOT / ".env"

MAX_RETRIES = 5
RETRYABLE_CODES = {429, 500, 502, 503, 504}


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
    news_block: str
    practice_steps: list[tuple[str, str, str]] | None = None
    expected_output: str = ""


TOPICS: list[Topic] = [
    Topic(
        name="HNSW Indexes for Vector Search",
        category="vector databases",
        hook="Fast vector search is the retrieval layer behind many useful RAG systems.",
        overview="HNSW is an approximate nearest-neighbor index that stores vectors in a layered graph so similar items can be found quickly without scanning every vector.",
        terms=[
            (
                "Embedding",
                "A list of numbers that represents the meaning of text, images, or other data.",
            ),
            ("Nearest neighbor", "The stored vector most similar to a query vector."),
            (
                "Approximate search",
                "A faster search that may trade perfect accuracy for very close results.",
            ),
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
""",
        success_criteria=[
            "Your script returns the top 3 most similar documents for a query.",
            "You can explain why brute-force search slows down as vectors grow.",
        ],
        stretch="Scale the dataset to 1,000+ documents.",
        subtasks=[
            ("5 mins", "Create sample text data."),
            ("10 mins", "Implement brute-force cosine similarity."),
        ],
        news_block="* **Frontier Deployments:** Teams are routing workloads to GPT-5.5 and Gemini 3.5 Flash.\\n* **Agentic Ecosystems:** Microsoft officially rolled out 'Scout'.",
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
        name=str(data.get("name", "")),
        category=str(data.get("category", "")),
        hook=str(data.get("hook", "")),
        overview=str(data.get("overview", "")),
        terms=[
            (str(item.get("term", "")), str(item.get("definition", "")))
            for item in data.get("terms", [])
            if isinstance(item, dict)
        ],
        steps=[str(item) for item in data.get("steps", [])],
        use_cases=[str(item) for item in data.get("use_cases", [])],
        resource_name=str(data.get("resource_name", "")),
        resource_url=str(data.get("resource_url", "")),
        exercise_title=str(data.get("exercise_title", "")),
        exercise_intro=str(data.get("exercise_intro", "")),
        starter_code=str(data.get("starter_code", "")),
        success_criteria=[str(item) for item in data.get("success_criteria", [])],
        stretch=str(data.get("stretch", "")),
        subtasks=[
            (str(item.get("duration", "")), str(item.get("task", "")))
            for item in data.get("subtasks", [])
            if isinstance(item, dict)
        ],
        news_block=str(data.get("news_block", "No new updates available for today.")),
        practice_steps=[
            (
                str(item.get("title", "")),
                str(item.get("duration", "")),
                str(item.get("instructions", "")),
            )
            for item in data.get("practice_steps", [])
            if isinstance(item, dict)
        ],
        expected_output=str(data.get("expected_output", "")),
    )


def lesson_schema() -> dict[str, Any]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "category": {"type": "string"},
            "hook": {"type": "string"},
            "overview": {"type": "string"},
            "terms": {
                "type": "array",
                "items": {
                    "type": "object",
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
            "news_block": {"type": "string"},
        },
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
            "news_block",
        ],
    }


def extract_gemini_response_text(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return ""

    candidates = payload.get("candidates")
    if isinstance(candidates, list) and candidates:
        content = candidates[0].get("content")
        if isinstance(content, dict):
            parts = content.get("parts")
            if isinstance(parts, list) and parts:
                return str(parts[0].get("text", ""))
            return str(content.get("text", ""))

        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict):
                return str(first.get("text", ""))

    if isinstance(payload.get("content"), dict):
        return str(payload["content"].get("text", ""))

    return ""


def parse_gemini_json_text(text: str) -> Any:
    trimmed = text.strip()
    if not trimmed:
        raise ValueError("Gemini returned empty response text")

    try:
        return json.loads(trimmed)
    except json.JSONDecodeError as first_error:
        if trimmed.startswith('"') and trimmed.endswith('"'):
            try:
                unwrapped = json.loads(trimmed)
                return json.loads(unwrapped)
            except json.JSONDecodeError:
                pass

        decoder = json.JSONDecoder()
        candidates: list[Any] = []
        for idx, char in enumerate(trimmed):
            if char not in "{[":
                continue
            try:
                obj, _ = decoder.raw_decode(trimmed[idx:])
                candidates.append(obj)
            except json.JSONDecodeError:
                continue

        for candidate in candidates:
            lesson = find_lesson_object(candidate)
            if lesson is not None:
                return candidate

        if candidates:
            return candidates[0]

        raise first_error


def find_lesson_object(data: Any) -> dict[str, Any] | None:
    if isinstance(data, dict):
        required_keys = {"name", "category", "hook", "overview", "terms", "steps"}
        if required_keys.issubset(set(data.keys())):
            return data

        for value in data.values():
            if isinstance(value, (dict, list)):
                found = find_lesson_object(value)
                if found is not None:
                    return found

    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                found = find_lesson_object(item)
                if found is not None:
                    return found

    return None


def recent_history_for_prompt(
    history: list[dict[str, Any]], today: dt.date
) -> list[dict[str, str]]:
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


def _call_gemini_api(url: str, body: dict, timeout: int = 60) -> dict:
    """Raw HTTP call to Gemini. Raises urllib.error.HTTPError on failure."""
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _parse_retry_delay_from_api_error(exc: Any) -> float | None:
    response_json = getattr(exc, "response_json", None)
    if isinstance(response_json, dict):
        error = response_json.get("error", {})
        details = error.get("details", [])
        for item in details:
            if not isinstance(item, dict):
                continue
            if item.get("@type", "").endswith("RetryInfo"):
                retry_delay = item.get("retryDelay")
                if isinstance(retry_delay, dict):
                    seconds = retry_delay.get("seconds") or 0
                    nanos = retry_delay.get("nanos") or 0
                    try:
                        return float(seconds) + float(nanos) / 1_000_000_000
                    except (TypeError, ValueError):
                        continue
                if isinstance(retry_delay, str) and retry_delay.endswith("s"):
                    try:
                        return float(retry_delay[:-1])
                    except ValueError:
                        continue
        message = error.get("message", "")
        if isinstance(message, str):
            match = __import__("re").search(r"retry in ([0-9.]+)s", message)
            if match:
                return float(match.group(1))
    return None


def _call_gemini_sdk_api(
    model: str, prompt_context: dict[str, Any], api_key: str, system_instruction: str
) -> dict[str, Any]:
    try:
        from google.genai import client as genai_client, types
    except ImportError as exc:
        raise ImportError("google-genai SDK is not installed") from exc

    sdk = genai_client.Client(api_key=api_key)
    prompt_text = json.dumps(prompt_context)
    print("Calling Gemini SDK with model '%s'", model)
    response = sdk.models.generate_content(
        model=model,
        contents=[prompt_text],
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=lesson_schema(),
            max_output_tokens=4000,
        ),
    )

    if hasattr(response, "to_json_dict"):
        return response.to_json_dict()
    if hasattr(response, "dict"):
        return response.dict()
    return response


def _get_retry_delay_from_sdk_error(exc: Any) -> float | None:
    try:
        from google.genai.errors import APIError, ClientError, ServerError
    except ImportError:
        return None

    if not isinstance(exc, (APIError, ClientError, ServerError)):
        return None

    retry = _parse_retry_delay_from_api_error(exc)
    if retry is not None:
        return retry

    if getattr(exc, "code", None) in RETRYABLE_CODES:
        return 0.0
    return None


def _with_exponential_backoff(fn, max_retries: int = MAX_RETRIES):
    """
    Calls fn() with exponential backoff on retryable HTTP errors.
    Raises the last exception if all retries are exhausted.
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            return fn()
        except urllib.error.HTTPError as e:
            last_exc = e
            if e.code not in RETRYABLE_CODES:
                print(f"Non-retryable HTTP error {e.code}: {e.reason}")
                raise

            wait = (2**attempt) + random.uniform(
                0.5, 1.5
            )  # 1.5s, 2.5s, 4.5s, 8.5s, 16.5s
            print(
                f"Attempt {attempt + 1}/{max_retries} failed with HTTP {e.code}. "
                f"Retrying in {wait:.1f}s..."
            )
            sleep(wait)

        except urllib.error.URLError as e:
            # Network-level errors (timeouts, DNS failures) — always retry
            last_exc = e
            wait = (2**attempt) + random.uniform(0.5, 1.5)
            print(
                f"Attempt {attempt + 1}/{max_retries} network error: {e.reason}. "
                f"Retrying in {wait:.1f}s..."
            )
            sleep(wait)

        except Exception as e:
            retry_delay = _get_retry_delay_from_sdk_error(e)
            if retry_delay is None:
                raise

            last_exc = e
            wait = (
                retry_delay
                if retry_delay > 0
                else (2**attempt) + random.uniform(0.5, 1.5)
            )
            print(
                f"Attempt {attempt + 1}/{max_retries} failed with SDK rate limit. "
                f"Retrying in {wait:.1f}s..."
            )
            sleep(wait)

    raise last_exc


def generate_topic_with_gemini(
    history: list[dict[str, Any]], today: dt.date
) -> Topic | None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set. Using local fallback.")
        return None

    api_key = api_key.strip().strip("[]'\"")
    env_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
    model = env_model.strip().strip("[]'\"")

    # Updated category rotation mapping
    categories = [
        # Primary Priorities
        "prompt and context engineering",
        "agentic design patterns",
        "ai workflow automation",
        "tool use and orchestration",
        "multi-agent systems",
        # Technical Building Blocks
        "RAG and retrieval systemsLLM fine-tuning",
        "vector databases",
        "embeddings",
        "multimodal models",
        # Foundational & Specialized
        "MLOps and evaluation",
        "ai governance and ethics",
        "computer vision",
        "NLP fundamentals",
        "ai code agents",
    ]

    prompt_context = {
        "date": today.isoformat(),
        "recent_lessons": recent_history_for_prompt(history, today),
        "rotation_categories": categories,
        "requirements": [
            "Pick one focused concept from the rotation_categories list for a 60-minute lesson.",
            "Prioritize 'prompt and context engineering' and 'agentic design patterns' for the next two sessions.",
            "Do not repeat topics or categories that appeared recently.",
            "Generate a news_block string summarizing the top 3-5 high-impact breakthroughs in AI agents and workflow automation from the last 7 days.",
        ],
    }

    body = {
        "contents": [{"parts": [{"text": json.dumps(prompt_context)}]}],
        "systemInstruction": {
            "parts": [
                {
                    "text": "You are an AI learning coach. Select a category from rotation_categories and return a JSON daily lesson mapping the responseSchema configuration exactly."
                }
            ]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": lesson_schema(),
            "maxOutputTokens": 4000,
        },
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    output_text = ""
    payload = None
    try:
        try:
            payload = _with_exponential_backoff(
                lambda: _call_gemini_sdk_api(
                    model=model,
                    prompt_context=prompt_context,
                    api_key=api_key,
                    system_instruction="You are an AI learning coach. Select a category from rotation_categories and return a JSON daily lesson mapping the responseSchema configuration exactly.",
                ),
                max_retries=MAX_RETRIES,
            )
            print("Using google-genai SDK for Gemini generation.")
        except ImportError:
            print("google-genai SDK not available; falling back to HTTP API.")
            payload = _with_exponential_backoff(
                lambda: _call_gemini_api(url, body, timeout=90),
                max_retries=MAX_RETRIES,
            )

        output_text = extract_gemini_response_text(payload)

        if output_text:
            parsed = parse_gemini_json_text(output_text)
        else:
            parsed = payload

        lesson_data = find_lesson_object(parsed)
        if lesson_data is None:
            print(
                "Gemini lesson match failed. Parsed output type:", type(parsed).__name__
            )
            if isinstance(parsed, dict):
                print("Parsed keys:", list(parsed.keys()))
            elif isinstance(parsed, list):
                print("Parsed list length:", len(parsed))
                if parsed and isinstance(parsed[0], dict):
                    print("First item keys:", list(parsed[0].keys()))
            raise ValueError(
                "Gemini JSON did not contain a lesson object with required fields"
            )

        return topic_from_dict(lesson_data)

    except urllib.error.HTTPError as e:
        print(
            f"Gemini generation failed after {MAX_RETRIES} retries — HTTP {e.code}: {e.reason}"
        )
        return None
    except urllib.error.URLError as e:
        print(f"Gemini generation failed — network error: {e.reason}")
        return None
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Gemini response parsing failed: {e}")
        if output_text:
            snippet = output_text[:1200]
            print(f"Raw Gemini output (truncated): {repr(snippet)}")
        else:
            print(
                f"Raw Gemini payload keys: {list(payload.keys()) if isinstance(payload, dict) else type(payload)}"
            )
        return None
    except Exception as e:
        print(f"Gemini generation failed — unexpected error: {e}")
        return None


def pick_topic(history: list[dict[str, Any]], today: dt.date) -> Topic:
    recent_names = {item["topic"] for item in history}
    for topic in TOPICS:
        if topic.name not in recent_names:
            return topic
    return TOPICS[0]


def render_html_email(topic: Topic, today: dt.date) -> str:
    display_date = f"{today.strftime('%B')} {today.day}, {today.year}"

    terms_html = "".join(
        f"<li><strong>{html.escape(t)}:</strong> {html.escape(d)}</li>"
        for t, d in topic.terms
    )
    steps_html = "".join(f"<li>{html.escape(s)}</li>" for s in topic.steps)
    use_cases_html = "".join(f"<li>{html.escape(u)}</li>" for u in topic.use_cases)
    subtasks_html = "".join(
        f"<li><strong>{html.escape(dur)}:</strong> {html.escape(tsk)}</li>"
        for dur, tsk in topic.subtasks
    )

    # Safely convert plain text or markdown bullets from news_block to HTML breaks
    formatted_news = html.escape(topic.news_block).replace("\n", "<br/>")
    escaped_code = html.escape(topic.starter_code.rstrip())

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>AI Today: {html.escape(topic.name)}</title>
  </head>
  <body style="margin:0; padding:0; background-color:#f4f6f9; color:#1e293b; font-family:Arial, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#f4f6f9; padding:20px 10px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:650px; background-color:#ffffff; border:1px solid #e2e8f0; border-radius:12px; overflow:hidden; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
            
            <tr>
              <td style="background-color:#0f172a; padding:30px; color:#ffffff;">
                <div style="font-size:12px; text-transform:uppercase; letter-spacing:0.05em; color:#38bdf8; font-weight:700; margin-bottom:6px;">Daily Learning Plan</div>
                <h1 style="margin:0 0 10px 0; font-size:26px; line-height:32px; font-weight:800;">{html.escape(topic.name)}</h1>
                <p style="margin:0; font-size:15px; color:#94a3b8; line-height:22px;">{html.escape(topic.hook)}</p>
                <div style="margin-top:15px; font-size:13px; color:#cbd5e1;">
                  <span style="background-color:#1e293b; padding:4px 10px; border-radius:20px; font-weight:600; margin-right:8px;">{html.escape(topic.category)}</span>
                  <span>{html.escape(display_date)}</span>
                </div>
              </td>
            </tr>

            <tr>
              <td style="padding:25px 30px 10px 30px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#f0f9ff; border:1px solid #bae6fd; border-radius:8px;">
                  <tr>
                    <td style="padding:20px;">
                      <h3 style="margin:0 0 10px 0; font-size:16px; color:#0369a1; font-weight:800; text-transform:uppercase; letter-spacing:0.02em;">📰 What's Latest in AI (5 mins read)</h3>
                      <div style="font-size:14px; line-height:22px; color:#0c4a6e;">{formatted_news}</div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <tr>
              <td style="padding:20px 30px;">
                <h2 style="margin:0 0 12px 0; font-size:20px; color:#0f172a; border-bottom:2px solid #f1f5f9; padding-bottom:6px;">🧠 Core Study Concepts (15 mins)</h2>
                <p style="font-size:15px; line-height:24px; color:#334155; margin:0 0 16px 0;">{html.escape(topic.overview)}</p>
                
                <h4 style="margin:0 0 6px 0; font-size:14px; color:#475569; text-transform:uppercase;">Key Terms</h4>
                <ul style="margin:0 0 16px 0; padding-left:20px; font-size:14px; line-height:22px; color:#334154;">{terms_html}</ul>

                <h4 style="margin:0 0 6px 0; font-size:14px; color:#475569; text-transform:uppercase;">Mechanics & Steps</h4>
                <ol style="margin:0 0 16px 0; padding-left:20px; font-size:14px; line-height:22px; color:#334154;">{steps_html}</ol>

                <h4 style="margin:0 0 6px 0; font-size:14px; color:#475569; text-transform:uppercase;">Enterprise Use Cases</h4>
                <ul style="margin:0 0 20px 0; padding-left:20px; font-size:14px; line-height:22px; color:#334154;">{use_cases_html}</ul>

                <a href="{html.escape(topic.resource_url)}" style="display:inline-block; background-color:#2563eb; color:#ffffff; text-decoration:none; padding:10px 20px; font-size:14px; font-weight:700; border-radius:6px;">Explore Full Documentation</a>
              </td>
            </tr>

            <tr>
              <td style="padding:10px 30px 30px 30px;">
                <h2 style="margin:0 0 12px 0; font-size:20px; color:#0f172a; border-bottom:2px solid #f1f5f9; padding-bottom:6px;">💻 Hands-On Lab Exercise (40 mins)</h2>
                <h3 style="margin:0 0 6px 0; font-size:16px; color:#1e293b;">{html.escape(topic.exercise_title)}</h3>
                <p style="font-size:14px; line-height:22px; color:#475569; margin:0 0 16px 0;">{html.escape(topic.exercise_intro)}</p>

                <div style="background-color:#0f172a; border-radius:8px; padding:16px; margin-bottom:20px; overflow-x:auto;">
                  <pre style="margin:0; font-family:'Courier New', Courier, monospace; font-size:13px; color:#e2e8f0; line-height:18px; white-space:pre;">{escaped_code}</pre>
                </div>

                <h4 style="margin:0 0 6px 0; font-size:14px; color:#475569; text-transform:uppercase;">Time Breakdown Matrix</h4>
                <ul style="margin:0 0 16px 0; padding-left:20px; font-size:14px; line-height:22px; color:#334154;">{subtasks_html}</ul>

                <div style="background-color:#f8fafc; border-left:4px solid #cbd5e1; padding:12px 16px; font-size:14px; line-height:20px; color:#334155; margin-bottom:12px;">
                  <strong>Expected Artifact Output:</strong> {html.escape(topic.expected_output or "A clean working validation execution script.")}
                </div>

                <div style="background-color:#fffbeb; border-left:4px solid #f59e0b; padding:12px 16px; font-size:14px; line-height:20px; color:#78350f;">
                  <strong>Stretch Target Optimization:</strong> {html.escape(topic.stretch)}
                </div>
              </td>
            </tr>

            <tr>
              <td style="background-color:#f1f5f9; padding:20px 30px; text-align:center; font-size:13px; color:#64748b; border-top:1px solid #e2e8f0;">
                Execution log tracking active. Next core architecture module deploys tomorrow morning at 09:00 AM.
              </td>
            </tr>

          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def send_email(subject: str, topic: Topic, today: dt.date, html_body: str) -> bool:
    required = [
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASS",
        "MAIL_FROM",
        "MAIL_TO",
    ]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print(f"Email not sent. Missing environment variables: {', '.join(missing)}")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ["MAIL_FROM"]
    msg["To"] = os.environ["MAIL_TO"]
    msg.add_alternative(html_body, subtype="html")

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
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()

    today = dt.date.today()
    history = load_history()

    topic = generate_topic_with_gemini(history, today) or pick_topic(history, today)

    display_date = f"{today.strftime('%B')} {today.day}, {today.year}"
    subject = f"🧠 AI Today: {topic.name} - {display_date}"

    # Render unified layout
    html_content = render_html_email(topic, today)

    # Save artifact strictly as HTML inside output location
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "daily-email.html").write_text(html_content, encoding="utf-8")

    sent = False
    if args.send:
        sent = send_email(subject, topic, today, html_content)

    history.append(
        {
            "date": today.isoformat(),
            "topic": topic.name,
            "category": topic.category,
            "sent": sent,
            "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
    )
    save_history(history)

    print(f"Generated topic: {topic.name} ({topic.category})")
    print(f"Success! Output file compiled at: {OUT_DIR / 'daily-email.html'}")
    print(f"Email sent: {'Yes' if sent else 'No'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
