from sigma_tutor import (MOVES, SOCRATIC_JSON, SOCRATIC_RULES, ConceptProgress, clamp_hint_level, describe_learner,
                         valid_move)

COURSE = [ConceptProgress("alpha", "Alpha", 2), ConceptProgress("beta", "Beta", 1), ConceptProgress("gamma", "Gamma", 0),
          ConceptProgress("delta", "Delta", 0)]


def test_rules_and_schema():
    assert "do NOT give the final answer" in SOCRATIC_RULES
    assert all(m in SOCRATIC_JSON for m in MOVES) and "4 the full solution" in SOCRATIC_JSON


def test_move_and_hint_level_are_cleaned():
    assert valid_move("hint") == "hint" and valid_move("dance") is None and valid_move(None) is None
    assert clamp_hint_level(9) == 4 and clamp_hint_level(-1) == 0 and clamp_hint_level(None) is None


def test_on_a_concept_page():
    text = describe_learner(COURSE, "gamma")
    assert "- Mastered (passed the quiz): Alpha" in text
    assert "- Studied (read the lesson): Beta" in text
    assert "- Working on now: Gamma" in text
    assert "- Later in the course (not taught yet): Delta" in text


def test_skipped_concepts_and_the_home_page():
    text = describe_learner([ConceptProgress("a", "A"), ConceptProgress("b", "B", 2), ConceptProgress("c", "C")], "c")
    assert "- Earlier in the course, not studied yet: A" in text and "Mastered (passed the quiz): B" in text
    home = describe_learner(COURSE, None)                   # met = up to the furthest started concept (Beta)
    assert "Alpha" in home and "- Later in the course (not taught yet): Gamma, Delta" in home


def test_new_student_and_empty_course():
    text = describe_learner([ConceptProgress("a", "A"), ConceptProgress("b", "B")], None)
    assert "start of the course" in text and "Later in the course (not taught yet): A, B" in text
    assert describe_learner([], "a") == ""
