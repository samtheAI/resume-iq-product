"""Deterministically target a resume without inventing or rewriting facts."""

import re


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "our", "that", "the", "their", "this",
    "to", "we", "will", "with", "you", "your", "candidate", "role", "work",
}


def _keywords(text: str) -> set[str]:
    """Return useful lowercase words for simple relevance scoring."""

    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]*", text.lower())
    return {word for word in words if len(word) > 2 and word not in STOP_WORDS}


def _relevance(text: str, job_keywords: set[str]) -> int:
    """Count how many job-description keywords occur in an existing line."""

    return len(_keywords(text) & job_keywords)


def _is_bullet(line: str) -> bool:
    return line.lstrip().startswith(("- ", "• ", "* "))


def _prioritize_comma_list(line: str, job_keywords: set[str]) -> str:
    """Reorder existing comma-separated skills without adding new ones."""

    prefix = ""
    value = line
    if ":" in line:
        possible_prefix, possible_value = line.split(":", 1)
        if len(possible_prefix) < 30:
            prefix = possible_prefix + ":"
            value = possible_value

    items = [item.strip() for item in value.split(",") if item.strip()]
    if len(items) < 2:
        return line
    ranked = sorted(
        enumerate(items),
        key=lambda pair: (-_relevance(pair[1], job_keywords), pair[0]),
    )
    ordered = ", ".join(item for _, item in ranked)
    return f"{prefix} {ordered}".strip()


def build_targeted_resume(resume_text: str, job_description: str) -> tuple[str, list[str]]:
    """Reassemble existing resume content according to job relevance.

    The function never creates or rewrites candidate claims. It only reorders
    existing bullet points and comma-separated skills within their own sections.
    """

    job_keywords = _keywords(job_description)
    lines = resume_text.splitlines()
    output: list[str] = []
    bullets_reordered = False
    skills_reordered = False
    index = 0
    current_heading = ""

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped and len(stripped) <= 45 and (
            stripped.isupper() or stripped.endswith(":")
        ):
            current_heading = stripped.rstrip(":").upper()

        if _is_bullet(line):
            block: list[str] = []
            while index < len(lines) and _is_bullet(lines[index]):
                block.append(lines[index])
                index += 1
            ranked = sorted(
                enumerate(block),
                key=lambda pair: (-_relevance(pair[1], job_keywords), pair[0]),
            )
            reordered = [item for _, item in ranked]
            bullets_reordered = bullets_reordered or reordered != block
            output.extend(reordered)
            continue

        if "SKILL" in current_heading and "," in line:
            prioritized = _prioritize_comma_list(line, job_keywords)
            skills_reordered = skills_reordered or prioritized != line
            output.append(prioritized)
        else:
            output.append(line)
        index += 1

    changes: list[str] = []
    if bullets_reordered:
        changes.append(
            "Reordered existing bullet points within their original sections so "
            "job-relevant evidence appears first."
        )
    if skills_reordered:
        changes.append(
            "Reordered existing skills so those mentioned in the job description "
            "appear earlier."
        )
    if not changes:
        changes.append(
            "The existing order was retained because no safer relevance-based "
            "reordering was needed."
        )
    return "\n".join(output).strip(), changes
