"""
Knowledge Graph builder and query engine.
Uses NetworkX for graph storage and an LLM for triple extraction.
No external database required.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv(override=True)

try:
    import networkx as nx
    NX_AVAILABLE = True
except ImportError:
    NX_AVAILABLE = False
    print("networkx not installed — run: pip install networkx")

client = OpenAI()


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class Triple(BaseModel):
    subject: str
    predicate: str
    obj: str          # 'object' is a Python builtin, use 'obj'
    confidence: float = 1.0

class TripleList(BaseModel):
    triples: list[Triple]


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

EXTRACT_PROMPT = """Extract all factual relationships from the text as (subject, predicate, object) triples.

Rules:
- Subject and object should be specific named entities (people, organisations, places, products)
- Predicate should be a concise verb phrase ('works_at', 'acquired', 'founded', 'located_in')
- Use underscore_case for predicates
- Only include facts explicitly stated in the text
- Assign confidence 0.0–1.0 based on how clearly the text states the fact

Text:
{text}"""


def extract_triples(text: str) -> list[Triple]:
    """Extract knowledge graph triples from text using an LLM."""
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You extract structured knowledge from text. Be precise."},
            {"role": "user", "content": EXTRACT_PROMPT.format(text=text)},
        ],
        response_format=TripleList,
    )
    return response.choices[0].message.parsed.triples


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

class KnowledgeGraph:
    """In-memory directed knowledge graph backed by NetworkX."""

    def __init__(self):
        if not NX_AVAILABLE:
            raise ImportError("networkx required: pip install networkx")
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self.triple_count = 0

    def add_triple(self, triple: Triple):
        self.graph.add_edge(
            triple.subject,
            triple.obj,
            predicate=triple.predicate,
            confidence=triple.confidence,
        )
        self.triple_count += 1

    def add_triples(self, triples: list[Triple]):
        for t in triples:
            self.add_triple(t)

    def add_text(self, text: str) -> list[Triple]:
        """Extract triples from text and add to graph."""
        triples = extract_triples(text)
        self.add_triples(triples)
        return triples

    def neighbors(self, entity: str, direction: str = "out") -> list[dict]:
        """Return entities connected to `entity`.
        direction='out': entities this entity points to
        direction='in':  entities that point to this entity
        direction='both': both
        """
        results = []
        if direction in ("out", "both"):
            for _, target, data in self.graph.out_edges(entity, data=True):
                results.append({"entity": target, "predicate": data["predicate"], "direction": "→"})
        if direction in ("in", "both"):
            for source, _, data in self.graph.in_edges(entity, data=True):
                results.append({"entity": source, "predicate": data["predicate"], "direction": "←"})
        return results

    def shortest_path(self, source: str, target: str) -> Optional[list[str]]:
        """Find shortest path between two entities."""
        try:
            return nx.shortest_path(self.graph, source, target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def find_by_predicate(self, predicate: str) -> list[tuple[str, str]]:
        """Return all (subject, object) pairs with the given predicate."""
        results = []
        for s, o, data in self.graph.edges(data=True):
            if data.get("predicate") == predicate:
                results.append((s, o))
        return results

    def multi_hop_query(self, start: str, hops: list[str]) -> list[str]:
        """
        Traverse the graph following a chain of predicates.
        Example: multi_hop_query('Alice', ['works_at', 'located_in'])
        → Find where Alice works, then find where that company is located.
        """
        current_entities = {start}
        for predicate in hops:
            next_entities = set()
            for entity in current_entities:
                for _, target, data in self.graph.out_edges(entity, data=True):
                    if data.get("predicate") == predicate:
                        next_entities.add(target)
            current_entities = next_entities
            if not current_entities:
                break
        return list(current_entities)

    def answer_question(self, question: str) -> str:
        """Use LLM to answer a question by providing the relevant graph context."""
        # Dump the graph as triples for context
        triples_text = "\n".join(
            f"({s}) --[{data['predicate']}]--> ({o})"
            for s, o, data in self.graph.edges(data=True)
        )
        prompt = f"""Answer the question using ONLY the knowledge graph provided.
If the answer cannot be found in the graph, say 'Not found in graph.'

Knowledge graph:
{triples_text}

Question: {question}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        return response.choices[0].message.content

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        edges = [
            {"source": s, "target": o, "predicate": d["predicate"], "confidence": d.get("confidence", 1.0)}
            for s, o, d in self.graph.edges(data=True)
        ]
        return {"nodes": list(self.graph.nodes()), "edges": edges}

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeGraph":
        """Load from serialised dict."""
        kg = cls()
        for edge in data["edges"]:
            kg.add_triple(Triple(
                subject=edge["source"],
                predicate=edge["predicate"],
                obj=edge["target"],
                confidence=edge.get("confidence", 1.0),
            ))
        return kg

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "KnowledgeGraph":
        with open(path) as f:
            return cls.from_dict(json.load(f))

    def stats(self) -> dict:
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "predicates": len({d["predicate"] for _, _, d in self.graph.edges(data=True)}),
        }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    TEXT = """
    Elon Musk founded SpaceX in 2002 and Tesla in 2003. SpaceX is headquartered in Hawthorne, California.
    Tesla is headquartered in Austin, Texas. In 2022, Musk acquired Twitter and renamed it X.
    Gwynne Shotwell is the President of SpaceX and has worked there since 2002.
    Sam Altman is the CEO of OpenAI, which is based in San Francisco.
    Microsoft invested in OpenAI in 2019 and 2023.
    """

    print("Building knowledge graph from text...")
    kg = KnowledgeGraph()
    triples = kg.add_text(TEXT)

    print(f"\nExtracted {len(triples)} triples:")
    for t in triples:
        print(f"  ({t.subject}) --[{t.predicate}]--> ({t.obj})")

    print(f"\nGraph stats: {kg.stats()}")

    print("\nNeighbors of 'Elon Musk':")
    for n in kg.neighbors("Elon Musk"):
        print(f"  {n['direction']} [{n['predicate']}] {n['entity']}")

    print("\nMulti-hop: Where is the company SpaceX's president's employer headquartered?")
    result = kg.multi_hop_query("Gwynne Shotwell", ["works_at", "located_in"])
    print(f"  Answer: {result}")

    print("\nQ&A:")
    print(kg.answer_question("Who founded SpaceX and where is it located?"))
    print(kg.answer_question("What company did Microsoft invest in?"))
