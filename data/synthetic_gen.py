import json
import asyncio
import os
from typing import List, Dict
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

async def generate_qa_from_text(text: str, num_pairs: int = 50) -> List[Dict]:
    """
    Sử dụng OpenAI API để tạo các cặp (Question, Expected Answer, Context)
    từ đoạn văn bản cho trước.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key == "mock" or api_key == "":
        print("⚠️ Không tìm thấy OPENAI_API_KEY hợp lệ. Đang tạo dữ liệu giả lập (Mock Data).")
        return generate_mock_data(num_pairs)

    client = AsyncOpenAI(api_key=api_key)
    print(f"Calling OpenAI API to generate {num_pairs} QA pairs...")
    
    prompt = f"""Bạn là chuyên gia tạo bộ dữ liệu đánh giá AI (Golden Dataset).
Dựa vào đoạn văn bản sau, hãy tạo ra {num_pairs} cặp (Câu hỏi, Câu trả lời kỳ vọng).
Bao gồm cả những câu hỏi khó, lừa (adversarial).

Văn bản: {text[:1000]}

Định dạng đầu ra BẮT BUỘC là 1 JSON Object chứa 1 key là "dataset". Key "dataset" là 1 mảng chứa {num_pairs} object, mỗi object có cấu trúc:
{{
  "question": "nội dung câu hỏi",
  "expected_answer": "câu trả lời chi tiết",
  "expected_retrieval_ids": ["doc_1", "doc_2"],
  "metadata": {{"difficulty": "easy/medium/hard", "type": "reasoning/fact-check"}}
}}
KHÔNG IN THÊM BẤT KỲ VĂN BẢN NÀO BÊN NGOÀI JSON!
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={ "type": "json_object" }
        )
        content = response.choices[0].message.content.strip()
        data = json.loads(content)
        
        dataset = data.get("dataset", [])
        if len(dataset) > 0:
            return dataset
            
    except Exception as e:
        print(f"❌ Lỗi khi sinh dữ liệu từ OpenAI: {e}")
        print("Đang fallback sang tạo Mock Data...")
        
    return generate_mock_data(num_pairs)

def generate_mock_data(num_pairs: int) -> List[Dict]:
    return [
        {
            "question": f"Câu hỏi đánh giá tự động số {i+1}?",
            "expected_answer": f"Câu trả lời chính xác, chi tiết cho câu hỏi {i+1}.",
            "expected_retrieval_ids": [f"doc_{i%5}"],
            "metadata": {"difficulty": "medium", "type": "fact-check"}
        } for i in range(num_pairs)
    ]

async def main():
    raw_text = "AI Evaluation là một quy trình kỹ thuật nhằm đo lường chất lượng của các hệ thống Trí tuệ nhân tạo. Quy trình này bao gồm các bước đánh giá độ chính xác, an toàn, hiệu năng của model..."
    qa_pairs = await generate_qa_from_text(raw_text, 50)
    
    os.makedirs("data", exist_ok=True)
    with open("data/golden_set.jsonl", "w", encoding="utf-8") as f:
        for pair in qa_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    print(f"Done! Saved {len(qa_pairs)} cases to data/golden_set.jsonl")

if __name__ == "__main__":
    asyncio.run(main())
