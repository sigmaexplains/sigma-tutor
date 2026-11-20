"""What the student already knows, as prompt text, so the tutor builds only on ideas they've met."""

from collections.abc import Sequence

from sigma_tutor.types import ConceptProgress

MASTERED = "Mastered (passed the quiz)"
STUDIED = "Studied (read the lesson)"
SKIPPED = "Earlier in the course, not studied yet"
LIMIT = 30


def describe_learner(concepts: Sequence[ConceptProgress], current_slug: str | None) -> str:
    """concepts: the course's concepts in teaching order with this student's progress. Titles only, no personal data.

    On a concept page, everything before it counts as met (with its progress) and everything after it as not taught yet.
    On the course home page (no current concept), everything up to the furthest concept they've started counts as met."""
    if not concepts:
        return ""
    at = next((i for i, c in enumerate(concepts) if c.slug == current_slug), None)
    on_concept = at is not None
    if at is None:
        at = max((i for i, c in enumerate(concepts) if c.mastery > 0), default=-1) + 1
    groups: dict[str, list[str]] = {MASTERED: [], STUDIED: [], SKIPPED: []}
    for c in concepts[:at]:
        groups[MASTERED if c.mastery >= 2 else STUDIED if c.mastery == 1 else SKIPPED].append(c.title)
    lines = [f"- {k}: {', '.join(v[-LIMIT:])}" for k, v in groups.items() if v]
    if on_concept:
        lines.append(f"- Working on now: {concepts[at].title}")
        later = concepts[at + 1:]
    else:
        later = concepts[at:]
    if later:
        lines.append(f"- Later in the course (not taught yet): {', '.join(c.title for c in later[:LIMIT])}")
    if not any(groups.values()):
        lines.insert(0, "- This is the start of the course for them.")
    return "\n\nWHAT THE STUDENT KNOWS (from their progress in this course)\n" + "\n".join(lines)
