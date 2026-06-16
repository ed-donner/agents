import argparse
import json
import os
import random
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

from debate_engine.crew import DebateEngine

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Make stdout more Unicode-friendly on Windows terminals (CrewAI logs use emojis).
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DOTENV_PATH = PROJECT_ROOT / ".env"
REPO_ROOT_DOTENV_PATH = PROJECT_ROOT.parent.parent / ".env"


def _load_env() -> None:
    """
    Load API keys from `.env` files (if present).
    This helps `uv run` and Windows shells pick up provider keys automatically.
    """
    try:
        from dotenv import load_dotenv  # type: ignore[import-not-found]

        # Load repo-level `.env` first, then project-level `.env` (project wins).
        if REPO_ROOT_DOTENV_PATH.exists():
            load_dotenv(REPO_ROOT_DOTENV_PATH, override=False)
        if DOTENV_PATH.exists():
            load_dotenv(DOTENV_PATH, override=False)
    except Exception:
        # Optional dependency / best-effort load
        return


def _has_any_provider_key() -> bool:
    return any(os.getenv(k) for k in _PROVIDER_ENV_KEYS.values())


def _require_provider_keys_for_pool(pool: list[str]) -> None:
    """
    Fail fast with a friendly message when no provider keys are configured.
    """
    if _has_any_provider_key():
        return

    needed = sorted(set(_provider_for_model(m) for m in pool))
    keys = ", ".join(f"{p.upper()}_API_KEY" for p in needed if p in _PROVIDER_ENV_KEYS)
    raise RuntimeError(
        "No provider API keys detected. Add keys to your environment or to "
        f"'{DOTENV_PATH}'. For your selected models you likely need: {keys}. "
        "Example: OPENAI_API_KEY=... "
    )


def _strip_markdown_code_fences(text: str) -> str:
    """
    Some task outputs are saved with Markdown code fences like:
      ```json
      {...}
      ```
    Convert to raw JSON text for parsing.
    """
    s = text.strip()
    if s.startswith("```"):
        # Drop first fence line
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl + 1 :]
        # Drop trailing fence
        if s.strip().endswith("```"):
            s = s.rsplit("```", 1)[0]
    return s.strip()


def _read_json_file(path: Path) -> dict | list:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    raw = _strip_markdown_code_fences(raw)
    return json.loads(raw) if raw else {}


def get_debate_case(case_number=1):
    """
    Get different debate cases for testing various scenarios.
    """
    cases = {
        1: {
            'motion': 'The defendant\'s AI hiring system is liable for discriminatory practices under Title VII of the Civil Rights Act',
            'case_documents': '''
            Case Background:
            - TechCorp implemented an AI-powered resume screening system in 2023
            - The system was trained on historical hiring data from 2010-2022
            - Statistical analysis shows the AI rejected 85% of female applicants vs 65% male
            - The AI favored candidates with "male-coded" keywords in resumes
            - Plaintiff class: 1,200 women rejected between 2023-2024
            - Expert testimony: AI inherited biases from training data
            - Defendant claims: AI is neutral and follows mathematical optimization
            - Damages sought: $50 million in compensatory damages
            - Additional claims: Violation of Equal Employment Opportunity Commission guidelines
            ''',
            'name': 'AI Hiring Discrimination'
        },
        2: {
            'motion': 'The AI-generated artwork infringes on the plaintiff\'s copyrighted images used for training',
            'case_documents': '''
            Case Background:
            - Artist created unique digital artwork series "Nature Visions" in 2020
            - AI company scraped millions of images including plaintiff\'s work for training
            - Plaintiff\'s distinctive style: golden hour lighting, specific brush techniques
            - Defendant\'s AI generated similar compositions with identical stylistic elements
            - Expert analysis shows 78% similarity in visual elements and composition
            - Defendant claims: AI creates original work, training is fair use
            - Damages sought: $25 million in statutory damages
            - Additional claims: DMCA violation and right of publicity
            ''',
            'name': 'AI Copyright Infringement'
        },
        3: {
            'motion': 'The autonomous vehicle manufacturer is strictly liable for the accident caused by its self-driving car',
            'case_documents': '''
            Case Background:
            - AutoTech deployed Level 4 autonomous vehicles in urban areas since 2022
            - Incident occurred when vehicle failed to detect pedestrian in crosswalk
            - Vehicle software version had known edge case in low-light conditions
            - Plaintiff suffered permanent injuries requiring lifelong care
            - NTSB investigation found software glitch, not human error
            - Defendant claims: Vehicle was in autonomous mode, human backup driver available
            - Damages sought: $15 million in compensatory damages
            - Additional claims: Product liability and negligence
            ''',
            'name': 'Autonomous Vehicle Liability'
        },
        4: {
            'motion': 'The social media platform\'s AI content moderation system violates the First Amendment',
            'case_documents': '''
            Case Background:
            - SocialNet uses AI to automatically flag and remove "hate speech"
            - Conservative commentator\'s posts repeatedly flagged as hate speech
            - AI algorithm trained on biased datasets favoring certain political views
            - Statistical analysis shows 92% of flagged content from conservative sources
            - Defendant claims: AI is viewpoint-neutral, human review available
            - Plaintiff argues: Government compelled speech regulation via algorithm
            - Injunctive relief sought: Algorithm changes and damages
            - Additional claims: Selective enforcement and due process violations
            ''',
            'name': 'AI Content Moderation'
        }
    }
    
    return cases.get(case_number, cases[1])  # Default to case 1

_PROVIDER_ENV_KEYS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
    "google": "GOOGLE_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}

# You can extend/replace these with any LiteLLM-supported `provider/model` strings.
_MODEL_POOL_CANDIDATES: list[str] = [
    # OpenAI
    # CrewAI's native OpenAI provider expects bare model IDs (no `openai/` prefix).
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-3.5-turbo",
]


def _provider_for_model(model: str) -> str:
    # Allow both "provider/model" and bare OpenAI model IDs like "gpt-4o-mini".
    if "/" not in model:
        return "openai"
    return model.split("/", 1)[0].strip().lower()


def _default_model_pool() -> list[str]:
    """
    Build a safe default model pool:
    - only include providers with the required API key set
    - ensure at least 2 models are available

    Note: If *no* provider keys are detected, we still return an OpenAI-only pool so
    random selection can proceed; the run will then fail later with a clearer
    provider auth error if keys truly aren't configured.
    """
    enabled_providers = {
        provider for provider, env_key in _PROVIDER_ENV_KEYS.items() if os.getenv(env_key)
    }

    # Default behavior: use only OpenAI models (most stable in your environment).
    # You can opt-in other providers by setting:
    #   INCLUDE_GROQ_MODELS=true, INCLUDE_GOOGLE_MODELS=true, INCLUDE_DEEPSEEK_MODELS=true
    pool: list[str] = []
    if "openai" in enabled_providers:
        pool.extend([m for m in _MODEL_POOL_CANDIDATES if _provider_for_model(m) == "openai"])

    include_groq = os.getenv("INCLUDE_GROQ_MODELS", "").strip().lower() in {"1", "true", "yes"}
    include_google = os.getenv("INCLUDE_GOOGLE_MODELS", "").strip().lower() in {"1", "true", "yes"}
    include_deepseek = os.getenv("INCLUDE_DEEPSEEK_MODELS", "").strip().lower() in {"1", "true", "yes"}

    # (Optional) allow adding extra provider models if you add them to _MODEL_POOL_CANDIDATES.
    for provider, enabled in [("groq", include_groq), ("google", include_google), ("deepseek", include_deepseek)]:
        if enabled and provider in enabled_providers:
            pool.extend([m for m in _MODEL_POOL_CANDIDATES if _provider_for_model(m) == provider])

    if len(pool) < 2:
        # Still allow running with a single working model (we'll mirror it for both sides).
        if "openai" in enabled_providers:
            return ["gpt-3.5-turbo"]
        return pool

    return pool


_DEFAULT_SPECIALIST_MODELS: list[str] = [
    # Keep specialists on OpenAI by default (what you said is working).
    "gpt-4o-mini",
    "gpt-3.5-turbo",
]


def _default_specialist_model() -> str:
    """
    Pick a default model for judge/evidence/fact-check roles based on configured keys.
    """
    for m in _DEFAULT_SPECIALIST_MODELS:
        provider = _provider_for_model(m)
        env_key = _PROVIDER_ENV_KEYS.get(provider)
        if env_key and os.getenv(env_key):
            return m
    return "gpt-4o-mini"


def _ensure_project_cwd() -> None:
    """
    CrewAI output_file paths in YAML are relative to CWD.
    Force CWD to the project root so outputs are stable.
    """
    os.chdir(PROJECT_ROOT)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def run(
    case_number: int = 1,
    prosecutor_model: str | None = None,
    defense_model: str | None = None,
    judge_model: str | None = None,
    evidence_analyst_model: str | None = None,
    fact_checker_model: str | None = None,
    model_pool: list[str] | None = None,
) -> None:
    """Run a single debate case and print leaderboard + rankings."""
    _load_env()
    _ensure_project_cwd()

    case_data = get_debate_case(case_number)
    print(f"Running debate case {case_number}: {case_data['name']}")

    pool = model_pool or _default_model_pool()
    _require_provider_keys_for_pool(pool)
    if prosecutor_model and defense_model:
        model_a, model_b = prosecutor_model, defense_model
    else:
        if len(pool) == 1:
            model_a = pool[0]
            model_b = pool[0]
        else:
            model_a, model_b = random.sample(pool, 2)

    judge_model = judge_model or _default_specialist_model()
    evidence_analyst_model = evidence_analyst_model or _default_specialist_model()
    fact_checker_model = fact_checker_model or _default_specialist_model()

    print("\nDebate Match:")
    print(f"Prosecutor -> {model_a}")
    print(f"Defense    -> {model_b}")
    print(f"Judge      -> {judge_model}")
    print(f"Evidence   -> {evidence_analyst_model}")
    print(f"FactCheck  -> {fact_checker_model}\n")

    inputs = {
        "motion": case_data["motion"],
        "case_documents": case_data["case_documents"],
        "current_year": str(datetime.now().year),
        "prosecutor_model": model_a,
        "defense_model": model_b,
        "judge_model": judge_model,
        "evidence_analyst_model": evidence_analyst_model,
        "fact_checker_model": fact_checker_model,
    }

    try:
        # Ensure agent LLMs can be set at construction time (CrewBase creates agents before kickoff).
        os.environ["DEBATE_PROSECUTOR_MODEL"] = model_a
        os.environ["DEBATE_DEFENSE_MODEL"] = model_b
        os.environ["DEBATE_JUDGE_MODEL"] = judge_model
        os.environ["DEBATE_EVIDENCE_ANALYST_MODEL"] = evidence_analyst_model
        os.environ["DEBATE_FACT_CHECKER_MODEL"] = fact_checker_model

        # Groq (and other providers) can rate-limit; retry with backoff when we can.
        last_err: Exception | None = None
        for attempt in range(6):
            try:
                DebateEngine().crew().kickoff(inputs=inputs)
                last_err = None
                break
            except Exception as e:
                last_err = e
                msg = str(e)

                # Common patterns (LiteLLM/Groq):
                # - "... code\":\"rate_limit_exceeded\" ... Please try again in 36.35s ..."
                msg_l = msg.lower()
                is_rate_limit = (
                    "rate_limit_exceeded" in msg_l
                    or "rate limit reached" in msg_l
                    or e.__class__.__name__.lower() == "ratelimiterror"
                )
                if is_rate_limit and "try again in" in msg_l:
                    wait_s = None
                    try:
                        after = msg_l.split("try again in", 1)[1]
                        number = after.split("s", 1)[0].strip().strip(".")
                        wait_s = float(number)
                    except Exception:
                        wait_s = None

                    # Fallback exponential backoff if we can't parse.
                    if wait_s is None:
                        wait_s = min(60.0, 5.0 * (2**attempt))

                    time.sleep(max(1.0, wait_s) + 1.0)
                    continue
                raise

        if last_err is not None:
            raise last_err

        verdict_path = OUTPUTS_DIR / "final_verdict.json"
        verdict = {}
        if verdict_path.exists():
            verdict = _read_json_file(verdict_path) or {}

        verdict["prosecutor_model"] = model_a
        verdict["defense_model"] = model_b
        verdict["judge_model"] = judge_model
        verdict["evidence_analyst_model"] = evidence_analyst_model
        verdict["fact_checker_model"] = fact_checker_model

        verdict_path.write_text(json.dumps(verdict, indent=2), encoding="utf-8")

        display_leaderboard(case_data["name"])
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}") from e


def train():
    """
    Train the crew for a given number of iterations.
    """
    _load_env()
    _ensure_project_cwd()

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("n_iterations", type=int)
    parser.add_argument("filename", type=str)
    parser.add_argument("case_number", type=int, nargs="?", default=1)
    args, _ = parser.parse_known_args(sys.argv[1:])

    case_data = get_debate_case(args.case_number)
    inputs = {
        "motion": case_data["motion"],
        "case_documents": case_data["case_documents"],
        "current_year": str(datetime.now().year),
    }

    try:
        DebateEngine().crew().train(
            n_iterations=args.n_iterations, filename=args.filename, inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}") from e

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        _load_env()
        _ensure_project_cwd()
        DebateEngine().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}") from e


def save_debate_result(verdict_data, case_name="AI Hiring Discrimination Case"):
    """
    Save debate result to persistent storage.
    """
    results_file = OUTPUTS_DIR / "debate_results.json"
    
    # Load existing results
    if results_file.exists():
        try:
            loaded = _read_json_file(results_file)
            results = loaded if isinstance(loaded, list) else []
        except Exception:
            results = []
    else:
        results = []
    
    # Add current result
    result_entry = {
        'timestamp': datetime.now().isoformat(),
        'motion': case_name,
        'winner': verdict_data.get('winner', 'Unknown'),
        'scores': verdict_data.get('scores', {}),
        'confidence': verdict_data.get('confidence', 0),
        'reasoning': verdict_data.get('reasoning', ''),
        'models': {
            'prosecutor': verdict_data.get('prosecutor_model', 'unknown'),
            'defense': verdict_data.get('defense_model', 'unknown'),
            'judge': verdict_data.get('judge_model', 'unknown'),
            'evidence_analyst': verdict_data.get('evidence_analyst_model', 'unknown'),
            'fact_checker': verdict_data.get('fact_checker_model', 'unknown'),
        }
    }
    
    results.append(result_entry)
    
    # Save back
    results_file.write_text(json.dumps(results, indent=2), encoding="utf-8")


def calculate_rankings(results):
    rankings = {}

    for result in results:
        winner = result.get('winner', '').lower()
        scores = result.get('scores', {})
        models = result.get('models', {})

        for side in ['prosecution', 'defense']:
            if side in scores:
                model_name = models.get(
                    'prosecutor' if side == 'prosecution' else 'defense',
                    'unknown'
                )

                if model_name not in rankings:
                    rankings[model_name] = {
                        'wins': 0,
                        'total_score': 0,
                        'debates': 0,
                        'avg_score': 0
                    }

                score = scores[side].get('total', 0)

                rankings[model_name]['total_score'] += score
                rankings[model_name]['debates'] += 1
                rankings[model_name]['avg_score'] = (
                    rankings[model_name]['total_score'] /
                    rankings[model_name]['debates']
                )

                if winner == side:
                    rankings[model_name]['wins'] += 1

    return rankings


def display_leaderboard(case_name="AI Hiring Discrimination Case"):
    """
    Display the debate leaderboard based on the final verdict scores.
    """
    try:
        verdict = _read_json_file(OUTPUTS_DIR / "final_verdict.json")
        
        # Save this debate result
        save_debate_result(verdict, case_name)
        
        scores = verdict.get('scores', {})
        winner = verdict.get('winner', 'Unknown')
        reasoning = verdict.get('reasoning', '')
        
        print("\n" + "="*60)
        print("COURTROOM DEBATE LEADERBOARD")
        print("="*60)
        print(f"Winner: {winner.upper()}")
        print(f"Reasoning: {reasoning}")
        print("\nCURRENT DEBATE SCORES:")
        print("-"*30)
        
        # Sort by total score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1]['total'], reverse=True)
        
        for i, (side, score_data) in enumerate(sorted_scores, 1):
            medal = "1st" if i == 1 else "2nd" if i == 2 else "3rd"
            print(f"{medal} {side.upper()}:")
            print(f"   Logic: {score_data['logic']}/10")
            print(f"   Evidence: {score_data['evidence']}/10")
            print(f"   Rebuttal: {score_data['rebuttal']}/10")
            print(f"   Clarity: {score_data['clarity']}/10")
            print(f"   TOTAL: {score_data['total']}/10")
            print()
        
        # Load historical results and show rankings
        results_file = OUTPUTS_DIR / "debate_results.json"
        if results_file.exists():
            loaded = _read_json_file(results_file)
            all_results = loaded if isinstance(loaded, list) else []
            
            rankings = calculate_rankings(all_results)
            
            print("HISTORICAL RANKINGS (All Debates):")
            print("-"*40)
            print(f"Total Debates: {len(all_results)}")
            print()
            
            # Sort by win rate, then by average score
            sorted_rankings = sorted(rankings.items(), 
                                   key=lambda x: (x[1]['wins']/x[1]['debates'] if x[1]['debates'] > 0 else 0, x[1]['avg_score']), 
                                   reverse=True)
            
            for i, (side, stats) in enumerate(sorted_rankings, 1):
                win_rate = (stats['wins'] / stats['debates'] * 100) if stats['debates'] > 0 else 0
                medal = "1st" if i == 1 else "2nd" if i == 2 else "3rd"
                print(f"{medal} {side.upper()}:")
                print(f"   Wins: {stats['wins']}/{stats['debates']} ({win_rate:.1f}%)")
                print(f"   Avg Score: {stats['avg_score']:.1f}/10")
                print()
        
        print("="*60)
        
    except FileNotFoundError:
        print("No final verdict found. Please run the debate first.")
    except json.JSONDecodeError:
        print("Error reading verdict file.")
    except Exception as e:
        print(f"Error displaying leaderboard: {e}")


def display_rankings_only():
    """
    Display only the historical rankings without running a new debate.
    """
    _load_env()
    _ensure_project_cwd()
    results_file = OUTPUTS_DIR / "debate_results.json"
    if results_file.exists():
        try:
            all_results = json.loads(results_file.read_text(encoding="utf-8"))
            
            rankings = calculate_rankings(all_results)
            
            print("\n" + "="*60)
            print("DEBATE MODEL RANKINGS")
            print("="*60)
            print(f"Total Debates: {len(all_results)}")
            print("\nPERFORMANCE RANKINGS:")
            print("-"*40)
            
            # Sort by win rate, then by average score
            sorted_rankings = sorted(rankings.items(), 
                                   key=lambda x: (x[1]['wins']/x[1]['debates'] if x[1]['debates'] > 0 else 0, x[1]['avg_score']), 
                                   reverse=True)
            
            for i, (side, stats) in enumerate(sorted_rankings, 1):
                win_rate = (stats['wins'] / stats['debates'] * 100) if stats['debates'] > 0 else 0
                medal = "1st" if i == 1 else "2nd" if i == 2 else "3rd"
                model = "GPT-4o-mini" if side == "prosecution" else "GPT-3.5-Turbo"
                print(f"{medal} {side.upper()} ({model}):")
                print(f"   Wins: {stats['wins']}/{stats['debates']} ({win_rate:.1f}%)")
                print(f"   Avg Score: {stats['avg_score']:.1f}/10")
                print()
            
            print("="*60)
        except Exception as e:
            print(f"Error displaying rankings: {e}")
    else:
        print(
            "No debate results found. Run a debate first with "
            "'python -m debate_engine.main run 1' (or use uv run)."
        )


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        _load_env()
        _ensure_project_cwd()
        DebateEngine().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}") from e

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        _load_env()
        _ensure_project_cwd()
        result = DebateEngine().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}") from e




if __name__ == "__main__":
    _load_env()
    _ensure_project_cwd()

    parser = argparse.ArgumentParser(prog="debate_engine")
    sub = parser.add_subparsers(dest="cmd")

    run_p = sub.add_parser("run", help="Run a debate case")
    run_p.add_argument("case_number", type=int, nargs="?", default=1)
    run_p.add_argument("--prosecutor-model", type=str, default=None)
    run_p.add_argument("--defense-model", type=str, default=None)
    run_p.add_argument("--judge-model", type=str, default=None)
    run_p.add_argument(
        "--evidence-analyst-model", type=str, default=None
    )
    run_p.add_argument("--fact-checker-model", type=str, default=None)
    run_p.add_argument(
        "--model-pool",
        type=str,
        default="",
        help="Comma-separated model list used when prosecutor/defense not set",
    )

    sub.add_parser("rankings", help="Show historical rankings only")

    train_p = sub.add_parser("train", help="Train the crew")
    train_p.add_argument("n_iterations", type=int)
    train_p.add_argument("filename", type=str)
    train_p.add_argument("case_number", type=int, nargs="?", default=1)

    replay_p = sub.add_parser("replay", help="Replay from task id")
    replay_p.add_argument("task_id", type=str)

    args, unknown = parser.parse_known_args()

    # Backwards compatible: `python main.py 2` runs case 2; `python main.py rankings` shows rankings.
    if args.cmd is None:
        if len(sys.argv) > 1 and sys.argv[1] == "rankings":
            display_rankings_only()
        else:
            case_number = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 1
            run(case_number=case_number)
    elif args.cmd == "rankings":
        display_rankings_only()
    elif args.cmd == "run":
        pool = [m.strip() for m in (args.model_pool or "").split(",") if m.strip()] or None
        run(
            case_number=args.case_number,
            prosecutor_model=args.prosecutor_model,
            defense_model=args.defense_model,
            judge_model=args.judge_model,
            evidence_analyst_model=args.evidence_analyst_model,
            fact_checker_model=args.fact_checker_model,
            model_pool=pool,
        )
    elif args.cmd == "train":
        # `crewai train` will call `train()` script entrypoint, but this supports `python -m ... train ...`
        sys.argv = [sys.argv[0], str(args.n_iterations), args.filename, str(args.case_number), *unknown]
        train()
    elif args.cmd == "replay":
        sys.argv = [sys.argv[0], args.task_id, *unknown]
        replay()
