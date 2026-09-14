"""Semantic-ish text similarity between a resume and a job description.

Uses scikit-learn's TF-IDF vectorizer (unigrams + bigrams) and cosine
similarity so resumes that are topically aligned with a job score well
even when they don't share exact skill keywords. Falls back to a plain
term-frequency cosine similarity if scikit-learn isn't installed, so the
matching engine still works in a minimal environment.
"""

from __future__ import annotations

import re
from collections import Counter

_TOKEN_RE = re.compile(r"[a-z0-9+.#]+")

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "for", "to", "of", "in", "on",
    "at", "by", "with", "from", "as", "is", "are", "was", "were", "be", "been", "being", "this",
    "that", "these", "those", "it", "its", "we", "you", "your", "our", "their", "they", "he",
    "she", "his", "her", "i", "me", "my", "us", "them", "will", "would", "shall", "should",
    "can", "could", "may", "might", "must", "have", "has", "had", "do", "does", "did", "not",
    "no", "so", "up", "down", "out", "about", "into", "over", "after", "before", "between",
    "through", "during", "above", "below", "again", "further", "once", "here", "there", "all",
    "any", "both", "each", "few", "more", "most", "other", "some", "such", "only", "own",
    "same", "than", "too", "very", "just", "per", "etc", "including", "include", "includes",
    "across", "within", "without", "looking", "experience", "years", "year", "work", "working",
    "role", "job", "team", "company",
}


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    tokens = _TOKEN_RE.findall(text.lower())
    return [tok for tok in tokens if len(tok) > 1 and tok not in STOPWORDS]


def _tf_cosine_similarity(text_a: str, text_b: str) -> float:
    freq_a = Counter(tokenize(text_a))
    freq_b = Counter(tokenize(text_b))
    if not freq_a or not freq_b:
        return 0.0
    vocab = set(freq_a) | set(freq_b)
    dot = sum(freq_a.get(t, 0) * freq_b.get(t, 0) for t in vocab)
    norm_a = sum(v * v for v in freq_a.values()) ** 0.5
    norm_b = sum(v * v for v in freq_b.values()) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def tfidf_cosine_similarity(text_a: str, text_b: str) -> float:
    """Cosine similarity between the TF-IDF vectors of two documents.

    TF-IDF (rather than raw term frequency) automatically downweights
    common filler words and upweights terms that are distinctive to one
    of the two documents, which is a better proxy for topical relevance.
    """
    if not text_a or not text_b:
        return 0.0
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(
            tokenizer=tokenize,
            preprocessor=lambda x: x,
            token_pattern=None,
            ngram_range=(1, 2),
        )
        matrix = vectorizer.fit_transform([text_a, text_b])
        if matrix.shape[1] == 0:
            return 0.0
        return float(cosine_similarity(matrix[0], matrix[1])[0][0])
    except ImportError:
        return _tf_cosine_similarity(text_a, text_b)
