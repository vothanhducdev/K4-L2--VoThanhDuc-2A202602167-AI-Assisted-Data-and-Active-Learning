# Bảng so sánh các vòng

Tập kiểm thử: 20 ảnh, 403 box tham chiếu (bỏ qua 14 box cao dưới 16 px). Ngưỡng IoU 0.5; P, R, F1 tính tại conf 0.25.

| vòng | model | ảnh train | box train | AP50 | Δ AP50 so cold start | P@0.25 | R@0.25 | F1 | R small | R medium | R large |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | yolov8n cold start (COCO car+bus+truck) | 0 | 0 | 0.771 | — | 0.925 | 0.489 | 0.640 | 0.182 | 0.547 | 0.561 |
| 1 | yolov8n fine-tune vong 1..1 | 12 | 169 | 0.348 | -0.424 | 1.000 | 0.015 | 0.029 | 0.000 | 0.007 | 0.098 |
| 2 | yolov8n fine-tune vong 1..2 | 24 | 180 | 0.372 | -0.399 | 0.909 | 0.025 | 0.045 | 0.015 | 0.014 | 0.122 |
