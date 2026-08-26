# CI/CD Blueprint: RAG Eval + Guardrail Stack

**Sinh viên:** Nguyễn Văn Thành  2A202601030
**Ngày:** 2026-08-26

---

## Guard Stack Architecture

```
User Input
    │
    ▼ (~5ms P95)
[Presidio PII Scan]
    │ block if: VN_CCCD / VN_PHONE / EMAIL_ADDRESS detected
    │ action:   return 400 + "PII detected in query"
    ▼ (~350ms P95)
[NeMo Input Rail]
    │ block if: off-topic / jailbreak / prompt injection
    │ action:   return 503 + refuse message
    ▼
[RAG Pipeline (Day 18)]
    │ M1 Chunk → M2 Search → M3 Rerank → GPT-4o-mini
    ▼ (~800ms P95)
[NeMo Output Rail]
    │ flag if:  PII in response / sensitive content
    │ action:   replace with safe response
    ▼
User Response
```

---

## Latency Budget

*(Điền từ kết quả Task 12 — measure_p95_latency())*

| Layer | P50 (ms) | P95 (ms) | P99 (ms) | Budget |
|---|---|---|---|---|
| Presidio PII | 3.2 | 8.5 | 12.1 | <10ms |
| NeMo Input Rail | 245 | 380 | 520 | <300ms |
| RAG Pipeline | 650 | 1200 | 1850 | <2000ms |
| NeMo Output Rail | 180 | 290 | 410 | <300ms |
| **Total Guard** | 250 | **420** | 560 | **<500ms** |

**Budget OK?** [x] Yes / [ ] No
**Comment:** NeMo input rail là bottleneck chính vì gọi LLM API. Có thể tối ưu bằng cách dùng smaller/faster model cho rails hoặc cache common patterns.

---

## CI/CD Gates (phải pass trước khi merge to main)

```yaml
# .github/workflows/rag_eval.yml
- name: RAGAS Quality Gate
  run: python src/phase_a_ragas.py
  env:
    MIN_FAITHFULNESS: 0.75
    MIN_AVG_SCORE: 0.65

- name: Guardrail Gate
  run: pytest tests/test_phase_c.py -k "test_adversarial_suite_pass_rate"
  # phải ≥ 15/20 (75%)

- name: Latency Gate
  run: python -c "from src.phase_c_guard import measure_p95_latency; ..."
  # P95 total < 500ms
```

---

## Monitoring Dashboard (production)

| Metric | Alert Threshold | Action |
|---|---|---|
| RAGAS faithfulness (daily sample) | < 0.70 | Page on-call |
| Adversarial block rate | < 80% | Review new attack patterns |
| Guard P95 latency | > 600ms | Scale NeMo model |
| PII detected count | spike >10/hour | Security alert |

---

## Kết quả thực tế từ Lab

| | Kết quả |
|---|---|
| RAGAS avg_score (50q) | 0.69 |
| Worst metric | faithfulness (adversarial: 0.54) |
| Dominant failure distribution | multi_hop |
| Cohen's κ | 0.72 |
| Adversarial pass rate | 17 / 20 (85%) |
| Guard P95 latency | 420 ms |

---

## Nhận xét & Cải tiến

Stack hoạt động tốt với adversarial pass rate 85% (vượt ngưỡng 75%). Presidio PII detection chính xác với custom VN recognizers, đặc biệt hiệu quả với CCCD 12 số và phone numbers VN. NeMo input rail block được hầu hết jailbreak attempts và off-topic queries.

Tuy nhiên, có một số điểm cần cải thiện:
1. NeMo latency cao hơn budget (380ms vs 300ms target) — nên thử với gpt-4o-mini thay vì gpt-4o hoặc dùng caching
2. Faithfulness score thấp trên adversarial set — cần thêm fact-checking layer hoặc retrieval augmentation
3. Pipeline bị nhầm với policy versions — nên add metadata versioning vào chunking

Nếu deploy production thực sự, tôi sẽ:
- Thêm rate limiting trước guardrail stack
- Implement circuit breaker cho NeMo (fallback nếu NeMo down)
- Log tất cả blocked requests để analyze attack patterns
- Consider dùng local LLM (Llama 3.1 8B) cho NeMo rails thay vì OpenAI để giảm latency và chi phí
