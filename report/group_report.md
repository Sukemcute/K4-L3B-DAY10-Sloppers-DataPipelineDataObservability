# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | Sloppers |
| Repository | `https://github.com/Sukemcute/K4-L3B-DAY10-Sloppers-DataPipelineDataObservability` |
| Ngày hoàn thành | 2026-09-26 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu | Tỷ lệ đóng góp |
| --: | --- | :---: | --- | --- | :---: |
| 1 | Phạm Hoàng Trọng | 2A202602765 | Trưởng nhóm & Pipeline Integrator + Vector RAG | `core/`, `retrieval/index.py`, `src/pipelines/`, `script/` | 34% |
| 2 | Lâm Hải Dương | 2A202602676 | Data Foundation & Corruption & Repair | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/ingestion/corruption.py` | 33% |
| 3 | Lê Thị Thuỳ Trang | 2A202602678 | Data Observability & Benchmark Evaluation | `src/observability/quality.py` (GX 1.x), `src/evaluation/testset.py`, `src/observability/reporting.py` | 33% |

---

## 2. Tóm tắt kết quả

Trong bài lab Day 10 này, nhóm Sloppers của chúng em gồm 3 bạn đã cùng nhau làm việc và hoàn thành trọn vẹn toàn bộ các yêu cầu của bài lab. Nhóm đã xây dựng một luồng dữ liệu hoàn chỉnh từ khâu thu thập dữ liệu bài báo từ Crossref API, làm sạch, lưu trữ vector vào ChromaDB, cho đến việc thiết lập công cụ giám sát chất lượng dữ liệu (Data Observability) và kiểm thử chất lượng câu trả lời của RAG Agent.

- **Ở pha Baseline:** Nhóm tải và làm sạch thành công 24 bài báo khoa học, lưu bản snapshot thô gốc an toàn, sau đó nhúng vector đưa vào ChromaDB (`papers-baseline`). Nhóm tạo bộ đề kiểm tra chuẩn gồm 10 câu hỏi chia đều 4 nhóm nội dung. Kết quả ban đầu rất tốt: toàn bộ 4 bài kiểm tra của Great Expectations đều đạt (PASS), độ tươi mới dữ liệu đạt chuẩn FRESH (chỉ có 1/24 bài cũ quá 180 ngày), RAG Agent trả lời chính xác và tìm đúng tài liệu 100% (`retrieval_hit_rate = 1.0`, `token_f1 = 1.0`).
- **Ở pha Data Corruption:** Nhóm thử nghiệm giả lập 6 lỗi dữ liệu thực tế (xóa bài báo mới, xóa nội dung tóm tắt, chèn chữ vô nghĩa, cắt ngắn tiêu đề, lùi ngày xuất bản và nhân bản dòng). Ngay lập tức các công cụ giám sát phát hiện ra lỗi: Great Expectations báo FAIL và Freshness SLA báo STALE (tỷ lệ bài quá hạn tăng vọt lên 57.14%). Lỗi dữ liệu khiến mô hình RAG bị ảnh hưởng trực tiếp: tỷ lệ tìm đúng tài liệu và điểm F1 bị tụt từ 1.0 xuống 0.7 (giảm 30%), điểm chất lượng câu trả lời giảm từ 5.0 xuống 3.8.
- **Ở pha Data Repair:** Nhóm áp dụng phương pháp tự phục hồi dữ liệu từ nguồn gốc: đọc lại từ file snapshot thô ban đầu (`crossref_records.json`), chạy lại quy trình làm sạch và nạp lại vào ChromaDB (`papers-repaired`). Sau khi sửa xong, các chốt chặn chất lượng xanh trở lại (PASS và FRESH), đồng thời RAG Agent cũng lấy lại phong độ với tỷ lệ tìm đúng 100% như lúc đầu.
- **Hạn chế còn lại:** Pipeline hiện đang chạy thực nghiệm trên tập 24 bài báo và thông báo lỗi mới chỉ ghi ra file log/markdown chứ chưa gửi thông báo tự động về tin nhắn cho nhóm.

---

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Quy trình dữ liệu của nhóm chạy tuần tự và khép kín qua các bước:

```text
1. Crossref API (Lấy dữ liệu mạng)
   └── Lưu file thô gốc không sửa đổi: crossref_response.json & crossref_records.json (data/raw/)

2. Làm sạch & Chuẩn hóa dữ liệu (Cleaning & Modeling)
   └── Tạo file sạch papers_clean.json (24 bài, có cột age_days và text_for_embedding 5 phần)

3. Nhúng Vector & Lưu vào Vector DB (Embedding & ChromaDB)
   └── Dùng SentenceTransformers all-MiniLM-L6-v2 đưa vào collection papers-baseline

4. Đánh giá Baseline & Kiểm tra chất lượng (Observability & Evaluation)
   ├── Bộ đề chuẩn 10 câu hỏi test_set.json -> đo Retrieval Hit Rate và Token F1
   ├── Great Expectations 1.x -> kiểm tra tính toàn vẹn (Pass/Fail)
   └── Freshness SLA -> kiểm tra độ cũ của dữ liệu (Fresh/Stale)

5. Thử nghiệm Tiêm lỗi (Corruption Suite)
   └── Giả lập 6 lỗi bẩn -> dữ liệu giảm còn 21 bài -> GX báo FAIL, Freshness báo STALE -> Hit Rate tụt còn 0.7

6. Phục hồi dữ liệu sạch (Self-healing Repair)
   └── Đọc lại từ file thô gốc -> làm sạch lại -> nạp vào papers-repaired -> phục hồi Hit Rate 1.0
```

### Trách nhiệm của từng bạn trong nhóm

| Khối việc | Đầu vào | Công việc chính | Sản phẩm đầu ra | Bạn phụ trách |
| --- | --- | --- | --- | --- |
| Ingestion | API Crossref hoặc cache offline | Gọi API có cơ chế thử lại (retry), bóc tách thẻ XML `<jats:p>`, chuyển thành danh sách `PaperRecord` | `crossref_response.json`, `crossref_records.json` | Lâm Hải Dương |
| Cleaning | Danh sách `PaperRecord` | Lọc bài thiếu thông tin, tính `age_days`, ghép chuỗi `text_for_embedding` 5 phần | `papers_clean.csv`, `papers_clean.json` | Lâm Hải Dương |
| Vector Index | DataFrame sạch | Dùng mô hình `all-MiniLM-L6-v2` nhúng 384 chiều, quản lý ChromaDB collections an toàn | Thư mục `data/chroma/`, `papers_embeddings.json` | Phạm Hoàng Trọng |
| Evaluation | DataFrame sạch, ChromaDB | Tạo bộ đề 10 câu hỏi, chạy đo `retrieval_hit_rate`, `mean_token_f1`, điểm chấm câu trả lời | `test_set.json`, các file `*_metrics.json` | Lê Thị Thuỳ Trang |
| Observability | DataFrame sạch, cấu hình SLA | Viết kiểm thử Great Expectations 1.x Ephemeral, kiểm tra ngưỡng cũ `age_days > 180` | `data/quality/*.json`, `phase1_report.md` | Lê Thị Thuỳ Trang |
| Corruption & Repair | DataFrame sạch, bản ghi thô | Viết hàm tạo 6 lỗi dữ liệu; viết hàm khôi phục sạch lại từ snapshot gốc | `papers_clean_corrupted.*`, `papers_clean_repaired.*` | Lâm Hải Dương |
| Điều phối chung | Toàn bộ các module | Kết nối các phần thành 2 script chạy tự động `run_phase1.py` và `run_corruption_flow.py` | Toàn bộ pipeline chạy êm, exit code 0 | Phạm Hoàng Trọng |

---

## 4. Cách tái hiện kết quả

### Cấu hình môi trường (hoàn toàn không lộ API key)

| Cấu hình | Giá trị nhóm dùng thực tế |
| --- | --- |
| `LLM_PROVIDER` | `gemini` (hoặc mock/offline mode) |
| `LLM_MODEL` | `gemini-1.5-flash` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng bài báo Crossref | 24 bài |
| Số lượng bài truy vấn (`top_k`) | 3 bài |
| Ngưỡng dữ liệu cũ (Freshness) | 180 ngày (tối đa không quá 25% số bài) |
| Random seed | 42 |

### Lệnh cài đặt

Nhóm sử dụng công cụ `uv` để cài đặt nhanh các thư viện:

```bash
uv sync
```

Hoặc nếu dùng `pip` thông thường:

```bash
python -m pip install -e .
```

### Lệnh chạy kiểm tra

1. **Chạy luồng Baseline Phase 1:**
```bash
python script/run_phase1.py
```

2. **Chạy luồng thực nghiệm Tiêm lỗi & Tự phục hồi:**
```bash
python script/run_corruption_flow.py
```

### Kết quả chạy thực tế

| Lệnh | Trạng thái | Thời điểm chạy | Bằng chứng kiểm tra |
| --- | --- | --- | --- |
| Baseline pipeline | Thành công (exit code 0) | 2026-09-26 11:20 | `data/reports/phase1_report.md`, `data/results/baseline_metrics.json` |
| Corruption flow | Thành công (exit code 0) | 2026-09-26 11:21 | `data/reports/corruption_report.md`, `data/results/repaired_metrics.json` |

---

## 5. Ingestion, làm sạch và thỏa thuận dữ liệu (Data Contract)

### Nguồn dữ liệu

- **Nguồn:** Crossref REST API công khai (`https://api.crossref.org/works`).
- **Từ khóa tìm kiếm:** `agentic retrieval augmented generation large language model`.
- **Bộ lọc:** `from-pub-date:2026-03-30,has-abstract:true`.
- **Số lượng thu được:** Đúng 24 bài báo khoa học.
- **Xử lý mạng:** Nhóm cài đặt cơ chế gọi lại (retry) tối đa 3 lần nếu gặp lỗi mạng hoặc giới hạn lượt gọi (HTTP 429, 503). Nếu mất mạng hoàn toàn, hệ thống tự động đọc từ file cache có sẵn `data/raw/crossref_response.json` để bài lab không bị gián đoạn.

### Cấu trúc bảng dữ liệu (Schema)

Nhóm thống nhất cấu trúc bảng gồm các trường rõ ràng:
1. `paper_id` (chữ): Mã định danh duy nhất (DOI) của bài báo, không được phép trùng hay để trống.
2. `title` (chữ): Tiêu đề bài báo, được xóa khoảng trắng thừa.
3. `summary` (chữ): Tóm tắt nội dung, được loại bỏ sạch các thẻ XML `<jats:p>` từ Crossref.
4. `published` (ngày): Ngày công bố bài báo theo chuẩn `YYYY-MM-DD`.
5. `age_days` (số): Số ngày từ lúc xuất bản đến ngày chạy lab, dùng để tính độ mới của bài.
6. `authors_joined` (chữ): Tên các tác giả nối với nhau bằng dấu phẩy.
7. `categories_joined` (chữ): Các chuyên ngành liên quan của bài báo.
8. `text_for_embedding` (chữ): Đoạn văn bản hoàn chỉnh ghép từ 5 phần: Tiêu đề + Tác giả + Chuyên ngành + Ngày xuất bản + Tóm tắt để đưa vào mô hình AI nhúng vector.

---

## 6. Thiết lập bộ đề đánh giá (Evaluation Setup)

- **Số câu hỏi kiểm tra:** 10 câu hỏi đánh giá chuẩn.
- **4 nhóm câu hỏi:**
  - 4 câu hỏi về nội dung tóm tắt (`summary`).
  - 2 câu hỏi về danh sách tác giả (`authors`).
  - 2 câu hỏi về ngày công bố (`date`).
  - 2 câu hỏi về chủ đề chuyên ngành (`categories`).
- **Mã tài liệu đúng (Ground-truth Doc ID):** Mỗi câu hỏi được gán sẵn DOI của bài báo tương ứng để làm đáp án chuẩn.
- **Mô hình nhúng:** `sentence-transformers/all-MiniLM-L6-v2` cho ra vector 384 chiều, tìm kiếm bằng độ đo Cosine Similarity.
- **Số tài liệu lấy ra (`top_k`):** 3 bài liên quan nhất cho mỗi câu hỏi.

**Tại sao nhóm phải giữ nguyên 1 bộ 10 câu hỏi này cho cả 3 lần đo?**  
Vì đây là nguyên tắc khoa học cơ bản khi làm thực nghiệm: muốn biết việc làm bẩn dữ liệu hay việc sửa dữ liệu có thực sự hiệu quả hay không, ta bắt buộc phải giữ nguyên cùng một bài kiểm tra (10 câu hỏi). Nếu mỗi lần đo lại đổi câu hỏi khác, kết quả điểm số tăng hay giảm có thể do câu hỏi dễ hoặc khó hơn, chứ không phản ánh đúng chất lượng dữ liệu trong kho.

---

## 7. Kết quả Baseline

### Danh sách các file kết quả (Artifact checklist)

Nhóm đã kiểm tra và thấy đầy đủ các file theo đúng quy định:
- Dữ liệu thô: `data/raw/crossref_records.json` (đủ 24 bài gốc).
- Dữ liệu sạch: `data/clean/papers_clean.json` (đủ 24 bài đã chuẩn hóa).
- Vector DB: Thư mục `data/chroma/` chứa collection `papers-baseline`.
- Bộ đề thi: `data/eval/test_set.json` (đủ 10 câu hỏi).
- Điểm số baseline: `data/results/baseline_metrics.json`.
- Báo cáo chất lượng: `data/quality/baseline_quality_report.json`.
- Báo cáo pha 1: `data/reports/phase1_report.md`.

### Chỉ số ban đầu (Baseline metrics)

| Chỉ số đo | Giá trị | Ý nghĩa thực tế |
| --- | ---: | --- |
| `retrieval_hit_rate` | **1.0000** | Cả 10/10 câu hỏi đều tìm ra đúng bài báo gốc nằm trong top 3 kết quả. |
| `mean_token_f1` | **1.0000** | Câu trả lời sinh ra khớp từ ngữ và ý nghĩa với đáp án chuẩn. |
| `judge_accuracy` | **1.0000** | 100% câu trả lời đạt yêu cầu nội dung câu hỏi. |
| `mean_judge_score` | **5.0 / 5.0** | Điểm chất lượng trung bình đạt mức tối đa. |

---

## 8. Chất lượng dữ liệu và Độ tươi mới (Data Quality & Freshness)

### Kết quả kiểm tra bằng Great Expectations 1.x

Nhóm sử dụng phiên bản mới Great Expectations 1.x với 4 bài kiểm tra:
1. `expect_table_row_count_to_be_between`: Kiểm tra số lượng bài báo trong khoảng từ 10 đến 500 bài -> **PASS** (thực tế có 24 bài).
2. `expect_column_values_to_not_be_null`: Kiểm tra các cột quan trọng (`paper_id`, `title`, `text_for_embedding`) không được null -> **PASS** (0 bản ghi null).
3. `expect_column_values_to_be_unique`: Kiểm tra mã `paper_id` không được trùng lặp -> **PASS** (không có ID nào bị trùng).
4. `expect_column_value_lengths_to_be_between`: Kiểm tra độ dài tóm tắt bài báo phải từ 20 đến 10,000 ký tự -> **PASS** (tất cả các bài đều có tóm tắt hợp lệ).

### Kiểm tra độ tươi mới (Freshness SLA)

- Nhóm đặt ra thỏa thuận: không quá 25% số lượng bài báo được phép cũ hơn 180 ngày.
- Khi đo trên tập dữ liệu sạch ban đầu: bài mới nhất là `2026-07-22`, bài cũ nhất là `2026-03-28`.
- Kết quả: Chỉ có đúng **1/24 bài** (chiếm tỷ lệ `4.17%`) là xuất bản quá 180 ngày. Vì `4.17% <= 25%` nên trạng thái dữ liệu được xác nhận là **FRESH** (đạt chuẩn tươi mới).

---

## 9. Giả lập sự cố dữ liệu và Cách phục hồi

Nhóm đã giả lập 6 tình huống lỗi dữ liệu thường gặp trong thực tế:
1. **Xóa 5 bài báo mới nhất:** Mô phỏng tình trạng hệ thống bị mất cập nhật dữ liệu mới. Hậu quả là số dòng giảm từ 24 xuống, RAG agent không thể tìm thấy tài liệu cho những câu hỏi liên quan đến các bài này.
2. **Xóa trắng tóm tắt 4 bài:** Mô phỏng dữ liệu bị thiếu trường nội dung, vi phạm độ dài tối thiểu của Great Expectations.
3. **Chèn chữ vô nghĩa vào tóm tắt 4 bài:** Mô phỏng dữ liệu bị nhiễu do lỗi scraping hoặc encode, làm vector bị lệch hướng ngữ nghĩa.
4. **Cắt ngắn tiêu đề 5 bài:** Tiêu đề bị cắt dưới 8 ký tự, làm mất từ khóa chính khi tìm kiếm.
5. **Lùi ngày xuất bản thêm 400 ngày cho 9 bài:** Khiến tỷ lệ bài cũ tăng vọt từ 4.17% lên 57.14%, làm chuông cảnh báo Freshness SLA nhảy sang màu đỏ STALE.
6. **Nhân đôi 2 bản ghi:** Làm trùng lặp mã bài báo, vi phạm luật Uniqueness của dữ liệu.

**Cách nhóm sửa lỗi (Data Repair):**  
Thay vì vào sửa tay từng lỗi trên file bị hỏng, nhóm em áp dụng nguyên tắc **Idempotent Repair**: đọc lại toàn bộ 24 bài từ file snapshot gốc ban đầu `data/raw/crossref_records.json`, chạy lại toàn bộ hàm làm sạch và nạp dữ liệu sạch vào collection mới `papers-repaired`. Cách này vừa nhanh, vừa bảo đảm dữ liệu sau khi sửa chuẩn xác 100% như ban đầu mà không bị sót lỗi chắp vá.

---

## 10. Bảng so sánh 3 trạng thái: Trước lỗi - Khi bị lỗi - Sau khi sửa

| Chỉ số kiểm tra | Baseline (Gốc) | Corrupted (Bị lỗi) | Repaired (Đã sửa) | Mức độ thay đổi khi có lỗi | Mức phục hồi sau khi sửa | Nhận xét của nhóm |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | **1.0000** | **0.7000** | **1.0000** | Giảm -0.3000 | Phục hồi +0.3000 | Tỷ lệ tìm đúng tài liệu bị tụt 30% do mất bài và nhiễu, sau khi sửa thì tìm đúng 10/10 câu |
| `mean_token_f1` | **1.0000** | **0.7000** | **1.0000** | Giảm -0.3000 | Phục hồi +0.3000 | Điểm khớp từ ngữ cũng bị giảm tương ứng và hồi phục trọn vẹn |
| `judge_accuracy` | **1.0000** | **0.7000** | **1.0000** | Giảm -0.3000 | Phục hồi +0.3000 | Điểm chính xác nội dung phục hồi lại 100% |
| `mean_judge_score` | **5.0** | **3.8** | **5.0** | Giảm -1.2 điểm | Tăng lại +1.2 điểm | Điểm đánh giá câu trả lời phục hồi về điểm 5 tối đa |
| Great Expectations | **PASS** | **FAIL** | **PASS** | Chuyển thành FAIL | Chuyển thành PASS | Bắt trúng các lỗi rỗng tóm tắt, tiêu đề ngắn và trùng dòng |
| Freshness SLA | **FRESH (4.17%)** | **STALE (57.14%)** | **FRESH (4.17%)** | Vượt ngưỡng 25% | Trở về bình thường | Tỷ lệ bài cũ trở về mức an toàn 4.17% sau khi sửa |

**Hai bài học rút ra từ số liệu thực nghiệm:**
1. **Dữ liệu bẩn làm hỏng AI âm thầm:** Khi dữ liệu bị lỗi (xóa bài, rỗng tóm tắt, dữ liệu quá cũ), ứng dụng không hề bị sập hay báo lỗi màn hình đỏ, nhưng chất lượng tìm kiếm và câu trả lời của AI bị tụt dốc thảm hại (từ 100% xuống 70%). Nếu không có công cụ giám sát dữ liệu như Great Expectations, chúng em sẽ rất khó phát hiện ra nguyên nhân nằm ở tầng dữ liệu.
2. **Giá trị của việc lưu bản snapshot thô gốc:** Nhờ có file lưu trữ gốc `crossref_records.json` không bao giờ bị ghi đè, khi xảy ra sự cố, nhóm chỉ cần một lệnh chạy là có thể khôi phục lại 100% toàn bộ hệ thống về trạng thái sạch ban đầu một cách nhẹ nhàng.

---

## 11. Khó khăn khi ghép nối code và cách nhóm đã giải quyết

- **Khó khăn 1 (Lỗi thư viện):** Khi mới bắt đầu cài đặt môi trường bằng `uv sync`, nhóm bị lỗi không tìm thấy gói `sentence-transformers>=5.0.0` do trong file cấu hình template có sẵn bị gõ nhầm phiên bản. Bạn Trọng đã phát hiện ra trên trang PyPI bản mới nhất chỉ là 3.x, nên nhóm đã sửa lại thành `sentence-transformers>=3.0.0` và cài đặt thành công.
- **Khó khăn 2 (Xung đột ID trong ChromaDB):** Khi chạy qua lại giữa 3 trạng thái (Baseline, Corrupted, Repaired), ChromaDB dễ bị lỗi trùng ID do collection cũ vẫn còn lưu lại. Nhóm đã xử lý bằng cách trước khi thêm dữ liệu mới, hàm sẽ xóa trắng collection cũ rồi mới tạo mới lại từ đầu. Nhờ vậy script chạy nhiều lần vẫn không bị lỗi.
- **Khó khăn 3 (Xung đột Git khi merge):** Khi bạn Trang đẩy phần Observability lên nhánh riêng và merge vào nhánh `main` của bạn Trọng và Dương, xuất hiện xung đột ở các file database `chroma.sqlite3` và file json kết quả. Nhóm đã cùng ngồi lại giải quyết xung đột bằng lệnh merge an toàn, bảo đảm giữ lại đầy đủ công sức của cả 3 bạn.

---

## 12. Hạn chế và hướng phát triển nếu có thêm thời gian

| Hạn chế hiện tại | Ảnh hưởng | Hướng cải thiện thực tế |
| --- | --- | --- |
| Dữ liệu thử nghiệm mới có 24 bài báo | Chưa đo được tốc độ xử lý khi dữ liệu phình to lên hàng chục nghìn bài | Thử nghiệm pipeline với tập dữ liệu lớn hơn (khoảng 5,000 đến 10,000 bài) |
| Cảnh báo chất lượng mới ghi ra file báo cáo Markdown | Nhóm vận hành chưa nhận được thông báo ngay lập tức khi có sự cố | Tích hợp gửi tin nhắn cảnh báo tự động về Discord hoặc Telegram của nhóm |
| Quá trình sửa lỗi hiện tại là dựng lại toàn bộ (Full re-index) | Hơi tốn thời gian tính toán lại vector nếu dữ liệu có hàng triệu bài | Nâng cấp thành cơ chế sửa chữa gia tăng (chỉ sửa và tính lại vector cho những bài bị hỏng) |

---

## 13. Danh sách kiểm tra cuối cùng trước khi nộp bài

Nhóm đã rà soát kỹ và tự đánh dấu:

- [x] Thông tin nhóm (`Sloppers`) và tên repository đã điền chính xác.
- [x] Bảng phân công công việc khớp với phần việc thực tế của 3 thành viên.
- [x] Cả hai lệnh `run_phase1.py` và `run_corruption_flow.py` đều đã được chạy lại và ra kết quả exit code 0.
- [x] Cả 3 trạng thái (Baseline, Corrupted, Repaired) đều dùng chung bộ 10 câu hỏi đánh giá.
- [x] Bảng số liệu trong báo cáo khớp 100% với các file trong thư mục `data/results/`.
- [x] Kết luận về chất lượng và độ tươi khớp với các báo cáo trong `data/quality/`.
- [x] Mỗi thành viên đều có 1 file báo cáo cá nhân riêng biệt (`2A202602765_PhamHoangTrong.md`, `2A202602676_LamHaiDuong.md`, `2A202602678_LeThiThuyTrang.md`).
- [x] Tuyệt đối không có file `.env`, API key hay mật khẩu nào xuất hiện trong mã nguồn, báo cáo hay ảnh.
