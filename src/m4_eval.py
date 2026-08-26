from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import os, sys, json
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run RAGAS evaluation."""
    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
        from datasets import Dataset

        dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        })

        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
        )

        # ragas 0.4.x returns EvaluationResult with .scores (list of dicts)
        try:
            scores_list = result.scores
        except Exception:
            scores_list = [{} for _ in questions]

        # Build per-question EvalResult from scores
        per_question = []
        for i, q in enumerate(questions):
            s = scores_list[i] if i < len(scores_list) else {}
            per_question.append(EvalResult(
                question=q,
                answer=answers[i],
                contexts=contexts[i],
                ground_truth=ground_truths[i],
                faithfulness=float(s.get("faithfulness", 0.0) or 0.0),
                answer_relevancy=float(s.get("answer_relevancy", 0.0) or 0.0),
                context_precision=float(s.get("context_precision", 0.0) or 0.0),
                context_recall=float(s.get("context_recall", 0.0) or 0.0),
            ))

        # Aggregate (mean across valid scores, NaN-safe)
        def safe_mean(key):
            vals = [float(s.get(key, 0) or 0) for s in scores_list]
            vals = [v for v in vals if v == v]  # drop NaN
            return sum(vals) / len(vals) if vals else 0.0

        aggregate = {
            "faithfulness": safe_mean("faithfulness"),
            "answer_relevancy": safe_mean("answer_relevancy"),
            "context_precision": safe_mean("context_precision"),
            "context_recall": safe_mean("context_recall"),
        }

        return {**aggregate, "per_question": per_question}

    except Exception as e:
        print(f"  ⚠️  RAGAS evaluation failed: {e}")
        return {
            "faithfulness": 0.0,
            "answer_relevancy": 0.0,
            "context_precision": 0.0,
            "context_recall": 0.0,
            "per_question": []
        }


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    diagnostic_tree = {
        "faithfulness": ("LLM hallucinating", "Tighten prompt, lower temperature"),
        "context_recall": ("Missing relevant chunks", "Improve chunking or add BM25"),
        "context_precision": ("Too many irrelevant chunks", "Add reranking or metadata filter"),
        "answer_relevancy": ("Answer doesn't match question", "Improve prompt template"),
    }

    # Compute avg of 4 metrics and find worst_metric for each result
    scored_results = []
    for result in eval_results:
        metrics = {
            "faithfulness": result.faithfulness,
            "answer_relevancy": result.answer_relevancy,
            "context_precision": result.context_precision,
            "context_recall": result.context_recall,
        }
        avg_score = sum(metrics.values()) / len(metrics)
        worst_metric = min(metrics, key=metrics.get)
        scored_results.append({
            "result": result,
            "avg_score": avg_score,
            "worst_metric": worst_metric,
            "worst_score": metrics[worst_metric]
        })

    # Sort by avg ascending and take bottom_n
    sorted_results = sorted(scored_results, key=lambda x: x["avg_score"])
    bottom_results = sorted_results[:bottom_n]

    # Build failure analysis
    failures = []
    for item in bottom_results:
        result = item["result"]
        worst_metric = item["worst_metric"]
        diagnosis, suggested_fix = diagnostic_tree.get(worst_metric, ("Unknown issue", "Investigate further"))

        failures.append({
            "question": result.question,
            "ground_truth": result.ground_truth,
            "answer": result.answer,
            "worst_metric": worst_metric,
            "score": item["worst_score"],
            "avg_score": item["avg_score"],
            "diagnosis": diagnosis,
            "suggested_fix": suggested_fix
        })

    return failures


def save_report(results: dict, failures: list[dict], path: str = "ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    report = {
        "aggregate": {k: v for k, v in results.items() if k != "per_question"},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
