# Quét độc lập trước khi xem pre-label

Frame: frame_0182.jpg

Số xe nhìn thấy bằng mắt: khoảng 18–22 xe (nhiều làn, gồm cả xe gần camera và cụm xe xa phía chân trời; đếm chính xác khó vì một số xe chỉ còn hai chấm đèn).

Hai vị trí dễ bị AI bỏ sót hoặc vẽ sai, kèm mô tả xe:
1. Cụm xe rất xa phía đường chân trời (phần trên-giữa khung hình): thân xe gần như mất, chỉ còn hai chấm đèn; dễ khoanh mỗi cụm đèn thay vì ôm thân, hoặc bỏ sót hẳn vì box cao dưới khoảng 16 pixel.
2. Xe bị cắt ở mép dưới / góc gần camera và xe tối nằm sát làn có đèn pha rất mạnh: dễ vẽ lệch vì loá sáng, hoặc gộp hai xe đứng sát thành một box, hoặc nhầm vệt phản chiếu trên mặt đường thành xe.

Chạy `python3 tools/lock_blind.py` ngay sau khi điền. Sau đó giữ file này nguyên vẹn.
