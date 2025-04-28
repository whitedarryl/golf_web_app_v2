
from typing import List, Tuple

print("🔥 Using FINAL callaway_logic version")

def calculate_callaway_score(hole_scores: List[int], par: int) -> Tuple[int, int, int, int]:
    if len(hole_scores) != 18:
        raise ValueError("Must provide 18 hole scores.")

    par = int(par)  # ✅ Ensure integer par
    gross = int(sum(hole_scores))
    sorted_scores = sorted(hole_scores, reverse=True)

    rules = [
        (0, 75, 0, 0.0, 0),
        (76, 80, 1, 0.0, 0),
        (81, 85, 2, 0.0, 0),
        (86, 90, 2, 0.0, -1),
        (91, 95, 3, 0.0, -1),
        (96, 100, 3, 0.0, -2),
        (101, 105, 4, 0.0, -2),
        (106, 110, 4, 0.0, -3),
        (111, 115, 5, 0.0, -3),
        (116, 120, 5, 0.0, -4),
        (121, 125, 5, 0.5, -4),
        (126, 130, 6, 0.0, -4),
        (131, 135, 6, 0.5, -4),
        (136, 999, 7, 0.0, -4)
    ]

    if par is None:
        raise ValueError("Course par must be provided.")

    gross = int(sum(hole_scores))
    par = int(par)
    match = next((r for r in rules if r[0] <= gross <= r[1]), None)
    print(f"📐 Gross score: {gross}, matching rule: {match}")
    if not match:
        raise ValueError("No matching Callaway rule")

    min_score, max_score, holes, fractional, adj = match

    deduction_scores = sorted_scores[:holes]
    full_sum = sum(deduction_scores)

    partial = 0
    if fractional > 0 and len(sorted_scores) > holes:
        partial = sorted_scores[holes] * fractional

    total_deducted = int(round(full_sum + partial))
    net = gross - (total_deducted + adj)

    print(f"📊 Callaway breakdown → Gross: {gross}, Deducted: {total_deducted}, Adj: {adj}, Net: {net}")

    return gross, total_deducted, adj, net
