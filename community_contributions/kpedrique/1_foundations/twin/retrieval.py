"""Small lexical FAQ retriever; no embeddings or external services required."""

import json
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache

from documents import read_document
STOP_WORDS = set("""a al algo and are as at be can con cual cuales como de del do does el ella en
eres es esta este for from ha has have how i in is it karina la las lo los me
mi my of on or para por que se sobre soy su tell the to tu tus un una what
when where which who with you your tienes tiene experiencia experience
""".split())


def tokenize(text):
    normalized = unicodedata.normalize("NFKD", text.casefold())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    return [word for word in re.findall(r"[a-z0-9]+", normalized)
            if len(word) > 1 and word not in STOP_WORDS]


@lru_cache(maxsize=1)
def load_faqs():
    """Only answered FAQs are facts; exclude notes and pending questions."""
    records = []
    for language in ("en", "es"):
        document = json.loads(read_document(
            f"twin_faqs_{language}.json", f"TWIN_FAQS_{language.upper()}_URL",
        ).decode("utf-8-sig"))
        for faq in document["faqs"]:
            if isinstance(faq.get("answer"), str) and faq["answer"].strip():
                records.append({
                    "id": faq["id"],
                    "language": document["language"],
                    "question": faq["question"],
                    "answer": faq["answer"],
                    "tags": faq.get("tags", []),
                })
    if not records:
        raise ValueError("No answered FAQs found in docs/twin_faqs_*.json")
    return records


def retrieve_faqs(query, history=None, limit=3):
    """Rank by weighted word overlap, keeping both translations of each hit.

    Short follow-ups also use the previous user question for topic context.
    This is lexical retrieval: paraphrases without shared words may be missed.
    """
    terms = Counter(tokenize(query))
    if len(terms) <= 2:
        previous = next((m["content"] for m in reversed(history or [])
                         if m.get("role") == "user" and isinstance(m.get("content"), str)), "")
        for term in tokenize(previous):
            terms[term] += 0.25
    if not terms or limit <= 0:
        return []

    records = load_faqs()
    documents = [Counter(tokenize(" ".join([
        faq["question"], faq["question"], " ".join(faq["tags"]), faq["answer"],
    ]))) for faq in records]
    frequency = Counter(term for document in documents for term in document)
    scores = {}
    for faq, document in zip(records, documents):
        score = sum(
            weight * (1 + math.log((1 + len(records)) / (1 + frequency[term])))
            * document[term] / (document[term] + 1)
            for term, weight in terms.items() if term in document
        ) / math.sqrt(max(1, sum(document.values())))
        if score > 0:
            scores[faq["id"]] = max(scores.get(faq["id"], 0), score)
    ids = sorted(scores, key=scores.get, reverse=True)[:limit]
    return [faq for faq_id in ids for faq in records if faq["id"] == faq_id]


def format_faqs(records):
    if not records:
        return "No matching FAQs. Do not infer missing facts."
    return "\n\n".join(
        f"FAQ {faq['id']} ({faq['language']})\n"
        f"Question: {faq['question']}\nAnswer: {faq['answer']}"
        for faq in records
    )
