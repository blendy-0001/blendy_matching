#!/usr/bin/env python3
"""
In-memory matching simulation
Validates matching accuracy using test data without Notion API dependency

Usage: python test_matching_simulation_en.py
"""

import sys
import re
from typing import Set

# ── Test Members (In-memory) ────────────────────────────
TEST_MEMBERS = [
    {
        "name": "Member_A (SaaS Dev)",
        "company": "TechVenture Inc.",
        "category": "SaaS / IT",
        "phase": "Growth",
        "industries": {"Healthcare", "Finance", "Education"},
        "strengths": ["Web Development", "API Design", "Database Architecture"],
        "issues": ["Sales", "Marketing", "Customer Support"],
        "positions": ["CTO", "Engineering"],
        "company_sizes": ["Startup", "Mid-market"],
        "service_keywords": "Custom Web Development API Integration Cloud Infrastructure",
    },
    {
        "name": "Member_B (Sales & Marketing)",
        "company": "GrowthMarketing Co.",
        "category": "Sales / Marketing",
        "phase": "Growth",
        "industries": {"SaaS", "Finance", "Real Estate"},
        "strengths": ["Sales", "Marketing", "Lead Generation", "Business Development"],
        "issues": ["System Development", "Technical Support"],
        "positions": ["Sales", "Marketing"],
        "company_sizes": ["Startup", "Enterprise"],
        "service_keywords": "Sales Support Marketing Lead Generation Business Development",
    },
    {
        "name": "Member_C (DB Optimization)",
        "company": "DataOptimize Ltd.",
        "category": "Infrastructure / Operations",
        "phase": "Mature",
        "industries": {"Finance", "eCommerce", "Healthcare"},
        "strengths": ["Database", "System Operations", "Performance Tuning", "Security"],
        "issues": ["Sales Strategy", "Market Expansion"],
        "positions": ["CTO", "Operations", "Security"],
        "company_sizes": ["Mid-market", "Enterprise"],
        "service_keywords": "Database Optimization Performance Tuning Security Audit",
    },
    {
        "name": "Member_D (Branding Design)",
        "company": "BrandLab Design.",
        "category": "Branding / Design",
        "phase": "Growth",
        "industries": {"SaaS", "Fashion", "Food & Beverage"},
        "strengths": ["UI/UX Design", "Branding", "Creative"],
        "issues": ["Sales", "Technical Support", "Marketing Implementation"],
        "positions": ["Designer", "Product Manager"],
        "company_sizes": ["Startup", "Mid-market"],
        "service_keywords": "UI Design Branding Logo Design Brand Identity",
    },
    {
        "name": "Member_E (Sales & BD)",
        "company": "BusinessGrowth Partners.",
        "category": "Sales / Business Development",
        "phase": "Growth",
        "industries": {"SaaS", "Healthcare", "Education", "Finance"},
        "strengths": ["Sales", "Business Development", "Partnerships", "Network"],
        "issues": ["System Development", "Technical Knowledge", "Operations"],
        "positions": ["Sales", "Business Development"],
        "company_sizes": ["Startup", "Mid-market", "Enterprise"],
        "service_keywords": "Sales Support Business Development Partner Matching",
    },
    {
        "name": "Member_F (AI/Data Science)",
        "company": "AI Research Labs.",
        "category": "AI / Data Science",
        "phase": "Growth",
        "industries": {"Healthcare", "Finance", "Manufacturing"},
        "strengths": ["Machine Learning", "Data Analysis", "AI Model Development"],
        "issues": ["Sales", "Marketing", "Productization"],
        "positions": ["Data Scientist", "Engineering"],
        "company_sizes": ["Enterprise"],
        "service_keywords": "Machine Learning Data Analytics AI Implementation",
    },
]


def _text_overlap(text1: str, text2: str, min_overlap: int = 1) -> bool:
    """Check if two text strings have common words"""
    if not text1 or not text2:
        return False

    words1 = set(re.split(r'[\s,;.]+', text1.lower().strip()))
    words2 = set(re.split(r'[\s,;.]+', text2.lower().strip()))

    words1.discard('')
    words2.discard('')

    words1 = {w for w in words1 if len(w) >= 2}
    words2 = {w for w in words2 if len(w) >= 2}

    overlap_count = len(words1 & words2)
    return overlap_count >= min_overlap


def _calc_client_fit(a: dict, b: dict) -> int:
    """Client Fit (0-20 pts) - Industry and customer alignment"""
    score = 0

    # Industry overlap
    a_industries = a.get("industries", set())
    b_industries = b.get("industries", set())
    if a_industries & b_industries:
        score += 4

    # Category match
    if a.get("category") and a.get("category") == b.get("category"):
        score += 3

    # Company size compatibility
    a_sizes = set(a.get("company_sizes", []))
    b_sizes = set(b.get("company_sizes", []))
    if a_sizes & b_sizes:
        score += 2

    # Win-Win bidirectional assessment
    a_strengths_text = " ".join(a.get("strengths", []))
    a_issues_text = " ".join(a.get("issues", []))
    b_strengths_text = " ".join(b.get("strengths", []))
    b_issues_text = " ".join(b.get("issues", []))

    a_helps_b = b_issues_text and a_strengths_text and _text_overlap(a_strengths_text, b_issues_text)
    b_helps_a = a_issues_text and b_strengths_text and _text_overlap(b_strengths_text, a_issues_text)

    if a_helps_b and b_helps_a:
        score += 8
    elif a_helps_b or b_helps_a:
        score += 3

    return min(score, 20)


def _calc_chain_fit(a: dict, b: dict) -> int:
    """Value Chain Connectivity (0-20 pts) - Position complementarity"""
    score = 0

    a_positions = set(a.get("positions", []))
    b_positions = set(b.get("positions", []))

    if not a_positions or not b_positions:
        return 0

    complementary_pairs = [
        ("Sales", "Engineering"),
        ("Sales", "Product Manager"),
        ("Sales", "Engineering"),
        ("Product Manager", "Engineering"),
        ("Marketing", "Sales"),
        ("Marketing", "Engineering"),
        ("CTO", "Sales"),
        ("CTO", "Engineering"),
        ("Business Development", "Engineering"),
        ("Operations", "Engineering"),
    ]

    has_complementary = False
    for pos1, pos2 in complementary_pairs:
        if (pos1 in a_positions and pos2 in b_positions) or (pos2 in a_positions and pos1 in b_positions):
            has_complementary = True
            break

    if has_complementary:
        score += 15

    if a_positions != b_positions and (a_positions | b_positions):
        score += 5

    return min(score, 20)


def _calc_market_fit(a: dict, b: dict) -> int:
    """Market Solution Fit (0-20 pts) - Technical x Market complementarity"""
    score = 0

    a_strengths = set(a.get("strengths", []))
    b_strengths = set(b.get("strengths", []))
    a_issues = set(a.get("issues", []))
    b_issues = set(b.get("issues", []))

    solution_keywords = ["Development", "Technology", "System", "API", "Database", "Design"]
    market_keywords = ["Sales", "Marketing", "Business", "Network", "Customer", "Partnerships"]

    a_has_solution = any(kw in strength for strength in a_strengths for kw in solution_keywords)
    b_has_solution = any(kw in strength for strength in b_strengths for kw in solution_keywords)
    a_has_market = any(kw in strength for strength in a_strengths for kw in market_keywords)
    b_has_market = any(kw in strength for strength in b_strengths for kw in market_keywords)

    a_needs_solution = any(kw in issue for issue in a_issues for kw in solution_keywords)
    b_needs_solution = any(kw in issue for issue in b_issues for kw in solution_keywords)
    a_needs_market = any(kw in issue for issue in a_issues for kw in market_keywords)
    b_needs_market = any(kw in issue for issue in b_issues for kw in market_keywords)

    if (a_has_solution and b_needs_solution and b_has_market and a_needs_market) or \
       (b_has_solution and a_needs_solution and a_has_market and b_needs_market):
        score = 20
    elif (a_has_solution and b_has_market) or (b_has_solution and a_has_market):
        score = 15
    elif a_has_solution or b_has_solution or a_has_market or b_has_market:
        score = 8

    return min(score, 20)


def _calc_expansion_potential(a: dict, b: dict) -> int:
    """Expansion Potential (0-20 pts) - Growth synergy"""
    score = 0

    a_strengths = set(a.get("strengths", []))
    b_strengths = set(b.get("strengths", []))
    a_issues = set(a.get("issues", []))
    b_issues = set(b.get("issues", []))

    a_addresses_b = any(kw in strength for strength in a_strengths for kw in b_issues)
    b_addresses_a = any(kw in strength for strength in b_strengths for kw in a_issues)

    if a_addresses_b or b_addresses_a:
        score += 12

    a_phase = a.get("phase", "")
    b_phase = b.get("phase", "")

    if a_phase in ["Growth", "Expansion"] and b_phase in ["Growth", "Expansion"]:
        score += 5
    elif a_phase == "Mature" and b_phase in ["Growth", "Expansion"]:
        score += 3

    return min(score, 20)


def _calc_target_market_fit(a: dict, b: dict) -> int:
    """Target Market Alignment (0-20 pts) - Service overlap"""
    score = 0

    a_service = a.get("service_keywords", "")
    b_service = b.get("service_keywords", "")

    if _text_overlap(a_service, b_service):
        score += 10

    a_industries = a.get("industries", set())
    b_industries = b.get("industries", set())

    if len(a_industries & b_industries) >= 2:
        score += 10

    return min(score, 20)


def score_pair(a: dict, b: dict) -> dict:
    """Score a matching pair"""
    scores = {
        "Client Fit": _calc_client_fit(a, b),
        "Value Chain": _calc_chain_fit(a, b),
        "Market Fit": _calc_market_fit(a, b),
        "Expansion": _calc_expansion_potential(a, b),
        "Target Market": _calc_target_market_fit(a, b),
    }

    total_score = min(sum(scores.values()), 100)

    return {
        "Member_A": a["name"],
        "Member_B": b["name"],
        "Score": total_score,
        "Breakdown": scores,
    }


def run_simulation():
    """Run in-memory simulation"""
    print("\n" + "="*70)
    print("[MATCHING ACCURACY SIMULATION]")
    print("="*70)
    print(f"\nTest Members: {len(TEST_MEMBERS)}")
    for i, member in enumerate(TEST_MEMBERS, 1):
        print(f"  {i}. {member['name']} ({member['company']})")

    # Generate pairs
    pairs = []
    for i, a in enumerate(TEST_MEMBERS):
        for b in TEST_MEMBERS[i+1:]:
            pairs.append((a, b))

    print(f"\nTotal Pairs Generated: {len(pairs)}\n")

    # Score all pairs
    results = []
    for a, b in pairs:
        result = score_pair(a, b)
        results.append(result)

    # Sort by score descending
    results.sort(key=lambda x: -x["Score"])

    # Distribute analysis
    min_score = 45
    high_quality = [r for r in results if r["Score"] >= 75]
    medium_quality = [r for r in results if 60 <= r["Score"] < 75]
    low_quality = [r for r in results if min_score <= r["Score"] < 60]
    below_min = [r for r in results if r["Score"] < min_score]

    print("\n[SCORE DISTRIBUTION]")
    print(f"  High Quality (75+)      : {len(high_quality)} pairs ({100*len(high_quality)//len(results)}%)")
    print(f"  Medium Quality (60-74)  : {len(medium_quality)} pairs ({100*len(medium_quality)//len(results)}%)")
    print(f"  Low Quality (45-59)     : {len(low_quality)} pairs ({100*len(low_quality)//len(results)}%)")
    print(f"  Below Min (<45)         : {len(below_min)} pairs ({100*len(below_min)//len(results)}%)")

    acceptance_rate = (len(high_quality) + len(medium_quality) + len(low_quality)) / len(results) * 100
    print(f"\n  [OK] Matching acceptance rate (>= 45pts): {acceptance_rate:.1f}%")

    # Display detailed results
    print("\n[TOP MATCHING RESULTS (by score)]")
    print("-" * 70)

    for i, result in enumerate(results[:12], 1):
        print(f"\n{i}. {result['Member_A']} x {result['Member_B']}")
        print(f"   Score: {result['Score']} pts")
        print(f"   Breakdown: ", end="")
        items = [f"{k}={v}pts" for k, v in result["Breakdown"].items()]
        print(", ".join(items))

        # Win-Win assessment
        a = next(m for m in TEST_MEMBERS if m["name"] == result["Member_A"])
        b = next(m for m in TEST_MEMBERS if m["name"] == result["Member_B"])

        a_strengths_text = " ".join(a.get("strengths", []))
        a_issues_text = " ".join(a.get("issues", []))
        b_strengths_text = " ".join(b.get("strengths", []))
        b_issues_text = " ".join(b.get("issues", []))

        a_helps_b = b_issues_text and a_strengths_text and _text_overlap(a_strengths_text, b_issues_text)
        b_helps_a = a_issues_text and b_strengths_text and _text_overlap(b_strengths_text, a_issues_text)

        if a_helps_b and b_helps_a:
            print(f"   Win-Win: [OK] Mutual complementarity")
        elif a_helps_b or b_helps_a:
            print(f"   Win-Win: [--] Unidirectional complementarity")
        else:
            print(f"   Win-Win: [NO] No complementarity")

    print("\n" + "="*70)
    print("[QUALITY SUMMARY]")
    print("="*70)
    print(f"[A] High Quality (75+)  : {len(high_quality):2d} pairs - Ready for intro")
    print(f"[B] Medium Quality (60-74): {len(medium_quality):2d} pairs - Review then intro")
    print(f"[C] Low Quality (45-59) : {len(low_quality):2d} pairs - Latent synergy target")
    print(f"[X] Below Min (<45)     : {len(below_min):2d} pairs - Filtered out")
    print(f"\nTarget: High > 40%, Medium > 30%")
    print(f"Result: High {100*len(high_quality)//len(results)}%, Medium {100*len(medium_quality)//len(results)}%")

    if len(high_quality) > len(results) * 0.4:
        print("\n[VERDICT] Matching accuracy is EXCELLENT")
    elif len(high_quality) + len(medium_quality) > len(results) * 0.7:
        print("\n[VERDICT] Matching accuracy is GOOD")
    else:
        print("\n[VERDICT] Matching accuracy needs improvement")


if __name__ == "__main__":
    run_simulation()
