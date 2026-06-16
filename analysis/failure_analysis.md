# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 1. Tổng quan Benchmark
- **Tổng số cases:** 50
- **Điểm LLM-Judge trung bình:** 3.0 / 5.0 (Do fallback khi API bị lỗi)
- **Hit Rate trung bình:** 0.76 (76%)
- **Agreement Rate:** 1.0 (100%)
- **Pipeline:** Agent_V2_Optimized

## 2. Phân nhóm lỗi (Failure Clustering)
Dựa vào các cases mà Agent sinh lỗi trong quá trình Benchmark với bộ Golden Dataset về Luật Phòng, chống ma tuý, các lỗi được phân vào 3 nhóm chính:

| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |
|----------|----------|---------------------|
| Retrieval Miss (Miss Context) | 12 | Thuật toán BM25 / Embedding không bắt được keyword phức tạp hoặc các từ viết tắt chuyên ngành luật, dẫn đến việc lấy sai tài liệu (Hit Rate = 0). |
| Hallucination / Out of context | 5 | Khi hỏi về các chất ít phổ biến (như Fentanyl, Safrole), Agent không tìm thấy context và cố bịa ra thông tin. |
| Incomplete (Thiếu ý) | 3 | Câu hỏi yêu cầu tổng hợp từ nhiều điều khoản (ví dụ: Hình phạt bổ sung + Phạt tiền), nhưng hệ thống chỉ trích xuất được một phần. |

## 3. Phân tích 5 Whys (Chọn 3 case tệ nhất)

### Case #1: Lỗi Retrieval Miss - Hỏi về Morphine (Danh mục II)
1. **Symptom:** Agent trả lời Morphine bị cấm hoàn toàn, thay vì được dùng hạn chế trong y tế.
2. **Why 1:** LLM không nhận được context từ Nghị định 57/2022 về Morphine.
3. **Why 2:** Vector DB không tìm thấy tài liệu liên quan nhất (Hit Rate = 0).
4. **Why 3:** Từ khoá người dùng gõ là "Morphine", nhưng tài liệu lại ghi "Morphine — thuốc giảm đau mạnh trong y tế", vector embedding không match được chính xác intent "cấm hoàn toàn hay không".
5. **Why 4:** Embedding model hiện tại không phân tách rõ ràng Semantic (Ý nghĩa cấm vs không cấm).
6. **Root Cause:** Thiếu bước Reranking (Sử dụng Cross-Encoder) để đánh giá độ liên quan sâu sắc giữa Câu hỏi và Document.

### Case #2: Lỗi Hallucination - Xác định tình trạng nghiện
1. **Symptom:** Agent bịa ra rằng trạm y tế cấp xã có quyền xác định tình trạng nghiện ma tuý.
2. **Why 1:** LLM bị mâu thuẫn giữa kiến thức chung (địa phương) và tài liệu pháp luật thực tế (chỉ tuyến tỉnh/cơ sở uỷ quyền mới được xác định).
3. **Why 2:** Context cung cấp cho LLM bị cắt mất đoạn Điều 11 của Nghị định 105.
4. **Why 3:** Chunking size (kích thước cắt văn bản) chia cắt ngay giữa Điều 10 và Điều 11.
5. **Why 4:** Hệ thống sử dụng Fixed-size Chunking (cắt theo số lượng từ cố định) cơ bản mà không có Semantic overlap.
6. **Root Cause:** Chiến lược Chunking chưa tối ưu cho các văn bản Pháp luật (cần cắt theo Điều/Khoản thay vì theo token).

### Case #3: Lỗi Incomplete - Tổng hợp hình phạt
1. **Symptom:** Câu trả lời đúng về hình phạt tù nhưng thiếu phần hình phạt bổ sung (phạt tiền 5-500 triệu đồng).
2. **Why 1:** Model lấy được thông tin từ Điều 248 nhưng sót Điều 259 (Hình phạt bổ sung).
3. **Why 2:** Thuật toán retrieval chỉ lấy `top_k = 1`.
4. **Why 3:** Giới hạn `top_k` quá nhỏ để bắt được các điều khoản rải rác.
5. **Why 4:** Muốn tiết kiệm token và tăng tốc độ xử lý (latency).
6. **Root Cause:** Đánh đổi (Trade-off) sai lầm giữa Cost/Latency và Chất lượng (Quality). Cần tăng `top_k` lên ít nhất 3.

## 4. Kế hoạch cải tiến (Action Plan)
- [x] Thay đổi Chunking strategy từ Fixed-size sang **Semantic Chunking** hoặc cắt theo ký tự đặc biệt (`Điều`, `Khoản`).
- [x] Tăng `top_k` trong bước Retrieval từ 1 lên 3 hoặc 5 để lấy đủ ngữ cảnh (Incomplete fix).
- [x] Thêm bước Reranking vào Pipeline (Sử dụng Cross-Encoder) để cải thiện điểm Hit Rate và MRR.
- [x] Triển khai **Query Expansion** bằng LLM trước khi thực hiện Retrieval để xử lý các từ lóng/từ đồng nghĩa ngành Luật.
