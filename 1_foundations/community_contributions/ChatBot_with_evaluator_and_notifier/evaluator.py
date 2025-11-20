from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from typing import List, Dict, Any


GEMINI_MODEL = "gemini-2.0-flash"


class GeminiEvaluator:
    def __init__(self, model: str = GEMINI_MODEL):
        load_dotenv(override=True)
        google_api_key = os.getenv('GOOGLE_API_KEY')
        self.client = OpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
        self.model = model

    def create_evaluation_prompt(self, query: str, context: List[str], response: str) -> str:
        ctx = "\n- " + "\n- ".join(context) if context else "(no context retrieved)"
        return (
            "You are a strict evaluator. Decide if the Response is supported by the Context.\n"
            "Rules:\n"
            "- If the key facts of the Response are not present in the Context and Context is empty, mark REJECTED and set has_external_info=True.\n"
            "- If partially supported but missing crucial facts, mark REJECTED.\n"
            "- Otherwise APPROVED.\n"
            "Return ONLY a compact JSON with keys: decision, confidence, reason, has_external_info.\n"
            "Respond with JSON only, no prose.\n\n"
            f"Context:\n{ctx}\n\n"
            f"Query: {query}\n"
            f"Response: {response}\n"
        )

    def evaluate_response(self, query: str, context: List[str], llm_response: str) -> Dict[str, Any]:
        try:
            prompt = self.create_evaluation_prompt(query, context, llm_response)
            messages = [
                {"role": "system", "content": "Return strict JSON only."},
                {"role": "user", "content": prompt},
            ]
            resp = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0)
            text = resp.choices[0].message.content or "{}"
            start = text.find("{")
            end = text.rfind("}")
            blob = text[start:end+1] if start != -1 and end != -1 else "{}"
            data = json.loads(blob)

            class EvaluationResult(BaseModel):
                decision: str = Field(pattern=r"^(APPROVED|REJECTED)$")
                confidence: int = Field(ge=0, le=100)
                reason: str
                has_external_info: bool = False

            try:
                # normalize decision before validation
                if "decision" in data:
                    data["decision"] = str(data["decision"]).upper()
                validated = EvaluationResult(**{
                    "decision": data.get("decision", "REJECTED"),
                    "confidence": int(data.get("confidence", 50)),
                    "reason": data.get("reason", ""),
                    "has_external_info": bool(data.get("has_external_info", False)),
                })
                return validated.model_dump()
            except ValidationError as ve:
                print(f"[evaluator] validation error: {ve}")
                return {"decision": "REJECTED", "confidence": 0, "reason": "validation_error", "has_external_info": False}
        except Exception as e:
            print(f"[evaluator] error: {e}")
            return {"decision": "REJECTED", "confidence": 0, "reason": str(e), "has_external_info": False}

    def evaluate_no_context(self, query: str, llm_response: str) -> Dict[str, Any]:
        try:
            prompt = (
                "You are a strict evaluator. There is NO database context for this query.\n"
                "Evaluate how well the Response addresses the Query in terms of relevance, helpfulness and clarity.\n"
                "Return ONLY JSON with keys: decision (APPROVED|REJECTED), confidence (0-100), reason, has_external_info (true).\n\n"
                f"Query: {query}\n"
                f"Response: {llm_response}\n"
            )
            messages = [
                {"role": "system", "content": "Return strict JSON only."},
                {"role": "user", "content": prompt},
            ]
            resp = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0)
            text = resp.choices[0].message.content or "{}"
            start = text.find("{")
            end = text.rfind("}")
            blob = text[start:end+1] if start != -1 and end != -1 else "{}"
            data = json.loads(blob)

            def _coerce_conf(v):
                try:
                    return max(0, min(100, int(float(v))))
                except Exception:
                    return 50

            decision = str(data.get("decision", "APPROVED")).upper()
            return {
                "decision": "APPROVED" if decision == "APPROVED" else "REJECTED",
                "confidence": _coerce_conf(data.get("confidence", 75)),
                "reason": data.get("reason", "no_context"),
                "has_external_info": True,
            }
        except Exception as e:
            # Heuristic fallback when model errors
            rel = 1.0 if (query and llm_response and query.split()[0].lower() in (llm_response or "").lower()) else 0.5
            return {"decision": "APPROVED" if rel >= 0.5 else "REJECTED", "confidence": int(rel * 100), "reason": "fallback_no_context", "has_external_info": True}