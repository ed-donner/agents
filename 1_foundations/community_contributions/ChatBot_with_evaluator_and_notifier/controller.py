import os
import re
from typing import List, Tuple, Set
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from rag import get_retriever, ingest as ingest_docs
from evaluator import GeminiEvaluator
from tools import notify

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
DISCLAIMER = "This info does not exist in our DB, but according to your input this is your output: "

# --- Cursor Implementation Prompt: Minimal LLM and Evaluator functions ---

def LLM(user_input, db_retrieved, history):
    """
    Builds a comprehensive prompt using user input, retrieved context, and chat history,
    then calls the OpenAI chat model (via LangChain ChatOpenAI) to generate a response.
    """
    load_dotenv(override=True)
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model, temperature=0.2)

    context_text = "\n\n".join(db_retrieved if isinstance(db_retrieved, list) else [str(db_retrieved)])
    history_text = str(history or [])
    system = (
        "Answer using ONLY the provided DB retrieval and keep consistency with the chat history. "
        "If the retrieval does not contain the answer, reply: I am unsure."
    )
    user = (
        f"This is the user input: {user_input}\n\n"
        f"This is the db_retrieval: {context_text}\n\n"
        f"This is the history of chat: {history_text}\n\n"
        "Based on these, generate a comprehensive response that answers the user's question using the retrieved context and maintaining consistency with chat history."
    )
    reply = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)]).content
    return reply.strip() if reply else ""


def _token_set(text: str) -> set:
    t = (text or "").lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return {w for w in t.split() if w}


def Evaluator(user_input, db_retrieved, llm_response, history):
    """
    Simple, deterministic evaluator returning metric scores and a pass/fail decision.
    Uses lexical overlap heuristics; values are in [0,1].
    """
    db_text = "\n\n".join(db_retrieved if isinstance(db_retrieved, list) else [str(db_retrieved)])
    q_set = _token_set(user_input)
    db_set = _token_set(db_text)
    r_set = _token_set(llm_response)
    h_text = str(history or [])
    h_set = _token_set(h_text)

    def jaccard(a: set, b: set) -> float:
        if not a or not b:
            return 0.0
        inter = len(a & b)
        union = len(a | b)
        return inter / union if union else 0.0

    relevance = jaccard(q_set, r_set)
    accuracy = jaccard(db_set, r_set)
    consistency = 1.0 if jaccard(h_set, r_set) >= 0.1 or not h_set else jaccard(h_set, r_set)
    completeness = min(1.0, (len(llm_response) / 300.0)) if accuracy >= 0.2 else 0.3
    faithfulness = accuracy

    overall = max(0.0, min(1.0, 0.3 * relevance + 0.3 * accuracy + 0.15 * completeness + 0.15 * consistency + 0.1 * faithfulness))
    passed = overall >= 0.7

    feedback_parts = []
    if relevance < 0.5:
        feedback_parts.append("Improve focus on the user's question.")
    if accuracy < 0.5:
        feedback_parts.append("Cite or use details from the retrieved context more precisely.")
    if completeness < 0.7:
        feedback_parts.append("Add missing details supported by context.")
    if consistency < 0.6:
        feedback_parts.append("Ensure alignment with prior conversation.")
    if faithfulness < 0.7:
        feedback_parts.append("Avoid claims not supported by retrieved context.")
    if not feedback_parts:
        feedback_parts.append("Good response: relevant, accurate, and grounded.")

    return {
        "relevance": round(relevance, 3),
        "accuracy": round(accuracy, 3),
        "completeness": round(completeness, 3),
        "consistency": round(consistency, 3),
        "faithfulness": round(faithfulness, 3),
        "overall": round(overall, 3),
        "passed": passed,
        "feedback": " ".join(feedback_parts),
    }

class ChatbotController:
    def __init__(self):
        load_dotenv(override=True)
        self.llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.2)
        self.evaluator = GeminiEvaluator()
        self._smalltalk_patterns = [
            (re.compile(r"^(hi|hello|hey|yo)\b", re.I), "Hello! How can I help today?"),
            (re.compile(r"how\s+are\s+you\b", re.I), "I'm doing well, thanks for asking. How can I help?"),
            (re.compile(r"(good\s+(morning|afternoon|evening))\b", re.I), "Hello! How can I help?"),
            (re.compile(r"\b(thank(s)?|thanks a lot|ty)\b", re.I), "You're welcome!"),
            (re.compile(r"\b(bye|goodbye|see\s+you)\b", re.I), "Goodbye!"),
            (re.compile(r"tell\s+me\s+a\s+joke", re.I), "Why did the developer go broke? Because they used up all their cache."),
            (re.compile(r"\b(help|what\s+can\s+you\s+do)\b", re.I), "I can answer questions based on our knowledge base or just chat!"),
        ]

    def ingest(self, data_dir: str = None) -> str:
        return ingest_docs(data_dir) if data_dir else ingest_docs()

    def _extract_emails(self, text: str) -> Set[str]:
        return set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text or ""))

    def _extract_name(self, text: str) -> str | None:
        t = (text or "").strip()
        m = re.search(r"\bmy name is\s+([A-Z][a-zA-Z'.-]{1,40}(\s+[A-Z][a-zA-Z'.-]{1,40}){0,2})\b", t, re.I)
        if m:
            return m.group(1).strip()
        m = re.search(r"\bi am\s+([A-Z][a-zA-Z'.-]{1,40}(\s+[A-Z][a-zA-Z'.-]{1,40}){0,2})\b", t, re.I)
        if m:
            return m.group(1).strip()
        m = re.search(r"\bthis is\s+([A-Z][a-zA-Z'.-]{1,40}(\s+[A-Z][a-zA-Z'.-]{1,40}){0,2})\b", t, re.I)
        if m:
            return m.group(1).strip()
        return None

    def _extract_emails_from_conversation(self, current_message: str, history: List[dict]) -> Set[str]:
        all_emails = set()
        
        # Extract from current message
        all_emails.update(self._extract_emails(current_message))
        
        # Extract from chat history (user messages only)
        for msg in (history or []):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                all_emails.update(self._extract_emails(content))
        
        return all_emails

    def _extract_name_from_conversation(self, current_message: str, history: List[dict]) -> str | None:
        # First try current message
        name = self._extract_name(current_message)
        if name:
            return name
        
        # Then search through chat history (user messages only, most recent first)
        for msg in reversed(history or []):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                name = self._extract_name(content)
                if name:
                    return name
        
        return None

    def _build_prompt(self, q, hits) -> Tuple[str, str]:
        ctx = "\n\n".join([f"[Doc {i+1}]\n{d.page_content}" for i, d in enumerate(hits)])
        sys = (
            "You are a concise assistant. Answer ONLY using the provided Context. "
            "If the Context does not contain the answer, reply exactly: 'I am unsure'. "
            "Do not invent facts or pull from outside knowledge."
        )
        prompt = (
            f"User Question:\n{q}\n\n"
            f"Context (Top {len(hits)}):\n{ctx}\n\n"
            "Provide a short, direct answer grounded in the Context."
        )
        return sys, prompt

    def _build_conversation_with_history(self, current_message: str, history: List[dict], include_context: bool = False, context_chunks: List[str] = None):
        messages = []
        
        if include_context and context_chunks:
            # RAG mode with context
            ctx = "\n\n".join([f"[Doc {i+1}]\n{chunk}" for i, chunk in enumerate(context_chunks)])
            system_msg = (
                "You are a helpful assistant. Use the provided Context to answer questions accurately. "
                "If the Context doesn't contain the answer, say 'I am unsure'. "
                "Maintain conversation continuity and refer to previous messages when relevant.\n\n"
                f"Context:\n{ctx}"
            )
        else:
            # General mode without context
            system_msg = (
                "You are a helpful, practical, and concise assistant. "
                "Maintain conversation continuity and refer to previous messages when relevant."
            )
        
        messages.append(SystemMessage(content=system_msg))
        
        # Add recent history (last 10 messages to avoid token limits)
        recent_history = (history or [])[-10:] if history else []
        for msg in recent_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        
        # Add current message
        messages.append(HumanMessage(content=current_message))
        
        return messages

    def _smalltalk_reply(self, text: str):
        s = (text or "").strip()
        if not s:
            return None
        for pattern, reply in self._smalltalk_patterns:
            if pattern.search(s):
                return reply
        return None

    def _is_conversational(self, text: str) -> bool:
        t = (text or "").strip().lower()
        conversational_phrases = [
            "how are you",
            "what's up",
            "whats up",
            "tell me a joke",
            "what do you think",
            "your opinion",
            "talk to me",
            "let's chat",
            "lets chat",
            "who are you",
            "help",
            "thank you",
            "thanks",
            "good morning",
            "good evening",
        ]
        return any(p in t for p in conversational_phrases)

    def get_response(self, message: str, history: List[dict], name: str = None, email: str = None, recorded_emails: Set[str] = None):
        quick = self._smalltalk_reply(message)
        if quick is not None:
            ans = quick
            found_emails = self._extract_emails_from_conversation(message, history)
            if email:
                found_emails.add(email)
            seen = recorded_emails or set()
            new_seen = seen | found_emails
            return ans or "Hello!", new_seen
        retriever = get_retriever()
        hits = retriever.get_relevant_documents(message)
        context_chunks = [d.page_content for d in hits]
        
        # Check if context is actually relevant using a quick relevance test
        if context_chunks:
            context_text = " ".join(context_chunks)
            relevance_prompt = f"Does this context contain information relevant to answering: '{message}'?\nContext: {context_text[:500]}...\nAnswer only YES or NO."
            relevance_check = self.llm.invoke([HumanMessage(content=relevance_prompt)]).content.strip().upper()
            context_is_relevant = "YES" in relevance_check
        else:
            context_is_relevant = False
            
        if not context_chunks or not context_is_relevant:
            # No RAG support or irrelevant context → allow general LLM answer with history
            messages = self._build_conversation_with_history(message, history, include_context=False)
            ans = self.llm.invoke(messages).content.strip()
            decision = self.evaluator.evaluate_no_context(message, ans)
            # Mark this as needing notification since we used general LLM knowledge
            decision["used_general_knowledge"] = True
        else:
            # RAG response with history
            messages = self._build_conversation_with_history(message, history, include_context=True, context_chunks=context_chunks)
            ans = self.llm.invoke(messages).content.strip()
            decision = self.evaluator.evaluate_response(message, context_chunks, ans)
            decision["used_general_knowledge"] = False
        found_emails = self._extract_emails_from_conversation(message, history)
        if email:
            found_emails.add(email)
        found_name = name or self._extract_name_from_conversation(message, history)
        seen = recorded_emails or set()
        new_seen = seen | found_emails
        # Check if we used general knowledge and should send notification
        if decision.get("used_general_knowledge") and ans and ans.lower() != "i am unsure":
            if self._is_conversational(message):
                return ans, new_seen
            fields = []
            if found_name:
                fields.append(f"name={found_name}")
            if found_emails:
                fields.append(f"emails={','.join(sorted(found_emails))}")
            meta = (" | ".join(fields) + " | ") if fields else ""
            title = "RAG missing knowledge"
            message_payload = f"{meta}question={message}"
            notify(title, message_payload)
            return ans, new_seen
        
        if decision.get("decision") == "APPROVED":
            return ans or "i am unsure", new_seen
        
        return "Insufficient support in our DB.", new_seen
