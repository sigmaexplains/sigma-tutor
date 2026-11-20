"""Teaching logic for Sigma's STEM tutor.

Pure functions only: data in, decisions and prompt text out. No database, network or web framework, so the same
code runs in the live tutor (sigma-backend), in training and evaluation, and for anyone using Sigma's open model.
"""

from sigma_tutor.learner import describe_learner
from sigma_tutor.leak_guard import fallback_reply, leak_reason, match_quiz_item, protection_note, regenerate_note
from sigma_tutor.pedagogy import MOVES, SOCRATIC_JSON, SOCRATIC_RULES, clamp_hint_level, valid_move
from sigma_tutor.types import ConceptProgress, QuizItem

__version__ = "0.1.0"

__all__ = [
    "MOVES", "SOCRATIC_JSON", "SOCRATIC_RULES", "ConceptProgress", "QuizItem", "clamp_hint_level", "describe_learner",
    "fallback_reply", "leak_reason", "match_quiz_item", "protection_note", "regenerate_note", "valid_move",
]
