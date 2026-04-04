"""generate_personas + AdvocateAgent + SkepticAgent + CommitteeModerator."""

import logging
import random
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from messages import AllPersonas, CommitteeVerdict, CommitteeVerdictSchema, JobBrief
from models import gpt4o_mini_model, haiku_model, grok_model, sonnet_model

_stage = logging.getLogger("stage")


# Committee definitions

COMMITTEES = [
    ("technical", "Technical Skills"),
    ("experience", "Experience"),
    ("culture", "Cultural Fit"),
    ("trajectory", "Career Trajectory"),
    ("impact", "Impact & Leadership"),
]

PERSONA_FIELDS = {
    "technical": ("technical_advocate", "technical_skeptic"),
    "experience": ("experience_advocate", "experience_skeptic"),
    "culture": ("culture_advocate", "culture_skeptic"),
    "trajectory": ("trajectory_advocate", "trajectory_skeptic"),
    "impact": ("impact_advocate", "impact_skeptic"),
}

# Fixed role identities — each committee has a named perspective
ROLE_IDENTITIES = {
    "technical": (
        "You are a Technical Lead evaluating system design and execution capability. "
        "Argue for the candidate's technical depth and ability to ship at scale.",
        "You are a Senior Engineer stress-testing claimed technical depth. "
        "Challenge specificity: vague descriptions of 'built systems' or 'led migrations' are not evidence.",
    ),
    "experience": (
        "You are a Hiring Manager evaluating whether the candidate is ready for the org's level and pace. "
        "Argue for the candidate's readiness based on scope, scale, and seniority signals in the CV.",
        "You are a Department Head questioning seniority and ownership claims. "
        "Flag titles that do not match described responsibilities, or experience gaps relative to the role.",
    ),
    "culture": (
        "You are a People and Leadership Coach arguing for the candidate's cultural alignment and growth trajectory. "
        "Look for evidence of collaboration, self-awareness, and adaptability.",
        "You are a Culture Skeptic surfacing red flags: job-hopping patterns, vague impact language, "
        "team friction signals, or a trajectory inconsistent with the company's stage.",
    ),
    "trajectory": (
        "You are a Product and Strategy Lead evaluating whether this candidate could drive 10x outcomes. "
        "Argue that the candidate's career arc positions them to create order-of-magnitude impact in this role.",
        "You are a Growth Skeptic challenging trajectory evidence. "
        "Distinguish genuine compound growth from lateral moves dressed as progression.",
    ),
    "impact": (
        "You are an External Industry Expert arguing that the candidate's demonstrated impact is "
        "market-comparable or above-benchmark for this role and level. Cite specific quantified outcomes.",
        "You are an Executive Skeptic challenging the measurability of claimed impact. "
        "If outcomes are not quantified, attribute, or traceable to the candidate's direct contribution, flag it.",
    ),
}

REPLY_PROBABILITY = 0.65
MAX_EXTRA_ROUNDS = 4


# Persona generation

async def generate_personas(brief: JobBrief) -> AllPersonas:
    print("PersonaCreator: generating 10 personas")
    delegate = AssistantAgent(
        "persona_gen", model_client=gpt4o_mini_model(),
        system_message=(
            "Refine these named hiring committee role identities into 2-3 sentence system messages "
            "that are tailored to the specific job and company provided. "
            "Preserve the advocate/skeptic polarity and the named role identity. "
            "Committees: Technical Skills (Technical Lead / Senior Engineer), "
            "Experience (Hiring Manager / Department Head), "
            "Cultural Fit (People Coach / Culture Skeptic), "
            "Career Trajectory (Product Strategy Lead / Growth Skeptic), "
            "Impact & Leadership (Industry Expert / Executive Skeptic)."
        ),
        output_content_type=AllPersonas,
    )
    prompt = f"Job:\n{brief.job_text[:2000]}\nCompany:\n{brief.company_profile[:1000]}"
    resp = await delegate.on_messages([TextMessage(content=prompt, source="user")], CancellationToken())
    result = resp.chat_message.content
    if isinstance(result, AllPersonas):
        return result
    # Fallback to fixed identities if LLM output failed
    return AllPersonas(
        technical_advocate=ROLE_IDENTITIES["technical"][0],
        technical_skeptic=ROLE_IDENTITIES["technical"][1],
        experience_advocate=ROLE_IDENTITIES["experience"][0],
        experience_skeptic=ROLE_IDENTITIES["experience"][1],
        culture_advocate=ROLE_IDENTITIES["culture"][0],
        culture_skeptic=ROLE_IDENTITIES["culture"][1],
        trajectory_advocate=ROLE_IDENTITIES["trajectory"][0],
        trajectory_skeptic=ROLE_IDENTITIES["trajectory"][1],
        impact_advocate=ROLE_IDENTITIES["impact"][0],
        impact_skeptic=ROLE_IDENTITIES["impact"][1],
    )


# Advocate & Skeptic

ADVOCATE_BASE = (
    "Your arguments must be grounded solely in the candidate's actual CV. "
    "You may reframe experience using JD language and highlight underappreciated strengths. "
    "You must NOT invent skills, fabricate outcomes, or claim unearned qualifications. "
    "Be direct and precise — do not hedge or soften findings. "
    "Format your argument as 2–4 short bullets. "
    "End with exactly this line: SCORE: X/10 | KEY EVIDENCE: [one specific CV item that most supports your case]\n\n"
)

SKEPTIC_BASE = (
    "Surface genuine gaps between the candidate's CV and JD requirements. "
    "Cite specific JD requirements not met — do not manufacture weaknesses. "
    "State uncomfortable truths directly. Do not soften or hedge. "
    "Format your argument as 2–4 short bullets. "
    "End with exactly this line: SCORE: X/10 | KEY GAP: [one specific JD requirement the CV does not satisfy]\n\n"
)


class AdvocateAgent:
    def __init__(self, system_message: str = "") -> None:
        self._delegate = AssistantAgent(
            "advocate", model_client=haiku_model(),
            system_message=ADVOCATE_BASE + system_message,
        )

    async def debate(self, brief: JobBrief, committee_name: str,
                     prior_pro: str | None, prior_con: str | None) -> str:
        if prior_pro:
            prompt = (f"Committee: {committee_name}\nJOB:\n{brief.job_text[:2000]}\n"
                      f"CV:\n{brief.cv_text[:3000]}\n"
                      f"PRIOR PRO:\n{prior_pro}\nPRIOR CON:\n{prior_con}\n"
                      f"Counter-argue defending the candidate with CV evidence. "
                      f"End with SCORE: X/10 | KEY EVIDENCE: ...")
        else:
            prompt = (f"Committee: {committee_name}\nJOB:\n{brief.job_text[:2000]}\n"
                      f"CV:\n{brief.cv_text[:3000]}\n"
                      f"Opening argument FOR the candidate. Pin every point to CV content. "
                      f"End with SCORE: X/10 | KEY EVIDENCE: ...")
        resp = await self._delegate.on_messages([TextMessage(content=prompt, source="user")], CancellationToken())
        return str(resp.chat_message.content)


class SkepticAgent:
    def __init__(self, system_message: str = "") -> None:
        self._delegate = AssistantAgent(
            "skeptic", model_client=grok_model(),
            system_message=SKEPTIC_BASE + system_message,
        )

    async def debate(self, brief: JobBrief, committee_name: str,
                     prior_pro: str | None, prior_con: str | None) -> str:
        if prior_pro:
            prompt = (f"Committee: {committee_name}\nJOB:\n{brief.job_text[:2000]}\n"
                      f"CV:\n{brief.cv_text[:3000]}\n"
                      f"PRIOR PRO:\n{prior_pro}\nPRIOR CON:\n{prior_con}\n"
                      f"Rebuttal: challenge the advocate with JD evidence. "
                      f"End with SCORE: X/10 | KEY GAP: ...")
        else:
            prompt = (f"Committee: {committee_name}\nJOB:\n{brief.job_text[:2000]}\n"
                      f"CV:\n{brief.cv_text[:3000]}\n"
                      f"Opening argument identifying genuine gaps. Be specific and evidence-based. "
                      f"End with SCORE: X/10 | KEY GAP: ...")
        resp = await self._delegate.on_messages([TextMessage(content=prompt, source="user")], CancellationToken())
        return str(resp.chat_message.content)


# CommitteeModerator

class CommitteeModerator:
    def __init__(self, name: str, key: str) -> None:
        self._name = name
        self._key = key
        self._synthesis = AssistantAgent(
            f"synth_{key}", model_client=sonnet_model(),
            system_message=(
                "You are a senior hiring committee chair synthesising a structured debate into a hiring verdict. "
                "Be brutally honest and precise — state uncomfortable truths. Do not soften findings.\n\n"
                "From the debate transcript, produce a CommitteeVerdict with:\n"
                "- committee_name: the committee dimension being evaluated\n"
                "- hire_label: one of {Strong Hire | Lean Hire | No Hire | Hold}\n"
                "- score: 0–10 numeric score for this dimension\n"
                "- confidence_pct: your confidence in the score as a percentage (0–100)\n"
                "- pros: the strongest evidence supporting the candidate (2–3 bullets)\n"
                "- cons: the strongest evidence against the candidate (2–3 bullets)\n"
                "- summary: 2-sentence synthesis of the debate\n"
                "- top_objection: the single hardest objection a hiring manager would raise\n"
                "- mitigation: a concrete tactical mitigation (e.g. a probation goal, test task, or reference question)\n"
                "- cv_gaps: list of specific JD requirements not evidenced in the CV"
            ),
            output_content_type=CommitteeVerdictSchema,
        )

    async def run(self, brief: JobBrief, personas: AllPersonas) -> CommitteeVerdict:
        adv_f, skep_f = PERSONA_FIELDS[self._key]
        adv_sys = str(getattr(personas, adv_f, "")) or ROLE_IDENTITIES[self._key][0]
        skep_sys = str(getattr(personas, skep_f, "")) or ROLE_IDENTITIES[self._key][1]

        advocate = AdvocateAgent(adv_sys)
        skeptic = SkepticAgent(skep_sys)
        transcript: list[str] = []
        pro_text = con_text = ""

        print(f"Moderator[{self._name}]: starting debate")

        # Round 1: Advocate opens
        try:
            pro_text = await advocate.debate(brief, self._name, None, None)
            transcript.append(f"[Advocate]\n{pro_text}")
            print(f"[{self._name}] Advocate: {pro_text}")
        except Exception as e:
            print(f"Moderator[{self._name}]: opening failed ({e}) — fallback verdict")
            return self._fallback()

        # Round 2: Skeptic rebuts
        try:
            con_text = await skeptic.debate(brief, self._name, pro_text, None)
            transcript.append(f"[Skeptic]\n{con_text}")
            print(f"[{self._name}] Skeptic: {con_text}")
        except Exception:
            con_text = ""

        # Round 3: Advocate defends
        try:
            pro_text = await advocate.debate(brief, self._name, pro_text, con_text)
            transcript.append(f"[Advocate defense]\n{pro_text}")
            print(f"[{self._name}] Advocate defense: {pro_text}")
        except Exception:
            pass

        # Round 4: Skeptic presses
        try:
            con_text = await skeptic.debate(brief, self._name, pro_text, con_text)
            transcript.append(f"[Skeptic press]\n{con_text}")
            print(f"[{self._name}] Skeptic press: {con_text}")
        except Exception:
            pass

        # Round 5: Advocate final stand
        try:
            pro_text = await advocate.debate(brief, self._name, pro_text, con_text)
            transcript.append(f"[Advocate final]\n{pro_text}")
            print(f"[{self._name}] Advocate final: {pro_text}")
        except Exception:
            pass

        # Extended rounds with probability gate and hard cap
        for _ in range(MAX_EXTRA_ROUNDS):
            if random.random() >= REPLY_PROBABILITY:
                break
            try:
                con_text = await skeptic.debate(brief, self._name, pro_text, con_text)
                transcript.append(f"[Skeptic]\n{con_text}")
                print(f"[{self._name}] Skeptic: {con_text}")
                if random.random() < REPLY_PROBABILITY:
                    pro_text = await advocate.debate(brief, self._name, pro_text, con_text)
                    transcript.append(f"[Advocate]\n{pro_text}")
                    print(f"[{self._name}] Advocate: {pro_text}")
            except Exception:
                break

        print(f"Moderator[{self._name}]: {len(transcript)} turns — synthesising")
        full_debate = "\n\n".join(transcript)
        prompt = (f"Committee: {self._name}\n\n"
                  f"DEBATE TRANSCRIPT:\n{full_debate}\n\n"
                  f"Synthesise into a CommitteeVerdict. Include hire_label, score, confidence_pct, "
                  f"top_objection, and mitigation.")
        resp = await self._synthesis.on_messages([TextMessage(content=prompt, source="user")], CancellationToken())
        schema = resp.chat_message.content

        if isinstance(schema, CommitteeVerdictSchema):
            print(f"Moderator[{self._name}]: {schema.hire_label} score={schema.score} confidence={schema.confidence_pct}%")
            return CommitteeVerdict(
                committee_name=schema.committee_name or self._name,
                pros=schema.pros, cons=schema.cons,
                score=schema.score, confidence_pct=schema.confidence_pct,
                hire_label=schema.hire_label, summary=schema.summary,
                top_objection=schema.top_objection, mitigation=schema.mitigation,
                cv_gaps=schema.cv_gaps,
            )
        return CommitteeVerdict(
            committee_name=self._name, pros="See summary", cons="See summary",
            score=5, summary=str(schema), cv_gaps=[],
        )

    def _fallback(self) -> CommitteeVerdict:
        return CommitteeVerdict(
            committee_name=self._name, pros="N/A", cons="N/A",
            score=0, summary=f"{self._name} evaluation failed.", cv_gaps=[],
        )
