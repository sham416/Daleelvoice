"""Transcript analysis.

Deterministic work (parsing, talk-time, question extraction) happens
in Python. Only the nuanced classification/coaching work is offloaded
to the LLM. This keeps cost and latency low and makes the report
reproducible across runs.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from google import genai
from google.genai import types
from dotenv import load_dotenv

from prompts import ANALYSIS_PROMPT

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
_MODEL = os.getenv("ANALYSIS_MODEL", "gemini-2.5-flash")

# Accept Teacher / Student / Students / T / S, with optional name suffix.
# Examples that match:
#   Teacher: ...
#   Student 3: ...
#   T: ...
#   Mrs. Lee (Teacher): ...   -> falls through, we look for the keyword
_SPEAKER_RE = re.compile(
    r"^\s*(?:[\w.\-' ]{1,40}\s*\()?"          # optional "Mrs. Lee ("
    r"(teacher|students?|t|s|ss)"             # role keyword
    r"(?:\s+[\w\-]+)?"                        # optional name/number after role
    r"\)?"                                    # optional closing paren
    r"\s*[:\-–]\s*"                           # separator
    r"(.*)$",                                 # the line content
    re.IGNORECASE,
)


def parse_transcript(transcript: str) -> list[dict[str, str]]:
    """Turn a labeled transcript into a list of {speaker, text} turns.

    Lines without a recognized speaker label are attached to the
    previous turn (so multi-line teacher monologues stay intact).
    """
    turns: list[dict[str, str]] = []
    current_speaker: str | None = None
    current_text: list[str] = []

    def flush() -> None:
        if current_speaker and current_text:
            text = " ".join(current_text).strip()
            if text:
                turns.append({"speaker": current_speaker, "text": text})

    for raw_line in transcript.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = _SPEAKER_RE.match(line)
        if match:
            flush()
            role = match.group(1).lower()
            current_speaker = "teacher" if role.startswith("t") else "student"
            current_text = [match.group(2)] if match.group(2) else []
        else:
            # continuation line — attach to current speaker
            if current_speaker is None:
                # No label seen yet — default to teacher (common when
                # the first line is the teacher's opening).
                current_speaker = "teacher"
            current_text.append(line)
    flush()
    return turns


def compute_talk_time(turns: list[dict[str, str]]) -> dict[str, Any]:
    teacher_words = sum(len(t["text"].split()) for t in turns if t["speaker"] == "teacher")
    student_words = sum(len(t["text"].split()) for t in turns if t["speaker"] == "student")
    total = teacher_words + student_words

    teacher_turns = sum(1 for t in turns if t["speaker"] == "teacher")
    student_turns = sum(1 for t in turns if t["speaker"] == "student")

    if total == 0:
        return {
            "teacher_words": 0,
            "student_words": 0,
            "teacher_percentage": 0.0,
            "student_percentage": 0.0,
            "teacher_turns": teacher_turns,
            "student_turns": student_turns,
        }
    return {
        "teacher_words": teacher_words,
        "student_words": student_words,
        "teacher_percentage": round(teacher_words / total * 100, 1),
        "student_percentage": round(student_words / total * 100, 1),
        "teacher_turns": teacher_turns,
        "student_turns": student_turns,
    }


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def extract_teacher_questions(turns: list[dict[str, str]]) -> list[str]:
    """Pull every sentence ending in '?' from teacher turns."""
    questions: list[str] = []
    for turn in turns:
        if turn["speaker"] != "teacher":
            continue
        for sentence in _SENTENCE_SPLIT_RE.split(turn["text"]):
            sentence = sentence.strip()
            if sentence.endswith("?"):
                questions.append(sentence)
    return questions


def _extract_json(text: str) -> dict[str, Any]:
    """Pull the first balanced JSON object out of the model response."""
    # Strip ```json fences if present
    text = re.sub(r"```(?:json)?", "", text).strip()
    # Find first { and matching closing }
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in LLM response")
    depth = 0
    for i, ch in enumerate(text[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError("Unbalanced JSON object in LLM response")


def call_llm(prompt: str) -> dict[str, Any]:
    """Single LLM call. Swap implementation here to use a different provider.

    Gemini supports forced-JSON output via response_mime_type, so we
    don't need to scrape JSON out of code fences like we did with
    Anthropic. We still keep _extract_json as a safety net.
    """
    response = _client.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3,
            max_output_tokens=4000,
        ),
    )
    text = response.text or ""
    return _extract_json(text)


DISCLAIMER = (
    "This report is an AI-generated draft to support an instructional "
    "coaching conversation. It is not an evaluation of teacher "
    "performance. AI analysis can misinterpret tone, context, and "
    "classroom dynamics that are not visible in a transcript. Always "
    "pair this report with direct classroom observation and your own "
    "professional judgment before drawing conclusions or making "
    "decisions about a teacher's practice."
)


def analyze_transcript(transcript: str, metadata: dict[str, Any]) -> dict[str, Any]:
    """End-to-end analysis. Returns the full report dict."""
    turns = parse_transcript(transcript)
    talk_time = compute_talk_time(turns)
    questions = extract_teacher_questions(turns)

    # Drop transcript out of metadata before pretty-printing — it's
    # included separately in the prompt and would just bloat the
    # metadata block.
    metadata_for_prompt = {k: v for k, v in metadata.items() if k != "transcript"}

    prompt = ANALYSIS_PROMPT.format(
        metadata=json.dumps(metadata_for_prompt, indent=2),
        talk_time=json.dumps(talk_time, indent=2),
        questions=json.dumps(questions, indent=2),
        transcript=transcript,
    )

    try:
        llm_out = call_llm(prompt)
    except Exception as exc:  # noqa: BLE001
        # Fail gracefully — surface the deterministic parts at least.
        llm_out = {
            "summary": f"(LLM analysis failed: {exc}. The talk-time and question extraction below are still valid.)",
            "talk_time_notes": "",
            "questions": [{"text": q, "dok_level": 0, "rationale": "Not classified."} for q in questions],
            "dok_distribution": {"1": 0, "2": 0, "3": 0, "4": 0},
            "cfu_moments": [],
            "glows": [],
            "grows": [],
            "next_steps": [],
        }

    # Sanity: ensure dok_distribution is keyed by strings
    dok = llm_out.get("dok_distribution", {})
    dok = {str(k): int(v) for k, v in dok.items()}
    for level in ("1", "2", "3", "4"):
        dok.setdefault(level, 0)

    report = {
        "summary": llm_out.get("summary", ""),
        "talk_time": {**talk_time, "notes": llm_out.get("talk_time_notes", "")},
        "questions": llm_out.get("questions", []),
        "dok_distribution": dok,
        "cfu_moments": llm_out.get("cfu_moments", []),
        "glows": llm_out.get("glows", []),
        "grows": llm_out.get("grows", []),
        "next_steps": llm_out.get("next_steps", []),
        "disclaimer": DISCLAIMER,
    }
    return report
