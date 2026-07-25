# RAG Implementation Plan — Converting the `me/` Folder into Proper RAG

A step-by-step guide for converting the documents in the `me/` folder from the current
"context stuffing" approach into a real Retrieval-Augmented Generation (RAG) pipeline.

> **Honest framing:** The total content is only ~26k characters across all files. At that
> size, stuffing everything into the prompt (the current approach) genuinely works fine —
> RAG won't make the answers better here. Treat this purely as a **learning exercise** in
> the mechanics. That's the right reason to do it.

---

## The Conceptual Shift

Right now `system_prompt()` jams the *entire* summary + CV + LinkedIn into every request.
RAG replaces **"include everything"** with **"include only the few chunks relevant to *this*
question."**

Four moving parts:

1. **Chunk** the documents into smallish passages.
2. **Embed** each chunk into a vector (once, ahead of time) and store it.
3. At query time, **embed the question** and **retrieve** the nearest chunks.
4. **Inject only those chunks** into the prompt.

---

## Step 1 — Chunking

There's a lucky break here: `me/sources_Andras_Nemes.txt` already has natural section
boundaries (`-------`). That's a ready-made chunking scheme — each section (summary, elevator
pitch, leadership style, key achievements, ama, Flexera intro, contact) becomes one chunk.

```python
with open("me/sources_Andras_Nemes.txt", encoding="utf-8") as f:
    raw = f.read()
chunks = [c.strip() for c in raw.split("-------") if c.strip()]
```

For the PDFs (CV, LinkedIn), there's no delimiter, so use a generic splitter — fixed-size
windows with overlap so a sentence isn't cut mid-thought:

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
cv_chunks = splitter.split_text(self.read_pdf("me/Andras_Nemes_CV_2026.pdf"))
```

**The two parameters that matter:**

- **`chunk_size`** — too big → you retrieve irrelevant filler; too small → you lose context.
- **`chunk_overlap`** — so facts straddling a boundary survive.

500–1000 chars with ~15% overlap is a sane starting point.

---

## Step 2 — Embed + Store

Turn each chunk into a vector and put it in a vector store. Two common choices:

### Option A — Chroma (a real vector DB, persists to disk)

```python
import chromadb
from openai import OpenAI

client = OpenAI()
def embed(texts):
    resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]

db = chromadb.PersistentClient(path="me/vectorstore")
col = db.get_or_create_collection("andras")
col.add(ids=[f"c{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=embed(chunks))
```

### Option B — No database at all (instructive)

This demystifies what a vector DB *does*: store the vectors in a NumPy array and do cosine
similarity by hand. For ~30 chunks this is genuinely all a vector DB is doing under the hood:

```python
import numpy as np
vectors = np.array(embed(chunks))          # shape: (n_chunks, 1536)
# retrieval = dot product after normalizing
```

> **Recommendation:** Do **Option B first** as the exercise — it makes RAG click — then swap
> in Chroma to see what the library buys you (persistence, scaling, metadata filtering).

This whole step runs **once** (or whenever the `me/` files change), **not** on every chat.

---

## Step 3 — Retrieve at Query Time

```python
def retrieve(self, question, k=3):
    qvec = embed([question])[0]
    # Chroma:
    res = self.col.query(query_embeddings=[qvec], n_results=k)
    return res["documents"][0]
    # or NumPy: normalize, dot-product against `vectors`, argsort top-k
```

**`k`** (how many chunks to pull) is the third knob. Start with 3–5.

---

## Step 4 — Wire It Into the `Me` Class

This is the satisfying part — it's a small change to the existing code:

- In `__init__`: build (or load) the vector store instead of reading whole files into
  `self.summary` / `self.cv` / `self.linkedin`.
- Change `system_prompt()` into `system_prompt(self, message)` so it can take the user's
  question, retrieve, and inject *only* the matched chunks:

```python
def system_prompt(self, message):
    context = "\n\n---\n\n".join(self.retrieve(message))
    prompt = f"You are acting as {self.name}... "
    prompt += f"\n\n## Relevant context:\n{context}\n\n"
    return prompt
```

- In `chat()`: `self.run_with_tools(self.system_prompt(message), message, history)`.

> **Note:** This also means the **evaluator** should retrieve the same way, or just receive
> the same retrieved context, so the judge sees what the agent saw.

---

## Gotchas Worth Anticipating

- **Build vs query separation** — don't re-embed the whole corpus on every message (slow +
  costs money). Embed once, persist, load. The classic beginner bug is putting `col.add(...)`
  inside `chat()`.
- **Retrieval can miss** — if someone asks "What car do you drive?", retrieval returns the
  *closest* chunks even though none are relevant. So keep the "if you don't know, call
  `record_unknown_question`" instruction — RAG doesn't replace it.
- **Small-corpus caveat** — with only ~30 chunks, top-k retrieval might pull most of the
  content anyway, so you may not *see* a quality difference. That's expected; the value shows
  up at hundreds/thousands of chunks.
- **Embedding model** — `text-embedding-3-small` is cheap and plenty for this. The OpenAI key
  is already configured.

---

## Suggested Exercise Path

1. **Start in a notebook**, not `app.py` — chunk `sources_Andras_Nemes.txt` by `-------`,
   embed, and do top-k retrieval by hand with NumPy. Print the retrieved chunks for a few
   questions to build intuition.
2. Swap NumPy for **Chroma** with persistence.
3. Add the **PDFs** with a real text splitter.
4. Finally, fold it into a **copy of `app.py`** (e.g. `app_rag.py`) so the working app stays
   intact — same pattern as keeping `app_original.py`.

---

## Quick Reference — The Three Tuning Knobs

| Knob | Where | Starting value | Effect |
|------|-------|----------------|--------|
| `chunk_size` | text splitter | 500–1000 chars | Granularity of retrieved passages |
| `chunk_overlap` | text splitter | ~15% of chunk_size | Prevents facts being cut at boundaries |
| `k` | retrieval | 3–5 | How many chunks injected into the prompt |
