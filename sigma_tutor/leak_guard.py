"""Answer-leak guard: keep the tutor from giving away the answers to the course's own quiz questions.

The quiz files never reach the tutor's sources, but a student can paste a quiz question into the chat and a model can
simply work it out. The guard runs in three steps, all plain text matching (no model calls):

1. match_quiz_item(): is the student's message (or the last two messages together) one of the course's quiz questions?
2. protection_note(): if so, an instruction added to the prompt before the reply is written.
3. leak_reason(): does the reply still reveal the correct option or the result? Then regenerate once with
   regenerate_note(), and if it still leaks, send fallback_reply().

Callers skip the guard once the student has taken that quiz: grading already showed them the answer and why.
"""

import re
import unicodedata
from collections import Counter
from collections.abc import Iterable, Sequence

from sigma_tutor.types import QuizItem

STOP = frozenset("""a an the of and or is are was were what which who these this that those to in on for with its it be
do does did how you your if by at as from each there their they them can could use using into than then so has have
had will would should one find work out tell me my i we our please help whats""".split())

_NUM = re.compile(r"(?<![a-z\d.])\d+(?:\.\d+)?")
_WORD = re.compile(r"[a-z]+")
_RESULT = r"(?:=|≈|\bis|\bare|\bequals|\bgets?|\bgives|\bcomes to|\bbe|\bmakes)"


def normalize(text: str) -> str:
    """Lowercase, unify maths symbols and spacing so "18 ÷ 3 = 6" and "18/3=6" compare equal."""
    t = unicodedata.normalize("NFKC", text or "").lower()
    t = (t.replace("÷", "/").replace("×", "*").replace("−", "-").replace("–", "-").replace("’", "'")
         .replace("≈", " ≈ "))
    t = re.sub(r"(?<=\d),(?=\d{3}\b)", "", t)            # 1,000 → 1000
    t = re.sub(r"[^a-z0-9.%=≈/*+\-√'\s]", " ", t)
    t = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", t)             # keep decimal points only
    t = re.sub(r"\s*([=≈/*+√])\s*", r"\1", t)
    t = re.sub(r"(?<=\d)\s*-\s*(?=\d)", "-", t)
    t = t.replace("'", "")
    return re.sub(r"\s+", " ", t).strip()


def _nums(t: str) -> list[str]:
    return [n.rstrip("0").rstrip(".") if "." in n else n for n in _NUM.findall(t)]


def _words(t: str) -> set[str]:
    return {w for w in _WORD.findall(t) if w not in STOP and len(w) > 1}


def _score(item: QuizItem, text: str) -> float:
    p, t = normalize(item.prompt), normalize(text)
    if len(p) >= 20 and p in t:
        return 1.0
    pn, tn = Counter(_nums(p)), Counter(_nums(t))
    if pn - tn:                                   # every number in the quiz question must be in the message
        return 0.0
    pw, tw = _words(p), _words(t)
    shared = pw & tw
    if sum(pn.values()) >= 2:                     # numbers are the strongest signal: they plus one key word
        return 0.8 + 0.2 * len(shared) / len(pw) if shared and pw else 0.0
    if len(pw) >= 3:
        frac = len(shared) / len(pw)
        return frac if frac >= 0.6 else 0.0
    return 0.0


def match_quiz_item(question: str, items: Iterable[QuizItem], previous: str | None = None) -> QuizItem | None:
    """The quiz item the student's message is asking about, or None. `previous`: their message before this one,
    since students often paste the question first and then write "help"."""
    texts = [question] + ([f"{previous} {question}"] if previous else [])
    best, best_score = None, 0.0
    for item in items:
        s = max(_score(item, t) for t in texts)
        if s > best_score:
            best, best_score = item, s
    return best


def leak_reason(reply: str, item: QuizItem, move: str | None = None, hint_level: int | None = None) -> str | None:
    """Why the reply gives away the quiz item's answer, or None if it doesn't."""
    if move == "solution" or hint_level == 4:
        return "gave the full solution"
    r, c = normalize(reply), normalize(item.correct)
    if not c:
        return None
    letter = "abcdefghij"[item.correct_index] if item.correct_index < 10 else ""
    if re.search(rf"\b(?:option|choice)\s*(?:{letter}|{item.correct_index + 1})(?![a-z0-9])", r):
        return "named the correct option"
    words, nums = _WORD.findall(c), _nums(c)
    if len(words) >= 3 and c in r:
        return "repeated the correct option"
    if nums:
        if all(re.search(rf"{_RESULT}\s*(?:about |approximately |roughly |around )?{re.escape(n)}(?![\d.])", r)
               for n in set(nums)):
            return "stated the result"
    elif re.search(rf"(?:\banswer|\bcorrect|\bit is|\bits|\bthat is|\bthats|\bwould be|\bis|\bare)\s+(?:the |an? )?"
                   rf"{re.escape(c)}(?![a-z])", r):
        return "stated the correct option"
    steps = re.findall(r"[\d.+\-*/√()]+=[\d.]+", normalize(item.explanation))
    if steps and len(steps[-1]) >= 5 and steps[-1] in r:
        return "copied the worked solution"
    return None


def protection_note(item: QuizItem) -> str:
    """Added to the system prompt when the student asks about a quiz item they haven't taken. Never contains the answer."""
    return f"""

IMPORTANT: The student's question is from this course's quiz, and they haven't taken that quiz yet:
"{item.prompt}"
Never state, confirm or point to the correct option, and never give the final result. Guide with questions and hints
only (hint_level at most 3) and leave the last step to them. It's fine to tell them it's a quiz question."""


def regenerate_note(reason: str) -> str:
    return f"""

Your previous draft {reason} for a quiz question the student hasn't taken yet. Rewrite it as a hint or a guiding
question. Don't state, confirm or point to the correct option or the final result."""


def fallback_reply(item: QuizItem | None = None) -> str:
    """Sent when the reply still leaks after one rewrite. Never contains the answer."""
    return ("That looks like a question from your quiz, so I won't give the answer away. Let's work it out together: "
            "what do you think the first step is? Tell me what you'd try and I'll help from there.")


def quiz_items(rows: Sequence[dict]) -> list[QuizItem]:
    """Build QuizItems from rows with id, prompt, options, correct_index, explanation and optional concept_slug."""
    return [QuizItem(id=str(r["id"]), prompt=r["prompt"], options=tuple(r["options"]), correct_index=r["correct_index"],
                     explanation=r.get("explanation") or "", concept_slug=r.get("concept_slug")) for r in rows]
