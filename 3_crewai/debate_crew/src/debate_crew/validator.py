import re
from pathlib import Path


CRITERIA = [
    "Logical consistency",
    "Relevance",
    "Reasoning",
    "Evidence quality",
    "Counterargument handling",
]


def validate_verdict(text: str) -> list[str]:
    """Validate scoring, totals, winner consistency, and final decision."""
    errors: list[str] = []

    # 1. Check that all five scoring criteria appear.
    for criterion in CRITERIA:
        if criterion.lower() not in text.lower():
            errors.append(f"Missing scoring criterion: {criterion}")

    # 2. Extract reported totals.
    total_patterns = {
        "Pro": [
            r"\bPro\s+Total(?:\s+Score)?\s*:?\s*\*{0,2}\s*:?\s*\*{0,2}\s*(\d+)(?:\s+out\s+of\s+25)?\b",
            r"[-*]\s*\*{0,2}\s*Pro\s*:\s*\*{0,2}\s*(\d+)\s+out\s+of\s+25\b",
        ],
        "Counter": [
            r"\bCounter\s+Total(?:\s+Score)?\s*:?\s*\*{0,2}\s*:?\s*\*{0,2}\s*(\d+)(?:\s+out\s+of\s+25)?\b",
            r"[-*]\s*\*{0,2}\s*Counter\s*:\s*\*{0,2}\s*(\d+)\s+out\s+of\s+25\b",
        ],
    }

    totals: dict[str, int] = {}

    for side, patterns in total_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                totals[side] = int(match.group(1))
                break

        if side not in totals:
            errors.append(f"Missing or invalid {side} total out of 25")
        elif not 0 <= totals[side] <= 25:
            errors.append(f"{side} total is outside the range 0–25")

    # 3. Extract and validate the five-column Markdown scoring table.
    expected_header = [
        "criterion",
        "pro score",
        "pro justification",
        "counter score",
        "counter justification",
    ]
    table_rows: list[list[str]] = []
    expected_criteria = {criterion.lower() for criterion in CRITERIA}
    pipe_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith("|")
    ]

    header_found = False

    for line in pipe_lines:
        cells = [
            cell.strip()
            for cell in line.strip().strip("|").split("|")
        ]
        normalized = [cell.lower() for cell in cells]

        # Validate a header-like row rather than silently ignoring bad headers.
        if normalized and normalized[0] in {"criterion", "category", "criteria"}:
            if normalized != expected_header:
                errors.append(
                    "Invalid scoring table header; expected: "
                    "Criterion | Pro Score | Pro Justification | "
                    "Counter Score | Counter Justification"
                )
            else:
                if header_found:
                    errors.append("Duplicate scoring table header")
                header_found = True
            continue

        # Ignore Markdown separator rows.
        if cells and all(
            re.fullmatch(r":?-{3,}:?", cell.replace(" ", ""))
            for cell in cells
        ):
            continue

        # Scoring rows must have exactly five cells.
        if len(cells) != 5:
            if any(criterion.lower() in line.lower() for criterion in CRITERIA):
                errors.append(
                    "Malformed scoring table row: expected exactly 5 cells."
                )
            continue

        if cells[0].lower() in expected_criteria:
            table_rows.append(cells)

    if not header_found:
        errors.append("Missing required five-column scoring table header.")

    winner: str | None = None

    if len(table_rows) != 5:
        errors.append(
            "Expected exactly 5 scoring rows in a five-column Markdown table; "
            f"found {len(table_rows)}"
        )
    else:
        found_criteria = [row[0].lower() for row in table_rows]

        if len(set(found_criteria)) != 5:
            errors.append("The scoring table contains duplicate criteria")

        if set(found_criteria) != expected_criteria:
            errors.append(
                "The scoring table does not contain exactly the five required criteria"
            )

        expected_order = [criterion.lower() for criterion in CRITERIA]
        if found_criteria != expected_order:
            errors.append(
                "The scoring table criteria are not in the required order"
            )

        pro_scores: dict[str, int] = {}
        counter_scores: dict[str, int] = {}

        for row in table_rows:
            criterion = row[0].strip()

            try:
                pro_score = int(row[1].strip())
                counter_score = int(row[3].strip())
            except ValueError:
                errors.append(f"Invalid score in table row: {criterion}")
                continue

            if not 1 <= pro_score <= 5:
                errors.append(f"Pro score outside 1–5 for {criterion}")

            if not 1 <= counter_score <= 5:
                errors.append(f"Counter score outside 1–5 for {criterion}")

            pro_scores[criterion.lower()] = pro_score
            counter_scores[criterion.lower()] = counter_score

        # Conservative evidence-reference check for high Evidence quality scores.
        # This is a heuristic: a match suggests a reference, but does not prove
        # that the cited source is empirical or actually supports the claim.
        evidence_row = next(
            (row for row in table_rows if row[0].lower() == "evidence quality"),
            None,
        )

        if evidence_row:
            pro_justification = evidence_row[2]
            counter_justification = evidence_row[4]

            reference_pattern = re.compile(
                r"https?://|doi:\\s*10\\.|"
                r"\b(?:19|20)\d{2}\b|"
                r"\[\d+\]|"
                r"\b(?:et al\.|pp?\.\s*\d+)\b",
                re.IGNORECASE,
            )

            pro_has_reference = bool(reference_pattern.search(pro_justification))
            counter_has_reference = bool(reference_pattern.search(counter_justification))
            neither_side_has_reference = not (
                pro_has_reference or counter_has_reference
            )

            if neither_side_has_reference:
                if pro_scores.get("evidence quality", 0) >= 4:
                    errors.append(
                        "Evidence quality: Pro score of 4 or 5 is not allowed "
                        "when neither side provides an identifiable evidence reference."
                    )
                if counter_scores.get("evidence quality", 0) >= 4:
                    errors.append(
                        "Evidence quality: Counter score of 4 or 5 is not allowed "
                        "when neither side provides an identifiable evidence reference."
                    )

        # Check reported totals against the table.
        if len(pro_scores) == 5 and "Pro" in totals:
            pro_sum = sum(pro_scores.values())
            if pro_sum != totals["Pro"]:
                errors.append(
                    f"Pro total mismatch: table sums to {pro_sum}, "
                    f"but verdict reports {totals['Pro']}"
                )

        if len(counter_scores) == 5 and "Counter" in totals:
            counter_sum = sum(counter_scores.values())
            if counter_sum != totals["Counter"]:
                errors.append(
                    f"Counter total mismatch: table sums to {counter_sum}, "
                    f"but verdict reports {totals['Counter']}"
                )

    # 4. Recognize the declared winner.
    winner_match = re.search(
        r"\*\*\s*Winning\s+Side\s*:?\s*\*\*\s*:?\s*([^\r\n*]+)"
        r"|"
        r"\*\*\s*Winning\s+Side\s*:\s*([^\r\n*]+?)\s*\*\*",
        text,
        re.IGNORECASE,
    )

    if not winner_match:
        errors.append("Missing Winning Side declaration")
    else:
        winner_text = (
            winner_match.group(1) or winner_match.group(2) or ""
        ).strip().strip("*").strip()

        if re.search(r"\btie\b", winner_text, re.IGNORECASE):
            winner = "Tie"
        elif re.search(
            r"\bcounter(?:argument)?\b", winner_text, re.IGNORECASE
        ):
            winner = "Counter"
        elif re.search(r"\bpro\b", winner_text, re.IGNORECASE):
            winner = "Pro"
        else:
            errors.append(f"Unrecognized winner label: {winner_text}")

    # 5. Ensure the declared winner agrees with the reported totals.
    if winner and "Pro" in totals and "Counter" in totals:
        pro_total = totals["Pro"]
        counter_total = totals["Counter"]

        if pro_total > counter_total and winner != "Pro":
            errors.append(
                "Winner conflicts with the totals: Pro has the higher score"
            )
        elif counter_total > pro_total and winner != "Counter":
            errors.append(
                "Winner conflicts with the totals: Counter has the higher score"
            )
        elif pro_total == counter_total and winner != "Tie":
            errors.append(
                "Scores are tied, so the declared winner must be Tie"
            )

    # 6. Check the final decision against the declared winner.
    decision_match = re.search(
        r"(?ims)^#{1,6}\s*Final Decision\s*:?\s*$"
        r"\s*(.*?)"
        r"(?=^#{1,6}\s|\Z)",
        text,
    )

    if not decision_match:
        errors.append("Missing Final Decision section")
    elif winner:
        decision = decision_match.group(1)

        # Detect common explicit winner statements.
        # Do not infer a winner from general praise or criticism.
        decision_claims = []

        claim_patterns = {
            "Pro": [
                r"\bPro\s+(?:wins?|is\s+the\s+winner)\b",
                r"\bPro\s+(?:has|earned|achieved)\s+the\s+higher\s+(?:total|score)\b",
            ],
            "Counter": [
                r"\bCounter(?:argument)?\s+(?:wins?|is\s+the\s+winner)\b",
                r"\bCounter(?:argument)?\s+(?:has|earned|achieved)\s+the\s+higher\s+(?:total|score)\b",
            ],
            "Tie": [
                r"\b(?:it is|this is|the result is|the outcome is)\s+a tie\b",
                r"\bthe scores are tied\b",
                r"\bneither side wins\b",
                r"\bno overall winner\b",
            ],
        }

        for side, patterns in claim_patterns.items():
            if any(
                re.search(pattern, decision, re.IGNORECASE)
                for pattern in patterns
            ):
                decision_claims.append(side)

        if decision_claims:
            if len(set(decision_claims)) > 1:
                errors.append(
                    "Final decision contains conflicting winner statements"
                )
            elif decision_claims[0] != winner:
                errors.append(
                    "Final decision conflicts with the declared winner: "
                    f"heading says {winner}, "
                    f"narrative says {decision_claims[0]}"
                )

    return errors


def validate_verdict_file(
    path: str = "debate_verdict.md",
) -> list[str]:
    """Validate a saved verdict file."""
    verdict_path = Path(path)

    if not verdict_path.is_file():
        return [f"Verdict file not found: {verdict_path}"]

    try:
        text = verdict_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"Could not read verdict file: {exc}"]

    return validate_verdict(text)


def correct_verdict_consistency(text: str) -> str:
    """Correct reported totals and winner using valid table scores only.

    Does not change individual scores, repair malformed tables, or rewrite
    the judge's final decision narrative.
    """
    expected = [criterion.lower() for criterion in CRITERIA]
    rows: list[tuple[int, list[str]]] = []

    for index, line in enumerate(text.splitlines()):
        if not line.strip().startswith("|"):
            continue

        cells = [
            cell.strip()
            for cell in line.strip().strip("|").split("|")
        ]

        if len(cells) == 5 and cells[0].lower() in expected:
            rows.append((index, cells))

    if len(rows) != 5:
        raise ValueError(
            "Cannot correct verdict: expected five valid scoring rows."
        )

    if [cells[0].lower() for _, cells in rows] != expected:
        raise ValueError(
            "Cannot correct verdict: scoring criteria are missing, "
            "duplicated, or out of order."
        )

    pro_scores: list[int] = []
    counter_scores: list[int] = []

    for _, cells in rows:
        try:
            pro_score = int(cells[1])
            counter_score = int(cells[3])
        except ValueError as exc:
            raise ValueError(
                "Cannot correct verdict: table scores must be integers."
            ) from exc

        if not 1 <= pro_score <= 5 or not 1 <= counter_score <= 5:
            raise ValueError(
                "Cannot correct verdict: table scores must be between 1 and 5."
            )

        pro_scores.append(pro_score)
        counter_scores.append(counter_score)

    pro_total = sum(pro_scores)
    counter_total = sum(counter_scores)

    if pro_total > counter_total:
        winner = "Pro"
    elif counter_total > pro_total:
        winner = "Counter"
    else:
        winner = "Tie"

    # Correct only the standard total lines.
    total_patterns = {
        "Pro": re.compile(
            r"(?m)^[ \t]*\*\*Pro Total Score:[ \t]*\d+"
            r"[ \t]+out of 25\*\*[ \t]*$"
        ),
        "Counter": re.compile(
            r"(?m)^[ \t]*\*\*Counter Total Score:[ \t]*\d+"
            r"[ \t]+out of 25\*\*[ \t]*$"
        ),
    }

    for side, total in (
        ("Pro", pro_total),
        ("Counter", counter_total),
    ):
        matches = list(total_patterns[side].finditer(text))

        if len(matches) != 1:
            raise ValueError(
                "Cannot correct verdict: expected exactly one standard "
                f"{side} total line."
            )

        text = total_patterns[side].sub(
            f"**{side} Total Score: {total} out of 25**",
            text,
            count=1,
        )

    # Correct standard winner headings only.
    winner_pattern = re.compile(
        r"(?m)^[ \t]*\*\*Winning Side:[ \t]*"
        r"(?:Pro|Counter|Tie)\*\*[ \t]*$"
    )

    winner_matches = list(winner_pattern.finditer(text))

    if not winner_matches:
        raise ValueError(
            "Cannot correct verdict: no standard winner heading was found."
        )

    return winner_pattern.sub(
        f"**Winning Side: {winner}**",
        text,
    )
