# sigma-tutor

The teaching logic behind **Ask Sigma**, the STEM tutor on [Sigma Explains](https://sigmaexplains.com). It's built so
students learn to solve problems on their own instead of copying answers from AI.

It's pure Python with no dependencies: data goes in, prompt text and decisions come out. There's no database, network
or web framework, so the same code runs in the live tutor, in training and evaluation, and in any app that uses
Sigma's tutor model.

## What's inside

| Module | What it does |
|---|---|
| `pedagogy` | The Socratic rules: ask before telling, a hint ladder (question → rule → set-up → worked example), no full solutions before real attempts. Also the teaching moves (`hint`, `spot_mistake`, `explain` …) and `hint_level` 0–4. |
| `learner` | `describe_learner()` turns a student's progress through a course into prompt text: what they've mastered, studied and skipped, what they're on now, and what hasn't been taught yet. |
| `leak_guard` | Keeps the tutor from giving away the course's quiz answers: matches a student's message to a quiz item, adds a protection note to the prompt, checks the reply, and gives a rewrite note or a safe fallback. |

## Use it

```bash
pip install "sigma-tutor @ https://github.com/sigmaexplains/sigma-tutor/archive/refs/tags/v0.1.0.tar.gz"
```

```python
from sigma_tutor import QuizItem, match_quiz_item, protection_note, leak_reason, regenerate_note, fallback_reply

items = [QuizItem("q1", "What is the mean of 3, 5 and 10?", ("5", "18", "6"), 2)]

item = match_quiz_item("mean of 3 5 10??", items)          # → the quiz item
system_prompt += protection_note(item)                      # before calling the model

reason = leak_reason(reply, item)                           # "stated the result" for "The mean is 6."
if reason:
    reply = call_model(system_prompt + regenerate_note(reason))
    if leak_reason(reply, item):
        reply = fallback_reply(item)
```

Skip the guard once the student has taken that quiz: grading has already shown them the answer and why.

## Develop

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/python -m pytest
```

Release by bumping `version` in `pyproject.toml` and `sigma_tutor/__init__.py`, then tagging `vX.Y.Z`. Apps pin a tag.

## Licence

Apache-2.0. Course content on Sigma is CC-BY-SA-4.0 and lives in the `sigma-course-*` repositories.
