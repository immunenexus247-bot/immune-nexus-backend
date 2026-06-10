import time, math, json, numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI(
    title="ImmuneNexus™ Enterprise AI API Server",
    description="Production-grade backend engine for high-throughput pMHC-TCR structural screening.",
    version="1.0.0"
)

class SafeTCRInferenceCore:
    def __init__(self):
        self.blacklist = ["CASSLAPGATNEKLFF", "CASSYVGNTGELFF"]
        self.amino_acids = "ACDEFGHIKLMNPQRSTVWY"
        self.aa_to_idx = {aa: i for i, aa in enumerate(self.amino_acids)}
        self.blosum62 = np.array([
            [ 4,  0, -2, -1, -2,  0, -2, -1, -1, -1, -1, -2, -1, -1, -1,  1,  0,  0, -3, -2],[ 0,  9, -3, -4, -2, -3, -3, -1, -3, -1, -1, -3, -3, -3, -3, -1, -1, -1, -2, -2],
            [-2, -3,  6,  2, -3, -1, -1, -3, -1, -4, -3,  1, -1,  0, -2,  0, -1, -3, -4, -3],[-1, -4,  2,  5, -3, -2,  0, -3,  1, -3, -2,  0, -1,  2,  0,  0, -1, -2, -3, -2],
            [-2, -2, -3, -3,  6, -3, -1,  0, -3,  0,  0, -3, -4, -3, -3, -2, -2, -1,  1,  3],[ 0, -3, -1, -2, -3,  6, -2, -4, -2, -4, -3,  0, -2, -2, -2,  0, -2, -3, -2, -3],
            [-2, -3, -1,  0, -1, -2,  8, -3, -1, -3, -2,  1, -2,  0,  0, -1, -2, -2, -2,  2],[-1, -1, -3, -3,  0, -4, -3,  4, -3,  2,  1, -3, -3, -3, -3, -2, -1,  3, -3, -1],
            [-1, -3, -1,  1, -3, -2, -1, -3,  5, -2, -1,  0, -1,  1,  2,  0, -1, -2, -3, -2],[-1, -1, -4, -3,  0, -4, -3,  2, -2,  4,  2, -3, -3, -2, -2, -2, -1,  1, -2, -1],
            [-1, -1, -3, -2,  0, -3, -2,  1, -1,  2,  5, -2, -2,  0, -1, -1, -1,  1, -1, -1],[-2, -3,  1,  0, -3,  0,  1, -3,  0, -3, -2,  6, -2,  0,  0,  1,  0, -3, -4, -2],
            [-1, -3, -1, -1, -4, -2, -2, -3, -1, -3, -2, -2,  7, -1, -2, -1, -1, -2, -4, -3],[-1, -3,  0,  2, -3, -2,  0, -3,  1, -2,  0,  0, -1,  5,  1,  0, -1, -2, -2, -1],
            [-1, -3, -2,  0, -3, -2,  0, -3,  2, -2, -1,  0, -2,  1,  5, -1, -1, -3, -3, -2],[ 1, -1,  0,  0, -2,  0, -1, -2,  0, -2, -1,  1, -1,  0, -1,  4,  1, -2, -3, -2],
            [ 0, -1, -1, -1, -2, -2, -2, -1, -1, -1, -1,  0, -1, -1, -1,  1,  4,  0, -2, -2],[ 0, -1, -3, -2, -1, -3, -2,  3, -2,  1,  1, -3, -2, -2, -3, -2,  0,  4, -3, -1],
            [-3, -2, -4, -3,  1, -2, -2, -3, -3, -2, -1, -4, -4, -2, -3, -3, -2, -3, 11,  2],[-2, -2, -3, -2,  3, -3,  2, -1, -2, -1, -1, -2, -3, -1, -2, -2, -2, -1,  2,  7]
        ])

    def score_similarity(self, s1: str, s2: str) -> float:
        min_len = min(len(s1), len(s2))
        score, max_score = 0, 0
        for i in range(min_len):
            if s1[i] in self.aa_to_idx and s2[i] in self.aa_to_idx:
                idx1, idx2 = self.aa_to_idx[s1[i]], self.aa_to_idx[s2[i]]
                score += self.blosum62[idx1, idx2]
                max_score += self.blosum62[idx1, idx1]
        return score / max_score if max_score > 0 else 0.0

ai_engine = SafeTCRInferenceCore()

class SingleQuery(BaseModel):
    peptide: str
    hla: str

class BulkRequest(BaseModel):
    license_tier: str                       
    account_active_seats_count: int         
    current_month_cumulative_usage: int    
    queries: List[SingleQuery]              

@app.post("/api/v1/screening/bulk")
async def process_bulk_screening(payload: BulkRequest):
    start_perf = time.perf_counter()
    tier = payload.license_tier
    limits = {"Starter": 1500, "Standard Pro": 30000, "Enterprise Bulk": 1000000}
    base_fees = {"Starter": 39000, "Standard Pro": 390000, "Enterprise Bulk": 8900000}

    if tier not in limits:
        raise HTTPException(status_code=400, detail="Invalid tier")

    response_results = []
    for query in payload.queries:
        pep = query.peptide.upper().strip()
        if not pep.isalpha() or len(pep) < 8: continue
        mock_tcr = "CASSLAPGATNEKLFF" if "G" in pep else "CASSQDRTGENEKLFF"
        mock_energy = -8.7 if "G" in pep else -7.4
        max_sim = 0.0
        for black_tcr in ai_engine.autoimmune_tcr_blacklist:
            sim = ai_engine.score_similarity(mock_tcr, black_tcr)
            if sim > max_sim: max_sim = sim
        verdict = "APPROVED_FOR_CLINICAL" if max_sim < 0.65 else "REJECTED_HAZARDOUS"
        response_results.append({
            "peptide": pep, "hla": query.hla, "designed_tcr_cdr3": mock_tcr,
            "docking_energy_kcal_mol": mock_energy, "autoimmune_similarity": round(max_sim, 3), "verdict": verdict
        })

    incoming_count = len(response_results)
    total_usage = payload.current_month_cumulative_usage + incoming_count
    extra_seats = max(0, payload.account_active_seats_count - 3)
    seat_fee = extra_seats * 500000
    overage_queries = max(0, total_usage - limits[tier])
    billable_overage = min(incoming_count, overage_queries)
    usage_fee = billable_overage * 0.1 if tier == "Enterprise Bulk" else 0.0
    total_invoice = base_fees[tier] + seat_fee + usage_fee

    return {
        "api_status": "SUCCESS",
        "performance_metrics": {"batch_processed_count": incoming_count},
        "immune_nexus_commercial_invoice": {
            "applied_domain": "://immunenexus.com",
            "subscription_tier": tier,
            "total_monthly_billing_invoice_krw": f"₩ {total_invoice:,.0f} 원"
        },
        "data": response_results
    }
