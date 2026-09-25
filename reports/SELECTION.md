# Vì sao chọn lô này?

Trong 50 dòng đứng đầu `outputs/selection_round1.csv`, chọn năm frame bạn sẽ ưu tiên nếu chỉ có ngân sách rà năm ảnh. Ghi tên, điểm, thời điểm, thứ tự và lý do; tối thiểu một quyết định phải xét ảnh gần trùng hoặc trường hợp model không dự đoán được box:

Nếu chỉ đủ công rà **năm ảnh**, tôi không lấy nguyên top 5 theo `score` vì một số frame đứng sát nhau trên trục thời gian. Đề xuất:

| Ưu tiên | Frame | rank CSV | t_sec | score | U | A | n_boxes / n_ambiguous | Lý do |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | `frame_0182.jpg` | 1 | 72.8 | 0.9591 | 0.9182 | 1.0000 | 28 / 18 | Điểm cao nhất lô; A = 1.0 (nhiều box mập mờ nhất pool); cảnh đông, đáng rà |
| 2 | `frame_0369.jpg` | 2 | 147.6 | 0.9324 | 0.9315 | 0.8889 | 43 / 16 | Cuối video, mật độ cao; U cao |
| 3 | `frame_0099.jpg` | 8 | 39.6 | 0.9063 | 0.9460 | 0.7778 | 29 / 14 | Đầu–giữa video (cách `0182` khoảng 33 s) nên đa dạng thời gian; U rất cao |
| 4 | `frame_0312.jpg` | 7 | 124.8 | 0.9100 | 0.8199 | 1.0000 | 37 / 18 | A = 1.0 như `0182` nhưng ở cụm thời gian ~125 s, không trùng `0369` |
| 5 | `frame_0227.jpg` | 11 | 90.8 | 0.8915 | 0.9164 | 0.7778 | 37 / 14 | Lấp khoảng giữa 72.8 s và 124.8 s |

Quyết định **không** lấy dù điểm cao hơn mục 5:

- `frame_0380.jpg` (rank 3, score 0.9170, t = 152.0 s) chỉ cách `frame_0369.jpg` **4.4 s**. Camera cố định nên gần như cùng một đoàn xe; chi phí rà gần bằng một ảnh mới nhưng thông tin học thêm thấp.
- `frame_0331.jpg` (rank 5, score 0.9154, t = 132.4 s) chỉ cách `frame_0326.jpg` (rank 4, t = 130.4 s) đúng `MIN_GAP_S` = 2.0 s. Với ngân sách 5 ảnh, giữ `0312` (124.8 s) là đủ cho cụm này.
- `frame_0372.jpg` (rank 6, score 0.9101, t = 148.8 s, **selected=False**) bị thuật toán loại vì cách `0369` chỉ 1.2 s — đúng với luật ảnh gần trùng.

Trong 50 ứng viên đầu **không có frame `empty=True`**. Model cold start luôn ra box (24–53 box/ảnh ở conf ≥ 0.05). Trường hợp “model không dự đoán được box” xuất hiện ở **vòng 2** (`outputs/selection_round2.csv`: `frame_0009.jpg` empty, score = 0.7 nhờ EMPTY_BONUS), không phải ở vòng 1.

Ba frame thuộc lô 12 ảnh model chọn và bằng chứng trong CSV/ảnh contact sheet:

1. **`frame_0182.jpg`** (rank 1, selected=True). `score = 0.5·0.9182 + 0.3·1.0 + 0.2·1.0 = 0.9591`. Contact sheet `outputs/selection_round1.jpg` hàng 1: cảnh đêm đông xe, nhiều đèn pha. Đây là ảnh bất định + mơ hồ cao nhất, nên vào lô bắt buộc K = 12 là hợp lý.
2. **`frame_0392.jpg`** (rank 15, selected=True, t = 156.8 s). U = **0.9747** cao nhất trong 12 ảnh đã chọn, nhưng A chỉ 0.6667 (12 box mơ hồ / 35 box) nên `score` 0.8874 thấp hơn các ảnh rank 2–5. Model vẫn chọn vì D = 1.0 (vòng đầu chưa có nhãn) và `MIN_GAP_S` còn chỗ ở cuối video. Contact sheet hàng 2, ảnh cuối: mật độ thấp hơn `0331`/`0369`.
3. **`frame_0331.jpg`** (rank 5, selected=True, t = 132.4 s). n_boxes = **47** (nhiều nhất trong 12 ảnh), n_ambiguous = 18, A = 1.0. Contact sheet hàng 2 giữa: đoàn xe dày. Chi phí rà cao (nhiều box) nhưng đúng mục tiêu uncertainty: nơi model phân vân nhiều nhất.

Một frame có điểm cao nhưng không chọn hoặc một frame có điểm thấp vẫn nên xem, và lý do:

- **Không chọn dù điểm cao:** `frame_0372.jpg` (rank 6, score 0.9101, selected=False). Cách `frame_0369.jpg` 1.2 s. Gán thêm gần như dán nhãn trùng; `MIN_GAP_S` đã làm đúng việc tiết kiệm công.
- **Nên xem dù không nằm top score của vòng 1:** `frame_0002.jpg` (rank 18, score 0.8658, t = 0.8 s). Nằm ngoài 12 ảnh đã chọn nhưng ở đầu video, D vẫn = 1.0, 27 box / 13 mơ hồ. Nếu ngân sách cho phép thêm một ảnh “đa dạng thời gian”, đây đáng xem hơn `frame_0380` sát `0369`.
- **Bài học vòng 2:** `frame_0009.jpg` (rank 1 vòng 2, empty=True, 0 box). Điểm 0.7 không phải vì model “chắc chắn có xe khó”, mà vì frame trống được cộng EMPTY_BONUS. Contact sheet `selection_round2.jpg` vẫn thấy rõ nhiều xe — đây đúng kiểu ca người phải rà, không phải ca nên bỏ.

Điều phép chọn này chưa chứng minh về chất lượng mô hình:

Điểm bất định **không** chứng minh ảnh đó sẽ cải thiện mô hình. U/A chỉ mô tả phân bố confidence của model hiện tại trên pool; chúng không đo chất lượng nhãn sau khi người sửa, không đo độ lệch domain so với test, và không bảo đảm fine-tune trên lô nhỏ (12 ảnh) sẽ tăng AP50. Thực tế `outputs/metrics_round1.json` cho thấy AP50 giảm mạnh sau khi train trên đúng lô này. Phép chọn cũng không nói gì về việc pre-label (conf 0.25) đã thiếu bao nhiêu xe so với dự đoán conf 0.05 trong CSV (28–47 box/ảnh so với 13–20 box đóng gói).
