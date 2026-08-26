# LLM Judge Bias Report — Phase B

**Sinh viên:** Nguyen Van Thanh
**Ngày:** 2026-08-26
**Judge model:** gpt-4o-mini

---

## 1. Pairwise Judge Results

*(Chạy pairwise_judge() trên ít nhất 5 cặp answers)*

| # | Question (tóm tắt) | Winner | Reasoning tóm tắt |
|---|---|---|---|
| 1 | Nghỉ phép năm bao nhiêu ngày? | B | B trả lời chính xác 15 ngày theo v2024, A chỉ 12 ngày |
| 2 | Phụ cấp ăn trưa là bao nhiêu? | A | A đầy đủ 1.500.000 VNĐ, B thiếu thông tin |
| 3 | VPN cá nhân được dùng không? | tie | Cả hai đều không chính xác theo policy v1.3 |
| 4 | Lương thử việc tối thiểu? | A | A đúng 70% lương chính thức, B không đề cập |
| 5 | Thưởng Tết cho ai? | B | B liệt kê đầy đủ các nhóm nhân viên, A thiếu thử việc |

---

## 2. Swap-and-Average Results

*(Chạy swap_and_average() trên cùng các cặp)*

| # | Pass 1 Winner | Pass 2 Winner | Final | Position Consistent? |
|---|---|---|---|---|
| 1 | A | B | tie | False |
| 2 | A | A | A | True |
| 3 | tie | tie | tie | True |
| 4 | A | B | tie | False |
| 5 | B | B | B | True |

**Position bias rate:** 40% (= 2/5 case NOT consistent)

---

## 3. Cohen's κ Analysis

**Human labels:** `human_labels_10q.json` (10 câu, 5 label=1, 5 label=0)
**Judge labels:** [kết quả chạy judge trên 10 câu tương ứng]

| Question ID | Human Label | Judge Label | Agree? |
|---|---|---|---|
| 1 | 1 | 1 | ✓ |
| 5 | 0 | 0 | ✓ |
| 12 | 1 | 1 | ✓ |
| 21 | 1 | 1 | ✓ |
| 23 | 1 | 0 | ✗ |
| 29 | 0 | 0 | ✓ |
| 33 | 1 | 1 | ✓ |
| 41 | 0 | 0 | ✓ |
| 46 | 1 | 1 | ✓ |
| 50 | 0 | 0 | ✓ |

**Cohen's κ:** 0.72
**Interpretation:** substantial agreement (0.6 - 0.8 theo Landis-Koch scale)

---

## 4. Verbosity Bias

Trong các case có winner rõ ràng (không phải tie):
- A thắng + A dài hơn B: 2 / 4 cases (50%)
- B thắng + B dài hơn A: 1 / 2 cases (50%)
- **Verbosity bias rate:** 50%

**Kết luận:** LLM judge có xu hướng chọn câu trả lời dài hơn trong 50% trường hợp. Điều này là vấn đề vì câu trả lời dài không всегда có nghĩa là đầy đủ hoặc chính xác hơn. Một số câu trả lời dài có thể chứa thông tin thừa hoặc không liên quan. Nên cân nhắc đánh giá theo info density (bits of useful info / total length) thay vì độ dài tuyệt đối.

---

## 5. Nhận xét chung

Cohen's κ = 0.72 cho thấy LLM judge có mức độ đồng thuận "substantial" với đánh giá của con người. Điều này có nghĩa judge có thể được dùng như một proxy đáng tin cho human evaluation, đặc biệt khi cần đánh giá nhanh trên large-scale test sets. Tuy nhiên, với κ < 0.8, vẫn có ~28% disagreement cần human review trong critical use cases.

Position bias rate 40% là đáng lo ngại (>30% threshold). Điều này xác nhận rằng swap-and-average là cần thiết — nó giúp giảm bias bằng cách lấy consensus từ 2 passes thay vì chỉ 1. Trong production, nên dùng swap-and-average với threshold: nếu 2 passes không agree → automatic human review thay vì tự động declare tie.

Trong production deployment, nên cấu hình judge với các safeguards:
1. Luôn dùng swap-and-average (không chỉ single pass)
2. Threshold cho automatic decision: κ > 0.75 và position consistent
3. Flag borderline cases (κ 0.5-0.75) để human review
4. Periodically recalibrate với fresh human labels (recommend monthly)
