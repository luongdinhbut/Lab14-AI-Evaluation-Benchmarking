from typing import List, Dict

class RetrievalEvaluator:
    def __init__(self):
        pass

    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3) -> float:
        """
        TODO: Tính toán xem ít nhất 1 trong expected_ids có nằm trong top_k của retrieved_ids không.
        """
        top_retrieved = retrieved_ids[:top_k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        """
        TODO: Tính Mean Reciprocal Rank.
        Tìm vị trí đầu tiên của một expected_id trong retrieved_ids.
        MRR = 1 / position (vị trí 1-indexed). Nếu không thấy thì là 0.
        """
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    async def score(self, test_case: Dict, agent_response: Dict) -> Dict:
        """
        Đánh giá Retrieval cho 1 test case.
        """
        expected_ids = test_case.get("expected_retrieval_ids", [])
        # Lấy retrieved_ids từ agent metadata, fallback là danh sách rỗng
        metadata = agent_response.get("metadata", {})
        retrieved_ids = metadata.get("retrieved_ids", [])
        
        hit_rate = self.calculate_hit_rate(expected_ids, retrieved_ids)
        mrr = self.calculate_mrr(expected_ids, retrieved_ids)
        
        return {
            "retrieval": {
                "hit_rate": hit_rate,
                "mrr": mrr
            }
        }

    async def evaluate_batch(self, dataset: List[Dict], agent_responses: List[Dict]) -> Dict:
        """
        Chạy eval cho toàn bộ bộ dữ liệu.
        """
        if not dataset or not agent_responses or len(dataset) != len(agent_responses):
            return {"avg_hit_rate": 0.0, "avg_mrr": 0.0}

        total_hit_rate = 0.0
        total_mrr = 0.0
        
        for case, resp in zip(dataset, agent_responses):
            score_res = await self.score(case, resp)
            total_hit_rate += score_res["retrieval"]["hit_rate"]
            total_mrr += score_res["retrieval"]["mrr"]
            
        n = len(dataset)
        return {
            "avg_hit_rate": total_hit_rate / n,
            "avg_mrr": total_mrr / n
        }
