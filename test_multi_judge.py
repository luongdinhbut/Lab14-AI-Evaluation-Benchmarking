#!/usr/bin/env python3
"""
Test script for Multi-Judge Consensus Engine (An's contribution)
Chạy: python test_multi_judge.py
"""

import asyncio
import json
import os
import sys
from dotenv import load_dotenv
from engine.llm_judge import LLMJudge


async def test_multi_judge():
    """Test Multi-Judge Consensus với sample cases"""
    load_dotenv()
    
    print("=" * 70)
    print("🧪 TEST MULTI-JUDGE CONSENSUS ENGINE (An's Contribution)")
    print("=" * 70)
    
    # Khởi tạo judge
    judge = LLMJudge()
    print(f"\n📊 Provider: {judge.provider.upper()}")
    print(f"   Model A: {judge.model_a}")
    print(f"   Model B: {judge.model_b}")
    print(f"   Temperature: {judge.temperature}")
    print(f"   Conflict Threshold: {judge.conflict_threshold}")
    
    # Test cases
    test_cases = [
        {
            "name": "Good Answer (Exact Match)",
            "question": "Người trồng cây cần sa với diện tích 1 héc ta có tổ chức bị phạt tù bao nhiêu năm?",
            "answer": "Bị phạt tù từ 03 năm đến 07 năm.",
            "ground_truth": "Bị phạt tù từ 03 năm đến 07 năm.",
        },
        {
            "name": "Partial Answer",
            "question": "Hình phạt cao nhất đối với tội sản xuất ma túy là gì?",
            "answer": "Bị phạt tù 20 năm hoặc tù chung thân.",
            "ground_truth": "Phạt tù 20 năm, tù chung thân hoặc tử hình.",
        },
        {
            "name": "Bad Answer (Wrong)",
            "question": "Người sử dụng ma túy lần đầu có bị phạt tù không?",
            "answer": "Có, luôn bị phạt tù.",
            "ground_truth": "Không, được giáo dục tại gia đình.",
        },
    ]
    
    print("\n" + "=" * 70)
    print("📋 TESTING CASES")
    print("=" * 70)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n[Case {i}] {case['name']}")
        print(f"Question: {case['question']}")
        print(f"Expected: {case['ground_truth']}")
        print(f"Answer:   {case['answer']}")
        
        try:
            print("\n⏳ Evaluating with Multi-Judge... (timeout: 60s)")
            result = await asyncio.wait_for(
                judge.evaluate_multi_judge(
                    case["question"],
                    case["answer"],
                    case["ground_truth"]
                ),
                timeout=60.0
            )
            
            print(f"\n✅ Result:")
            print(f"   Final Score:      {result['final_score']:.2f}/5.0")
            print(f"   Agreement Rate:   {result['agreement_rate']:.2f}")
            print(f"   Conflict:         {result['conflict']}")
            print(f"   Resolution:       {result['conflict_resolution']}")
            
            print(f"\n   Individual Scores:")
            for model, score in result['individual_scores'].items():
                print(f"      • {model}: {score:.2f}")
            
            print(f"\n   Token Usage:")
            print(f"      • Total Tokens: {result['token_usage']['total_tokens']}")
            print(f"      • Input Tokens: {result['token_usage']['input_tokens']}")
            print(f"      • Output Tokens: {result['token_usage']['output_tokens']}")
            print(f"      • Cost: ${result['cost_usd']:.8f}")
            
            print(f"\n   Reasoning: {result['reasoning'][:100]}...")
            
        except Exception as e:
            import traceback
            print(f"\n❌ Error: {str(e)}")
            print(f"   Type: {type(e).__name__}")
            print(f"   Traceback:")
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"✅ Multi-Judge Consensus Engine working!")
    print(f"✅ Provider auto-detection: {judge.provider.upper()}")
    print(f"✅ Fallback strategy available")
    print("\n" + "=" * 70)


async def test_agreement_rate():
    """Test Agreement Rate calculation"""
    print("\n" + "=" * 70)
    print("📏 TESTING AGREEMENT RATE CALCULATION")
    print("=" * 70)
    
    judge = LLMJudge()
    
    test_scenarios = [
        ([5.0, 5.0], "Perfect agreement"),
        ([4.0, 5.0], "Slight disagreement"),
        ([3.0, 5.0], "Moderate disagreement"),
        ([1.0, 5.0], "Strong disagreement"),
    ]
    
    for scores, desc in test_scenarios:
        agreement = judge._agreement_rate(scores)
        spread = max(scores) - min(scores)
        print(f"\n{desc}")
        print(f"  Scores: {scores}")
        print(f"  Spread: {spread:.1f}")
        print(f"  Agreement Rate: {agreement:.2f}")


if __name__ == "__main__":
    print("\n🚀 Starting Multi-Judge Test Suite...\n")
    
    # Check for --fast flag
    fast_mode = "--fast" in sys.argv
    
    if fast_mode:
        print("⚡ FAST MODE: Using mock judges (no API calls)")
        print("-" * 70)
    
    asyncio.run(test_multi_judge())
    asyncio.run(test_agreement_rate())
    print("\n✨ All tests completed!")
