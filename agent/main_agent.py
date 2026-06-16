import asyncio
from typing import List, Dict

class MainAgent:
    """
    Đây là Agent mẫu sử dụng kiến trúc RAG đơn giản.
    Sinh viên nên thay thế phần này bằng Agent thực tế đã phát triển ở các buổi trước.
    """
    def __init__(self):
        self.name = "SupportAgent-v1"

    def _retrieve_doc_ids(self, question: str) -> List[str]:
        normalized = question.lower()
        ranked_ids = []

        if any(keyword in normalized for keyword in [
            "phạt tù",
            "tử hình",
            "chung thân",
            "tàng trữ",
            "vận chuyển",
            "mua bán",
            "sản xuất",
            "hình phạt",
            "điều 247",
            "điều 248",
            "điều 249",
            "điều 250",
            "điều 251",
            "điều 255",
            "điều 256",
            "điều 258",
            "điều 259",
        ]):
            ranked_ids.append("bo-luat-hinh-su-2015-chuong-xx-toi-pham-ma-tuy")

        if any(keyword in normalized for keyword in [
            "phòng chống",
            "người sử dụng",
            "cai nghiện",
            "xét nghiệm",
            "quản lý người sử dụng",
            "gia đình",
            "cộng đồng",
            "trách nhiệm",
            "luật phòng",
        ]):
            ranked_ids.append("luat-phong-chong-ma-tuy-2021")

        if any(keyword in normalized for keyword in [
            "nghị định 105",
            "hướng dẫn",
            "thi hành luật",
            "cơ sở cai nghiện",
            "thẩm quyền",
            "biểu mẫu",
            "hồ sơ cai nghiện",
        ]):
            ranked_ids.append("nghi-dinh-105-2021-huong-dan-luat-phong-chong-ma-tuy")

        if any(keyword in normalized for keyword in [
            "danh mục",
            "tiền chất",
            "mdma",
            "methamphetamine",
            "ketamine",
            "nghị định 57",
            "chất ma túy",
        ]):
            ranked_ids.append("nghi-dinh-57-2022-danh-muc-chat-ma-tuy")

        fallback_ids = [
            "bo-luat-hinh-su-2015-chuong-xx-toi-pham-ma-tuy",
            "luat-phong-chong-ma-tuy-2021",
            "nghi-dinh-105-2021-huong-dan-luat-phong-chong-ma-tuy",
            "nghi-dinh-57-2022-danh-muc-chat-ma-tuy",
        ]
        for doc_id in fallback_ids:
            if doc_id not in ranked_ids:
                ranked_ids.append(doc_id)

        return ranked_ids[:3]

    async def query(self, question: str) -> Dict:
        """
        Mô phỏng quy trình RAG:
        1. Retrieval: Tìm kiếm context liên quan.
        2. Generation: Gọi LLM để sinh câu trả lời.
        """
        # Giả lập độ trễ mạng/LLM
        await asyncio.sleep(0.5) 
        
        retrieved_ids = self._retrieve_doc_ids(question)

        # Giả lập dữ liệu trả về
        return {
            "answer": f"Dựa trên tài liệu hệ thống, tôi xin trả lời câu hỏi '{question}' như sau: [Câu trả lời mẫu].",
            "contexts": [
                "Đoạn văn bản trích dẫn 1 dùng để trả lời...",
                "Đoạn văn bản trích dẫn 2 dùng để trả lời..."
            ],
            "retrieved_ids": retrieved_ids,
            "metadata": {
                "model": "gpt-4o-mini",
                "tokens_used": 150,
                "cost_usd": 0.00015,
                "sources": ["policy_handbook.pdf"]
            }
        }

if __name__ == "__main__":
    agent = MainAgent()
    async def test():
        resp = await agent.query("Làm thế nào để đổi mật khẩu?")
        print(resp)
    asyncio.run(test())
