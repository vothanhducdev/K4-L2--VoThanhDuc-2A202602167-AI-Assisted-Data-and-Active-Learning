# Báo cáo Lab Ngày 08: Học chủ động cho bộ phát hiện xe

Họ và tên: Võ Thành Đức

Công cụ gán nhãn đã dùng: CVAT Docker local (xuất Ultralytics YOLO Detection 1.0). `labels/round1/batch.json` ghi nguồn pre-label là `anylabeling-json` (file gợi ý đóng gói cùng lô), không phải công cụ thay CVAT khi rà nhãn.

Mọi con số truy được từ `reports/rounds_table.md`, `outputs/selection_round1.csv`, `outputs/metrics_round*.json` hoặc `outputs/round*_diff.md`. Không coi nhãn test do mô hình tạo là chân lý tuyệt đối.

## 1. Dữ liệu và cách chia tập

Pool và test được chia **theo trục thời gian**, có **vùng đệm**, vì camera cầu vượt đứng yên và video là một cảnh liên tục (`data/DATA.md`). Hai frame cách 0.4 s gần như trùng; mỗi xe ở trong khung vài giây. Chia ngẫu nhiên sẽ để **cùng một chiếc xe** (cùng pose, cùng làn, cùng loá đèn) vào cả train lẫn test: mô hình bị chấm trên object nó đã thấy → **số đo (AP50, recall) bị lệch cao** so với khả năng thật trên thời điểm chưa gặp. Đó là rò rỉ dữ liệu.

Cách chia thực tế: test = 20 ảnh (4 đoạn tâm 20/60/100/140 s, mỗi đoạn 5 ảnh cách 1.2 s); buffer 112 ảnh (khoảng 4 s quanh test); pool 268 ảnh. Ảnh pool gần test nhất vẫn cách 4.4 s. Lab không dùng số train làm số test: mọi AP50/P/R dưới đây lấy từ `outputs/metrics_round*.json` trên cùng 20 ảnh test, 403 box tham chiếu (bỏ 14 box cao < 16 px).

## 2. Mô hình khởi đầu lạnh (cold start)

Dòng vòng 0 từ `reports/rounds_table.md`:

| vòng | model                                   | ảnh train | box train |  AP50 | Δ AP50 so cold start | P@0.25 | R@0.25 |    F1 | R small | R medium | R large |
| ---: | --------------------------------------- | --------: | --------: | ----: | -------------------: | -----: | -----: | ----: | ------: | -------: | ------: |
|    0 | yolov8n cold start (COCO car+bus+truck) |         0 |         0 | 0.771 |                    — |  0.925 |  0.489 | 0.640 |   0.182 |    0.547 |   0.561 |

Chi tiết `outputs/metrics_round0.json` (Tesla T4, imgsz 960, học viên Võ Thành Đức): AP50 = **0.7714**; conf 0.25 cho P/R: TP **197**, FP **16**, FN **206**; precision **0.9249**, recall **0.4888**, F1 **0.6396**. Theo kích thước: R_small **0.1818** (66 box), R_medium **0.5473** (296), R_large **0.5610** (41).

**Chất lượng nhãn AI ban đầu (cold start trên test, đối chiếu `outputs/compare_round0.jpg`):**

- Khớp tốt (xanh) với xe **gần–trung bình**, thân rõ, đèn pha mạnh — đúng class `car` theo guideline (sedan/SUV/tải đêm).
- Không khớp tham chiếu chủ yếu ở: (1) xe **rất xa / nhỏ** sát chân trời; (2) xe tối hoặc bị loá; (3) xe **cắt mép** (đáy/phải ảnh); (4) một ít FP (cam) — có thể là phản chiếu, đèn đường, hoặc box tham chiếu/dự đoán lệch IoU.
- Recall theo size: model **bỏ sót nặng xe nhỏ** (R 0.18) trong khi P rất cao (0.92). Cold start thiên về “chỉ nói khi chắc” — thiếu độ phủ, không phải thiếu độ sạch.

**Một ca cần rà nhãn tham chiếu trước khi kết luận model sai:** trên `compare_round0.jpg`, `frame_0150` / `frame_0250` có box cam/đỏ ở vùng đèn đường và xe xa chỉ còn hai chấm. Nhãn test **do mô hình tạo, chưa người rà** (`data/DATA.md`). Một FN có thể là test gán quá tay cho chấm đèn, hoặc một FP là test thiếu xe. Không sửa `data/test/labels/`; chỉ ghi giới hạn này khi đọc AP50.

## 3. Chiến lược chọn mẫu

Công thức (notebook / `tools/al_select.py`, W_U=0.5, W_A=0.3, W_D=0.2):

`score = 0.5·U + 0.3·A + 0.2·D`

- **U**: trung bình độ bất định `u(c)=1-|2c-1|` của **5 box khó nhất** (cao khi conf ~ 0.5). Ưu tiên chỗ model phân vân.
- **A**: số box mơ hồ `0.15 ≤ c < 0.50`, chuẩn hoá theo max trong pool. Ưu tiên ảnh có nhiều ứng viên “lửng lơ”.
- **D**: khoảng cách thời gian tới frame **đã gán** gần nhất, chặn 10 s rồi chia 10. Vòng 0 chưa có nhãn → D = 1 cho mọi ảnh.

Frame **không có box** (conf ≥ 0.05): U = A = 0, cộng **EMPTY_BONUS = 0.5** vì camera này luôn có xe — trống nghĩa là model bỏ sót hàng loạt.

**`MIN_GAP_S` = 2.0 s:** chọn tham lam theo score, bỏ ứng viên cách một ảnh đã chọn dưới 2 s. Camera cố định: hai frame 0.4–2 s gần như trùng; gán cả hai tốn công, model học thêm rất ít.

Ba frame trong lô 12 và một frame khác — chi tiết số liệu và lập luận nằm ở `reports/SELECTION.md`:

- `frame_0182.jpg` (rank 1, score 0.9591, A=1.0, 18 box mơ hồ): điển hình uncertainty.
- `frame_0392.jpg` (U=0.9747 cao nhất lô, A thấp hơn): vào lô nhờ U và D, không phải vì đông xe nhất.
- `frame_0331.jpg` (47 box, A=1.0): chi phí rà cao, đúng chỗ model rối.
- Frame **không** chọn: `frame_0372.jpg` (rank 6, score 0.9101) — cách `0369` chỉ 1.2 s, `selected=False`.

**Điểm bất định không chứng minh ảnh sẽ cải thiện mô hình.** U chỉ là thống kê confidence. Lô vòng 1 toàn cảnh đông, đêm, conf thấp; fine-tune 50 epoch trên 12 ảnh (`metrics_round1.json`) làm AP50 giảm 0.424. Chọn đúng chỗ “khó” nhưng nhãn đóng gói thưa hơn chính dự đoán pool (CSV 28–47 box vs 13–20 box YOLO) thì model học “hãy im lặng”.

## 4. Các vòng học chủ động (active learning)

Bảng `reports/rounds_table.md` (test 20 ảnh, 403 box, IoU 0.5, P/R/F1 tại conf 0.25):

| vòng | model                                   | ảnh train | box train |  AP50 | Δ AP50 so cold start | P@0.25 | R@0.25 |    F1 | R small | R medium | R large |
| ---: | --------------------------------------- | --------: | --------: | ----: | -------------------: | -----: | -----: | ----: | ------: | -------: | ------: |
|    0 | yolov8n cold start (COCO car+bus+truck) |         0 |         0 | 0.771 |                    — |  0.925 |  0.489 | 0.640 |   0.182 |    0.547 |   0.561 |
|    1 | yolov8n fine-tune vong 1..1             |        12 |       169 | 0.348 |               -0.424 |  1.000 |  0.015 | 0.029 |   0.000 |    0.007 |   0.098 |
|    2 | yolov8n fine-tune vong 1..2             |        24 |       180 | 0.372 |               -0.399 |  0.909 |  0.025 | 0.045 |   0.015 |    0.014 |   0.122 |

`outputs/metrics_round2.json`: 24 ảnh train, 180 box, AP50 **0.372** (Δ **−0.399** so cold start, +0.024 so vòng 1). `compare_round2.jpg` cùng bố cục so sánh test. Bằng chứng ảnh chi tiết vẫn đọc `compare_round1.jpg` (sụt TP trên `frame_0050`/`0150`).

### Vòng 0 — cold start, 0 ảnh train

Đã phân tích mục 2. Đây là **baseline mô hình**, không phải nhãn người.

### Vòng 1 — fine-tune trên 12 ảnh pool

**Mức sửa pre-label** (`outputs/round1_diff.md`, IoU accept 0.85): 12 ảnh; model đề xuất **169** box; sau sửa còn **169**. accepted **169**, edited **0**, deleted **0**, added **0**, accept rate **100%**. Từng ảnh: `0099` 13, `0107` 13, `0182` 13, `0187` 14, `0227` 13, `0270` 13, `0312` 13, `0326` 15, `0331` 20, `0369` 14, `0380` 15, `0392` 13.

Đối chiếu `selection_round1.csv`: cùng những frame đó, cold start (conf ≥ 0.05) báo 28–47 box/ảnh. Pre-label đóng gói (conf 0.25) đã **cắt hơn một nửa** ứng viên. Diff 100% accepted nghĩa là **nhãn đã sửa ≈ nhãn gợi ý đã lọc**, chưa bù FN.

**AP50:** 0.7714 → **0.3478** (Δ **−0.4236** so cold start; không có vòng trước khác). `metrics_round1.json`: 50 epoch, 12 ảnh, 169 box, strategy `uncertainty`. TP **6**, FP **0**, FN **397**. Precision **1.000** vì gần như không còn dự đoán tại 0.25; recall **0.0149**; F1 **0.0293**.

**Theo kích thước (cùng test):** R_small 0.182 → **0**; R_medium 0.547 → **0.0068**; R_large 0.561 → **0.0976**. Mọi nhóm đều xấu đi; xe nhỏ mất hoàn toàn; chỉ còn sót rất ít xe lớn.

**Một ca đổi sau fine-tune (có bằng chứng ảnh):** `outputs/compare_round1.jpg`, `reference frame_0050` (19 box). Cold start: TP 11 / FP 2 / FN 7 — bắt được các xe lớn phía trước. Round 1: **TP 0 / FP 0 / FN 18**. Các xe gần, đèn rõ mà vòng 0 bắt được (xanh) biến thành bỏ sót (vàng). `frame_0150` tương tự TP 10 → 0. `frame_0250` / `frame_0350` còn **TP 1**. Đây không phải “AP50 nhiễu ±0.01 trên 20 ảnh” mà là **mô hình xẹp**: quên COCO, chỉ còn vài box tin cậy.

**Phân biệt ba lớp bằng chứng (rubric mục 5):**

| Lớp                        | Bằng chứng                                                                                                                                                                                  | Kết luận                                                                                                 |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Quan sát độc lập           | `reports/BLIND_SCAN.md` trên `frame_0182.jpg`: ~18–22 xe; rủi ro xe chân trời và mép/loá                                                                                                    | Người nhìn thấy mật độ cao hơn 13 box pre-label                                                          |
| Lỗi / trạng thái pre-label | `round1_diff.md` + `REVIEW_LOG.csv`: **giữ** box xe lớn rõ (`0331`), xe cắt mép (`0099`), xe xa (`0182`); **không thêm** phản chiếu mặt đường (`0380`). Diff không ghi edited/deleted/added | Pre-label không bị xóa nhầm phản chiếu, nhưng **thiếu xe** so với CSV và blind scan thì **chưa được bù** |
| Model sau train            | `metrics_round1.json` + `compare_round1.jpg`                                                                                                                                                | P=1.0 là ảo (6 TP); chất lượng phát hiện kém hơn cold start rõ rệt                                       |

**Ca khó theo guideline:** xe đêm chỉ còn hai chấm đèn, box < 16 px — gán hay bỏ đều được khi chấm; thiếu nhất quán giữa ảnh sẽ thành nhiễu. Hai xe sát nhau dưới loá đèn pha dễ gộp một box. Vệt sáng mặt đường **không** được gán. Lab giữ convention: ôm thân đoán được quanh đèn, không khoanh vệt đường; xe quá nhỏ có thể giữ như pre-label vì bị ignore lúc eval.

### Hiệu quả Active Learning

Uncertainty + `MIN_GAP_S` **làm đúng việc chọn chỗ khó và tránh trùng 1.2 s** (`0372` bị loại). Contact sheet vòng 1 toàn cảnh đông — đúng ngân sách 12 ảnh. Hiệu quả **end-to-end thì thất bại**: chọn khó + nhãn thưa + 50 epoch / 12 ảnh → catastrophic forgetting. AL không thất bại ở khâu ranking; thất bại ở **vòng lặp người–nhãn–train**.

### Vòng 2 — 12 ảnh thêm, 11 box

`labels/round2/batch.json`: đề xuất bởi **yolov8n fine-tune vòng 1**, K=12, `min_gap_s=2.0`. `outputs/round2_diff.md`: 12 ảnh, **11** box đề xuất và 11 box sau sửa; accepted 11, edited/deleted/added = 0. Bốn ảnh **0 box**: `0009`, `0021`, `0272`, `0367`. `selection_round2.csv` rank 1 = `frame_0009.jpg` empty, score **0.7** = EMPTY_BONUS + D. Contact sheet vòng 2 vẫn đầy xe. Số đo file vòng 2 (`metrics_round2.json`) TP 10 / FP 1 / FN 393 — recall vẫn rất thấp; không đảo được kết luận vòng 1.

## 5. Kết luận và giới hạn

**So với cold start:** vòng 1 **kém hơn** trên mọi trục có nghĩa: AP50 0.771 → 0.348; recall 0.489 → 0.015; xe nhỏ/trung bình/lớn đều giảm. Precision 1.0 không phải thắng — mẫu dự đoán gần như hết. Điểm lab **không** phụ thuộc AP50 tăng (`RUBRIC.md`); đọc đúng sự sụt giảm vẫn là kết quả hợp lệ.

**Vì sao dừng fine-tune (không train vòng 2) nhưng vẫn đề xuất rà nhãn có chọn lọc:** train thêm trên pre-label 11 box / nhiều frame trống sẽ củng cố hành vi “không dự đoán”. Dừng **cập nhật trọng số**; không dừng **phân tích chỗ còn yếu**.

**Hai ca còn yếu / bất định cho vòng sau:**

1. **`frame_0009.jpg` (và kiểu empty `frame_0272.jpg`)** — `selection_round2.csv`: 0 box, empty=True; contact sheet vẫn có đoàn xe. Đây là FN hàng loạt. **Nên chọn** để người gán từ đầu. Chi phí rà **cao** (nhiều xe, đêm). **Không** chọn thêm `frame_0012.jpg` (rank 2, empty, t=4.8 s, selected=False) vì cách `0009` (3.6 s) chỉ 1.2 s — gần trùng.
2. **Xe nhỏ / chân trời và `frame_0209.jpg`** — rank 3 vòng 2, U=0.9858 nhưng chỉ **1 box** mơ hồ. Model gần như mù, một box lửng không đại diện mật độ thật. **Nên rà** nếu ngân sách còn; ưu tiên sau các frame empty đã đa dạng thời gian. Nguy cơ trùng: `0367`/`0376`/`0387` (146.8–154.8 s) D rất thấp (0.08–0.20) vì đã gán `0369`/`0380`/`0392` vòng 1 — **không chọn cả cụm**.

**Chi phí gán, ảnh gần trùng, test nhỏ, nhãn tham chiếu do model tạo:**

- 12 ảnh đông (`0331` 47 ứng viên CSV) tốn thời gian; accept 100% tiết kiệm công nhưng **để sót FN** thì rẻ một lần, đắt ở mọi vòng sau.
- `MIN_GAP_S` đã lọc `0372`; ngân sách 5 ảnh còn phải tự loại `0380` vs `0369`.
- Test **20 ảnh**: Δ AP50 0.42 không phải nhiễu; nhưng so sánh tinh (0.01) thì không đủ. Nhãn test **chưa người rà** + luật bỏ xe < 16 px: AP50 là **độ khớp với một model khác**, không phải mAP thực địa. Cold start gần domain của chính bộ tham chiếu nên AP50 0.77 có thể **lạc quan**. Sau fine-tune, lệch khỏi “giọng” model-ref thì AP50 rơi — một phần là quên, một phần là **thước đo lệch**.

**Nếu AP50 giảm, kiểm tra gì trước khi train thêm:**

1. `round*_diff.md`: có added/edited thật không, hay chỉ accept pre-label thưa?
2. So CSV `n_boxes` (conf 0.05) với số box YOLO đóng gói (conf 0.25).
3. `compare_round*.jpg`: quên xe lớn gần camera hay chỉ lệch xe nhỏ?
4. Epoch / lr / freeze backbone: 50 epoch trên 12 ảnh là nghi phạm.
5. Không sửa test labels; không lấy metric train làm metric test.
6. QC: `REVIEW_LOG.csv` đối chiếu diff; `python tools/check_submission.py` chỉ kiểm hình thức.

**Bài học:** (1) AL chọn khó ≠ AL thành công — nhãn phải **đủ phủ**. (2) P=1.0 + R≈0 là dấu hiệu model chết, không phải model sạch. (3) Frame empty sau một vòng sụt recall là tín hiệu ưu tiên gán, không phải tín hiệu “ảnh không có xe”. (4) Lô nhỏ đêm + fine-tune mạnh dễ xóa kiến thức COCO; vòng sau nên ít epoch hơn, freeze sớm, và **thêm FN** trước khi bấm train.
