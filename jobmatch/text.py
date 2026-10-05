"""Text cleaning shared by training and inference.

The same `prepare` function must be used on training resumes and on new
resumes at prediction time, otherwise the models see differently formatted
text and accuracy drops.
"""

import re

_URL = re.compile(r"(https?://|www\.)\S+", re.IGNORECASE)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
_NON_TEXT = re.compile(r"[^a-z0-9+#.\s]")
_SPACES = re.compile(r"\s+")

HEADLINE_WORDS = 8
HEADLINE_REPEAT = 3


def scrub_personal_info(text: str) -> str:
    """Remove URLs, email addresses and phone numbers."""
    text = _URL.sub(" ", text)
    text = _EMAIL.sub(" ", text)
    return _PHONE.sub(" ", text)


def clean_text(text: str) -> str:
    """Lowercase, drop personal info and symbols, collapse whitespace."""
    if not isinstance(text, str):
        return ""
    text = scrub_personal_info(text).lower()
    text = _NON_TEXT.sub(" ", text)
    # Drop dots that are not inside a token (keeps "node.js", "asp.net").
    text = re.sub(r"(?<![a-z0-9])\.|\.(?![a-z0-9])", " ", text)
    return _SPACES.sub(" ", text).strip()


def emphasize_headline(text: str, words: int = HEADLINE_WORDS, repeat: int = HEADLINE_REPEAT) -> str:
    """Repeat the first few words (the resume headline / job title).

    A resume usually opens with the person's current title ("HR MANAGER",
    "STAFF ACCOUNTANT"). Repeating it gives those words more weight in the
    bag-of-words and sequence models. In experiments this raised linear-SVM
    accuracy from about 68% to 74%.
    """
    tokens = text.split()
    headline = " ".join(tokens[:words])
    return f"{(headline + ' ') * repeat}{text}".strip()


def prepare(text: str) -> str:
    """Full preprocessing pipeline used before every model."""
    return emphasize_headline(clean_text(text))
