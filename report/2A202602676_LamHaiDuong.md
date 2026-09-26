# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Lâm Hải Dương |
| MSSV | 2A202602676 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | Sloppers |
| Vai trò chính | Data Foundation & Corruption & Repair (`src/ingestion/`) |
| Repository | `K4-L3B-DAY10-Sloppers-DataPipelineDataObservability` |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Raw Data Ingestion & Lineage | `src/ingestion/crossref.py` (`parse_crossref_payload`, `fetch_source_records`, `load_raw_records`) | Cấu hình `Settings` hoặc snapshot `data/raw/crossref_response.json` | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` (24 bản ghi `PaperRecord`) | Hoàn thành |
| Data Cleaning & Pre-embed Modeling | `src/ingestion/cleaning.py` (`build_clean_dataframe`, `format_text_for_embedding`) | `list[PaperRecord]` và mốc thời gian `run_date` | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` (24 dòng sạch có `age_days` và `text_for_embedding` 5 phần) | Hoàn thành |
| Synthetic Data Corruption Suite (6 kịch bản) | `src/ingestion/corruption.py` (`corrupt_clean_dataframe`) | Clean DataFrame (24 dòng) | `data/clean/papers_clean_corrupted.csv`, `data/clean/papers_clean_corrupted.json` (21 dòng bẩn) và `data/results/corruption_log.json` | Hoàn thành |
| Idempotent Data Repair | Tái tạo từ `load_raw_records` + `build_clean_dataframe` | Raw snapshot bất biến `data/raw/crossref_records.json` | `data/clean/papers_clean_repaired.csv`, `data/clean/papers_clean_repaired.json` (khôi phục đủ 24 dòng sạch) | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Thống nhất Data Contract & Schema | Phạm Hoàng Trọng (`retrieval/index.py`, `pipelines/`) & Lê Thị Thuỳ Trang (`observability/quality.py`, `evaluation/testset.py`) | Đảm bảo DataFrame đầu ra có đầy đủ các cột `paper_id`, `title`, `summary`, `published`, `age_days`, `authors_joined`, `categories_joined`, `summary_chars`, `text_for_embedding` tương thích 100% với ChromaDB index và GX 1.x suite. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Thu thập và parse 24 bài báo từ Crossref payload, xóa thẻ JATS XML `<jats:p>` | `src/ingestion/crossref.py`, `data/raw/crossref_records.json` | 24 đối tượng `PaperRecord` đầy đủ DOI, tiêu đề, tóm tắt, tác giả, chủ đề và ngày xuất bản | Chạy `fetch_source_records(s)` in ra `Tín hiệu hoàn thành: Đã tải 24 bài báo` |
| Chuẩn hóa dữ liệu sạch, tính `age_days`, tạo cột `text_for_embedding` cấu trúc 5 phần | `src/ingestion/cleaning.py`, `data/clean/papers_clean.json` | DataFrame 24 dòng không trùng `paper_id`, chỉ có 1/24 bài có `age_days > 180` (`4.17% <= 25%` SLA) | Chạy `build_clean_dataframe(...)` in ra `Tín hiệu hoàn thành: Clean thành công 24 dòng` |
| Giả lập 6 kịch bản lỗi dữ liệu bẩn (drop latest, blank summary, inject noise, truncate title, stale date, duplicate rows) | `src/ingestion/corruption.py`, `data/results/corruption_log.json`, `data/clean/papers_clean_corrupted.json` | Tập dữ liệu bị làm bẩn gồm 21 dòng (xóa 5 bài mới nhất, nhân bản 2 dòng, 4 dòng rỗng summary, 4 dòng nhiễu, 5 dòng tiêu đề `< 8` ký tự, 9 dòng lùi ngày 400 ngày) | Kiểm tra `data/results/corruption_log.json` ghi nhận đủ 6 scenarios |
| Thực thi Idempotent Repair từ raw snapshot | `data/clean/papers_clean_repaired.csv`, `data/clean/papers_clean_repaired.json` | Khôi phục chính xác 24 bài báo sạch từ `data/raw/crossref_records.json` | Đối chiếu `papers_clean.json` và `papers_clean_repaired.json` khớp nhau 24 dòng |

Một output cụ thể mà phần việc của tôi tạo ra:
- File `data/results/corruption_log.json` ghi lại chi tiết thời điểm tiêm lỗi, số dòng ban đầu (`initial_rows: 24`), số dòng sau khi làm bẩn (`final_rows: 21`), và danh sách `affected_paper_ids` cùng tham số của cả 6 kịch bản làm bẩn dữ liệu.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Trong hệ thống RAG thực tế, dữ liệu đầu vào từ API bên ngoài (Crossref) thường chứa thẻ định dạng XML (`<jats:p>`), thiếu trường, trùng lặp hoặc có nguy cơ gặp lỗi mạng (`429`/`503`). Ngoài ra, nếu dữ liệu ở tầng phục vụ bị hỏng âm thầm (Silent Data Corruption) như mất bản ghi mới, rỗng tóm tắt, nhiễu văn bản, tiêu đề bị cắt ngắn hoặc dữ liệu quá hạn (stale), вектор index sẽ bị nhiễm bẩn mà không phát sinh ngoại lệ runtime. Module `src/ingestion/` giải quyết bài toán:
1. Bảo toàn dữ liệu gốc (Raw Data Lineage) có fallback offline.
2. Chuẩn hóa văn bản và xây dựng biểu diễn ngữ nghĩa 5 phần (`text_for_embedding`).
3. Cung cấp bộ giả lập 6 kịch bản lỗi (Corruption Suite) và cơ chế khôi phục bất biến (Idempotent Repair) từ nguồn raw.

### Cách triển khai

1. **`src/ingestion/crossref.py`:**
   - Xây dựng `_fetch_api_payload_with_retry` với cơ chế exponential backoff (3 lần thử) cho các mã lỗi `429, 500, 502, 503, 504`. Nếu `settings.refresh_source=False` hoặc mất kết nối mạng, tự động fallback đọc từ `data/raw/crossref_response.json`.
   - Trong `parse_crossref_payload`, dùng biểu thức chính quy `re.sub(r"<[^>]+>", " ", text)` kết hợp `normalize_whitespace` để loại bỏ toàn bộ thẻ JATS XML trong `abstract`, chuẩn hóa `date-parts` về định dạng ISO `YYYY-MM-DD`, trích xuất danh sách tác giả (`given` + `family`) và danh mục (`subject`).
2. **`src/ingestion/cleaning.py`:**
   - Trong `build_clean_dataframe`, chuẩn hóa mọi trường văn bản, parse ngày `published` theo múi giờ UTC và tính `age_days = max(0, (run_day - published_date).days)`.
   - Tạo cột `text_for_embedding` gồm 5 phần rõ ràng: `Title`, `Authors`, `Categories`, `Published`, `Summary`.
   - Khử trùng lặp bằng `drop_duplicates(subset=["paper_id"], keep="first")`, lọc bỏ các bản ghi có `title < 8` ký tự hoặc `summary_chars < 20`, và sắp xếp giảm dần theo `published`.
3. **`src/ingestion/corruption.py`:**
   - Trong `corrupt_clean_dataframe`, sắp xếp giảm dần theo ngày xuất bản và thực thi tuần tự 6 kịch bản:
     1. `drop_latest_records`: Cắt bỏ 20% (5/24) bài báo mới nhất (còn 19 dòng).
     2. `blank_summary`: Gán `summary = ""` trên 4 bản ghi.
     3. `inject_noise`: Chèn chuỗi nhiễu `@@@###$$$ NOISE_CORRUPTED_PAYLOAD_999 %%%^^^&&&` vào `summary` của 4 bản ghi.
     4. `truncate_title`: Cắt ngắn `title` xuống còn 5 ký tự (`< 8` ký tự) trên 5 bản ghi.
     5. `stale_date`: Lùi ngày `published` về quá khứ 400 ngày và cộng thêm `400` vào `age_days` trên 9 bản ghi để vi phạm ngưỡng Freshness SLA (> 25% bài quá hạn 180 ngày).
     6. `duplicate_rows`: Nhân bản 2 bản ghi đầu và nối vào cuối bảng (tổng cộng 21 dòng).
   - Sau khi tiêm lỗi, tính lại `summary_chars` và tái tạo `text_for_embedding` bằng `format_text_for_embedding` để các thay đổi lỗi thực sự đi vào vector index khi nhúng lại.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Payload JSON từ Crossref API / `data/raw/crossref_response.json`, cấu hình `Settings`, và `run_date: datetime` |
| Output | `list[PaperRecord]`, Clean/Corrupted/Repaired `pd.DataFrame`, các file CSV/JSON trong `data/raw/`, `data/clean/` và `data/results/corruption_log.json` |
| Module phụ thuộc | `src/core/config.py` (`Settings`, `Paths`), `src/core/utils.py` (`normalize_whitespace`, `compact_join`, `read_json`, `write_json`, `write_csv`) |
| Module sử dụng output | `src/observability/quality.py`, `src/evaluation/testset.py`, `src/retrieval/index.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` |
| Điều kiện lỗi cần xử lý | API trả về `429/503` hoặc mất mạng; bản ghi thiếu DOI/title/abstract; chuỗi abstract chứa thẻ XML `<jats:p>`; kiểu ngày tháng bị pandas ép kiểu khi đọc lại từ JSON |

### Cách xác minh

```powershell
$env:PYTHONUTF8="1"
uv run python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s=load_settings(); r=fetch_source_records(s); print(f'Tín hiệu hoàn thành: Đã tải {len(r)} bài báo')"
uv run python -c "from datetime import datetime, timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), datetime.now(timezone.utc)); print(f'Tín hiệu hoàn thành: Clean thành công {len(df)} dòng')"
```

- **Kết quả mong đợi:** Console in ra `Tín hiệu hoàn thành: Đã tải 24 bài báo` và `Tín hiệu hoàn thành: Clean thành công 24 dòng`.
- **Kết quả thực tế:** Khớp 100% với kỳ vọng (`Đã tải 24 bài báo`, `Clean thành công 24 dòng`), đồng thời sinh đầy đủ các file trong `data/clean/` và `data/results/corruption_log.json`.
- **Artifact/log:** `data/raw/crossref_records.json`, `data/clean/papers_clean.json`, `data/clean/papers_clean_corrupted.json`, `data/clean/papers_clean_repaired.json`, `data/results/corruption_log.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi tiêm lỗi trong `corrupt_clean_dataframe`, nếu chỉ sửa trực tiếp các cột `title`, `summary`, `published` mà giữ nguyên cột `text_for_embedding` đã tạo từ bước Clean, thì khi ChromaDB đánh chỉ mục lại (`LocalEmbeddingIndex.build`), mô hình embedding vẫn nhúng nội dung sạch cũ trong `text_for_embedding`.
- **Các phương án đã cân nhắc:**
  1. Chỉ sửa các cột metadata (`title`, `summary`, `published`) để làm fail các bài kiểm tra Great Expectations.
  2. Tách hàm dùng chung `format_text_for_embedding` trong `src/ingestion/cleaning.py` và gọi lại ở bước 7 của `corrupt_clean_dataframe` để tái tạo `text_for_embedding` từ các trường đã bị làm bẩn.
- **Phương án đã chọn:** Phương án 2 — tái tạo `text_for_embedding` và `summary_chars` sau khi áp dụng cả 6 kịch bản lỗi.
- **Lý do:** Đảm bảo tính nhất quán dữ liệu giữa các cột thành phần và văn bản dùng để sinh vector embedding, giúp phản ánh trung thực tác động của dữ liệu bẩn lên cả tầng Data Quality Gate lẫn tầng Semantic Retrieval của RAG Agent.
- **Bằng chứng quyết định phù hợp:** Trong `data/clean/papers_clean_corrupted.json`, các bản ghi bị xóa tóm tắt hoặc chèn chuỗi `NOISE_CORRUPTED_PAYLOAD_999` đều được cập nhật trực tiếp vào `text_for_embedding`.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  UnicodeEncodeError: 'charmap' codec can't encode characters in position 6-7: character maps to <undefined>
  ```
- **Lệnh hoặc bước tái hiện:** Chạy lệnh kiểm chứng tiếng Việt `uv run python -c "... print('Môi trường sẵn sàng')"` trực tiếp trên Windows PowerShell mặc định.
- **Nguyên nhân gốc:** Console mặc định trên Windows sử dụng bảng mã `cp1252` cho `stdout` khi gọi Python qua subshell, không mã hóa được các ký tự tiếng Việt có dấu (`ườ`, `ệ`).
- **Cách xử lý:** Thiết lập biến môi trường `$env:PYTHONUTF8="1"` trên PowerShell và đảm bảo toàn bộ các hàm đọc/ghi file trong pipeline đều chỉ định rõ `encoding="utf-8"`.
- **Cách xác minh sau khi sửa:** Chạy lại lệnh kiểm chứng với `$env:PYTHONUTF8="1"`, lệnh thoát với `exit code 0` và hiển thị chính xác chuỗi tiếng Việt.
- **Điều học được:** Trên môi trường Windows đa nền tảng, luôn cần chuẩn hóa UTF-8 cho cả I/O file lẫn luồng standard output khi tích hợp tự động hóa.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Dữ liệu thô từ Crossref API (hoặc snapshot `crossref_response.json`) được `parse_crossref_payload` bóc tách thành danh sách `PaperRecord` (`crossref_records.json`). Sau đó `build_clean_dataframe` làm sạch thẻ XML, chuẩn hóa ngày tháng, tính `age_days`, khử trùng lặp và ghép 5 trường thông tin thành `text_for_embedding` (`papers_clean.json`). Cuối cùng, `LocalEmbeddingIndex.build` dùng mô hình `sentence-transformers/all-MiniLM-L6-v2` mã hóa cột `text_for_embedding` thành vector và nạp cùng metadata vào ChromaDB collection (`papers-baseline`).
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Mỗi câu hỏi trong `test_set.json` gắn với `ground_truth_doc_ids` (chứa `paper_id` gốc) và câu trả lời chuẩn `ground_truth`. Khi RAG truy vấn top-$k$ tài liệu, nếu `ground_truth_doc_ids` xuất hiện trong `retrieved_doc_ids` thì tính là một Retrieval Hit (`retrieval_hit_rate`). Câu trả lời sinh ra được so khớp từ vựng với `ground_truth` qua `token_f1` và chấm điểm ngữ nghĩa qua LLM Judge (`judge_accuracy`, `mean_judge_score`).
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   Quality checks (Great Expectations 1.x) kiểm tra tính toàn vẹn cấu trúc và nội dung tĩnh của bảng dữ liệu (số lượng dòng, không null, tính duy nhất của `paper_id`, độ dài hợp lệ của `title` và `summary`). Ngược lại, Freshness monitoring kiểm tra tính kịp thời theo thời gian (temporal SLA) thông qua cột `age_days = (run_date - published).days`, cảnh báo `is_fresh = False` khi tỷ lệ bài báo cũ hơn 180 ngày vượt quá 25%.
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Giữ cố định tập câu hỏi đánh giá (`test_set.json`) là biến kiểm soát bắt buộc để phép so sánh giữa 3 trạng thái có ý nghĩa nhân quả: mọi sự sụt giảm chỉ số ở trạng thái Corrupted và sự phục hồi ở trạng thái Repaired đều đến từ chất lượng dữ liệu trong index chứ không phải do độ khó của câu hỏi thay đổi.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Repair thành công khi tập dữ liệu phục hồi (`papers_clean_repaired.json`) được tái tạo idempotent từ nguồn raw (`crossref_records.json`), vượt qua 100% bài kiểm tra GX 1.x (`success = True`) và Freshness SLA (`is_fresh = True`), đồng thời các chỉ số `retrieval_hit_rate` và `mean_token_f1` trong `repaired_metrics.json` phục hồi về mức tương đương `baseline_metrics.json`.

## 8. Phân tích kết quả

### Metrics chính (Phạm vi Data Ingestion, Corruption & Repair đã hoàn thành)

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| Số dòng dữ liệu (`row_count`) | 24 | 21 | 24 | Corrupted mất 5 bài mới nhất và thêm 2 dòng trùng lặp; Repaired khôi phục đúng 24 dòng gốc. |
| Số dòng trùng `paper_id` | 0 | 2 | 0 | Kịch bản `duplicate_rows` tạo 2 bản ghi trùng DOI (`3671824`, `3671823`). |
| Số dòng vi phạm độ dài `title < 8` | 0 | 5 | 0 | Kịch bản `truncate_title` cắt tiêu đề xuống 5 ký tự. |
| Số dòng rỗng/nhiễu `summary` | 0 | 8 (4 rỗng + 4 nhiễu) | 0 | Làm mất thông tin tóm tắt và gây nhiễu vector embedding. |
| Tỷ lệ bài quá hạn `age_days > 180` | 4.17% (1/24) | 47.62% (10/21) | 4.17% (1/24) | Kịch bản `stale_date` đẩy tỷ lệ quá hạn vượt ngưỡng SLA 25% (`is_fresh = False`). |
| `retrieval_hit_rate` / `mean_token_f1` | *(Chờ tích hợp nhóm)* | *(Chờ tích hợp nhóm)* | *(Chờ tích hợp nhóm)* | Sẽ được cập nhật vào `group_report.md` khi ghép với module `evaluation` và `pipelines` của nhóm. |

### Kết luận từ số liệu

1. **Chuỗi nguyên nhân – bằng chứng 1 (Corruption):** Việc áp dụng 6 kịch bản trong `src/ingestion/corruption.py` (xóa 5 bài mới nhất, làm rỗng 4 summary, chèn nhiễu 4 summary, cắt ngắn 5 tiêu đề, lùi ngày xuất bản 9 bài thêm 400 ngày, nhân bản 2 dòng — lưu tại `data/results/corruption_log.json`) $\rightarrow$ làm tỷ lệ bài quá hạn tăng vọt từ `4.17%` lên `47.62%` (vượt trần 25% Freshness SLA) và phá vỡ tính duy nhất của `paper_id` cũng như độ dài tối thiểu của `title`/`summary` $\rightarrow$ làm hỏng trực tiếp cả khóa tra cứu chính xác theo tiêu đề lẫn chất lượng ngữ cảnh trong `text_for_embedding`.
2. **Chuỗi nguyên nhân – bằng chứng 2 (Repair):** Thực thi cơ chế Idempotent Repair bằng cách nạp lại bản lưu trữ bất biến `data/raw/crossref_records.json` qua `build_clean_dataframe` $\rightarrow$ loại bỏ hoàn toàn các dòng trùng lặp, khôi phục đủ 24 bài báo sạch vào `data/clean/papers_clean_repaired.json` và đưa tỷ lệ bài quá hạn về lại `4.17% <= 25%` $\rightarrow$ phục hồi hoàn toàn chất lượng dữ liệu đầu vào cho Vector Store.

**Corruption nào ảnh hưởng rõ nhất và vì sao?**
Kịch bản **`drop_latest_records`** (kết hợp với **`truncate_title`** và **`blank_summary`**) gây tác động nặng nề nhất. Khi 20% bản ghi mới nhất bị xóa khỏi tập dữ liệu, mọi truy vấn nhắm vào các bài báo đó hoàn toàn mất ground-truth document trong ChromaDB (Retrieval Hit chắc chắn bằng 0). Đồng thời, `truncate_title` làm gãy cơ chế exact-title lookup của QA Agent và `blank_summary` khiến câu trả lời trích xuất từ tóm tắt trở thành chuỗi rỗng.

**Kết quả nào khác với kỳ vọng ban đầu?**
Khi kiểm tra tập dữ liệu sạch ban đầu với ngày chạy hiện tại (`2026-09-26`), có 1 bài báo (`10.1145/3637528.3671805`, xuất bản ngày `2026-03-28`) có `age_days = 182 > 180`. Tuy nhiên, nhờ quy định Freshness SLA cho phép tối đa 25% bản ghi quá hạn, tỷ lệ `1/24 = 4.17%` vẫn hoàn toàn đạt chuẩn `is_fresh = True`.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline:** Việc lưu trữ tách biệt tầng Raw (`data/raw/crossref_response.json`, `crossref_records.json`) và tầng Clean (`data/clean/`) là nền tảng bắt buộc để xây dựng pipeline có tính **Idempotent** và khả năng tự phục hồi (**Self-healing**) khi tầng serving bị lỗi.
2. **Về Data Quality/Observability:** Các lỗi dữ liệu như chuỗi rỗng `""`, nhiễu văn bản hay ngày xuất bản cũ không gây ra lỗi cú pháp Python nhưng làm suy giảm nghiêm trọng chất lượng hệ thống; do đó cần kết hợp cả kiểm định cấu trúc/độ dài (GX 1.x) lẫn giám sát độ tươi (Freshness SLA).
3. **Về ảnh hưởng của Data đến RAG Agent:** Chất lượng câu trả lời của RAG phụ thuộc trực tiếp vào cấu trúc của `text_for_embedding` và độ chính xác của metadata (`title`, `summary`, `published`) trong Vector Store.

### Nếu có thêm thời gian

Tôi sẽ bổ sung cơ chế **Checksum/Hash Verification (SHA-256)** cho các file snapshot trong `data/raw/` trước khi chạy luồng Repair để đảm bảo bản thân nguồn dữ liệu thô chưa bị can thiệp trái phép trước khi khôi phục tầng Clean.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Lâm Hải Dương
**Ngày xác nhận:** 2026-09-26
