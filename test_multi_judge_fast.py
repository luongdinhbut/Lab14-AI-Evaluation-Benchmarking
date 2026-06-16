#!/usr/bin/env python3
"""
Fast test script - Mock Mode (< 1 second)
Chạy: python test_multi_judge_fast.py
"""

import asyncio
from dotenv import load_dotenv
from engine.llm_judge import LLMJudge


async def test_mock_judges_directly():
    """Test mock judges directly - bypass API calls completely"""
    load_dotenv()
    
    print("=" * 70)
    print("⚡ FAST TEST - DIRECT MOCK MODE (< 1 second)")
    print("=" * 70)
    
    judge = LLMJudge()
    print(f"\n📊 Provider Detected: {judge.provider.upper()}")
    print(f"   (Will use MOCK judges for instant testing)\n")
    
    test_cases = [
        {
            "name": "Good Answer",
            "question": "Người trồng cây cần sa bị phạt tù bao lâu?",
            "answer": "Bị phạt tù từ 03 năm đến 07 năm.",
            "ground_truth": "Bị phạt tù từ 03 năm đến 07 năm.",
        },
        {
            "name": "Partial Answer",
            "question": "Hình phạt cao nhất tội sản xuất ma túy?",
            "answer": "Tù 20 năm hoặc tù chung thân.",
            "ground_truth": "Phạt tù 20 năm, tù chung thân hoặc tử hình.",
        },
        {
            "name": "Bad Answer",
            "question": "Người sử dụng ma túy lần đầu bị phạt?",
            "answer": "Có, luôn bị phạt tù.",
            "ground_truth": "Không, được giáo dục tại gia đình.",
        },
    ]
    
    print("=" * 70)
    print("📋 TESTING CASES (Direct Mock - No API)")
    print("=" * 70)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n[Case {i}] {case['name']}")
        print(f"Q: {case['question']}")
        print(f"A: {case['answer']}")
        
        # Call mock judges DIRECTLY, no API
        mock_a = judge._mock_judge(
            judge.model_a,
            case["question"],
            case["answer"],
            case["ground_truth"]
        )
        mock_b = judge._mock_judge(
            judge.model_b,
            case["question"],
            case["answer"],
            case["ground_truth"]
        )
        
        scores = [mock_a["score"], mock_b["score"]]
        final_score = sum(scores) / len(scores)
        agreement = judge._agreement_rate(scores)
        
        print(f"\n✅ Results (Mock):")
        print(f"   Final Score: {final_score:.2f}/5.0")
        print(f"   Agreement Rate: {agreement:.2f}")
        print(f"   Model A ({judge.model_a.split('/')[-1]}): {mock_a['score']:.2f}")
        print(f"   Model B ({judge.model_b.split('/')[-1]}): {mock_b['score']:.2f}")
        print(f"   Spread: {max(scores) - min(scores):.1f}")

async def test_agreement_formula():
    """Test Agreement Rate formula"""
    print("\n" + "=" * 70)
    print("📏 AGREEMENT RATE FORMULA TEST")
    print("=" * 70)
    
    judge = LLMJudge()
    
    scenarios = [
        ([5.0, 5.0], 1.00, "Perfect match"),
        ([4.0, 5.0], 0.75, "Spread=1"),
        ([3.0, 5.0], 0.50, "Spread=2"),
        ([1.0, 5.0], 0.00, "Spread=4"),
    ]
    
    print("\nFormula: max(0.0, 1.0 - spread/4.0)")
    print("-" * 70)
    
    all_pass = True
    for scores, expected, desc in scenarios:
        actual = judge._agreement_rate(scores)
        spread = max(scores) - min(scores)
        matches = abs(actual - expected) < 0.01
        status = "✅" if matches else "❌"
        all_pass = all_pass and matches
        print(f"{status} {desc:20s} | Scores: {scores} | Spread: {spread} | Rate: {actual:.2f} (expected: {expected:.2f})")
    
    return all_pass


if __name__ == "__main__":
    print("\n🚀 Fast Test Mode - Direct Mock Judges\n")
    asyncio.run(test_mock_judges_directly())
    formula_ok = asyncio.run(test_agreement_formula())
    
    print("\n" + "=" * 70)
    if formula_ok:
        print("✅ All tests PASSED! (< 1 second)")
    else:
        print("⚠️ Some formula tests failed")
    print("=" * 70 + "\n")
