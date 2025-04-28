from typing import List, Tuple

def calculate_callaway_score(hole_scores: List[int]) -> Tuple[int, int, int, int]:
    if len(hole_scores) != 18:
        raise ValueError("Must provide 18 hole scores.")

    gross = sum(hole_scores)
    sorted_scores = sorted(hole_scores, reverse=True)
    print("🟡 Hole Scores:", hole_scores)
    print("🧮 Gross:", gross)
    print("🔽 Sorted (High → Low):", sorted_scores)

    # Format: (min, max, holes_to_deduct, fractional, adjustment)
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

    print("🧾 DEDUCTION RULES:")
    for r in rules:
        print(r)

    # Sort and match rule
    rules_sorted = sorted(rules, key=lambda r: r[0])
    print("📋 Sorted Rules:")
    for r in rules_sorted:
        print(r)

    match = next((r for r in rules_sorted if r[0] <= gross <= r[1]), None)
    if not match:
        raise ValueError("No matching Callaway rule")

    min_score, max_score, holes, fractional, adj = match
    print(f"📐 Rule matched: {min_score}-{max_score} ⇒ Deduct {holes} + {fractional}, Adj {adj}")

    deduction_scores = sorted_scores[:holes]
    full_sum = sum(deduction_scores)
    print(f"🧮 Full Deducted Holes: {deduction_scores} = {full_sum}")

    partial = 0
    if fractional > 0 and len(sorted_scores) > holes:
        partial = sorted_scores[holes] * fractional
        print(f"➗ Partial: {sorted_scores[holes]} * {fractional} = {partial:.2f}")

    total_deducted = int(round(full_sum + partial))
    print(f"✅ Total Deducted (rounded): {total_deducted}")

    net = gross - (total_deducted + adj)
    print(f"🏁 Final: {gross} - ({total_deducted} + {adj}) = {net}")

    return gross, total_deducted, adj, net
