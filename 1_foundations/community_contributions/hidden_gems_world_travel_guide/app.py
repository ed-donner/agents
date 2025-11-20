from dotenv import load_dotenv
import os
import re
import json
import glob
import math
import requests
import numpy as np
import gradio as gr


load_dotenv(override=True)

#Retrieval model
OPENAI_MODEL = "gpt-5-nano"
EMBEDDING_MODEL = "text-embedding-3-small"

# evaluation model
ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"  # maps to claude-sonnet-4-5 naming

# API endpoints and keys (no SDKs)
OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_BASE = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Countries expected in the generated knowledge base (limit: 15)
ALLOWED_COUNTRIES = {
    "Algeria", "Angola", "Kenya",
    "France", "Slovenia", "Greece",
    "Japan", "Bhutan", "India",
    "Fiji", "New Zealand", "Australia",
    "Peru", "Dominica", "United States",
}
ALLOWED_COUNTRIES_LOWER = {c.lower() for c in ALLOWED_COUNTRIES}


class VectorStore:

    def __init__(self):
        self.documents = []  # list of dicts: {id, text, metadata}
        self.vectors = None  # np.ndarray [n, d]

    def add(self, texts, metadatas):
        for text, meta in zip(texts, metadatas):
            self.documents.append({"id": len(self.documents), "text": text, "metadata": meta})

    def build(self, embed_fn):
        embeddings = embed_fn([d["text"] for d in self.documents])
        self.vectors = np.array(embeddings, dtype=np.float32)
        # normalize for cosine similarity
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True) + 1e-10
        self.vectors = self.vectors / norms

    def search(self, query, embed_fn, k=5):
        q = np.array(embed_fn([query])[0], dtype=np.float32)
        q = q / (np.linalg.norm(q) + 1e-10)
        scores = (self.vectors @ q)
        idx = np.argpartition(-scores, min(k, len(scores)-1))[:k]
        ranked = sorted(((int(i), float(scores[int(i)])) for i in idx), key=lambda t: -t[1])
        return [(self.documents[i], s) for i, s in ranked]


class HiddenGemsRAG:

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.vs = VectorStore()
        self.known_countries: set[str] = set()
        self._load_and_index()

    def infer_site_fields(self):
        # Attempt to infer available per-site metadata fields from bullet lists in the documents
        def normalize_field(raw: str):
            s = raw.strip().strip("-•*:\u2013\u2014 ")
            s = re.sub(r"^\*+|\*+$", "", s)  # trim asterisks
            s = re.sub(r"\s+", " ", s)
            s = s.replace("**", "").strip()
            # Lower for matching aliases
            low = s.lower()
            aliases = {
                "best time": "Best time to visit",
                "best time t": "Best time to visit",
                "best time to visit": "Best time to visit",
                "ideal visiting season": "Best time to visit",
                "climate and timing": "Best time to visit",
                "when to visit": "Best time to visit",
                "weather": "Weather conditions",
                "weather conditions": "Weather conditions",
                "travel tips": "Travel tips",
                "packing tips": "Travel tips",
                "packing essentials": "Travel tips",
                "eco-conscious travel": "Travel tips",
                "getting around": "Transportation access",
                "transportation basics": "Transportation access",
                "transportation access": "Transportation access",
                "transpor": "Transportation access",
                "description": "Description",
                "key features": "Key features",
                "key featu": "Key features",
                "key": "Key features",
                "unique features": "Unique features",
                "unique f": "Unique features",
                "unique features distinguishing it": "Unique features",
                "unique features distinguishing it from other sites": "Unique features",
                "unique features distinguishing it from other parks": "Unique features",
                "unique features distinguishing": "Unique features",
                "nearby lodging": "Nearby lodging",
                "booking guidelines": "Booking guidelines",
                "safety information": "Safety information",
                "safety tips": "Safety information",
                "health and safety": "Safety information",
                "safety in": "Safety information",
                "safety infor": "Safety information",
                "accessibility information": "Accessibility information",
                "accessibility infor": "Accessibility information",
                "not fully wheelchair accessible": "Accessibility information",
                "cost estimate": "Cost estimate",
                "cost est": "Cost estimate",
                "cost estim": "Cost estimate",
                "name": "Name",
                "location": "Location",
                "local language": "Local language",
                "language": "Local language",
                "local currency": "Local currency",
                "currency": "Local currency",
                "local customs": "Local customs and traditions",
                "local customs and traditions": "Local customs and traditions",
                "respect and culture": "Local customs and traditions",
                "local culture": "Local culture",
                "local cuisine": "Local cuisine",
            }
            # Map truncated variants (prefix match) to alias bucket
            for k, v in aliases.items():
                if low == k or low.startswith(k):
                    return v
            # Title case sensible defaults
            if 3 <= len(s) <= 60 and re.search(r"[A-Za-z]", s):
                return s[:1].upper() + s[1:]
            return None

        seen = {}
        for d in self.vs.documents:
            text = d.get("text", "")
            # Only capture bullets that look like a metadata key followed by a colon
            for m in re.finditer(r"^\s*[-*•]\s+([^:\n]{2,60}):\s*", text, flags=re.MULTILINE):
                key_raw = m.group(1)
                key = normalize_field(key_raw)
                if key:
                    seen[key] = seen.get(key, 0) + 1

        preferred_order = [
            "Name",
            "Location",
            "Description",
            "Key features",
            "Unique features",
            "Transportation access",
            "Best time to visit",
            "Cost estimate",
            "Accessibility information",
            "Nearby lodging",
            "Booking guidelines",
            "Safety information",
            "Travel tips",
            "Weather conditions",
            "Local customs and traditions",
            "Local cuisine",
            "Local culture",
            "Local language",
            "Local currency",
        ]

        if not seen:
            return preferred_order

        # Order by preferred list, then by frequency, then alpha
        def sort_key(item):
            k, freq = item
            pref_idx = preferred_order.index(k) if k in preferred_order else 999
            return (pref_idx, -freq, k)

        # Keep only labels that are in our preferred schema to avoid leaking values like languages/regions
        ordered = [k for k, _ in sorted(seen.items(), key=sort_key) if k in preferred_order]
        # Keep only the first occurrence and cap length
        deduped = []
        seen_set = set()
        for k in ordered:
            if k not in seen_set:
                seen_set.add(k)
                deduped.append(k)
        return deduped[:24]

    def _openai_post(self, path: str, payload: dict):
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not set")
        url = f"{OPENAI_BASE}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        r.raise_for_status()
        return r.json()

    def _read_guides(self):
        guide_dir = os.path.join(self.base_dir, "hidden_gems_output")
        paths = sorted(glob.glob(os.path.join(guide_dir, "*_guide.md")))
        contents = []
        for p in paths:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    contents.append((p, f.read()))
            except Exception:
                continue
        return contents

    def _chunk_markdown(self, md_text: str, source_path: str):
        # Split by country sections that start with ### Country
        blocks = re.split(r"\n(?=###\s+[^\n]+)", md_text)
        chunks = []
        # Capture country names using only the FIRST heading of each block
        for block in blocks:
            first_heading = re.search(r"^###\s+([^\n]+)$", block, flags=re.MULTILINE)
            if first_heading:
                raw = first_heading.group(1).strip()
                mname = re.match(r"[A-Za-z][A-Za-z\s]+", raw)
                country = mname.group(0).strip() if mname else raw
                if country and country.lower() in ALLOWED_COUNTRIES_LOWER:
                    # Normalize to canonical casing from ALLOWED_COUNTRIES
                    for ac in ALLOWED_COUNTRIES:
                        if ac.lower() == country.lower():
                            country = ac
                            break
                    self.known_countries.add(country)
            text = block.strip()
            if not text:
                continue
            # further sub-chunk long sections (~1200-1600 chars)
            for i in range(0, len(text), 1400):
                sub = text[i:i+1600]
                chunks.append({
                    "text": sub,
                    "metadata": {"source": source_path}
                })
        return chunks

    def _embed(self, texts):
        resp = self._openai_post("embeddings", {"model": EMBEDDING_MODEL, "input": texts})
        return [d["embedding"] for d in resp["data"]]

    def _load_and_index(self):
        texts, metas = [], []
        for path, content in self._read_guides():
            for ch in self._chunk_markdown(content, path):
                texts.append(ch["text"])
                metas.append(ch["metadata"])
        if not texts:
            raise RuntimeError("No guide data found to index.")
        self.vs.add(texts, metas)
        self.vs.build(self._embed)
        if not self.known_countries:
            # Fallback: show the intended list so the UI isn't blank
            self.known_countries = set(ALLOWED_COUNTRIES)

    def _compose_system(self):
        countries_list = ", ".join(sorted(self.known_countries)) if self.known_countries else "(not detected)"
        return (
            "You are a travel assistant for hidden gems around the world. "
            "Use the provided context to answer accurately and concisely. "
            "Important limitations: The dataset only covers 15 countries total, "
            "and each country contains up to 10 sites. If a question is outside these, say so. "
            f"Countries currently in the knowledge base: {countries_list}."
        )

    def retrieve(self, query: str, k: int = 5):
        results = self.vs.search(query, self._embed, k=k)
        return results

    def answer(self, query: str):
        # Attempt to detect a requested country and advise if missing
        requested_country = None
        # Simple pattern: in/for/about <Country>
        m = re.search(r"\b(?:in|for|about|on|regarding)\s+([A-Z][A-Za-z]+(?:\s[A-Z][A-Za-z]+)*)\b", query)
        if m:
            requested_country = m.group(1).strip()
        else:
            # Fallback: look for any known country mentioned
            for c in self.known_countries:
                if c.lower() in query.lower():
                    requested_country = c
                    break

        top = self.retrieve(query, k=6)
        context_blocks = []
        sources = []
        for (doc, score) in top:
            context_blocks.append(doc["text"])  # type: ignore[index]
            sources.append(doc["metadata"]["source"])  # type: ignore[index]
        context = "\n\n---\n\n".join(context_blocks)
        sys = self._compose_system()
        messages = [
            {"role": "system", "content": sys},
            {
                "role": "user",
                "content": (
                    "Answer the user's question using the CONTEXT. "
                    "If insufficient, state the limitation.\n\n"
                    f"CONTEXT:\n{context}\n\nQUESTION: {query}"
                ),
            },
        ]
        resp = self._openai_post("chat/completions", {"model": OPENAI_MODEL, "messages": messages})
        answer_text = resp["choices"][0]["message"]["content"]
        return answer_text, list(dict.fromkeys(sources))


def evaluate_with_anthropic(question: str, answer: str, history: list, sources: list[str], known_countries: list[str], requested_country: str | None):
    if not ANTHROPIC_API_KEY:
        return {"is_acceptable": True, "feedback": "Evaluator unavailable; skipping."}

    countries_csv = ", ".join(sorted(known_countries)) if known_countries else ""
    requested = requested_country or "(none detected)"
    rubric = (
        "You are an evaluator that decides whether a response is acceptable.\n"
        "Requirements for ACCEPTABLE: (1) Answer is grounded in the provided CONTEXT/SOURCES (no hallucinated facts); "
        "(2) If the requested country IS in the known list, the answer must NOT claim it is missing or not covered (flag phrases like 'not covered', 'we don't yet cover', 'will be added'); "
        "(3) If the requested country is NOT in the known list, the answer MUST politely say it's not covered yet; "
        "(4) The answer is concise and directly addresses the user's question.\n"
        f"Known countries: {countries_csv}. Requested country detected: {requested}.\n"
        "Return JSON with fields: is_acceptable (true/false) and feedback (1-3 short sentences)."
    )
    src_summary = "\n".join(sorted(set(sources))[:8]) or "(no sources)"
    convo = json.dumps(history, ensure_ascii=False)
    prompt = (
        f"Conversation so far (JSON array of messages):\n{convo}\n\n"
        f"User question: {question}\n\nAgent answer: {answer}\n\n"
        f"Available sources:\n{src_summary}\n\n"
        "Provide only the JSON object."
    )

    url = f"{ANTHROPIC_BASE}/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 300,
        "messages": [
            {"role": "system", "content": rubric},
            {"role": "user", "content": prompt},
        ],
    }
    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        r.raise_for_status()
        out = r.json()
        content_parts = out.get("content", [])
        content = "".join([p.get("text", "") for p in content_parts if isinstance(p, dict)])
        try:
            data = json.loads(content)
        except Exception:
            data = {"is_acceptable": True, "feedback": content.strip()[:800]}
        # Ensure required fields
        if "is_acceptable" not in data:
            data["is_acceptable"] = True
        if "feedback" not in data:
            data["feedback"] = ""
        return data
    except Exception as e:
        return {"is_acceptable": True, "feedback": str(e)}


def build_ui(app: HiddenGemsRAG):
    note = (
        "This assistant uses a limited dataset: only 15 countries are covered, "
        "with up to 10 sites per country."
    )

    def respond(message, history):
        # Normalize history to role/content pairs for retrieval + evaluator
        clean_history = []
        for h in history:
            if isinstance(h, dict) and "role" in h and "content" in h:
                clean_history.append({"role": h["role"], "content": h["content"]})
            elif isinstance(h, (list, tuple)) and len(h) == 2:
                clean_history.append({"role": "user", "content": h[0]})
                if h[1] is not None:
                    clean_history.append({"role": "assistant", "content": h[1]})

        # Build a retrieval query that includes recent context
        recent_context = " ".join([m["content"] for m in clean_history[-4:]]) if clean_history else ""
        search_query = (message + " " + recent_context).strip()

        # First attempt based on combined query
        answer, sources = app.answer(search_query)
        # Try to re-detect requested country from the produced answer pipeline
        req = None
        m = re.search(r"\b(?:in|for|about|on|regarding)\s+([A-Z][A-Za-z]+(?:\s[A-Z][A-Za-z]+)*)\b", message)
        if m:
            req = m.group(1).strip()
        else:
            for c in app.known_countries:
                if c.lower() in message.lower():
                    req = c
                    break
        evaluation = evaluate_with_anthropic(message, answer, clean_history, sources, list(app.known_countries), req)
        attempts = 0
        # Retry loop similar to 3_lab3: rerun with feedback context until acceptable or max attempts
        while not evaluation.get("is_acceptable", True) and attempts < 3:
            attempts += 1
            sys = app._compose_system() + (
                "\n\n## Previous answer rejected\n"
                f"Your previous answer was:\n{answer}\n\n"
                f"Reason for rejection (from evaluator):\n{evaluation.get('feedback','')}\n\n"
                "Revise your answer to address the feedback, grounded in the provided context."
            )
            # Rebuild context for consistency
            top = app.retrieve(search_query, k=6)
            context_blocks = [doc["text"] for (doc, _) in top]
            context = "\n\n---\n\n".join(context_blocks)
            messages = [
                {"role": "system", "content": sys},
                {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {message}"},
            ]
            resp = app._openai_post("chat/completions", {"model": OPENAI_MODEL, "messages": messages})
            answer = resp["choices"][0]["message"]["content"]
            evaluation = evaluate_with_anthropic(
                message,
                answer,
                clean_history,
                [d["metadata"]["source"] for (d, _) in top],
                list(app.known_countries),
                req,
            )

        return answer

    with gr.Blocks() as demo:
        countries_md = ", ".join(sorted(app.known_countries)) if app.known_countries else "(loading)"
        gr.Markdown("# Hidden Gems World Travel Guide")
        gr.Markdown(
            "This chat retrieves from locally generated guides. "
            "Model: OpenAI gpt-5-nano for answers; Evaluator: Anthropic claude-sonnet-4-5."
        )
        fields = app.infer_site_fields()
        if fields:
            # Render compact rows separated by commas (e.g., 6 per row)
            per_row = 6
            rows = []
            for i in range(0, len(fields), per_row):
                rows.append(", ".join(fields[i:i+per_row]))
            gr.Markdown("**For each site you can ask about:**\n" + "\n".join(rows))
        gr.Markdown(f"**Countries currently covered:** {countries_md}")
        gr.Markdown(note)
        chatbot = gr.Chatbot(type="messages", height=420)
        with gr.Row():
            msg = gr.Textbox(placeholder="Ask about hidden gems, e.g., 'What are unique sites in Bhutan?'", scale=4)
            send = gr.Button("Send", variant="primary")

        def on_send(user_message, history):
            history = history + [{"role": "user", "content": user_message}]
            answer = respond(user_message, history)
            history = history + [{"role": "assistant", "content": answer}]
            return history, ""

        send.click(on_send, inputs=[msg, chatbot], outputs=[chatbot, msg])
        msg.submit(on_send, inputs=[msg, chatbot], outputs=[chatbot, msg])

        return demo


if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    app = HiddenGemsRAG(base_dir)
    ui = build_ui(app)
    ui.launch()


