# Kế hoạch phân công nhóm - Lab Day 14

> Ghi chú nội bộ: file này chỉ dùng để chia việc trong nhóm, không push lên GitHub.

## 1. Tóm tắt yêu cầu đề bài

Nhóm cần xây dựng hệ thống đánh giá tự động để benchmark AI Agent. Bài nộp cần chứng minh bằng số liệu rằng agent tốt ở đâu, yếu ở đâu, retrieval có lấy đúng tài liệu không, judge có đáng tin không, và phiên bản mới có đủ điều kiện release không.

Đầu ra bắt buộc:

- Source code hoàn chỉnh.
- `data/golden_set.json` có ít nhất 50 golden cases.
- `reports/summary.json`.
- `reports/benchmark_results.json`.
- `analysis/failure_analysis.md`.
- `analysis/reflections/reflection_[Ten_SV].md` cho Bút, An, Quang.

Tiêu chí quan trọng:

- Retrieval Evaluation: Hit Rate và MRR.
- Dataset & SDG: 50+ cases, có `expected_retrieval_ids`, có hard/red-team cases.
- Multi-Judge Consensus: ít nhất 2 judge, có `agreement_rate` và xử lý lệch điểm.
- Regression Testing: so sánh V1 vs V2, có Release Gate.
- Performance: chạy async, có latency/token/cost.
- Failure Analysis: phân cụm lỗi và phân tích 5 Whys.

## 2. Phân công công việc cho 3 thành viên

| Thành viên | Vai trò chính | File/phần phụ trách | Kết quả cần bàn giao |
| --- | --- | --- | --- |
| Bút | Golden Dataset, Benchmark Runner, Regression Gate, reports | `data/golden_set.json`, `main.py`, `engine/runner.py`, `agent/main_agent.py`, `reports/summary.json`, `reports/benchmark_results.json`, `analysis/reflections/reflection_But.md` | Tạo/duy trì 50 golden cases; runner chạy async theo batch; tính latency/token/cost; tổng hợp Hit Rate/MRR; so sánh V1 vs V2; xuất quyết định `APPROVE` hoặc `BLOCK_RELEASE`. |
| An | Multi-Judge Consensus, rubric, judge reliability | `engine/llm_judge.py`, phần judge trong `main.py`, `analysis/reflections/reflection_An.md` | Triển khai hoặc mô phỏng ít nhất 2 judge; định nghĩa rubric Accuracy/Relevancy/Safety/Tone; tính `agreement_rate`; xử lý khi 2 judge lệch điểm; ghi reasoning và individual scores. |
| Quang | Retrieval Evaluation, agent retrieval, failure analysis, final check | `engine/retrieval_eval.py`, phần retrieval trong `agent/main_agent.py`, `analysis/failure_analysis.md`, `check_lab.py`, `analysis/reflections/reflection_Quang.md` | Tính Hit Rate/MRR thật; đảm bảo agent trả `retrieved_ids`; phân tích các case fail theo nhóm lỗi; điền 5 Whys; chạy `python check_lab.py` trước khi nộp. |

## 3. Thứ tự làm việc nhóm

1. Bút chốt `data/golden_set.json` đủ 50 cases và schema thống nhất.
2. Quang đảm bảo retrieval trả `retrieved_ids` khớp với `expected_retrieval_ids`, sau đó kiểm tra Hit Rate/MRR.
3. An hoàn thiện Multi-Judge để benchmark có điểm đánh giá cuối và agreement rate.
4. Bút chạy benchmark cuối, tạo `reports/summary.json` và `reports/benchmark_results.json`.
5. Quang điền `analysis/failure_analysis.md`, cả nhóm bổ sung reflection cá nhân.
6. Quang hoặc Bút chạy `python check_lab.py` trước khi nộp.

## 4. Hợp đồng dữ liệu

Mỗi case trong `data/golden_set.json` nên có schema:

```json
{
  "id": "case_001",
  "question": "Câu hỏi kiểm thử",
  "expected_answer": "Câu trả lời đúng",
  "context": "Context hoặc đoạn tài liệu liên quan",
  "expected_retrieval_ids": ["bo-luat-hinh-su-2015-chuong-xx-toi-pham-ma-tuy"],
  "metadata": {
    "difficulty": "easy|medium|hard",
    "type": "fact-check|adversarial|out-of-context|ambiguous|conflicting|multi-turn"
  }
}
```

Mỗi response của agent nên có:

```json
{
  "answer": "Câu trả lời của agent",
  "contexts": ["Context 1", "Context 2"],
  "retrieved_ids": ["doc_id_1", "doc_id_2", "doc_id_3"],
  "metadata": {
    "model": "gpt-4o-mini",
    "tokens_used": 150,
    "cost_usd": 0.001,
    "sources": ["source.pdf"]
  }
}
```

## 5. Phần cá nhân của Bút

Bút đã nhận phần cá nhân lớn hơn vì bao gồm cả golden cases và benchmark integration.

Checklist riêng của Bút:

- [ ] `data/golden_set.json` đủ 50 cases, có `expected_retrieval_ids`.
- [ ] `main.py` đọc được golden set dạng `.json`.
- [ ] `engine/runner.py` chạy async theo batch và không sập toàn bộ khi một case lỗi.
- [ ] `reports/summary.json` có `avg_score`, `hit_rate`, `mrr`, `agreement_rate`, `avg_latency`, `total_tokens`, `total_cost_usd`.
- [ ] `reports/benchmark_results.json` có kết quả từng case.
- [ ] Regression Gate có `release_decision` và `reasons`.
- [ ] `analysis/reflections/reflection_But.md` giải thích contribution, MRR, async batching, release gate, cost/quality trade-off.

## 6. Checklist cuối trước khi nộp

- [ ] `data/golden_set.json` có ít nhất 50 cases hợp lệ.
- [ ] Mỗi case có `expected_retrieval_ids`.
- [ ] Agent response có `retrieved_ids`.
- [ ] Hit Rate và MRR được tính thật.
- [ ] Multi-Judge có ít nhất 2 judge và có agreement/conflict handling.
- [ ] Benchmark chạy async và có latency/cost/token.
- [ ] `reports/summary.json` có metrics và regression result.
- [ ] `reports/benchmark_results.json` có kết quả từng case.
- [ ] `analysis/failure_analysis.md` đã điền dữ liệu thật.
- [ ] Có đủ reflection cá nhân cho Bút, An, Quang.
- [ ] Chạy `python check_lab.py` pass trước khi nộp.
