import pytest

from sigma_tutor import QuizItem, fallback_reply, leak_reason, match_quiz_item, protection_note
from sigma_tutor.leak_guard import normalize, quiz_items

# Real items from the Statistics 101 course.
MEAN = QuizItem("q-mean", "What is the mean of 3, 5 and 10?", ("5", "18", "6"), 2,
                "The sum is 3 + 5 + 10 = 18. Divide by the 3 values: 18 ÷ 3 = 6.", "the-basics")
CENTRES = QuizItem("q-centres", "For 2, 4, 6, 8, 10, what are the mean and the median?",
                   ("Mean 6, median 8", "Mean 5, median 6", "Mean 6, median 6"), 2,
                   "The sum is 30, and 30 ÷ 5 = 6. The middle value of the sorted list is also 6.", "mean-vs-median")
SAMPLE = QuizItem("q-sample", "She asks 20 of the 800 students in Little Pascal. Which statement is right?",
                  ("The 800 students are the sample", "n = 800 and N = 20",
                   "The 20 students are the sample and the 800 are the population"), 2, "", "the-basics")
CONTINUOUS = QuizItem("q-cont", "Which of these is a continuous variable?",
                      ("Number of siblings", "Favourite flavour", "Time spent on homework"), 2, "", "the-basics")
CAFE = QuizItem("q-cafe", "A café records each customer's favourite drink: tea, coffee, cocoa. Which center can you use?",
                ("Mode only", "Mean only", "Median only"), 0, "", "mean-vs-median")
ITEMS = [MEAN, CENTRES, SAMPLE, CONTINUOUS, CAFE]


@pytest.mark.parametrize("message,expected", [
    ("What is the mean of 3, 5 and 10?", MEAN),                       # pasted
    ("mean of 3 5 10??", MEAN),                                       # paraphrased with the same numbers
    ("can u tell me the mean & median for 2,4,6,8,10", CENTRES),
    ("Which of these is a continuous variable?", CONTINUOUS),
    ("cafe records favourite drink tea coffee cocoa which center can i use", CAFE),
    ("what is mean?", None),                                          # a concept question, not the quiz
    ("What is the mean of 4, 8 and 9?", None),                        # different numbers: a practice problem
    ("why do we divide by n - 1 for a sample?", None),
])
def test_match(message, expected):
    assert match_quiz_item(message, ITEMS) == expected


def test_match_uses_the_previous_message():
    assert match_quiz_item("help pls", ITEMS, previous="What is the mean of 3, 5 and 10?") == MEAN


@pytest.mark.parametrize("reply,leaks", [
    ("The mean is 6.", True),
    ("Add them: 18. Then 18 ÷ 3 = 6.", True),
    ("So the answer is option C.", True),
    ("It comes to about 6", True),
    ("What do you get when you add 3 + 5 + 10? Then think about how many values there are.", False),
    ("Start with the sum. What is 3 + 5 + 10?", False),
    ("Remember: mean = sum ÷ count. How many values are there?", False),
])
def test_numeric_leaks(reply, leaks):
    assert (leak_reason(reply, MEAN) is not None) == leaks


def test_text_option_leaks():
    assert leak_reason("The 20 students are the sample and the 800 are the population.", SAMPLE)
    assert leak_reason("Which group did she actually ask? That's the sample.", SAMPLE) is None
    assert leak_reason("The answer is mode only, because you can't add drinks.", CAFE)
    assert leak_reason("Can you add or sort tea and cocoa? What could you still count?", CAFE) is None


def test_full_solution_moves_count_as_leaks():
    assert leak_reason("Let's go through it.", MEAN, move="solution") == "gave the full solution"
    assert leak_reason("Let's go through it.", MEAN, hint_level=4) == "gave the full solution"
    assert leak_reason("What's the first step?", MEAN, move="ask_attempt", hint_level=0) is None


def test_notes_and_fallback_never_contain_the_answer():
    note = protection_note(MEAN)
    assert MEAN.prompt in note and "Never state" in note
    assert leak_reason(note.replace(MEAN.prompt, ""), MEAN) is None
    assert leak_reason(fallback_reply(MEAN), MEAN) is None


def test_normalize_unifies_maths():
    assert normalize("18 ÷ 3 = 6") == normalize("18/3=6") == "18/3=6"
    assert normalize("12 − 3 = 9") == "12-3=9"


def test_quiz_items_from_rows():
    [item] = quiz_items([{"id": 1, "prompt": "P?", "options": ["a", "b"], "correct_index": 1, "explanation": None}])
    assert item.correct == "b" and item.id == "1" and item.explanation == ""
