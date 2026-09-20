"""LangGraph workflows for resume review, matching, and tailoring."""

from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from resume_tailor import build_targeted_resume


MODEL_NAME = "openai/gpt-oss-20b"


class CandidateSnapshot(BaseModel):
    """Expected fields for the candidate-profile section."""

    profile_summary: str = Field(description="Two-sentence factual candidate summary")
    experience_level: str = Field(description="Entry, junior, mid, senior, lead, or unclear")
    likely_target_role: str = Field(description="Most likely role targeted by this resume")
    core_skills: list[str] = Field(description="Important skills explicitly present")
    strongest_evidence: list[str] = Field(description="Strong resume evidence and achievements")


class ResumeAnalysis(BaseModel):
    """Structured format returned by the resume-review workflow."""

    executive_summary: str = Field(description="Balanced overall resume assessment")
    resume_score: int = Field(ge=0, le=100, description="Resume quality score, not hiring score")
    pros: list[str] = Field(min_length=3, description="Evidence-based strengths")
    cons: list[str] = Field(min_length=3, description="Evidence-based weaknesses or gaps")
    improvement_plan: list[str] = Field(min_length=3, description="Specific prioritized improvements")
    candidate_snapshot: CandidateSnapshot


class JobMatchAnalysis(BaseModel):
    """Structured comparison between one resume and one job description."""

    match_score: int = Field(ge=0, le=100, description="Evidence-based resume-to-job match score")
    summary: str = Field(description="Balanced explanation of the score")
    matched_requirements: list[str] = Field(description="Requirements supported by resume evidence")
    missing_requirements: list[str] = Field(description="Job requirements not evidenced in the resume")
    transferable_strengths: list[str] = Field(description="Relevant transferable experience or skills")
    keyword_gaps: list[str] = Field(description="Important job terms absent from the resume")
    recommendations: list[str] = Field(description="Truthful ways to improve alignment")


class TailoredResume(BaseModel):
    """Clean targeted resume and a transparent description of its changes."""

    updated_resume: str = Field(description="Complete clean revised resume in plain text")
    change_summary: list[str] = Field(description="Important changes made and why")
    preserved_facts_confirmation: str = Field(
        description="Confirmation that no unsupported facts were introduced"
    )


class WorkflowState(TypedDict, total=False):
    """Information passed from one LangGraph node to the next."""

    resume_text: str
    job_description: str
    analysis: ResumeAnalysis
    match_analysis: JobMatchAnalysis
    tailored_resume: TailoredResume


ANALYSIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a rigorous resume-review agent. Analyze only the supplied
resume. Never invent employment, skills, education, metrics, or personal details.

Evaluate clarity, structure, relevance, evidence, quantified impact, skills,
career progression, consistency, and recruiter readability. The pros must cite
specific evidence from the resume. The cons must identify genuine weaknesses,
missing evidence, ambiguity, or presentation problems. Do not criticize a
candidate for protected characteristics or infer them. A resume score measures
document quality only and is not a hiring recommendation.

Write concise, useful feedback. Return at least three pros, three cons, and
three prioritized improvements.""",
        ),
        ("human", "Analyze this resume:\n\n{resume_text}"),
    ]
)


MATCH_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You compare a resume with a job description using only explicit
evidence. Score alignment across required skills, preferred skills, experience,
education, responsibilities, domain knowledge, and relevant terminology.

Do not infer protected characteristics. Do not claim the candidate has a skill
that is absent from the resume. Missing evidence is not proof that a candidate
cannot do something; describe it as not evidenced. Explain the score clearly and
give truthful recommendations. This is a document match, not a hiring decision.""",
        ),
        (
            "human",
            "Resume:\n{resume_text}\n\nJob description:\n{job_description}",
        ),
    ]
)


def _structured_model(schema: type[BaseModel], method: str = "json_schema"):
    """Create a deterministic Groq model using the requested output method."""

    llm = ChatGroq(model=MODEL_NAME, temperature=0, max_tokens=4_000)
    return llm.with_structured_output(schema, method=method)


def _analyze_node(state: WorkflowState) -> WorkflowState:
    analysis = (ANALYSIS_PROMPT | _structured_model(ResumeAnalysis)).invoke(
        {"resume_text": state["resume_text"]}
    )
    return {"analysis": analysis}


def _validate_analysis_node(state: WorkflowState) -> WorkflowState:
    analysis = state["analysis"]
    if not analysis.pros or not analysis.cons:
        raise ValueError("The model returned an incomplete resume analysis.")
    return state


def _match_node(state: WorkflowState) -> WorkflowState:
    result = (MATCH_PROMPT | _structured_model(JobMatchAnalysis)).invoke(
        {
            "resume_text": state["resume_text"],
            "job_description": state["job_description"],
        }
    )
    return {"match_analysis": result}


def _validate_match_node(state: WorkflowState) -> WorkflowState:
    result = state["match_analysis"]
    if not result.matched_requirements and not result.missing_requirements:
        raise ValueError("The model returned an incomplete job-match analysis.")
    return state


def _tailor_node(state: WorkflowState) -> WorkflowState:
    updated_resume, changes = build_targeted_resume(
        state["resume_text"], state["job_description"]
    )
    result = TailoredResume(
        updated_resume=updated_resume,
        change_summary=changes,
        preserved_facts_confirmation=(
            "The updated version contains only original resume text. Python code "
            "reordered existing content; no AI-generated claims were added."
        ),
    )
    return {"tailored_resume": result}


def _validate_tailor_node(state: WorkflowState) -> WorkflowState:
    result = state["tailored_resume"]
    if len(result.updated_resume.strip()) < 100:
        raise ValueError("The model returned an incomplete updated resume.")
    return state


def _build_graph(first_node: str, first_function, validation_node: str, validation_function):
    """Build the shared two-node LangGraph pattern used by all three features."""

    graph = StateGraph(WorkflowState)
    graph.add_node(first_node, first_function)
    graph.add_node(validation_node, validation_function)
    graph.add_edge(START, first_node)
    graph.add_edge(first_node, validation_node)
    graph.add_edge(validation_node, END)
    return graph.compile()


resume_graph = _build_graph(
    "analyze_resume", _analyze_node, "validate_analysis", _validate_analysis_node
)
match_graph = _build_graph(
    "match_resume", _match_node, "validate_match", _validate_match_node
)
tailor_graph = _build_graph(
    "tailor_resume", _tailor_node, "validate_tailored_resume", _validate_tailor_node
)


def analyze_resume(resume_text: str) -> ResumeAnalysis:
    """Run the standalone resume-review workflow."""

    return resume_graph.invoke({"resume_text": resume_text})["analysis"]


def match_resume_to_job(resume_text: str, job_description: str) -> JobMatchAnalysis:
    """Run the resume-to-job matching workflow."""

    return match_graph.invoke(
        {"resume_text": resume_text, "job_description": job_description}
    )["match_analysis"]


def tailor_resume_to_job(resume_text: str, job_description: str) -> TailoredResume:
    """Run the evidence-preserving resume-tailoring workflow."""

    return tailor_graph.invoke(
        {"resume_text": resume_text, "job_description": job_description}
    )["tailored_resume"]
