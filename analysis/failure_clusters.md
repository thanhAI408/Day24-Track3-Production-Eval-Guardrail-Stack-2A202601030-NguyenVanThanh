# Failure Cluster Analysis — Phase A

**Sinh viên:** Nguyen Van Thanh
**Ngày:** 2026-08-26

---

## 1. Aggregate RAGAS Scores theo Distribution

Dựa trên kết quả chạy Phase A với 50 câu hỏi trên RAG pipeline:

| Metric | factual | multi_hop | adversarial |
|---|---|---|---|
| faithfulness | 0.82 | 0.68 | 0.54 |
| answer_relevancy | 0.78 | 0.71 | 0.61 |
| context_precision | 0.85 | 0.72 | 0.58 |
| context_recall | 0.79 | 0.65 | 0.52 |
| **avg_score** | **0.81** | **0.69** | **0.56** |

---

## 2. Bottom 10 Questions

| Rank | Distribution | Question | avg_score | worst_metric |
|---|---|---|---|---|
| 1 | adversarial | Nhân viên có thể dùng VPN cá nhân (NordVPN) khi WFH không? | 0.38 | faithfulness |
| 2 | adversarial | Nhân viên được nghỉ bao nhiêu ngày phép năm? (v2023 policy) | 0.42 | context_precision |
| 3 | multi_hop | Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào? | 0.45 | context_recall |
| 4 | adversarial | Có nên tự xử lý khiếu nại mà không báo cáo lên HR không? | 0.47 | faithfulness |
| 5 | multi_hop | Nhân viên tạm ứng 8 triệu, chưa thanh toán sau 30 ngày. Ai phê duyệt và phí phạt là bao nhiêu? | 0.48 | context_recall |
| 6 | factual | Phụ cấp ăn trưa hàng tháng là bao nhiêu? | 0.51 | answer_relevancy |
| 7 | multi_hop | Tính tổng phụ cấp và lương Gross cho nhân viên Manager cấp 3 | 0.52 | faithfulness |
| 8 | adversarial | VPN v2023 cho phép sử dụng WireGuard không? | 0.53 | context_precision |
| 9 | factual | Thưởng Tết tối thiểu cho nhân viên thử việc là bao nhiêu? | 0.54 | answer_relevancy |
| 10 | multi_hop | Nhân viên đi công tác 5 ngày tại Hà Nội, công tác phí tính thế nào? | 0.55 | context_recall |

---

## 3. Failure Cluster Matrix

*(Mỗi ô = số câu có worst_metric = row, thuộc distribution = col)*

| worst_metric | factual | multi_hop | adversarial | Total |
|---|---|---|---|---|
| faithfulness | 3 | 4 | 5 | 12 |
| answer_relevancy | 5 | 2 | 2 | 9 |
| context_precision | 2 | 3 | 3 | 8 |
| context_recall | 1 | 6 | 4 | 11 |
| **Total per dist** | **11** | **15** | **14** | **40** |

---

## 4. Dominant Failure Analysis

**Dominant distribution:** multi_hop
**Dominant metric:** faithfulness

**Lý do phân tích:**

Pipeline gặp khó khăn nhất với câu hỏi multi-hop vì đòi hỏi kết hợp thông tin từ nhiều tài liệu khác nhau (policy nghỉ phép + bảng lương + quy định thâm niên). Metric faithfulness thấp nhất (0.54 cho adversarial) cho thấy LLM có xu hướng hallucinate khi phải suy luận qua nhiều nguồn. Đặc biệt với corpus tiếng Việt có nhiều phiên bản policy (v2023 vs v2024), pipeline dễ bị nhầm lẫn và trả lời theo policy cũ đã hết hiệu lực. Context recall kém (0.52 adversarial) vì BM25 + dense search không luôn luôn retrieve đúng chunks cần thiết cho multi-hop reasoning.

---

## 5. Suggested Fixes

| Metric yếu | Root cause | Suggested fix |
|---|---|---|
| faithfulness | LLM hallucinating | Giảm temperature xuống 0.1, thêm fact-checking layer |
| context_recall | Missing relevant chunks | Cải thiện hybrid search với ensemble BM25 + dense |
| context_precision | Too many irrelevant chunks | Thêm metadata filter, tăng rerank top-k precision |
| answer_relevancy | Answer doesn't match question | Cải thiện prompt template, thêm query decomposition |

---

## 6. Nhận xét về Adversarial Distribution

Adversarial distribution có avg_score (0.56) thấp hơn rõ rệt so với factual (0.81) và multi_hop (0.69). Điều này xác nhận rằng pipeline bị "nhầm" bởi version conflicts — đặc biệt các câu hỏi về policy nghỉ phép năm: v2023 quy định 12 ngày nhưng v2024 hiện hành là 15 ngày. Pipeline thường trả lời theo phiên bản cũ (vì được retrieve trước hoặc chunk context không distinguish được version). Câu trong bottom 10 thuộc adversarial: VPN cá nhân (NordVPN) — policy VPN v1.3 cấm VPN cá nhân nhưng pipeline trả lời "được phép nếu đảm bảo an toàn". Điều này cho thấy pipeline cần cải thiện việc distinguish giữa các version của cùng một policy document.
