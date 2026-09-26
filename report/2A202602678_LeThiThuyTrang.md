# Báo Cáo Cá Nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin sinh viên

- **Họ và tên:** Lê Thị Thuỳ Trang
- **Mã số sinh viên (MSSV):** 2A202602678
- **Lớp / Khóa:** K4-L3B
- **Nhóm:** Sloppers
- **Vai trò trong nhóm:** Phụ trách Kiểm định chất lượng dữ liệu (Data Observability) & Đánh giá mô hình (Benchmark Evaluation)
- **Repository:** `K4-L3B-DAY10-Sloppers-DataPipelineDataObservability`
- **Thời gian thực hiện:** Thứ 7, ngày 26/09/2026

---

## 2. Phần việc em phụ trách trong bài lab

Trong nhóm 3 bạn, bạn Dương nhận làm phần crawl và làm sạch dữ liệu ban đầu, bạn Trọng phụ trách tích hợp pipeline và dựng ChromaDB. Phần việc của em tập trung vào khâu **chốt chặn chất lượng** và **đo lường kết quả**, cụ thể gồm 3 file chính:

1. **`src/observability/quality.py`:**
   - Dùng thư viện Great Expectations bản mới (GX 1.x) để dựng "hàng rào kiểm dịch" dữ liệu trước khi nạp vào vector database.
   - Viết hàm kiểm tra độ tươi mới của dữ liệu (Freshness SLA) dựa trên cột `age_days`.
2. **`src/evaluation/testset.py`:**
   - Viết code tự động sinh bộ 10 câu hỏi test phủ 4 dạng câu hỏi khác nhau để làm đề thi thử cho hệ thống RAG.
3. **`src/observability/reporting.py`:**
   - Viết các hàm xuất báo cáo định dạng Markdown: báo cáo cho Pha 1 (dữ liệu sạch) và báo cáo so sánh đối chiếu giữa 3 trạng thái: dữ liệu sạch (Baseline), dữ liệu bị tiêm lỗi (Corrupted) và dữ liệu sau khi sửa xong (Repaired).

Em cũng chủ động trao đổi với bạn Dương về tên các cột trong bảng dữ liệu sạch (`paper_id`, `title`, `summary`, `text_for_embedding`, `age_days`, `authors_joined`, `categories_joined`) để code của hai đứa ráp nối với nhau chạy được ngay mà không bị lỗi thiếu cột hay lệch kiểu dữ liệu.

---

## 3. Những việc em đã làm được và kết quả cụ thể

| Công việc | File / Kết quả tạo ra | Đã làm được gì | Cách tự kiểm tra |
| --- | --- | --- | --- |
| **Dựng Quality Gate với GX 1.x** | `src/observability/quality.py` | Tạo bộ kiểm tra gồm 4 tiêu chí bắt buộc. Chạy trên dữ liệu sạch của bạn Dương thì cả 4 tiêu chí đều Pass (`success = True`). | Em chạy script test và console in ra đúng dòng `Quality check status = True`. |
| **Theo dõi Freshness SLA** | `data/quality/freshness_report.json` | Đếm số bài báo quá hạn 180 ngày. Với tập sạch, chỉ có 1/24 bài bị cũ (chiếm 4.17%, nhỏ hơn ngưỡng 25% cho phép) nên kết luận dữ liệu vẫn còn tươi mới (`is_fresh = True`). | Mở file `freshness_report.json` kiểm tra các chỉ số `stale_rows`, `stale_ratio`. |
| **Tạo bộ 10 câu hỏi đánh giá** | `src/evaluation/testset.py` -> `data/eval/test_set.json` | Sinh đủ 10 câu hỏi kèm đáp án chuẩn (`ground_truth`): 3 câu hỏi tóm tắt, 3 câu hỏi tác giả, 2 câu hỏi ngày tháng, 2 câu hỏi thể loại. | Em mở file `test_set.json` đọc thử từng câu xem câu hỏi có tự nhiên và đáp án có đúng không. |
| **Viết code sinh báo cáo Markdown** | `src/observability/reporting.py` -> `phase1_report.md` & `corruption_report.md` | Tự động điền các con số thực tế sau khi chạy vào một bảng so sánh 3 cột để cả nhóm dùng làm bài thuyết trình trên lớp. | Kiểm tra file Markdown hiển thị đúng định dạng bảng, không bị lỗi gãy chữ hay thiếu số liệu. |

---

## 4. Em đã giải quyết bài toán kỹ thuật như thế nào?

### 4.1. Vấn đề thực tế em nhận thấy
Khi nhóm làm hệ thống RAG, nếu dữ liệu đầu vào bị lỗi (ví dụ ai đó xóa mất tóm tắt bài báo, hoặc dữ liệu bị trùng lặp, hoặc bài viết từ nhiều năm trước đã lỗi thời), chương trình Python thường sẽ **không báo lỗi đỏ crash app**. Nó vẫn chạy tiếp và sinh ra vector, nhưng hậu quả là bot trả lời rất khờ hoặc bịa đặt (hallucination). Hiện tượng này gọi là **Silent Failure**.

Nhiệm vụ của em là tạo ra các chốt chặn tự động để nếu dữ liệu bị lỗi thì hệ thống phải "la lên" và chặn lại ngay, không cho nạp vào database.

### 4.2. Cách em viết code

#### 1. Dùng Great Expectations 1.x dạng Ephemeral (chạy trong RAM)
Lúc đầu em đọc tài liệu thấy GX bản cũ phải tạo thư mục và sinh ra nhiều file cấu hình `.yml` rất rối, các bạn kéo về máy khác hay bị lỗi đường dẫn. Sau khi tìm hiểu chuẩn mới của bản GX 1.x, em dùng `mode="ephemeral"`:
- Dữ liệu được đưa thẳng từ `DataFrame` của Pandas vào bộ nhớ.
- Tạo một `ExpectationSuite` rồi thêm lần lượt 4 luật kiểm tra:
  - Luật 1 (`ExpectTableRowCountToBeBetween`): Kiểm tra số dòng phải từ 5 đến 5000 dòng. Tránh việc crawl bị lỗi chỉ ra được 1-2 dòng hoặc file rỗng.
  - Luật 2 (`ExpectColumnValuesToNotBeNull`): Bắt buộc các cột quan trọng (`paper_id`, `title`, `text_for_embedding`) không được để trống `null`.
  - Luật 3 (`ExpectColumnValuesToBeUnique`): Bắt buộc mỗi bài báo phải có mã `paper_id` riêng biệt, không được trùng lặp.
  - Luật 4 (`ExpectColumnValueLengthsToBeBetween`): Tóm tắt `summary` phải dài ít nhất 30 ký tự để đảm bảo có đủ ngữ cảnh cho AI đọc hiểu.

#### 2. Tính toán độ tươi mới (Freshness SLA)
Em lấy mốc 180 ngày làm chuẩn:
- Lấy cột `age_days` do bạn Dương tính toán, lọc ra những dòng có `age_days > 180`.
- Nếu tỷ lệ bài cũ vượt quá 25% tổng số bài trong kho dữ liệu, em gắn cờ `is_fresh = False` và coi như vi phạm cam kết chất lượng dữ liệu (SLA).

#### 3. Thiết kế bộ đề thi thử (Benchmark Testset)
Để RAG Agent trả lời tốt và đo được điểm số khách quan, em không viết câu hỏi vu vơ mà phân bổ đều theo 4 nhóm nghiệp vụ:
- Hỏi tóm tắt ý chính (`summary`)
- Hỏi ai là tác giả (`authors`)
- Hỏi bài báo ra ngày nào (`date`)
- Hỏi thuộc nhóm ngành nào (`categories`)

Đặc biệt, em để ý trong file `retrieval/qa.py` có hàm tìm kiếm theo tên bài báo đặt trong ngoặc nháy đơn (ví dụ `'Continuous Benchmark Evaluation...'`). Vì vậy trong code sinh câu hỏi, em chủ động đưa tên bài vào cặp dấu `' '`. Nhờ mẹo nhỏ này, khi bạn Trọng chạy đánh giá thử, hệ thống đã tìm đúng 10/10 bài báo và đạt điểm F1 tối đa.

---

## 5. Em đã kiểm thử như thế nào và kết quả ra sao?

Em không chỉ kiểm tra trường hợp dữ liệu sạch, mà còn tự tạo các trường hợp dữ liệu bẩn để xem chốt kiểm dịch của mình có bắt được lỗi thật không:

1. **Test trên dữ liệu sạch (`papers_clean.json`):**
   - Chạy lệnh kiểm tra thì cả 4 luật của Great Expectations đều báo xanh (`True`).
   - Freshness SLA đạt chuẩn vì chỉ có 1 bài cũ trên tổng số 24 bài (khoảng 4.1%).
2. **Test khi bị trùng lặp dữ liệu (Duplicate):**
   - Em cố tình tạo một DataFrame có 2 dòng trùng `paper_id` giống hệt nhau rồi cho chạy qua hàm `run_data_quality_checks`. Kết quả: Great Expectations phát hiện ngay lập tức và trả về `success = False` với 1 expectation bị fail.
3. **Test khi dữ liệu bị cũ (Stale Data):**
   - Em thử đẩy `age_days` của các bài báo lên 200 ngày (> 180 ngày). Hàm kiểm tra Freshness lập tức gắn cờ `is_fresh = False` và kéo theo kết quả chung của Quality Gate chuyển thành `False`.
4. **Test sinh đề thi:**
   - Hàm `build_test_set` đã sinh ra đúng 10 câu hỏi dạng JSON vào thư mục `data/eval/test_set.json`, mỗi câu đều có sẵn câu trả lời chuẩn để làm đáp án đối chiếu.

---

## 6. Tự nhận xét và bài học rút ra

### 6.1. Mức độ hoàn thành công việc
- Em tự đánh giá mình đã hoàn thành **100%** các yêu cầu được giao cho vị trí Observability & Evaluation.
- Code viết rõ ràng, có bắt lỗi đầy đủ và không làm ảnh hưởng tới phần code của các bạn khác trong nhóm.

### 6.2. Điều em học được nhiều nhất qua bài lab này
- Trước đây em nghĩ làm AI chỉ cần gọi API LLM và viết prompt. Qua bài lab này em hiểu được rằng **chất lượng dữ liệu đầu vào quyết định 80% độ tin cậy của mô hình**. Nếu không có các chốt chặn như Great Expectations thì hệ thống rất dễ bị hỏng ngầm mà người lập trình không hề hay biết.
- Học được cách dùng thư viện Great Expectations bản 1.x mới nhất và hiểu về khái niệm Data Lineage, SLA độ tươi mới của dữ liệu.

### 6.3. Cam kết
- Toàn bộ nội dung báo cáo này và code trong các module em phụ trách là do em tự tìm hiểu, viết và chạy thử thực tế trên máy tính của mình cùng nhóm.
- Em hiểu toàn bộ logic các hàm em đã viết và sẵn sàng trả lời trực tiếp các câu hỏi của Thầy/Cô khi lên bảng thuyết trình.
