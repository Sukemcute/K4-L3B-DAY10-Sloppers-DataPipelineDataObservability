# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Phạm Hoàng Trọng |
| MSSV | 2A202602765 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | Sloppers |
| Vai trò chính | Trưởng nhóm & Pipeline Integrator + Vector RAG (`core/`, `src/retrieval/index.py`, `src/pipelines/`, `script/`) |
| Repository | `K4-L3B-DAY10-Sloppers-DataPipelineDataObservability` |
| Ngày hoàn thành | 2026-09-26 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Cấu hình & Môi trường thực thi | `src/core/config.py`, `.env.example`, `pyproject.toml` | Biến môi trường, cài đặt đường dẫn hệ thống | `Settings` object, bảo mật API key, quản lý `uv` virtualenv | Hoàn thành |
| Vector Indexing & ChromaDB Management | `src/retrieval/index.py` (`build_vector_index`) | Clean DataFrame (24 dòng) & Embedding model `all-MiniLM-L6-v2` | ChromaDB collections (`papers-baseline`, `papers-corrupted`, `papers-repaired`), metadata manifest | Hoàn thành |
| Orchestration Phase 1 Pipeline | `src/pipelines/phase1.py`, `script/run_phase1.py` | Toàn bộ các module con (Ingestion, Retrieval, Observability, Evaluation) | Chạy thông suốt Baseline pipeline, sinh đủ artifacts ở `data/` | Hoàn thành |
| Orchestration Multi-State Flow | `src/pipelines/corruption_flow.py`, `script/run_corruption_flow.py` | Pipeline Baseline + Tiêm 6 kịch bản lỗi + Khôi phục sạch từ raw | Chạy đối chiếu 3 trạng thái Baseline -> Corrupted -> Repaired | Hoàn thành |
| Quản lý nhóm & Tổng hợp báo cáo | `docs/TEAM.md`, `report/group_report.md` | Báo cáo tiến độ và commits của 3 thành viên | Phân công công việc công bằng, giải quyết xung đột nhánh Git | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Hỗ trợ Ingestion & Lineage | Lâm Hải Dương (`src/ingestion/`) | Thống nhất cấu trúc dữ liệu `text_for_embedding` gồm 5 trường để đưa vào embedding model một cách nhất quán |
| Hỗ trợ Testset & Quality Gate | Lê Thị Thuỳ Trang (`src/observability/`, `src/evaluation/`) | Cùng Trang rà soát cú pháp Great Expectations 1.x Ephemeral Context và chỉnh testset câu hỏi khớp với regex trích xuất tiêu đề trong QA agent |
| Xử lý xung đột Git nhánh | Cả nhóm (Dương, Trang) | Thực hiện merge nhánh `trangltt/evaluation_n_observability` và `main` an toàn, bảo toàn toàn bộ kết quả của các bạn |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Quản lý cấu hình tập trung và cơ chế an toàn cho API keys | `src/core/config.py`, `.env.example` | Class `Settings` tự động nhận diện thư mục gốc, cấu hình ChromaDB path, không hardcode path tuyệt đối | `python -c "from src.core.config import Settings; print(Settings().chroma_dir)"` |
| Xây dựng hàm index dữ liệu vào ChromaDB đa collection | `src/retrieval/index.py` | Tạo thành công 3 collection riêng biệt (`papers-baseline`, `papers-corrupted`, `papers-repaired`) | Thư mục `data/chroma/` chứa đủ vector database có thể truy vấn |
| Tích hợp luồng chạy Phase 1 | `src/pipelines/phase1.py`, `script/run_phase1.py` | Pipeline chạy mượt mà từ tải dữ liệu, clean, index, đánh giá QA đến kiểm tra chất lượng và xuất file Markdown | Chạy `python script/run_phase1.py` kết thúc exit code 0 |
| Tích hợp luồng thực nghiệm tiêm lỗi & phục hồi | `src/pipelines/corruption_flow.py`, `script/run_corruption_flow.py` | Pipeline chạy thông suốt toàn bộ chu trình 3 trạng thái, in rõ ràng các bước và sinh báo cáo so sánh | Chạy `python script/run_corruption_flow.py` kết thúc exit code 0 |

Một output cụ thể mà phần việc của tôi tạo ra:
- Bộ kịch bản điều phối thực thi hoàn chỉnh trong `script/run_phase1.py` và `script/run_corruption_flow.py`. Khi chạy hai script này, toàn bộ hệ sinh thái của dự án tự động kết nối với nhau nhịp nhàng: từ khâu lấy dữ liệu thô, làm sạch, lập chỉ mục vector, kiểm tra Great Expectations, chạy bộ 10 câu hỏi đánh giá RAG, giả lập lỗi rồi tự phục hồi lại, xuất đầy đủ 100% metrics và báo cáo đối chiếu.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Trong một dự án xây dựng RAG Agent có tích hợp Data Observability, mỗi thành viên làm một module riêng: Dương làm phần dữ liệu đầu vào và tạo kịch bản lỗi, Trang làm phần kiểm thử chất lượng dữ liệu và bộ câu hỏi đánh giá. Nếu không có một người điều phối kỹ thuật ở giữa:
1. Các module sẽ bị lệch contract (ví dụ: tên cột dataframe không khớp giữa hàm clean của Dương và hàm tạo batch của Trang).
2. ChromaDB nếu không được quản lý cẩn thận sẽ dễ bị ghi đè, trùng lặp vector hoặc lẫn lộn dữ liệu giữa các lần chạy.
3. Không có một pipeline khép kín, tự động để chạy một lệnh duy nhất là tái hiện được toàn bộ kết quả thực nghiệm.

### Cách triển khai

1. **Quản lý Vector Indexing trong `src/retrieval/index.py`:**
   - Sử dụng thư viện `chromadb.PersistentClient` với đường dẫn cấu hình động từ `Settings`.
   - Để đảm bảo tính Idempotent (chạy lại nhiều lần không bị lỗi trùng ID hay phình to dữ liệu), trước khi add tài liệu mới vào collection, em chủ động gọi `client.delete_collection(name)` nếu collection đã tồn tại, sau đó mới tạo mới lại bằng `client.create_collection(name, metadata={"hnsw:space": "cosine"})`.
   - Đóng gói tài liệu kèm metadata phong phú (title, published, authors, age_days) để phục vụ việc trích xuất và giải thích nguồn tài liệu sau này.

2. **Điều phối luồng Phase 1 trong `src/pipelines/phase1.py`:**
   - Kết nối dữ liệu theo đúng thứ tự logic: Tải dữ liệu từ Crossref -> Lưu raw snapshot -> Làm sạch và kiểm tra schema -> Đưa vào ChromaDB (`papers-baseline`) -> Tạo bộ đề đánh giá 10 câu hỏi -> Chạy đánh giá RAG agent -> Kiểm tra bộ luật Great Expectations & Freshness SLA -> Xuất báo cáo Markdown `phase1_report.md`.

3. **Điều phối luồng đa trạng thái trong `src/pipelines/corruption_flow.py`:**
   - Duy trì nguyên tắc kiểm nghiệm khoa học: **Giữ nguyên 10 câu hỏi của benchmark test set** trong suốt cả 3 giai đoạn (Baseline, Corrupted, Repaired).
   - Ở giai đoạn Corrupted: lấy dữ liệu bị làm bẩn, index vào collection `papers-corrupted`, đo đạc sự tụt giảm của hit rate và F1, kiểm tra các cảnh báo đỏ của Great Expectations.
   - Ở giai đoạn Repaired: đọc lại từ snapshot gốc `crossref_records.json`, làm sạch lại từ đầu, index vào collection `papers-repaired`, chứng minh hệ thống phục hồi lại trạng thái xanh 100%.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Cấu hình hệ thống, dữ liệu bài báo từ module `ingestion`, bộ kiểm thử từ `observability` & `evaluation` |
| Output | ChromaDB collections, báo cáo tổng hợp `corruption_report.md`, kết quả so sánh metrics |
| Module phụ thuộc | Toàn bộ các module con trong `src/` |
| Module sử dụng output | Người chấm bài, lệnh chạy sanity check, live demo của nhóm |
| Điều kiện lỗi cần xử lý | Mất kết nối internet, collection ChromaDB bị lock, thiếu file raw snapshot, lỗi cú pháp thư viện |

### Cách xác minh

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Cả hai lệnh chạy tuần tự không văng Exception nào, in ra log rõ ràng từng bước và hoàn thành với exit code 0.
- **Kết quả thực tế:** Cả 2 script đều chạy trơn tru, hiển thị đầy đủ các thông số đo lường trước và sau khi tiêm lỗi.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi khởi tạo ChromaDB vector collection giữa các lần chạy thử nghiệm (`run_phase1.py` hoặc `run_corruption_flow.py`), ChromaDB mặc định sẽ báo lỗi `UniqueConstraintError` hoặc lưu đè trùng lặp vector nếu ID bản ghi đã tồn tại trong collection cũ.
- **Các phương án đã cân nhắc:**
  - *Phương án A:* Dùng `collection.upsert(...)` để cập nhật từng bản ghi cũ hoặc thêm mới nếu chưa có.
  - *Phương án B:* Kiểm tra nếu collection đã tồn tại thì xóa trắng collection đó đi (`client.delete_collection`) rồi mới `create_collection` và add toàn bộ bản ghi mới vào.
- **Phương án đã chọn:** Chọn **Phương án B (Delete & Re-create)**.
- **Lý do:** Ở bài lab này, kích thước dữ liệu vừa phải (24 bài báo). Phương án B đảm bảo tính **Idempotent tuyệt đối**: mỗi lần chạy pipeline là một lần dựng lại vector store sạch sẽ từ đầu, tránh hoàn toàn nguy cơ rác dữ liệu còn sót lại từ lần chạy trước (đặc biệt khi chuyển đổi qua lại giữa tập Corrupted 21 bài và tập Sạch 24 bài).
- **Bằng chứng quyết định phù hợp:** Pipeline chạy lặp lại nhiều lần trên máy em và máy các bạn trong nhóm mà không hề bị lỗi xung đột ID hay sai lệch số lượng vector trong ChromaDB.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Khi cả nhóm bắt đầu cài đặt môi trường bằng lệnh `uv sync` hoặc `pip install -e .`, terminal báo lỗi không tìm thấy phiên bản package:
  `ERROR: Could not find a version that satisfies the requirement sentence-transformers>=5.0.0 (from day10-data-observability-lab-student)`
- **Lệnh hoặc bước tái hiện:** Chạy `uv sync` ngay sau khi clone repo mẫu về máy.
- **Nguyên nhân gốc:** Trong file cấu hình `pyproject.toml` và `requirements.txt` của đề bài có một lỗi gõ nhầm (typo) ghi là `sentence-transformers>=5.0.0`. Trong khi đó, tại thời điểm hiện tại trên kho PyPI chính thức của Python, thư viện `sentence-transformers` phiên bản mới nhất mới chỉ là `3.x`, hoàn toàn chưa có phiên bản `5.0.0`.
- **Cách xử lý:** Em đã vào `pyproject.toml` và `requirements.txt`, sửa điều kiện phiên bản thành `sentence-transformers>=3.0.0`. Sau đó chạy lại `uv sync`, toàn bộ 158 thư viện phụ thuộc đã được cài đặt thành công mà không gặp bất kỳ lỗi nào.
- **Cách xác minh sau khi sửa:** Chạy kiểm tra nạp mô hình:
  `python -c "from sentence_transformers import SentenceTransformer; print('OK')"` -> in ra `OK`.
- **Điều học được:** Khi bắt đầu một dự án mới, cần chủ động kiểm tra kỹ các file đặc tả phụ thuộc (dependency specifications) thay vì phụ thuộc hoàn toàn vào file template có sẵn, vì các template đôi khi cũng có thể chứa lỗi typo từ phía người soạn đề.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   - Đầu tiên, hàm thu thập gửi request đến Crossref REST API (hoặc đọc từ file snapshot lưu trữ local nếu mất mạng). Dữ liệu JSON thô chứa các trường phức tạp và thẻ XML `<jats:p>` được lọc sạch, chuyển thành danh sách các đối tượng chuẩn `PaperRecord`.
   - Tiếp theo, hàm clean sẽ chuẩn hóa dữ liệu vào bảng DataFrame của Pandas, tính toán số ngày xuất bản (`age_days`) và ghép thành chuỗi văn bản hoàn chỉnh `text_for_embedding` gồm 5 phần (Title, Authors, Categories, Published, Summary).
   - Cuối cùng, chuỗi văn bản này được đưa qua mô hình nhúng `all-MiniLM-L6-v2` để biến thành vector 384 chiều và lưu vào cơ sở dữ liệu vector ChromaDB cùng với các trường metadata tương ứng.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - Evaluation set gồm 10 câu hỏi đa dạng (hỏi tóm tắt, tác giả, ngày công bố, danh mục). Mỗi câu hỏi đi kèm với một `ground_truth_doc_id` (chính là DOI/ID của bài báo chứa câu trả lời đúng) và câu trả lời mẫu `ground_truth_answer`.
   - Khi chạy đánh giá, câu hỏi được đưa vào hệ thống RAG để truy vấn ra top 3 bài báo có độ tương đồng ngữ nghĩa cao nhất.
   - Để đo **Retrieval Hit Rate**: hệ thống kiểm tra xem `ground_truth_doc_id` có nằm trong top 3 bài báo được trả về hay không. Nếu có thì tính là 1 điểm hit, ngược lại là 0.
   - Để đo **Answer Quality**: câu trả lời sinh ra từ mô hình được so sánh với câu trả lời mẫu bằng chỉ số **Token F1** (độ trùng lặp từ ngữ) và điểm chấm **Judge Score** từ 1 đến 5 để đánh giá độ chính xác về mặt nội dung.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks (thực hiện qua Great Expectations):** Tập trung kiểm tra cấu trúc dữ liệu tĩnh và tính toàn vẹn (Data Integrity): số lượng dòng có nằm trong khoảng cho phép không, các cột khóa chính (`paper_id`, `title`) có bị null hoặc rỗng không, ID có bị trùng lặp không, độ dài tóm tắt có bị bất thường không.
   - **Freshness monitoring:** Tập trung vào yếu tố thời gian và sự cập nhật của dữ liệu (Data Timeliness / Staleness): đo lường xem dữ liệu trong kho có bị quá cũ so với mốc thời gian hiện tại hay không (trong bài lab đặt ngưỡng SLA là không quá 25% số bài báo có tuổi đời vượt quá 180 ngày).

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Đây là nguyên tắc cốt lõi của phương pháp nghiên cứu thực nghiệm (Controlled Experiment). Muốn so sánh chính xác mức độ ảnh hưởng của dữ liệu bẩn và hiệu quả của việc phục hồi dữ liệu, ta bắt buộc phải giữ cố định thước đo (cùng 10 câu hỏi kiểm tra). Nếu thay đổi câu hỏi giữa các pha, sự thay đổi của các chỉ số (Hit Rate, F1) có thể do câu hỏi dễ hơn hoặc khó hơn, chứ không phản ánh đúng chất lượng của dữ liệu trong vector store.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - Về mặt **Artifact**: Tập dữ liệu sau sửa chữa `papers_clean_repaired.json` được tái tạo lại đủ 24 bản ghi sạch, đối chiếu khớp hoàn toàn với dữ liệu sạch ban đầu; collection `papers-repaired` trong ChromaDB được dựng lại đầy đủ.
   - Về mặt **Metric**:
     - Great Expectations Quality Gate chuyển từ trạng thái `FAIL` ở pha Corrupted sang `PASS` ở pha Repaired (100% các kỳ vọng đều thỏa mãn).
     - Freshness SLA hồi phục từ `STALE` (tỷ lệ bài cũ 57.14% > 25%) trở về `FRESH` (tỷ lệ bài cũ chỉ còn 4.17%).
     - Các chỉ số của RAG Agent: `retrieval_hit_rate` và `mean_token_f1` hồi phục ngoạn mục từ 0.7000 (bị rớt do mất bài và nhiễu) trở lại mức hoàn hảo 1.0000.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.7000 | 1.0000 | Ở pha Corrupted, do có 5 bài báo mới bị xóa và một số bài bị làm nhiễu tiêu đề nên có 3/10 câu hỏi không tìm thấy tài liệu gốc. Sau khi repair, tỷ lệ tìm kiếm thành công đạt lại 100%. |
| `mean_token_f1` | 1.0000 | 0.7000 | 1.0000 | Điểm tương đồng câu trả lời rớt tương ứng theo độ chính xác của khâu retrieval, và phục hồi hoàn toàn về 1.0 sau khi dữ liệu được làm sạch lại. |
| `judge_accuracy` | 1.0000 | 0.7000 | 1.0000 | Đo lường mức độ câu trả lời đạt chuẩn nghiệp vụ, rớt 30% ở pha lỗi và khôi phục tuyệt đối ở pha sau repair. |
| `mean_judge_score` | 5.0 | 3.8 | 5.0 | Điểm đánh giá chất lượng câu trả lời bị giảm từ 5.0 xuống 3.8 do các câu trả lời bị thiếu thông tin hoặc trả lời sai ngữ cảnh, sau đó đạt lại điểm 5.0 tối đa. |
| Quality checks | PASS | FAIL | PASS | Bộ kiểm thử Great Expectations đã bắt trúng các lỗi: rỗng summary, tiêu đề bị cắt ngắn, dòng bị trùng lặp và số lượng bản ghi giảm bất thường. |
| Freshness status | FRESH (4.17%) | STALE (57.14%) | FRESH (4.17%) | Kịch bản lùi ngày xuất bản 400 ngày đã kích hoạt cảnh báo đỏ về độ trễ dữ liệu vượt trần SLA (57.14% > 25%), sau khi khôi phục từ snapshot gốc thì tỷ lệ này trở về mức an toàn 4.17%. |

### Kết luận từ số liệu

1. **Chuỗi nguyên nhân 1 (Tiêm lỗi):**
   Tiêm 6 kịch bản lỗi (xóa bài, nhân bản dòng, làm rỗng tóm tắt, cắt ngắn tiêu đề, lùi ngày xuất bản) -> Kích hoạt cảnh báo đỏ ở tầng Observability (Great Expectations chuyển thành FAIL, Freshness chuyển thành STALE) -> Dẫn đến sự suy giảm nghiêm trọng ở tầng RAG Agent (Retrieval hit rate và Token F1 tụt từ 1.0 xuống 0.7, Judge score giảm từ 5.0 xuống 3.8).

2. **Chuỗi nguyên nhân 2 (Phục hồi dữ liệu):**
   Thực thi Idempotent Data Repair đọc lại từ snapshot bất biến `data/raw/crossref_records.json` -> Dữ liệu sạch được khôi phục 24 dòng và collection ChromaDB được tái tạo mới -> Các chốt chặn Observability chuyển xanh (GX PASS, Freshness FRESH) -> Hiệu năng của RAG Agent phục hồi trọn vẹn về trạng thái Baseline (Hit Rate = 1.0, Token F1 = 1.0, Judge Score = 5.0).

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline & Idempotency:** Trong hệ thống dữ liệu, tính tái lập (Reproducibility) và tính bất biến (Immutability) của dữ liệu thô ban đầu là vô cùng quan trọng. Việc lưu giữ snapshot gốc giúp hệ thống luôn có điểm tựa vững chắc để tự phục hồi (Self-healing) khi có sự cố mà không sợ bị mất dữ liệu vĩnh viễn.
2. **Về Data Quality & Observability:** Nếu không có các công cụ giám sát như Great Expectations và Freshness SLA, các lỗi dữ liệu bẩn (Silent Data Corruption) sẽ âm thầm lọt vào vector database mà không làm sập server hay ném ra lỗi runtime. Người dùng cuối sẽ nhận được câu trả lời sai lệch (hallucination) mà đội ngũ kỹ thuật không hề hay biết.
3. **Về vai trò Leader & Tích hợp nhóm:** Khi làm việc nhóm kỹ thuật, việc thống nhất Data Contract rõ ràng ngay từ đầu (schema các cột, định dạng file, quy ước nhánh Git) là yếu tố quyết định để tránh xung đột mã nguồn và giúp các thành viên phối hợp trơn tru, đúng tiến độ.

### Nếu có thêm thời gian

Nếu có thêm thời gian, em sẽ tích hợp thêm một cơ chế tự động gửi cảnh báo qua Webhook (ví dụ gửi tin nhắn cảnh báo vào kênh Discord/Slack của nhóm) mỗi khi Great Expectations hoặc Freshness SLA phát hiện vi phạm, thay vì chỉ ghi log vào file Markdown/JSON như hiện tại. Điều này sẽ nâng cao tính thực chiến của hệ thống Data Observability trong môi trường Production.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Phạm Hoàng Trọng  
**Ngày xác nhận:** 2026-09-26
