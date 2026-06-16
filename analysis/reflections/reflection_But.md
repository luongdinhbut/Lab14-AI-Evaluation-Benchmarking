# Reflection - Bút

## Contribution

- Phụ trách phần Benchmark Runner, Regression Gate và tổng hợp report.
- Cập nhật `engine/runner.py` để chạy async theo batch, ghi nhận `latency`, `tokens_used`, `cost_usd`, `test_case_id`, `status` và `error_type`.
- Cập nhật `main.py` để tạo `reports/summary.json`, `reports/benchmark_results.json`, tính metrics tổng hợp và đưa ra quyết định `APPROVE` hoặc `BLOCK_RELEASE`.
- Tích hợp `data/golden_set.json` vào pipeline benchmark và giữ fallback cho `.jsonl` nếu nhóm cần export định dạng cũ.
- Bổ sung retrieval mô phỏng theo keyword trong agent mẫu để runner có thể tính Hit Rate/MRR với golden set hiện tại.

## Technical Depth

- MRR đo thứ hạng của tài liệu đúng đầu tiên trong danh sách retrieval. Tài liệu đúng xuất hiện càng sớm thì MRR càng cao.
- Hit Rate kiểm tra trong top-k tài liệu truy xuất có ít nhất một tài liệu đúng hay không.
- Async batching giúp benchmark nhiều test cases nhanh hơn, nhưng vẫn cần giới hạn `batch_size` để tránh rate limit khi dùng API thật.
- Regression Gate giúp chặn phiên bản agent mới nếu chất lượng, retrieval reliability, agreement rate, latency hoặc cost tệ hơn ngưỡng nhóm đặt ra.

## Problem Solving

- Vấn đề: Pipeline ban đầu chỉ đọc `data/golden_set.jsonl`, trong khi golden set của nhóm được tạo dưới dạng `data/golden_set.json`.
- Cách xử lý: Viết loader tự nhận nhiều định dạng dataset (`.json`, `.jsonl`) và đọc được JSON array gồm 50 cases.
- Kết quả: Benchmark chạy được với 50 cases, tạo report có Hit Rate, MRR, latency, token/cost và Regression Gate.

## Evidence

- Files changed:
  - `engine/runner.py`
  - `main.py`
  - `agent/main_agent.py`
  - `data/golden_set.json`
  - `analysis/reflections/reflection_But.md`
