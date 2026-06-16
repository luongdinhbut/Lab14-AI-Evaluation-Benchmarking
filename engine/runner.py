import asyncio
import time
from typing import Any, Dict, List, Optional

class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge

    @staticmethod
    def _usage_from_response(response: Dict[str, Any]) -> Dict[str, Any]:
        metadata = response.get("metadata", {}) if isinstance(response, dict) else {}
        return {
            "model": metadata.get("model", "unknown"),
            "tokens_used": int(metadata.get("tokens_used", metadata.get("total_tokens", 0)) or 0),
            "cost_usd": float(metadata.get("cost_usd", 0.0) or 0.0),
        }

    @staticmethod
    def _default_ragas() -> Dict[str, Any]:
        return {
            "faithfulness": 0.0,
            "relevancy": 0.0,
            "retrieval": {"hit_rate": 0.0, "mrr": 0.0},
        }

    @staticmethod
    def _default_judge(reasoning: str = "Evaluation failed.") -> Dict[str, Any]:
        return {
            "final_score": 0.0,
            "agreement_rate": 0.0,
            "individual_scores": {},
            "reasoning": reasoning,
        }

    @staticmethod
    def _classify_error(test_case: Dict[str, Any], ragas_scores: Dict[str, Any], judge_result: Dict[str, Any]) -> Optional[str]:
        score = float(judge_result.get("final_score", 0.0) or 0.0)
        expected_ids = test_case.get("expected_retrieval_ids", [])
        retrieval = ragas_scores.get("retrieval", {})

        if score >= 3:
            return None
        if expected_ids and retrieval.get("hit_rate", 0.0) == 0.0:
            return "retrieval_miss"
        return "low_judge_score"

    async def run_single_test(self, test_case: Dict, case_index: Optional[int] = None) -> Dict:
        start_time = time.perf_counter()
        case_id = test_case.get("id") or f"case_{(case_index or 0) + 1:03d}"
        question = test_case.get("question", "")
        expected_answer = test_case.get("expected_answer", "")
        response: Dict[str, Any] = {}

        try:
            response = await self.agent.query(question)
            latency = time.perf_counter() - start_time
            usage = self._usage_from_response(response)

            ragas_scores = await self.evaluator.score(test_case, response)
            judge_result = await self.judge.evaluate_multi_judge(
                question,
                response.get("answer", ""),
                expected_answer,
            )
            judge_tokens_used = int(judge_result.get("tokens_used", 0) or 0)
            judge_cost_usd = float(judge_result.get("cost_usd", 0.0) or 0.0)

            error_type = self._classify_error(test_case, ragas_scores, judge_result)
            status = "fail" if error_type else "pass"

            return {
                "test_case_id": case_id,
                "test_case": question,
                "question": question,
                "expected_answer": expected_answer,
                "agent_response": response.get("answer", ""),
                "contexts": response.get("contexts", []),
                "retrieved_ids": response.get("retrieved_ids", []),
                "latency": latency,
                "agent_tokens_used": usage["tokens_used"],
                "judge_tokens_used": judge_tokens_used,
                "tokens_used": usage["tokens_used"] + judge_tokens_used,
                "agent_cost_usd": usage["cost_usd"],
                "judge_cost_usd": judge_cost_usd,
                "cost_usd": usage["cost_usd"] + judge_cost_usd,
                "model": usage["model"],
                "ragas": ragas_scores,
                "judge": judge_result,
                "status": status,
                "error_type": error_type,
            }
        except Exception as exc:
            latency = time.perf_counter() - start_time
            usage = self._usage_from_response(response)

            return {
                "test_case_id": case_id,
                "test_case": question,
                "question": question,
                "expected_answer": expected_answer,
                "agent_response": response.get("answer", "") if isinstance(response, dict) else "",
                "contexts": response.get("contexts", []) if isinstance(response, dict) else [],
                "retrieved_ids": response.get("retrieved_ids", []) if isinstance(response, dict) else [],
                "latency": latency,
                "agent_tokens_used": usage["tokens_used"],
                "judge_tokens_used": 0,
                "tokens_used": usage["tokens_used"],
                "agent_cost_usd": usage["cost_usd"],
                "judge_cost_usd": 0.0,
                "cost_usd": usage["cost_usd"],
                "model": usage["model"],
                "ragas": self._default_ragas(),
                "judge": self._default_judge(str(exc)),
                "status": "fail",
                "error_type": "exception",
                "error_message": str(exc),
            }

    async def run_all(self, dataset: List[Dict], batch_size: int = 5) -> List[Dict]:
        """
        Chạy song song bằng asyncio.gather với giới hạn batch_size để không bị Rate Limit.
        """
        results = []
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i + batch_size]
            tasks = [self.run_single_test(case, i + offset) for offset, case in enumerate(batch)]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        return results
