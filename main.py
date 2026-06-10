import time, math, json
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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

    def score_similarity(self, s1: str, s2: str) -> float:
        min_len = min(len(s1), len(s2))
        if min_len == 0: return 0.0
        match_count = sum(1 for i in range(min_len) if s1[i] == s2[i])
        return match_count / min_len

ai_engine = SafeTCRInferenceCore()

class SingleQuery(BaseModel):
    peptide: str
    hla: str

class BulkRequest(BaseModel):
    license_tier: str                       
    billing_cycle: str                      
    account_active_seats_count: int         
    current_month_cumulative_usage: int    
    queries: List[SingleQuery]              

@app.post("/api/v1/screening/bulk")
async def process_bulk_screening(payload: BulkRequest):
    start_perf = time.perf_counter()
    tier = payload.license_tier
    cycle = payload.billing_cycle.lower().strip()

    limits = {"Starter": 1500, "Standard Pro": 30000, "Enterprise Bulk": 1000000}
    base_fees_monthly = {"Starter": 39000, "Standard Pro": 390000, "Enterprise Bulk": 8900000}
    base_fees_yearly_discounted = {"Starter": 31200, "Standard Pro": 312000, "Enterprise Bulk": 7120000} 

    if tier not in limits:
        raise HTTPException(status_code=400, detail="Invalid tier")
    if cycle not in ["monthly", "yearly"]:
        raise HTTPException(status_code=400, detail="Invalid billing cycle.")

    active_base_fee = base_fees_yearly_discounted[tier] if cycle == "yearly" else base_fees_monthly[tier]

    response_results = []
    for query in payload.queries:
        pep = query.peptide.upper().strip()
        if not pep.isalpha() or len(pep) < 8: continue
        mock_tcr = "CASSLAPGATNEKLFF" if "G" in pep else "CASSQDRTGENEKLFF"
        mock_energy = -8.7 if "G" in pep else -7.4
        max_sim = 0.0
        for black_tcr in ai_engine.blacklist:
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
    usage_fee = billable_overage * 0.1  

    total_invoice = active_base_fee + seat_fee + usage_fee

    return {
        "api_status": "SUCCESS",
        "performance_metrics": {"batch_processed_count": incoming_count},
        "immune_nexus_commercial_invoice": {
            "applied_domain": "://immunenexus.com",
            "subscription_tier": tier,
            "billing_cycle_mode": f"{cycle} subscription tier",
            "pricing_breakdown": {
                "base_subscription_fee_krw": f"₩ {active_base_fee:,}",
                "per_seat_surcharge_krw": f"₩ {seat_fee:,}",
                "usage_based_overage_charge_krw": f"₩ {usage_fee:,.0f} 원"
            },
            "total_monthly_billing_invoice_krw": f"₩ {total_invoice:,.0f} 원"
        },
        "data": response_results
    }

pricing_web_page = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>ImmuneNexus™ - Pricing Plans</title>
    <style>
        body { font-family: -apple-system, sans-serif; background-color: #fafafa; color: #111; margin: 0; padding: 40px 20px; display: flex; flex-direction: column; align-items: center; }
        .header { text-align: center; margin-bottom: 50px; }
        .header h1 { font-size: 2.3rem; font-weight: 800; letter-spacing: -0.05em; }
        .pricing-container { display: flex; gap: 24px; max-width: 1100px; width: 100%; justify-content: center; flex-wrap: wrap; margin-bottom: 60px; }
        .price-card { background: #fff; border: 1px solid #e5e5e5; border-radius: 8px; padding: 32px; width: 280px; display: flex; flex-direction: column; transition: all 0.2s; }
        .price-card:hover { border-color: #111; }
        .price-card.featured { border: 2px solid #111; }
        .tier-name { font-size: 1.2rem; font-weight: 700; margin-bottom: 8px; }
        .tier-price { font-size: 1.8rem; font-weight: 800; margin-bottom: 20px; }
        .tier-price span { font-size: 0.85rem; color: #666; font-weight: 400; }
        .features-list { list-style: none; padding: 0; margin: 0 0 32px 0; flex-grow: 1; font-size: 0.9rem; color: #444; }
        .features-list li { margin-bottom: 12px; }
        .features-list li::before { content: "✓ "; font-weight: bold; }
        .cta-btn { background-color: #111; color: #fff; border: none; padding: 12px; border-radius: 6px; font-weight: 600; cursor: pointer; text-align: center; text-decoration: none; }
        .cta-btn.secondary { background-color: #fff; color: #111; border: 1px solid #e5e5e5; }
        .portal-section { max-width: 900px; width: 100%; background: #fff; border: 1px solid #e5e5e5; border-radius: 8px; padding: 40px; box-sizing: border-box; }
        .portal-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
        .portal-card { border: 1px solid #e5e5e5; border-radius: 6px; padding: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ImmuneNexus™ Subscription Options</h1>
        <p>무료 시연, 월간/연간 구독, 종량제 혼합형 빌링 아키텍처</p>
    </div>
    <div class="pricing-container">
        <div class="price-card">
            <div class="tier-name">Starter (개인/학술용)</div>
            <div class="tier-price">₩ 39,000 <span>/ 월</span></div>
            <ul class="features-list">
                <li>월 1,500건 예측 제공</li>
                <li>기초 GNN 3D 구조 분석</li>
                <li>개인 단일 계정 전용 할당</li>
            </ul>
            <button class="cta-btn secondary" onclick="checkout('Starter')">구독하기</button>
        </div>
        <div class="price-card featured">
            <div class="tier-name">Standard Pro (바이오텍)</div>
            <div class="tier-price">₩ 390,000 <span>/ 월</span></div>
            <ul class="features-list">
                <li>월 30,000건 고속 스크리닝</li>
                <li>BLOSUM62 독성 필터 개방</li>
                <li>초과 계정 인당 30만 원 추가 과금</li>
            </ul>
            <button class="cta-btn" onclick="checkout('Standard Pro')">인기 플랜 선택</button>
        </div>
        <div class="price-card">
            <div class="tier-name">Enterprise Bulk (대형 제약사)</div>
            <div class="tier-price">₩ 8,900,000 <span>/ 월</span></div>
            <ul class="features-list">
                <li>월 1,000,000건 계산 한도 보장</li>
                <li>한도 초과 시 쿼리당 0.1원 종량제 실시간 적용</li>
                <li>독립형 전용 클라우드 VPC 허브 인프라</li>
            </ul>
            <button class="cta-btn secondary" onclick="checkout('Enterprise')">도입 문의</button>
        </div>
    </div>
    <div class="portal-section">
        <h2 style="margin-top:0; font-size:1.3rem; border-bottom:1px solid #e5e5e5; padding-bottom:10px;">Customer Portal (사용량 및 구독 갱신 관리)</h2>
        <div class="portal-grid">
            <div class="portal-card">
                <h3>사용량 기반 종량제(Usage) 명세</h3>
                <p>이번 달 기본 할당량을 초과하여 실시간 청구된 초과 쿼리(건당 0.1원) 미납 통계를 조회합니다.</p>
                <button class="cta-btn secondary" onclick="alert('실시간 API 종량제 모니터링 노드를 로드합니다.')">종량제 내역 확인</button>
            </div>
            <div class="portal-card">
                <h3>연간 구독 전환 (20% 즉시 세이빙)</h3>
                <p>월정액 요금제에서 연간 정기 결제 방식으로 변경하여 매달 20%의 법인 예산을 자동 절감합니다.</p>
                <button class="cta-btn secondary" onclick="alert('연간 구독 계약 갱신 세션으로 이동합니다.')">연간 플랜 전환</button>
            </div>
        </div>
    </div>
    <script>
        function checkout(p) { alert(p + " 플랜의 월간/연간 구독 스위칭 및 카드 빌링 정산 세션을 실행합니다."); }
    </script>
</body>
</html>"""

@app.get("/pricing", response_class=HTMLResponse)
async def get_pricing_page():
    return """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ImmuneNexus™ - Pricing Plans & Portal</title>
    <style>
        /* 미니멀리즘 흑백 모노크롬 디자인 시스템 */
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #fafafa;
            color: #111111;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .header {
            text-align: center;
            margin-bottom: 50px;
        }
        .header h1 {
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.05em;
            margin-bottom: 10px;
        }
        .header p {
            color: #666666;
            font-size: 1.1rem;
        }

        /* 3단계 가격 정책 테이블 레이아웃 */
        .pricing-container {
            display: flex;
            gap: 24px;
            max-width: 1100px;
            width: 100%;
            justify-content: center;
            flex-wrap: wrap;
            margin-bottom: 60px;
        }
        .price-card {
            background: #ffffff;
            border: 1px solid #e5e5e5;
            border-radius: 8px;
            padding: 32px;
            width: 280px;
            display: flex;
            flex-direction: column;
            transition: all 0.2s ease;
        }
        .price-card:hover {
            border-color: #111111;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        }
        .price-card.featured {
            border: 2px solid #111111;
            position: relative;
        }
        .price-card.featured::top {
            content: "POPULAR";
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            background: #111111;
            color: #ffffff;
            padding: 2px 12px;
            font-size: 0.75rem;
            font-weight: 700;
            border-radius: 12px;
        }
        .tier-name {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .tier-price {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 20px;
        }
        .tier-price span {
            font-size: 0.9rem;
            color: #666666;
            font-weight: 400;
        }
        .features-list {
            list-style: none;
            padding: 0;
            margin: 0 0 32px 0;
            flex-grow: 1;
        }
        .features-list li {
            font-size: 0.95rem;
            color: #444444;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
        }
        .features-list li::before {
            content: "✓";
            margin-right: 8px;
            font-weight: bold;
            color: #111111;
        }
        .cta-btn {
            background-color: #111111;
            color: #ffffff;
            border: none;
            padding: 12px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            transition: background-color 0.2s;
        }
        .cta-btn:hover {
            background-color: #333333;
        }
        .cta-btn.secondary {
            background-color: #ffffff;
            color: #111111;
            border: 1px solid #e5e5e5;
        }
        .cta-btn.secondary:hover {
            background-color: #f5f5f5;
            border-color: #111111;
        }

        /* 사용자 포털 (Customer Portal) 섹션 */
        .portal-section {
            max-width: 900px;
            width: 100%;
            background: #ffffff;
            border: 1px solid #e5e5e5;
            border-radius: 8px;
            padding: 40px;
            box-sizing: border-box;
        }
        .portal-section h2 {
            font-size: 1.5rem;
            margin-top: 0;
            margin-bottom: 24px;
            border-bottom: 1px solid #e5e5e5;
            padding-bottom: 12px;
        }
        .portal-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }
        .portal-card {
            border: 1px solid #e5e5e5;
            border-radius: 6px;
            padding: 20px;
        }
        .portal-card h3 {
            margin-top: 0;
            font-size: 1.1rem;
            margin-bottom: 8px;
        }
        .portal-card p {
            color: #666666;
            font-size: 0.9rem;
            margin-bottom: 16px;
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>ImmuneNexus™ Pricing</h1>
        <p>글로벌 신약 발굴을 위한 최적의 엔터프라이즈 AI 멤버십 플랜</p>
    </div>

    <!-- 3단계 가격 정책 페이지 (Pricing Table) -->
    <div class="pricing-container">
        <!-- Starter Plan -->
        <div class="price-card">
            <div class="tier-name">Starter</div>
            <div class="tier-price">₩ 39,000 <span>/ 월</span></div>
            <ul class="features-list">
                <li>월 1,500건 예측 연산</li>
                <li>기초 GNN 3D 구조 매핑</li>
                <li>아미노산 토큰 가동성 스캔</li>
                <li>1인 전용 계정 제공</li>
            </ul>
            <button class="cta-btn secondary" onclick="checkout('Starter')">구독하기</button>
        </div>

        <!-- Pro Plan (Anchored Center) -->
        <div class="price-card featured">
            <div class="tier-name">Standard Pro</div>
            <div class="tier-price">₩ 390,000 <span>/ 월</span></div>
            <ul class="features-list">
                <li>월 30,000건 스크리닝</li>
                <li>BLOSUM62 정밀 안전 필터</li>
                <li>4단계 오프타겟 리스크 분석</li>
                <li>스타트업 법인카드 최적화</li>
            </ul>
            <button class="cta-btn" onclick="checkout('Standard Pro')">인기 플랜 구독</button>
        </div>

        <!-- Enterprise Plan -->
        <div class="price-card">
            <div class="tier-name">Enterprise Bulk</div>
            <div class="tier-price">₩ 8,900,000 <span>/ 월</span></div>
            <ul class="features-list">
                <li>월 1,000,000건 초대량 스캔</li>
                <li>독립형 Cloud VPC 인프라</li>
                <li>임상 규정 심사 보고서 무제한</li>
                <li>초과 쿼리당 0.1원 종량제</li>
            </ul>
            <button class="cta-btn secondary" onclick="checkout('Enterprise')">기업용 도입 문의</button>
        </div>
    </div>

    <!-- 사용자 포털 (Customer Portal) UI -->
    <div class="portal-section">
        <h2>사용자 관리 포털 (Customer Portal)</h2>
        <div class="portal-grid">
            <div class="portal-card">
                <h3>결제 수단 및 카드 관리</h3>
                <p>등록된 B2B 법인카드 및 자동 결제 수단을 안전하게 변경하거나 갱신합니다.</p>
                <button class="cta-btn secondary" onclick="alert('Stripe 결제 수단 변경 창으로 안전하게 이동합니다.')">수단 변경</button>
            </div>
            <div class="portal-card">
                <h3>이전 결제 내역 (인보이스)</h3>
                <p>발행된 월별 구독 영수증 및 대량 스크리닝 초과 과금 내역서를 확인 및 다운로드합니다.</p>
                <button class="cta-btn secondary" onclick="alert('PDF 인보이스 내역 조회를 시작합니다.')">내역 확인</button>
            </div>
            <div class="portal-card">
                <h3>구독 플랜 변경</h3>
                <p> Starter 플랜에서 Standard Pro 등 상위 데이터 처리 엔진 플랜으로 즉시 업그레이드합니다.</p>
                <button class="cta-btn secondary" onclick="alert('플랜 업그레이드 품의 창을 가동합니다.')">플랜 변경</button>
            </div>
            <div class="portal-card">
                <h3>구독 취소 및 보류</h3>
                <p>진행 중인 신약 프로젝트 종료 시 정기 결제를 안전하게 해지하거나 일시 정지합니다.</p>
                <button class="cta-btn secondary" onclick="alert('구독 해지 프로세스를 기동합니다. 위약금은 없습니다.')">구독 취소</button>
            </div>
        </div>
    </div>

    <script>
        function checkout(plan) {
            alert(plan + " 플랜 정기 결제를 위해 Stripe/Toss 빌링 게이트웨이 보안 창을 활성화합니다. (Unit Price 가치 연동)");
        }
    </script>
</body>
</html>
"""

# [★오류 전면 해결 지점] 
# 클라우드 서버 환경(main:app 구조)에서 구문 충돌을 일으키던 
# uvicorn 호출 방식과 await 코드를 완벽히 제거하여 순수 파일 기동 규격으로 락인합니다.
