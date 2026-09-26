# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| **Họ và tên** | Lê Thị Thuỳ Trang |
| **MSSV** | 2A202602678 |
| **Khóa/Lớp** | K4-L3B |
| **Tên nhóm** | Sloppers |
| **Vai trò chính** | Data Observability & Benchmark Evaluation (`src/observability/`, `src/evaluation/testset.py`) |
| **Repository** | `K4-L3B-DAY10-Sloppers-DataPipelineDataObservability` |
| **Ngày hoàn thành** | 2026-09-26 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu chính

| Module / Deliverable | File / Hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| **Data Observability Gate (GX 1.x)** | `src/observability/quality.py` (`run_data_quality_checks`, `evaluate_freshness_sla`, `build_freshness_report`) | DataFrame (`papers_clean.json` hoặc corrupted/repaired) và `Settings` | `data/quality/baseline_quality_report.json`, `corrupted_quality_report.json`, `freshness_report.json` | **Hoàn thành** |
| **Freshness SLA Monitoring** | `src/observability/quality.py` (`evaluate_freshness_sla`) | Cột `age_days` và `published` trong DataFrame | Cảnh báo vi phạm SLA (`is_fresh: bool`), tỷ lệ `stale_ratio` | **Hoàn thành** |
| **Benchmark Testset Suite** | `src/evaluation/testset.py` (`build_test_set`) | Clean DataFrame (24 dòng) | `data/eval/test_set.json` (10 câu hỏi chuẩn hóa qua 4 nhóm nghiệp vụ) | **Hoàn thành** |
| **Multi-Stage Reporting** | `src/observability/reporting.py` (`generate_phase1_report`, `generate_corruption_report`) | Metrics đánh giá và kết quả Quality Gate qua các pha | `data/reports/phase1_report.md` và `data/reports/corruption_report.md` | **Hoàn thành** |

### Hoạt động phối hợp với các thành viên khác

| Hoạt động | Thành viên phối hợp | Kết quả đạt được |
| --- | --- | --- |
| **Data Contract & Schema Alignment** | Lâm Hải Dương (`src/ingestion/`) | Đồng nhất các trường dữ liệu bắt buộc (`paper_id`, `title`, `summary`, `text_for_embedding`, `age_days`, `authors_joined`, `categories_joined`) để chốt Quality Gate và Testset builder hoạt động trơn tru. |
| **Pipeline Integration & Evaluation** | Phạm Hoàng Trọng (`src/pipelines/`, `retrieval/`) | Tích hợp bộ Testset và hàm báo cáo vào toàn tuyến `run_phase1.py` và `run_corruption_flow.py`, đo lường chính xác các chỉ số Retrieval Hit Rate và Token F1. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | Artifact bàn giao | Kết quả định lượng | Phương thức xác minh |
| --- | --- | --- | --- |
| **Xây dựng Data Quality Gate GX 1.x** | `src/observability/quality.py`, `baseline_quality_report.json` | Đạt **100% Passed** trên dữ liệu sạch (6/6 expectations thành công, `success = True`). Phát hiện chính xác lỗi khi dữ liệu bị tiêm lỗi bẩn. | `uv run python -c "from observability.quality import run_data_quality_checks; ..."` |
| **Giám sát Freshness SLA** | `data/quality/freshness_report.json` | Đo lường tỷ lệ bài quá hạn 180 ngày. Trên tập sạch: `4.17% <= 25%` SLA $\rightarrow$ `is_fresh = True`. Trên tập tiêm lỗi stale: `is_fresh = False`. | Đọc trực tiếp trường `is_fresh` và `stale_ratio` trong report |
| **Tạo bộ đề Benchmark 10 câu hỏi** | `src/evaluation/testset.py`, `data/eval/test_set.json` | 10 câu hỏi phủ đủ 4 nhóm: 3 `summary`, 3 `authors`, 2 `date`, 2 `categories`. | Kiểm tra file `test_set.json` có đủ 10 items có kèm ground truth |
| **Xuất báo cáo đối chiếu 3 trạng thái** | `src/observability/reporting.py`, `corruption_report.md` | Bảng so sánh chi tiết: **Baseline vs Corrupted vs Repaired**, làm rõ hiện tượng Silent Failure và năng lực tự phục hồi. | Xem file `data/reports/corruption_report.md` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### 4.1. Vấn đề kỹ thuật cần giải quyết
Trong các hệ thống RAG đưa vào môi trường production, **dữ liệu bẩn thường không gây crash code mà gây ra hiện tượng Silent Failure (thất bại trong im lặng)**:
1. Thiếu thông tin hoặc tóm tắt rỗng khiến vector embedding bị sai lệch, dẫn tới hallucination.
2. Dữ liệu bị duplicate khiến kết quả tìm kiếm top-k bị loãng.
3. Dữ liệu trôi dạt theo thời gian (Data Drift/Stale data) khiến câu trả lời của mô hình bị lỗi thời mà hệ thống không có cảnh báo.

Vì vậy, vai trò Observability & Evaluation giải quyết 3 bài toán:
- Thiết lập chốt kiểm dịch nghiêm ngặt chặn đứng dữ liệu bẩn trước khi ghi vào Vector Store.
- Giám sát độ tươi mới dữ liệu theo cam kết dịch vụ (Freshness SLA).
- Xây dựng thước đo khách quan (Benchmark Testset) để đo lường mức độ suy giảm khi có sự cố và sự phục hồi của hệ thống.

### 4.2. Cách triển khai chi tiết

#### 1. Great Expectations 1.x Ephemeral Context (`src/observability/quality.py`):
Thay vì sử dụng cấu hình YAML tĩnh cồng kềnh của phiên bản cũ GX 0.x, tôi triển khai chuẩn **Ephemeral Context** mới nhất trên GX 1.x:
```python
context = gx.get_context(mode="ephemeral")
data_source = context.data_sources.add_pandas(name=source_name)
data_asset = data_source.add_dataframe_asset(name=asset_name)
batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
batch = batch_def.get_batch(batch_parameters={"dataframe": df})
```
Tôi thiết lập 4 hàng rào kiểm định bắt buộc:
- `gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000)`: Chặn sự cố API mất mát dữ liệu hoặc rỗng tập bản ghi.
- `gxe.ExpectColumnValuesToNotBeNull`: Đảm bảo các cột `paper_id`, `title`, `text_for_embedding` không bị khuyết thiếu.
- `gxe.ExpectColumnValuesToBeUnique("paper_id")`: Đảm bảo tính toàn vẹn thực thể (không bị trùng DOI).
- `gxe.ExpectColumnValueLengthsToBeBetween("summary", min_value=30)`: Chặn tóm tắt quá ngắn không đủ ngữ cảnh phục vụ retrieval.

#### 2. Giám sát Freshness SLA:
- Đo lường tuổi thọ tài liệu: `age_days = (run_date - published).days`.
- Ngưỡng SLA: 180 ngày.
- Nếu tỷ lệ bài báo cũ `stale_ratio = (stale_rows / total_rows) > 0.25` (vượt 25%), hệ thống tự động gắn cờ cảnh báo `is_fresh = False`.

#### 3. Bộ Đề Benchmark Chuẩn Hóa (`src/evaluation/testset.py`):
- Tự động sinh 10 câu hỏi đa dạng trải rộng 4 nhóm: `summary`, `authors`, `date`, `categories`.
- Bao bọc tiêu đề bài báo trong nháy đơn `'...'` để tương thích chính xác với regex lookup của `src/retrieval/qa.py`, đảm bảo trích xuất chính xác Ground Truth.

#### 4. Báo Cáo Đối Chiếu 3 Trạng Thái (`src/observability/reporting.py`):
- Kết xuất bảng đối chiếu Markdown 3 cột: **Baseline vs Corrupted vs Repaired**.
- Định lượng hóa sự sụp đổ chỉ số khi bị tiêm lỗi và sự phục hồi về mức chuẩn ban đầu sau khi chạy Idempotent Repair.

---

## 5. Thử nghiệm và bằng chứng (Testing & Verification)

### 5.1. Lệnh kiểm thử đã chạy và kết quả

#### Nghiệm thu Chốt Quality Gate trên dữ liệu sạch:
```powershell
uv run python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print('Quality check status =', res['success'])"
```
👉 **Kết quả:** `Quality check status = True` (100% Expectations Passed, `is_fresh = True`).

#### Nghiệm thu Sinh bộ đề Benchmark 10 câu hỏi:
```powershell
uv run python -c "from core.config import load_settings; from evaluation.testset import build_test_set; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); ts=build_test_set(df, s.paths.eval_testset); print('Sinh duoc:', len(ts), 'cau hoi test')"
```
👉 **Kết quả:** `Sinh duoc: 10 cau hoi test` (Được lưu ra `data/eval/test_set.json`).

#### Minh chứng phát hiện lỗi (Failure Case Verification):
- **Trường hợp vi phạm Duplicate ID:** Thử nghiệm với DataFrame chứa `paper_id` trùng lặp $\rightarrow$ GX 1.x lập tức phát hiện và trả về `success = False` với `failed_expectations = 1`.
- **Trường hợp vi phạm Freshness SLA:** Thử nghiệm với DataFrame bị lùi ngày xuất bản quá hạn $\rightarrow$ `is_fresh = False` và `success = False`.

---

## 6. Tự đánh giá và cam kết

### 6.1. Mức độ hoàn thành
- **Tiêu chuẩn hoàn thành:** 100% các yêu cầu thuộc vai trò Observability & Evaluation.
- **Tuân thủ quy định:** Áp dụng đúng chuẩn mới nhất **Great Expectations 1.x**, không dùng cú pháp cũ gây lỗi; mã nguồn module hóa sạch sẽ, có xử lý ngoại lệ đầy đủ.

### 6.2. Điểm số tự đánh giá
- **Điểm tự chấm cho vai trò cá nhân:** `100 / 100`.

### 6.3. Cam kết liêm chính học thuật
- Toàn bộ mã nguồn và báo cáo được nhóm tự tìm hiểu, triển khai và kiểm chứng trên dữ liệu thực tế của bài lab.
- Không sao chép mã nguồn hoặc số liệu từ bất kỳ nhóm nào khác.
- Tôi đã hiểu rõ toàn bộ luồng logic kỹ thuật và sẵn sàng trả lời phản biện trước Giảng viên và Mentor.
