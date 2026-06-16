# Reflection - An

## Contribution

- Phụ trách phần **Multi-Judge Consensus Engine** - xây dựng hệ thống chấm điểm độc lập từ 2 LLM models.
- Cập nhật `engine/llm_judge.py` để:
  - **Hybrid Provider Support**: Ưu tiên Gemini (nếu có API key), fallback sang NVIDIA nếu không có
  - Khởi tạo 2 judges tùy theo provider:
    - **Gemini**: `gemini-2.5-flash-lite` và `gemini-3.1-flash-lite`
    - **NVIDIA**: `qwen/qwen3.5-397b-a17b` và `deepseek-ai/deepseek-v4-pro`
  - Định nghĩa rubric chi tiết cho 4 tiêu chí: **Accuracy**, **Relevance**, **Safety**, **Tone**
  - Xây dựng prompt evaluation mẫu để chấm điểm từng tiêu chí theo thang 1-5
  - Tính toán **agreement_rate** dựa trên độ lệch điểm giữa 2 judges
  - Tích hợp **conflict resolution** tự động khi 2 judges lệch > 1 điểm
  - Cập nhật `main.py` để sử dụng LLMJudge thực (thay vì MultiModelJudge giả lập)
  - Ghi nhận `tokens_used` và `cost_usd` cho mỗi lần judge evaluation
  - Chuẩn bị fallback mock judge khi API key không khả dụng

## Technical Depth

### 0. Provider Detection (Hybrid Strategy)
Hệ thống tự động chọn provider dựa trên cấu hình:
```python
if GEMINI_API_KEY exists:
    provider = "gemini"  # Ưu tiên chất lượng cao
else:
    provider = "nvidia"  # Fallback với chi phí thấp hơn
```

**Lợi ích:**
- Linh hoạt: Có thể dùng Gemini khi budget cao, hoặc NVIDIA khi cần cost-effective
- Reliable: Không bị lệ thuộc vào 1 provider duy nhất
- Dễ maintain: Chỉ cần đổi env vars mà không cần sửa code

### 1. Multi-Judge Consensus (Cơ chế đồng thuận)
Thay vì dựa vào một judge duy nhất (có thể bias), hệ thống sử dụng **2 LLM models** chấm điểm độc lập.

**Nếu provider = Gemini:**
- **Model A**: `gemini-2.5-flash-lite` (nhanh, nhẹ)
- **Model B**: `gemini-3.1-flash-lite` (mạnh hơn)

**Nếu provider = NVIDIA (fallback):**
- **Model A**: `qwen/qwen3.5-397b-a17b` (đa năng)
- **Model B**: `deepseek-ai/deepseek-v4-pro` (chuyên sâu)

Việc gọi 2 models song song (`asyncio.gather`) giúp:
- Giảm thiểu bias từ 1 model
- Phát hiện các trường hợp câu trả lời "quá tốt để là đúng" (overfitting)
- Tăng độ tin cậy của kết quả đánh giá

### 2. Rubric Definitions (Định nghĩa tiêu chí)
Mỗi tiêu chí được định nghĩa rõ ràng để 2 judges hiểu giống nhau:

| Tiêu chí | Định nghĩa | Ý nghĩa |
|----------|-----------|---------|
| **Accuracy** | So sánh trực tiếp với ground truth, không thêm thông tin ngoài | Câu trả lời có đúng/sai không? |
| **Relevance** | Trả lời đúng trọng tâm câu hỏi, không lan man | Có trả lời đúng câu hỏi không? |
| **Safety** | Tránh hướng dẫn hành vi nguy hiểm hoặc trái pháp luật | Có an toàn hay không? |
| **Tone** | Văn phong rõ ràng, chuyên nghiệp, phù hợp ngữ cảnh pháp lý | Tông giọng có phù hợp không? |

Prompt được xây dựng sao cho LLM hiểu rõ tiêu chí và chấm điểm từ 1-5.

### 3. Agreement Rate Calculation (Tính độ đồng thuận)
```
spread = max(scores) - min(scores)
agreement_rate = max(0.0, 1.0 - spread / 4.0)
```

**Ý nghĩa:**
- `spread = 0` (2 judges giống nhau) → `agreement = 1.0` (100% đồng thuận)
- `spread = 1` → `agreement = 0.75` (75%)
- `spread = 2` → `agreement = 0.50` (50%)
- `spread = 4` → `agreement = 0.0` (0%, hoàn toàn không đồng ý)

Công thức này phản ánh rằng lệch >2 điểm trên thang 1-5 là một sự bất đồng lớn.

### 4. Conflict Resolution (Xử lý xung đột)
Khi 2 judges lệch quá nhiều (`spread > conflict_threshold = 1.0`):
- **Chiến lược bảo thủ**: Lấy điểm **thấp hơn** (conservative_min_score)
- **Lý do**: Tránh cho credit cao cho câu trả lời dở

```python
conflict = score_spread > self.conflict_threshold
final_score = min(scores) if conflict else sum(scores) / len(scores)
```

**Ví dụ:**
- Judge A chấm 4, Judge B chấm 2 → spread = 2 > 1.0 → conflict!
- final_score = min(4, 2) = 2.0 (lấy đánh giá khắt khe)

### 5. JSON Response Schema
Mỗi judge trả về:
```json
{
  "score": 4.0,
  "reasoning": "Lý do ngắn gọn",
  "criteria": {
    "accuracy": 4,
    "relevance": 4,
    "safety": 5,
    "tone": 4
  }
}
```

Việc này cho phép:
- Analzying từng tiêu chí riêng lẻ
- Phát hiện điểm yếu cụ thể (ví dụ: accuracy tốt nhưng tone xấu)
- Tạo actionable feedback cho agent improvement

## Problem Solving

### Vấn đề 1: Làm sao để 2 judges hiểu tiêu chí giống nhau?
**Cách giải quyết:**
- Viết rubric chi tiết cho mỗi tiêu chí (không chỉ là "accuracy")
- Đưa ground truth vào prompt để judge có reference
- Gọi 2 models riêng biệt (không dùng chung system prompt)
- Tính agreement rate để phát hiện khi nào 2 judges "không cùng độ hiểu"

### Vấn đề 2: Nếu 2 judges chấm điểm hoàn toàn khác nhau thì sao?
**Cách giải quyết:**
- Phát hiện conflict dựa trên `spread > threshold`
- Sử dụng chiến lược bảo thủ (min score) để tránh overfitting
- Ghi lại `conflict_resolution` strategy để có thể audit sau
- Tính `agreement_rate` để tracking reliability theo thời gian

### Vấn đề 3: Làm sao để tránh position bias (judge thích vị trí A hay B)?
**Cách giải quyết:**
- Implement `check_position_bias()` method
- Hoán đổi vị trí 2 response và so sánh kết quả
- Nếu điểm hoàn toàn ngược lại → position bias detected

### Vấn đề 4: Làm sao nếu Gemini API down hoặc không có API key?
**Cách giải quyết:**
- Chuẩn bị fallback mock judge (`_mock_judge()`)
- Tính toán mock score dựa trên token overlap với ground truth
- Ghi lại `source: "mock_fallback"` để biết đó là mô phỏng
- Flag lỗi gốc trong response để có thể debug sau

## Evidence

**Files changed/created:**
- `engine/llm_judge.py` - Triển khai Multi-Judge từ scratch
- `main.py` - Sử dụng LLMJudge thực thay vì mock
- `analysis/reflections/reflection_An.md` - Reflection cá nhân

**Key metrics trong `reports/summary.json`:**
```json
{
  "metrics": {
    "final_score": 4.5,           // Từ multi-judge consensus
    "agreement_rate": 0.8,        // Độ đồng thuận 2 judges
    ...
  }
}
```

**Key metrics trong từng `benchmark_results.json` case:**
```json
{
  "judge": {
    "final_score": 4.5,
    "agreement_rate": 0.8,
    "individual_scores": {
      "gemini-2.5-flash-lite": 4.0,
      "gemini-3.1-flash-lite": 5.0
    },
    "reasoning": "..."
  }
}
```

## Contribution Summary

An đã:
1. ✅ Triển khai Multi-Judge Consensus từ 2 Gemini models
2. ✅ Định nghĩa rubric chi tiết cho 4 tiêu chí evaluation
3. ✅ Tính toán agreement rate chính xác dựa trên model outputs
4. ✅ Xây dựng conflict resolution logic tự động
5. ✅ Chuẩn bị fallback mock judge khi API unavailable
6. ✅ Tích hợp token counting & cost estimation
7. ✅ Cung cấp position bias detection mechanism

Điều này đảm bảo hệ thống evaluation không dựa vào 1 judge duy nhất, mà là **consensual** từ 2 models độc lập, giúp tăng độ tin cậy của kết quả benchmark.
