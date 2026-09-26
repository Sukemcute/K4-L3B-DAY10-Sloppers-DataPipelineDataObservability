# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `Sloppers`
- **Mã Nhóm / Lớp:** `K4-L3B-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3B-DAY10-Sloppers-DataPipelineDataObservability`

---

## 👥 Danh Sách Thành Viên (Nhóm 3 người)

| STT | Họ và tên | MSSV | Vai trò chính | Phân công module code | Tỷ lệ đóng góp (% Contribution) | Báo cáo cá nhân |
|:---:|---|:---:|---|---|:---:|---|
| 1 | **Phạm Hoàng Trọng** | 2A202602765 | **Trưởng nhóm & Pipeline Integrator + Vector RAG** | `core/`, `retrieval/index.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `script/` | 34% | `report/2A202602765_PhamHoangTrong.md` |
| 2 | **Lâm Hải Dương** | 2A202602676 | **Data Foundation & Corruption & Repair** | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/ingestion/corruption.py`, raw snapshots | 33% | `report/2A202602676_LamHaiDuong.md` |
| 3 | **Lê Thị Thuỳ Trang** | 2A202602678 | **Data Observability & Benchmark Evaluation** | `src/observability/quality.py` (GX 1.x), `src/evaluation/testset.py`, `src/observability/reporting.py` | 33% | `report/2A202602678_LeThiThuyTrang.md` |

---

## 📝 Phân Công Công Việc Chi Tiết & Tự Khai Đóng Góp

### 1. Phạm Hoàng Trọng — MSSV: 2A202602765
- **Vai trò:** Trưởng nhóm & Pipeline Integrator + Vector RAG.
- **Công việc chi tiết:**
  - Quản lý cấu hình chung (`core/config.py`, `.env`), kiểm soát môi trường thực thi và bảo mật API keys.
  - Quản trị ChromaDB collections (`papers-baseline`, `papers-corrupted`, `papers-repaired`) và QA Agent.
  - Tích hợp và điều phối luồng toàn tuyến trong `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`.
  - Giám sát tiến độ commit GitHub của cả 3 thành viên, chuẩn bị Live Demo và tổng hợp `report/group_report.md`.
- **Đóng góp chính & Bài học:**
  - Nắm vững kiến trúc Idempotent Pipeline, điều phối các luồng dữ liệu đa tầng và quản lý state giữa các pha đánh giá.

### 2. Lâm Hải Dương — MSSV: 2A202602676
- **Vai trò:** Phụ trách Ingestion, Làm sạch & Tiêm lỗi/Phục hồi dữ liệu.
- **Công việc chi tiết:**
  - Xây dựng module thu thập Crossref API với cơ chế fallback đọc snapshot local trong `src/ingestion/crossref.py`.
  - Chuẩn hóa schema, tính toán trường `age_days` và định dạng `text_for_embedding` trong `src/ingestion/cleaning.py`.
  - Xây dựng 6 kịch bản tiêm lỗi thực nghiệm (Data Corruption Suite) và log trong `src/ingestion/corruption.py`.
  - Thực thi cơ chế Idempotent Repair khôi phục dữ liệu sạch từ bản lưu trữ thô ban đầu.
- **Đóng góp chính & Bài học:**
  - Hiểu sâu về Data Lineage, bảo toàn snapshot thô và nguyên lý tự phục hồi (Self-healing) trong data pipeline.

### 3. Lê Thị Thuỳ Trang — MSSV: 2A202602678
- **Vai trò:** Phụ trách Data Observability, Benchmark Testset & Reporting.
- **Công việc chi tiết:**
  - Thiết lập Quality Gate theo chuẩn mới **Great Expectations 1.x (Ephemeral Context)** và Freshness SLA trong `src/observability/quality.py`.
  - Xây dựng bộ đề benchmark đánh giá chuẩn hóa 10 câu hỏi qua 4 nhóm nghiệp vụ trong `src/evaluation/testset.py`.
  - Xây dựng các hàm kết xuất báo cáo Markdown `phase1_report.md` và `corruption_report.md` (bảng đối chiếu 3 trạng thái Baseline vs Corrupted vs Repaired) trong `src/observability/reporting.py`.
- **Đóng góp chính & Bài học:**
  - Làm chủ cú pháp GX 1.x mới nhất, kỹ thuật phát hiện sớm Silent Failure và đo lường định lượng sự suy giảm chất lượng của RAG Agent.
