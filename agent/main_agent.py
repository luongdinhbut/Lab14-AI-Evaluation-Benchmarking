import asyncio
from typing import List, Dict

class MainAgent:
    """
    Đây là Agent mẫu sử dụng kiến trúc RAG đơn giản.
    Sinh viên nên thay thế phần này bằng Agent thực tế đã phát triển ở các buổi trước.
    """
    def __init__(self):
        self.name = "SupportAgent-v1"

    async def query(self, question: str) -> Dict:
        """
        Mô phỏng quy trình RAG:
        1. Retrieval: Tìm kiếm context liên quan.
        2. Generation: Gọi LLM để sinh câu trả lời.
        """
        # Giả lập độ trễ mạng/LLM
        await asyncio.sleep(0.5) 
        
        # Simple keyword matching to simulate retrieval
        q_lower = question.lower()
        retrieved_ids = []
        if "tù" in q_lower or "hình phạt" in q_lower or "điều 247" in q_lower or "điều 248" in q_lower or "điều 249" in q_lower or "điều 250" in q_lower or "tàng trữ" in q_lower or "vận chuyển" in q_lower or "mua bán" in q_lower:
            retrieved_ids.append("bo-luat-hinh-su-2015-chuong-xx-toi-pham-ma-tuy")
        if "danh mục" in q_lower or "thuốc phiện" in q_lower or "cần sa" in q_lower or "ketamine" in q_lower or "nghị định 57" in q_lower or "fentanyl" in q_lower or "heroin" in q_lower:
            retrieved_ids.append("nghi-dinh-57-2022-danh-muc-chat-ma-tuy")
        if "cai nghiện" in q_lower or "thanh thiếu niên" in q_lower or "luật phòng" in q_lower or "xác định tình trạng nghiện" in q_lower or "trách nhiệm" in q_lower:
            retrieved_ids.append("luat-phong-chong-ma-tuy-2021")
        if "thuốc gây nghiện" in q_lower or "nghị định 105" in q_lower or "tiền chất" in q_lower or "cơ sở" in q_lower:
            retrieved_ids.append("nghi-dinh-105-2021-huong-dan-luat-phong-chong-ma-tuy")
            
        # Fallback if no match
        if not retrieved_ids:
            retrieved_ids = ["bo-luat-hinh-su-2015-chuong-xx-toi-pham-ma-tuy", "luat-phong-chong-ma-tuy-2021"]

        return {
            "answer": f"Dựa trên tài liệu hệ thống, tôi xin trả lời câu hỏi '{question}' như sau: [Câu trả lời mẫu].",
            "contexts": [
                "Đoạn văn bản trích dẫn 1 dùng để trả lời...",
                "Đoạn văn bản trích dẫn 2 dùng để trả lời..."
            ],
            "retrieved_ids": retrieved_ids,
            "metadata": {
                "model": "gpt-5.4-mini",
                "tokens_used": 150,
                "retrieved_ids": retrieved_ids,
                "cost_usd": 0.001
            }
        }

if __name__ == "__main__":
    agent = MainAgent()
    async def test():
        resp = await agent.query("Làm thế nào để đổi mật khẩu?")
        print(resp)
    asyncio.run(test())
