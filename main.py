import asyncio
from collections import Counter
import json
import os
import time
from engine.runner import BenchmarkRunner
from engine.retrieval_eval import RetrievalEvaluator
from engine.llm_judge import LLMJudge
from agent.main_agent import MainAgent

DATASET_CANDIDATES = [
    "data/golden_set.json",
    "data/golden_set.jsonl",
    "data/golden_dataset.json",
]

# Giả lập các components Expert
class ExpertEvaluator:
    def __init__(self, top_k: int = 3):
        self.top_k = top_k
        self.retrieval_eval = RetrievalEvaluator()

    async def score(self, case, resp):
        expected_ids = case.get("expected_retrieval_ids", [])
        retrieved_ids = resp.get("retrieved_ids", [])

        hit_rate = 0.0
        mrr = 0.0
        if expected_ids and retrieved_ids:
            hit_rate = self.retrieval_eval.calculate_hit_rate(expected_ids, retrieved_ids, self.top_k)
            mrr = self.retrieval_eval.calculate_mrr(expected_ids, retrieved_ids)

        return {
            "faithfulness": 0.9,
            "relevancy": 0.8,
            "retrieval": {
                "hit_rate": hit_rate,
                "mrr": mrr,
                "top_k": self.top_k,
                "evaluable": bool(expected_ids),
                "expected_ids": expected_ids,
                "retrieved_ids": retrieved_ids,
            },
        }

def resolve_dataset_path(path=None):
    if path:
        return path if os.path.exists(path) else None

    for candidate in DATASET_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return None

def load_dataset(path=None):
    dataset_path = resolve_dataset_path(path)
    if not dataset_path:
        searched = ", ".join(DATASET_CANDIDATES)
        raise FileNotFoundError(f"Không tìm thấy golden dataset. Đã thử: {searched}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        if dataset_path.endswith(".jsonl"):
            return [json.loads(line) for line in f if line.strip()]

        payload = json.load(f)
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("cases", "data", "dataset", "test_cases"):
                if isinstance(payload.get(key), list):
                    return payload[key]

        raise ValueError(f"Dataset không đúng format list cases: {dataset_path}")

def safe_avg(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0

def summarize_results(results, agent_version: str):
    total = len(results)
    pass_count = sum(1 for r in results if r.get("status") == "pass")
    retrieval_scores = [r.get("ragas", {}).get("retrieval", {}) for r in results]
    failure_breakdown = Counter(r.get("error_type") or "none" for r in results if r.get("status") == "fail")

    return {
        "metadata": {
            "version": agent_version,
            "total": total,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "metrics": {
            "avg_score": safe_avg(r.get("judge", {}).get("final_score", 0.0) for r in results),
            "pass_rate": pass_count / total if total else 0.0,
            "hit_rate": safe_avg(item.get("hit_rate", 0.0) for item in retrieval_scores),
            "mrr": safe_avg(item.get("mrr", 0.0) for item in retrieval_scores),
            "retrieval_coverage": safe_avg(1.0 if item.get("evaluable") else 0.0 for item in retrieval_scores),
            "agreement_rate": safe_avg(r.get("judge", {}).get("agreement_rate", 0.0) for r in results),
            "avg_latency": safe_avg(r.get("latency", 0.0) for r in results),
            "total_tokens": sum(r.get("tokens_used", 0) for r in results),
            "total_cost_usd": round(sum(r.get("cost_usd", 0.0) for r in results), 6),
        },
        "failure_breakdown": dict(failure_breakdown),
    }

def decide_release(baseline_summary, candidate_summary):
    baseline = baseline_summary["metrics"]
    candidate = candidate_summary["metrics"]
    score_delta = candidate["avg_score"] - baseline["avg_score"]
    latency_delta = candidate["avg_latency"] - baseline["avg_latency"]
    cost_delta = candidate["total_cost_usd"] - baseline["total_cost_usd"]

    thresholds = {
        "min_avg_score": 3.0,
        "min_hit_rate": 0.8,
        "min_retrieval_coverage": 0.8,
        "min_agreement_rate": 0.7,
        "max_avg_latency": 2.0,
        "max_cost_increase_ratio": 0.3,
    }

    reasons = []
    if score_delta < 0:
        reasons.append("Average score decreased compared with baseline.")
    if candidate["avg_score"] < thresholds["min_avg_score"]:
        reasons.append("Average score is below minimum threshold.")
    if candidate["retrieval_coverage"] < thresholds["min_retrieval_coverage"]:
        reasons.append("Not enough cases include expected_retrieval_ids for retrieval evaluation.")
    if candidate["hit_rate"] < thresholds["min_hit_rate"]:
        reasons.append("Hit Rate is below retrieval quality threshold.")
    if candidate["agreement_rate"] < thresholds["min_agreement_rate"]:
        reasons.append("Judge agreement is below reliability threshold.")
    if candidate["avg_latency"] > thresholds["max_avg_latency"]:
        reasons.append("Average latency is above performance threshold.")

    baseline_cost = baseline["total_cost_usd"]
    if baseline_cost > 0 and cost_delta / baseline_cost > thresholds["max_cost_increase_ratio"]:
        reasons.append("Evaluation cost increased more than allowed.")

    return {
        "baseline_version": baseline_summary["metadata"]["version"],
        "candidate_version": candidate_summary["metadata"]["version"],
        "score_delta": round(score_delta, 4),
        "latency_delta": round(latency_delta, 4),
        "cost_delta_usd": round(cost_delta, 6),
        "thresholds": thresholds,
        "release_decision": "APPROVE" if not reasons else "BLOCK_RELEASE",
        "reasons": reasons,
    }

async def run_benchmark_with_results(agent_version: str):
    print(f"🚀 Khởi động Benchmark cho {agent_version}...")

    dataset_path = resolve_dataset_path()
    if not dataset_path:
        searched = ", ".join(DATASET_CANDIDATES)
        print(f"❌ Thiếu golden dataset. Hãy tạo một trong các file: {searched}")
        return None, None

    dataset = load_dataset(dataset_path)

    if not dataset:
        print(f"❌ File {dataset_path} rỗng. Hãy tạo ít nhất 1 test case.")
        return None, None

    runner = BenchmarkRunner(MainAgent(), ExpertEvaluator(), LLMJudge())
    results = await runner.run_all(dataset)
    summary = summarize_results(results, agent_version)
    return results, summary

async def run_benchmark(version):
    _, summary = await run_benchmark_with_results(version)
    return summary

async def main():
    v1_summary = await run_benchmark("Agent_V1_Base")

    # Giả lập V2 có cải tiến (để test logic)
    v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized")

    if not v1_summary or not v2_summary:
        print("❌ Không thể chạy Benchmark. Kiểm tra lại golden dataset.")
        return

    regression = decide_release(v1_summary, v2_summary)
    v2_summary["regression"] = regression

    print("\n📊 --- KẾT QUẢ SO SÁNH (REGRESSION) ---")
    print(f"V1 Score: {v1_summary['metrics']['avg_score']}")
    print(f"V2 Score: {v2_summary['metrics']['avg_score']}")
    print(f"Delta: {'+' if regression['score_delta'] >= 0 else ''}{regression['score_delta']:.2f}")
    print(f"Hit Rate: {v2_summary['metrics']['hit_rate']:.2f}")
    print(f"MRR: {v2_summary['metrics']['mrr']:.2f}")
    print(f"Agreement Rate: {v2_summary['metrics']['agreement_rate']:.2f}")
    print(f"Avg Latency: {v2_summary['metrics']['avg_latency']:.2f}s")
    print(f"Total Tokens: {v2_summary['metrics']['total_tokens']}")
    print(f"Total Cost: ${v2_summary['metrics']['total_cost_usd']:.6f}")

    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    if regression["release_decision"] == "APPROVE":
        print("✅ QUYẾT ĐỊNH: CHẤP NHẬN BẢN CẬP NHẬT (APPROVE)")
    else:
        print("❌ QUYẾT ĐỊNH: TỪ CHỐI (BLOCK RELEASE)")
        for reason in regression["reasons"]:
            print(f"   - {reason}")

if __name__ == "__main__":
    asyncio.run(main())
