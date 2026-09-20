"""Product interface for ResumeIQ."""

import hashlib
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from document_loader import ResumeReadError, extract_resume_text
from resume_export import build_comparison_html, create_resume_docx
from resume_graph import analyze_resume, match_resume_to_job, tailor_resume_to_job


PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")
load_dotenv(PROJECT_DIR.parent / ".env")

st.set_page_config(
    page_title="ResumeIQ | Build a stronger resume",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #172033;
        --muted: #667085;
        --brand: #5b5bd6;
        --brand-dark: #4444b8;
        --surface: #ffffff;
        --line: #e6e8ef;
        --soft: #f6f7fb;
        --success: #087a55;
    }
    .stApp { background:
        radial-gradient(circle at 88% 8%, rgba(124,58,237,.12), transparent 28%),
        radial-gradient(circle at 48% 0%, rgba(59,130,246,.08), transparent 24%),
        #f7f8fc; }
    .block-container { max-width: 1220px; padding-top: 1.6rem; padding-bottom: 4rem; }
    [data-testid="stSidebar"] { background: #111827; }
    [data-testid="stSidebar"] * { color: #f9fafb; }
    [data-testid="stSidebar"] .stAlert * { color: inherit; }
    h1, h2, h3 { color: var(--ink); letter-spacing: -0.025em; }
    .brand { display:flex; align-items:center; gap:.7rem; margin:.25rem 0 2rem; }
    .brand-mark { width:36px; height:36px; border-radius:10px; background:linear-gradient(135deg,#818cf8,#4f46e5); display:grid; place-items:center; font-weight:800; }
    .brand-name { font-size:1.25rem; font-weight:750; }
    .eyebrow { color:var(--brand); font-weight:700; font-size:.78rem; letter-spacing:.12em; text-transform:uppercase; }
    .hero-shell { position:relative; overflow:hidden; display:grid; grid-template-columns:1.5fr .85fr; gap:1.5rem; padding:2.25rem; margin:.45rem 0 1.55rem; border:1px solid rgba(255,255,255,.85); border-radius:26px; background:linear-gradient(135deg,rgba(255,255,255,.96),rgba(244,241,255,.88)); box-shadow:0 24px 70px rgba(67,56,202,.10); }
    .hero-shell:after { content:""; position:absolute; width:320px; height:320px; border-radius:50%; right:-130px; top:-180px; background:linear-gradient(135deg,rgba(99,102,241,.25),rgba(168,85,247,.18)); filter:blur(2px); }
    .hero-copy { position:relative; z-index:2; }
    .hero-copy h1 { color:#111827 !important; font-size:3rem; line-height:1.03; margin:.45rem 0 .8rem; max-width:720px; }
    .hero-copy p { color:#667085 !important; font-size:1.08rem; line-height:1.65; max-width:700px; margin:0; }
    .preview-card { position:relative; z-index:2; background:rgba(17,24,39,.96); border:1px solid rgba(255,255,255,.12); border-radius:20px; padding:1.2rem; box-shadow:0 18px 45px rgba(17,24,39,.25); align-self:center; transform:rotate(1.5deg); }
    .preview-top { display:flex; justify-content:space-between; color:#c7d2fe; font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; }
    .preview-score { color:white; font-size:2.4rem; font-weight:800; margin:.7rem 0 .15rem; }
    .preview-bar { height:7px; border-radius:99px; background:#30394c; overflow:hidden; margin:.65rem 0 1rem; }
    .preview-bar span { display:block; width:84%; height:100%; background:linear-gradient(90deg,#818cf8,#c084fc); border-radius:99px; }
    .preview-row { display:flex; gap:.5rem; margin-top:.55rem; }
    .preview-pill { flex:1; background:#202a3d; color:#dbe4ff; padding:.55rem; border-radius:10px; font-size:.72rem; text-align:center; }
    .trust-row { display:flex; flex-wrap:wrap; gap:.55rem; margin-top:1rem; }
    .trust-pill { background:#eef0ff; color:#4444b8; border:1px solid #dfe1ff; border-radius:999px; padding:.35rem .7rem; font-size:.8rem; font-weight:600; }
    .feature-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:.8rem; margin:0 0 1.5rem; }
    .feature-card { background:rgba(255,255,255,.82); backdrop-filter:blur(10px); border:1px solid #e7e8f1; border-radius:16px; padding:1rem 1.05rem; box-shadow:0 8px 24px rgba(16,24,40,.04); }
    .feature-icon { width:34px; height:34px; display:grid; place-items:center; border-radius:10px; color:#fff; background:linear-gradient(135deg,#6366f1,#8b5cf6); font-weight:800; margin-bottom:.65rem; }
    .feature-card b { color:#172033; display:block; margin-bottom:.25rem; }
    .feature-card span { color:#667085; font-size:.82rem; line-height:1.45; }
    [data-testid="stTabs"] [data-baseweb="tab-list"] { gap:.55rem; background:#fff; padding:.45rem; border:1px solid var(--line); border-radius:14px; }
    [data-testid="stTabs"] button { border-radius:10px; padding:.65rem 1rem; }
    [data-testid="stTabs"] button[aria-selected="true"] { background:#eef0ff; color:var(--brand-dark); }
    [data-testid="stFileUploader"] { background:#fff; border:1px dashed #c7cad5; border-radius:14px; padding:.4rem; }
    [data-testid="stTextArea"] textarea { background:#fff; border-color:#d9dce7; border-radius:12px; }
    [data-testid="stMetric"] { background:#fff; border:1px solid var(--line); padding:1rem 1.1rem; border-radius:14px; box-shadow:0 1px 2px rgba(16,24,40,.03); }
    [data-testid="stMetricValue"] { color:var(--ink); }
    .section-intro { color:var(--muted); margin-top:-.55rem; margin-bottom:1.2rem; }
    .result-card { background:#fff; border:1px solid var(--line); border-radius:16px; padding:1.15rem 1.25rem; margin:.65rem 0; box-shadow:0 1px 3px rgba(16,24,40,.04); }
    .result-card h4 { color:var(--ink); margin:0 0 .55rem; font-size:1rem; }
    .score-wrap { background:#fff; border:1px solid var(--line); border-radius:18px; padding:1.2rem 1.4rem; margin:1rem 0; }
    .score-label { color:var(--muted); font-size:.83rem; font-weight:650; text-transform:uppercase; letter-spacing:.08em; }
    .score-value { color:var(--ink); font-size:2.2rem; font-weight:800; line-height:1.1; }
    .score-track { background:#eaecf0; height:9px; border-radius:99px; overflow:hidden; margin-top:.8rem; }
    .score-fill { background:linear-gradient(90deg,#6366f1,#8b5cf6); height:100%; border-radius:99px; }
    .privacy-note { color:#98a2b3; font-size:.78rem; line-height:1.5; }
    .stButton > button, .stDownloadButton > button { border-radius:10px; min-height:2.8rem; font-weight:650; }
    .stButton > button[kind="primary"] { background:var(--brand); border-color:var(--brand); }
    .stButton > button[kind="primary"]:hover { background:var(--brand-dark); border-color:var(--brand-dark); }
    @media (max-width: 900px) { .hero-shell { grid-template-columns:1fr; padding:1.5rem; } .hero-copy h1 { font-size:2.35rem; } .preview-card { transform:none; } .feature-grid { grid-template-columns:1fr; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_resume(uploaded_file):
    """Validate and extract one uploaded resume."""

    if uploaded_file is None:
        return None
    if uploaded_file.size > 10 * 1024 * 1024:
        st.error("This file is over 10 MB. Please upload a smaller resume.")
        return None
    try:
        return extract_resume_text(uploaded_file.name, uploaded_file.getvalue())
    except ResumeReadError as error:
        st.error(str(error))
        return None


def fingerprint(uploaded_file, job_description: str = "") -> str:
    digest = hashlib.sha256(uploaded_file.getvalue())
    digest.update(job_description.strip().encode("utf-8"))
    return digest.hexdigest()


def render_list(items: list[str], empty_message: str = "Nothing identified."):
    if not items:
        st.caption(empty_message)
    for item in items:
        st.markdown(f"- {item}")


def friendly_error(error: Exception) -> str:
    message = str(error)
    if "429" in message or "rate_limit" in message:
        return "The analysis service is busy. Please wait a moment and try again."
    if "json_validate_failed" in message:
        return "The analysis response was incomplete. Please try again."
    return message


def score_panel(label: str, score: int, summary: str):
    st.markdown(
        f"""
        <div class="score-wrap">
          <div class="score-label">{label}</div>
          <div class="score-value">{score}<span style="font-size:1rem;color:#98a2b3"> / 100</span></div>
          <div class="score-track"><div class="score-fill" style="width:{score}%"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write(summary)


with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-mark">R</div><div class="brand-name">ResumeIQ</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### Your resume workspace")
    st.caption("Review, compare, and tailor your resume from one secure workspace.")
    st.divider()
    st.markdown("**Supported files**")
    st.caption("PDF, DOCX, and TXT · Up to 10 MB")
    st.markdown("**Designed for privacy**")
    st.markdown(
        '<p class="privacy-note">Files are processed for your current session and are not stored by this application.</p>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.caption("Always review suggestions before using them in an application.")

st.markdown(
    """
    <div class="hero-shell">
      <div class="hero-copy">
        <div class="eyebrow">Your career, better positioned</div>
        <h1>Make every line of your resume work harder.</h1>
        <p>Understand what recruiters see, measure your fit for any role, and build a focused resume without losing the truth of your experience.</p>
        <div class="trust-row">
          <span class="trust-pill">Private by design</span>
          <span class="trust-pill">Evidence-first</span>
          <span class="trust-pill">Ready to export</span>
        </div>
      </div>
      <div class="preview-card">
        <div class="preview-top"><span>Resume pulse</span><span>Live preview</span></div>
        <div class="preview-score">84<span style="font-size:.9rem;color:#94a3b8"> / 100</span></div>
        <div style="color:#a5b4fc;font-size:.78rem">Strong role alignment</div>
        <div class="preview-bar"><span></span></div>
        <div class="preview-row"><div class="preview-pill">✓ 8 strengths</div><div class="preview-pill">↗ 3 upgrades</div></div>
      </div>
    </div>
    <div class="feature-grid">
      <div class="feature-card"><div class="feature-icon">01</div><b>Reveal your strengths</b><span>See the evidence, clarity, and impact already working in your favor.</span></div>
      <div class="feature-card"><div class="feature-icon">02</div><b>Measure role fit</b><span>Understand alignment, missing evidence, and the language recruiters expect.</span></div>
      <div class="feature-card"><div class="feature-icon">03</div><b>Build a focused version</b><span>Prioritize your real experience and export a clean, application-ready resume.</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not os.getenv("GROQ_API_KEY"):
    st.error("The analysis service is temporarily unavailable. Please contact support.")
    st.stop()

review_tab, match_tab, tailor_tab = st.tabs(
    ["Resume review", "Role match", "Tailor resume"]
)

with review_tab:
    st.header("Know what works—and what needs attention")
    st.markdown(
        '<p class="section-intro">Upload your resume for a practical review of its clarity, evidence, structure, and impact.</p>',
        unsafe_allow_html=True,
    )
    review_file = st.file_uploader(
        "Choose your resume", type=["pdf", "docx", "txt"], key="review_file"
    )
    review_text = read_resume(review_file)

    if review_text:
        with st.expander("Preview extracted content"):
            st.text(review_text)
        review_key = fingerprint(review_file)
        if st.button("Review my resume", type="primary", key="review_button", use_container_width=True):
            try:
                with st.spinner("Reviewing your resume..."):
                    st.session_state.review_result = analyze_resume(review_text)
                    st.session_state.review_key = review_key
            except Exception as error:
                st.error(friendly_error(error))

        result = st.session_state.get("review_result")
        if result and st.session_state.get("review_key") == review_key:
            st.divider()
            score_panel("Resume strength", result.resume_score, result.executive_summary)
            level_col, role_col = st.columns(2)
            level_col.metric("Experience level", result.candidate_snapshot.experience_level)
            role_col.metric("Best-fit direction", result.candidate_snapshot.likely_target_role)

            strengths_col, opportunities_col = st.columns(2)
            with strengths_col:
                with st.container(border=True):
                    st.subheader("What stands out")
                    render_list(result.pros)
            with opportunities_col:
                with st.container(border=True):
                    st.subheader("What to improve")
                    render_list(result.cons)

            with st.container(border=True):
                st.subheader("Recommended next steps")
                for number, item in enumerate(result.improvement_plan, start=1):
                    st.markdown(f"**{number}.** {item}")

with match_tab:
    st.header("See how your resume aligns with a role")
    st.markdown(
        '<p class="section-intro">Compare the evidence in your resume with the role’s skills and responsibilities.</p>',
        unsafe_allow_html=True,
    )
    input_col, job_col = st.columns([0.9, 1.1])
    with input_col:
        match_file = st.file_uploader(
            "Choose your resume", type=["pdf", "docx", "txt"], key="match_file"
        )
    with job_col:
        match_job = st.text_area(
            "Job description",
            height=225,
            key="match_job",
            placeholder="Paste the complete job description here...",
        )
    match_text = read_resume(match_file)

    if match_text and match_job.strip():
        match_key = fingerprint(match_file, match_job)
        if st.button("Check role match", type="primary", key="match_button", use_container_width=True):
            if len(match_job.strip()) < 100:
                st.error("Add a more complete job description to get a useful comparison.")
            else:
                try:
                    with st.spinner("Comparing your resume with this role..."):
                        st.session_state.match_result = match_resume_to_job(match_text, match_job.strip())
                        st.session_state.match_key = match_key
                except Exception as error:
                    st.error(friendly_error(error))

        result = st.session_state.get("match_result")
        if result and st.session_state.get("match_key") == match_key:
            st.divider()
            score_panel("Role alignment", result.match_score, result.summary)
            aligned_col, gap_col = st.columns(2)
            with aligned_col:
                with st.container(border=True):
                    st.subheader("Aligned requirements")
                    render_list(result.matched_requirements)
                    st.markdown("##### Transferable strengths")
                    render_list(result.transferable_strengths)
            with gap_col:
                with st.container(border=True):
                    st.subheader("Gaps to address")
                    render_list(result.missing_requirements)
                    st.markdown("##### Missing terminology")
                    render_list(result.keyword_gaps)
            with st.container(border=True):
                st.subheader("Ways to strengthen your application")
                render_list(result.recommendations)

with tailor_tab:
    st.header("Create a focused version for this role")
    st.markdown(
        '<p class="section-intro">Existing skills and achievements are prioritized according to the role. No new candidate claims are created.</p>',
        unsafe_allow_html=True,
    )
    input_col, job_col = st.columns([0.9, 1.1])
    with input_col:
        tailor_file = st.file_uploader(
            "Choose your resume", type=["pdf", "docx", "txt"], key="tailor_file"
        )
    with job_col:
        tailor_job = st.text_area(
            "Target job description",
            height=225,
            key="tailor_job",
            placeholder="Paste the complete job description here...",
        )
    tailor_text = read_resume(tailor_file)

    if tailor_text and tailor_job.strip():
        tailor_key = fingerprint(tailor_file, tailor_job)
        if st.button("Build focused resume", type="primary", key="tailor_button", use_container_width=True):
            if len(tailor_job.strip()) < 100:
                st.error("Add a more complete job description to create a useful version.")
            else:
                try:
                    with st.spinner("Prioritizing your most relevant experience..."):
                        st.session_state.tailor_result = tailor_resume_to_job(tailor_text, tailor_job.strip())
                        st.session_state.tailor_key = tailor_key
                except Exception as error:
                    st.error(friendly_error(error))

        result = st.session_state.get("tailor_result")
        if result and st.session_state.get("tailor_key") == tailor_key:
            st.divider()
            st.success("Your focused resume is ready to review.")
            st.subheader("Review changes")
            st.caption("Red shows moved content from the original position. Green shows its new position.")
            st.markdown(
                build_comparison_html(tailor_text, result.updated_resume),
                unsafe_allow_html=True,
            )
            with st.container(border=True):
                st.subheader("Update summary")
                render_list(result.change_summary)
                st.caption(result.preserved_facts_confirmation)

            st.subheader("Download your resume")
            docx_col, txt_col = st.columns(2)
            with docx_col:
                st.download_button(
                    "Download DOCX",
                    data=create_resume_docx(result.updated_resume),
                    file_name="focused_resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            with txt_col:
                st.download_button(
                    "Download TXT",
                    data=result.updated_resume,
                    file_name="focused_resume.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

st.markdown("---")
st.caption(
    "ResumeIQ provides document guidance, not hiring decisions. Review all results for accuracy before use."
)
