"""Lesson Voice Analyzer — Replit edition.

Single Streamlit process: handles UI, analysis, persistence, and PDF
export all in one. Designed to run on Replit with zero configuration
beyond setting the GEMINI_API_KEY secret.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

import streamlit as st

import branding
from analyzer import analyze_transcript
from report import generate_pdf

# --------------------------------------------------------------------
# Paths and config
# --------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "lessons.db"
SAMPLE_TRANSCRIPT_PATH = BASE_DIR / "samples" / "sample_transcript.txt"

st.set_page_config(
    page_title=f"{branding.APP_NAME} · {branding.SCHOOL_NAME_EN}",
    page_icon=str(branding.LOGO_NAVY) if branding.LOGO_NAVY.exists() else "📘",
    layout="wide",
)

# Apply Gopher font + brand colors. Safe if font files are missing —
# falls back to system sans-serif. Streamlit's [theme] in config.toml
# already handles navy as the primary; this layer adds the typeface
# and small visual touches the theme block can't reach.
_brand_css = branding.gopher_font_css() + f"""
<style>
  /* Subtle navy accent line under the page title */
  h1 {{
    border-bottom: 3px solid {branding.TEAL};
    padding-bottom: 0.3em;
    display: inline-block;
  }}
  /* School identity bar at the top of the sidebar */
  section[data-testid="stSidebar"] > div:first-child {{
    padding-top: 0;
  }}
  /* Tighten metric labels to match brand's clean look */
  [data-testid="stMetricLabel"] {{
    color: {branding.NAVY};
    font-weight: 500;
  }}
  [data-testid="stMetricValue"] {{
    color: {branding.NAVY};
    font-weight: 700;
  }}
</style>
"""
st.markdown(_brand_css, unsafe_allow_html=True)


# --------------------------------------------------------------------
# SQLite
# --------------------------------------------------------------------
def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    conn = _get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_name TEXT NOT NULL,
            grade TEXT,
            subject TEXT,
            topic TEXT,
            lesson_date TEXT,
            duration_minutes INTEGER,
            transcript TEXT NOT NULL,
            report_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


_init_db()


def save_lesson(meta: dict, transcript: str, report: dict) -> int:
    conn = _get_conn()
    cur = conn.execute(
        """
        INSERT INTO lessons (teacher_name, grade, subject, topic, lesson_date,
                             duration_minutes, transcript, report_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            meta["teacher_name"],
            meta["grade"],
            meta["subject"],
            meta["topic"],
            meta["lesson_date"],
            meta["duration_minutes"],
            transcript,
            json.dumps(report),
            datetime.utcnow().isoformat(timespec="seconds"),
        ),
    )
    lesson_id = cur.lastrowid
    conn.commit()
    conn.close()
    return lesson_id


def list_lessons() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, teacher_name, subject, topic, created_at FROM lessons "
        "ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fetch_lesson(lesson_id: int) -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["report"] = json.loads(data.pop("report_json"))
    return data


# --------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------
def _init_state() -> None:
    defaults = {
        "step": 1,
        "transcript": "",
        "metadata": {
            "teacher_name": "",
            "grade": "3",
            "subject": "Reading/ELA",
            "topic": "",
            "lesson_date": str(date.today()),
            "duration_minutes": 45,
        },
        "report": None,
        "lesson_id": None,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


_init_state()


def goto(step: int) -> None:
    st.session_state.step = step
    st.rerun()


# --------------------------------------------------------------------
# Plain-text report (for copy / .txt download)
# --------------------------------------------------------------------
def text_report(meta: dict, report: dict) -> str:
    out: list[str] = []
    out.append("LESSON VOICE ANALYZER — COACHING REPORT")
    out.append("=" * 52)
    out.append("")
    out.append("LESSON DETAILS")
    out.append(f"  Teacher:  {meta.get('teacher_name', '')}")
    out.append(f"  Grade:    {meta.get('grade', '')}")
    out.append(f"  Subject:  {meta.get('subject', '')}")
    out.append(f"  Topic:    {meta.get('topic', '')}")
    out.append(f"  Date:     {meta.get('lesson_date', '')}")
    out.append(f"  Duration: {meta.get('duration_minutes', '')} min")
    out.append("")

    out.append("LESSON SUMMARY")
    out.append(report.get("summary", "") or "—")
    out.append("")

    tt = report.get("talk_time", {})
    out.append("TALK-TIME BREAKDOWN")
    out.append(
        f"  Teacher: {tt.get('teacher_words', 0)} words "
        f"({tt.get('teacher_percentage', 0)}%) across {tt.get('teacher_turns', 0)} turns"
    )
    out.append(
        f"  Students: {tt.get('student_words', 0)} words "
        f"({tt.get('student_percentage', 0)}%) across {tt.get('student_turns', 0)} turns"
    )
    if tt.get("notes"):
        out.append(f"  Notes: {tt['notes']}")
    out.append("")

    out.append("QUESTIONING ANALYSIS")
    for i, q in enumerate(report.get("questions", []), 1):
        out.append(f"  {i}. [DOK {q.get('dok_level', '—')}] {q.get('text', '')}")
        if q.get("rationale"):
            out.append(f"     Why: {q['rationale']}")
    out.append("")

    out.append("DOK DISTRIBUTION")
    dok = report.get("dok_distribution", {})
    for level in ("1", "2", "3", "4"):
        out.append(f"  DOK {level}: {dok.get(level, 0)}")
    out.append("")

    out.append("CHECKING FOR UNDERSTANDING")
    cfus = report.get("cfu_moments", [])
    if cfus:
        for c in cfus:
            out.append(f"  • {c.get('type', 'CFU')} — {c.get('description', '')}")
            if c.get("effectiveness"):
                out.append(f"    {c['effectiveness']}")
    else:
        out.append("  No deliberate CFU structures identified.")
    out.append("")

    out.append("GLOWS")
    for g in report.get("glows", []) or ["—"]:
        out.append(f"  • {g}")
    out.append("")

    out.append("GROWS")
    for g in report.get("grows", []) or ["—"]:
        out.append(f"  • {g}")
    out.append("")

    out.append("SUGGESTED NEXT STEPS")
    for n in report.get("next_steps", []) or ["—"]:
        out.append(f"  • {n}")
    out.append("")

    out.append("DISCLAIMER")
    out.append(report.get("disclaimer", ""))
    return "\n".join(out)


# --------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------
with st.sidebar:
    if branding.LOGO_NAVY.exists():
        st.image(str(branding.LOGO_NAVY), use_container_width=True)
    st.markdown(
        f"<div style='color:{branding.NAVY}; font-weight:700; "
        f"font-size:1.1rem; margin-top:0.5rem;'>{branding.APP_NAME}</div>"
        f"<div style='color:{branding.MUTED}; font-size:0.85rem;'>"
        f"Instructional coaching support · Phase 1</div>",
        unsafe_allow_html=True,
    )
    st.divider()
    steps = [
        (1, "1. Upload transcript"),
        (2, "2. Lesson details"),
        (3, "3. Analysis results"),
        (4, "4. Export report"),
    ]
    for idx, label in steps:
        if st.button(
            label,
            key=f"nav_{idx}",
            use_container_width=True,
            type="primary" if st.session_state.step == idx else "secondary",
        ):
            goto(idx)

    st.divider()
    with st.expander("Past lessons"):
        rows = list_lessons()
        if not rows:
            st.caption("None yet.")
        for r in rows:
            if st.button(
                f"#{r['id']} {r['teacher_name']} · {r['topic'] or '—'}",
                key=f"past_{r['id']}",
                use_container_width=True,
            ):
                lesson = fetch_lesson(r["id"])
                if lesson:
                    st.session_state.report = lesson["report"]
                    st.session_state.lesson_id = lesson["id"]
                    st.session_state.metadata = {
                        k: lesson.get(k)
                        for k in (
                            "teacher_name",
                            "grade",
                            "subject",
                            "topic",
                            "lesson_date",
                            "duration_minutes",
                        )
                    }
                    st.session_state.transcript = lesson["transcript"]
                    goto(3)

    st.caption(
        "Phase 1 supports pasted transcripts only. Audio upload + "
        "transcription comes in Phase 2."
    )

# --------------------------------------------------------------------
# Page 1 — Upload
# --------------------------------------------------------------------
if st.session_state.step == 1:
    st.title("Upload lesson transcript")
    st.markdown(
        "Paste a transcript with speaker labels at the start of each line. "
        "Both `Teacher:` / `Student:` and short forms (`T:` / `S:`) work."
    )

    with st.expander("Show an example of the expected format"):
        st.code(
            "Teacher: What is the main idea of this passage?\n"
            "Student: It is about friendship.\n"
            "Teacher: How do you know?\n"
            "Student: Because the boy stayed with his friend even when it was hard.\n",
            language="text",
        )

    transcript = st.text_area(
        "Transcript",
        value=st.session_state.transcript,
        height=380,
        placeholder="Teacher: ...\nStudent: ...\nTeacher: ...",
        label_visibility="collapsed",
    )

    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_a:
        if st.button("Load sample transcript", use_container_width=True):
            try:
                st.session_state.transcript = SAMPLE_TRANSCRIPT_PATH.read_text(encoding="utf-8")
                st.rerun()
            except FileNotFoundError:
                st.error("Sample file not found at samples/sample_transcript.txt")
    with col_b:
        if st.button("Clear", use_container_width=True):
            st.session_state.transcript = ""
            st.rerun()
    with col_c:
        if st.button(
            "Next →",
            type="primary",
            use_container_width=True,
            disabled=not transcript.strip(),
        ):
            st.session_state.transcript = transcript
            goto(2)

# --------------------------------------------------------------------
# Page 2 — Details
# --------------------------------------------------------------------
elif st.session_state.step == 2:
    st.title("Lesson details")
    if not st.session_state.transcript.strip():
        st.warning("No transcript yet. Go back to step 1.")
        if st.button("← Back to upload"):
            goto(1)
        st.stop()

    md = st.session_state.metadata
    with st.form("metadata_form"):
        teacher = st.text_input("Teacher name", value=md["teacher_name"])
        col1, col2 = st.columns(2)
        with col1:
            grades = ["K", "1", "2", "3", "4", "5"]
            grade = st.selectbox(
                "Grade",
                grades,
                index=grades.index(md["grade"]) if md["grade"] in grades else 3,
            )
        with col2:
            subjects = ["Reading/ELA", "Math", "Science", "Social Studies", "Other"]
            subject = st.selectbox(
                "Subject",
                subjects,
                index=subjects.index(md["subject"]) if md["subject"] in subjects else 0,
            )
        topic = st.text_input("Lesson topic / focus", value=md["topic"])
        col3, col4 = st.columns(2)
        with col3:
            try:
                default_date = date.fromisoformat(md["lesson_date"])
            except (ValueError, TypeError):
                default_date = date.today()
            lesson_date = st.date_input("Date", value=default_date)
        with col4:
            duration = st.number_input(
                "Duration (minutes)",
                min_value=5,
                max_value=180,
                value=int(md.get("duration_minutes") or 45),
                step=5,
            )

        col_back, col_submit = st.columns([1, 2])
        with col_back:
            back = st.form_submit_button("← Back", use_container_width=True)
        with col_submit:
            submit = st.form_submit_button(
                "Analyze lesson →", type="primary", use_container_width=True
            )

    if back:
        goto(1)
    if submit:
        if not teacher.strip():
            st.error("Teacher name is required.")
            st.stop()
        meta = {
            "teacher_name": teacher.strip(),
            "grade": grade,
            "subject": subject,
            "topic": topic.strip(),
            "lesson_date": str(lesson_date),
            "duration_minutes": int(duration),
        }
        st.session_state.metadata = meta

        with st.spinner("Analyzing the lesson — this usually takes 5–15 seconds…"):
            try:
                report = analyze_transcript(
                    st.session_state.transcript,
                    {**meta, "transcript": st.session_state.transcript},
                )
                lesson_id = save_lesson(meta, st.session_state.transcript, report)
                st.session_state.report = report
                st.session_state.lesson_id = lesson_id
                goto(3)
            except Exception as e:  # noqa: BLE001
                st.error(
                    f"Analysis failed: {e}\n\n"
                    "If this mentions a missing API key, open the Secrets pane "
                    "(🔒 left sidebar in Replit) and make sure `GEMINI_API_KEY` is set, "
                    "then click Stop and Run again."
                )

# --------------------------------------------------------------------
# Page 3 — Results
# --------------------------------------------------------------------
elif st.session_state.step == 3:
    st.title("Analysis results")
    if not st.session_state.report:
        st.warning("No analysis yet. Start at step 1.")
        if st.button("← Back to upload"):
            goto(1)
        st.stop()

    report = st.session_state.report
    meta = st.session_state.metadata

    st.markdown(
        f"**{meta.get('teacher_name', '')}** — {meta.get('subject', '')}, "
        f"Grade {meta.get('grade', '')} · {meta.get('topic', '')} · "
        f"{meta.get('lesson_date', '')} · {meta.get('duration_minutes', '')} min"
    )
    st.divider()

    st.subheader("Lesson summary")
    st.write(report.get("summary", "—"))

    tt = report.get("talk_time", {})
    st.subheader("Talk-time breakdown")
    c1, c2 = st.columns(2)
    c1.metric(
        "Teacher talk",
        f"{tt.get('teacher_percentage', 0)}%",
        f"{tt.get('teacher_words', 0)} words • {tt.get('teacher_turns', 0)} turns",
    )
    c2.metric(
        "Student talk",
        f"{tt.get('student_percentage', 0)}%",
        f"{tt.get('student_words', 0)} words • {tt.get('student_turns', 0)} turns",
    )
    st.progress(min(tt.get("teacher_percentage", 0) / 100, 1.0))
    if tt.get("notes"):
        st.info(tt["notes"])

    st.subheader("Questioning analysis")
    questions = report.get("questions", [])
    if questions:
        for i, q in enumerate(questions, 1):
            preview = q.get("text", "")[:90]
            with st.expander(f"Q{i} · DOK {q.get('dok_level', '—')} · {preview}"):
                st.markdown(f"**Question:** {q.get('text', '')}")
                st.markdown(f"**DOK level:** {q.get('dok_level', '—')}")
                st.markdown(f"**Why:** {q.get('rationale', '')}")
    else:
        st.write("No teacher questions identified.")

    st.subheader("DOK distribution")
    dok = report.get("dok_distribution", {})
    cols = st.columns(4)
    descriptions = {
        "1": "Recall",
        "2": "Skill/concept",
        "3": "Strategic thinking",
        "4": "Extended thinking",
    }
    for i, level in enumerate(("1", "2", "3", "4")):
        cols[i].metric(f"DOK {level}", dok.get(level, 0), descriptions[level])

    st.subheader("Checking for understanding")
    cfus = report.get("cfu_moments", [])
    if cfus:
        for c in cfus:
            st.markdown(
                f"**{c.get('type', 'CFU')}** — {c.get('description', '')}  \n"
                f"*{c.get('effectiveness', '')}*"
            )
    else:
        st.write("No deliberate CFU structures identified in this lesson.")

    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Glows")
        for g in report.get("glows", []) or ["—"]:
            st.markdown(f"- {g}")
    with g2:
        st.subheader("Grows")
        for g in report.get("grows", []) or ["—"]:
            st.markdown(f"- {g}")

    st.subheader("Suggested next steps")
    for n in report.get("next_steps", []) or ["—"]:
        st.markdown(f"- {n}")

    st.caption(report.get("disclaimer", ""))

    st.divider()
    b1, b2 = st.columns(2)
    with b1:
        if st.button("← Back to details", use_container_width=True):
            goto(2)
    with b2:
        if st.button("Go to export →", type="primary", use_container_width=True):
            goto(4)

# --------------------------------------------------------------------
# Page 4 — Export
# --------------------------------------------------------------------
elif st.session_state.step == 4:
    st.title("Export report")
    if not st.session_state.report:
        st.warning("No report to export.")
        if st.button("← Back to upload"):
            goto(1)
        st.stop()

    report = st.session_state.report
    meta = st.session_state.metadata
    txt = text_report(meta, report)

    st.subheader("Copyable plain text")
    st.caption("Select all and copy, or use the download button below.")
    st.text_area("Plain-text report", value=txt, height=420, label_visibility="collapsed")

    safe_name = (meta.get("teacher_name", "lesson") or "lesson").replace(" ", "_")

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇️ Download as .txt",
            data=txt,
            file_name=f"coaching_report_{safe_name}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with c2:
        lesson_for_pdf = {**meta}
        pdf_bytes = generate_pdf(lesson_for_pdf, report)
        st.download_button(
            "📄 Download as PDF",
            data=pdf_bytes,
            file_name=f"coaching_report_{safe_name}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )

    st.divider()
    if st.button("← Back to results"):
        goto(3)
