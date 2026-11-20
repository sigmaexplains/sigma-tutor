"""The data the teaching logic works on. Plain dataclasses, so callers can build them from any store."""

from dataclasses import dataclass


@dataclass(frozen=True)
class QuizItem:
    """One multiple-choice quiz question. `correct_index` points into `options`."""
    id: str
    prompt: str
    options: tuple[str, ...]
    correct_index: int
    explanation: str = ""
    concept_slug: str | None = None

    @property
    def correct(self) -> str:
        return self.options[self.correct_index] if 0 <= self.correct_index < len(self.options) else ""


@dataclass(frozen=True)
class ConceptProgress:
    """A concept in teaching order and how far the student got: 0 none, 1 read the lesson, 2 passed, 3 perfect."""
    slug: str
    title: str
    mastery: int = 0
