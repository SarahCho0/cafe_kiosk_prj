"""
5지는 카페 AI 키오스크 — 오지 (Oji)
RAG-based Natural Language Kiosk Interface
"""
import json
import math
import re
import os
import streamlit as st

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# ─────────────────────────  PAGE CONFIG  ──────────────────────
st.set_page_config(
    page_title="5지는 카페 키오스크 ✨",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────  CSS  ──────────────────────────────
# 럭셔리 스페셜티 카페 감성: 따뜻한 크림 + 에스프레소 브라운 + 앤틱 골드
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Jua&display=swap');

/* ═══════════════ 전체 레이아웃 ═══════════════ */
.stApp {
    background: #F7F3EE !important;
    font-family: 'Nunito', -apple-system, sans-serif !important;
}
.stApp > .main .block-container {
    background: transparent;
    padding-top: 1.5rem;
    max-width: 1200px;
}
/* Streamlit 기본 요소 */
h1,h2,h3,h4 { font-family: 'Nunito', sans-serif !important; color: #1C110A !important; font-weight: 800 !important; }
.stMarkdown p, .stMarkdown li { color: #3D2C22 !important; }
.stText, .stCaption { color: #5C4A3A !important; }

/* ═══════════════ 사이드바 ═══════════════ */
section[data-testid="stSidebar"] {
    background: #F0EAE0 !important;
    border-right: 1px solid #DDD0C0 !important;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stMetric label { color: #2C1A0E !important; }
section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #2C1A0E !important;
    border: 1.5px solid #C9A55A !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #3D2010 !important;
    color: #F5E095 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stButton > button:hover { filter: brightness(1.12) !important; }

/* ═══════════════ 채팅 메시지 ═══════════════ */
.stChatMessage {
    background: #FFFFFF !important;
    border: 1px solid #E8DDD0 !important;
    border-radius: 14px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 2px 10px rgba(44,26,14,0.06) !important;
}
div[data-testid="stChatMessageContent"] p { color: #2C1A0E !important; }
.stChatInputContainer { border-top: 1px solid #E8DDD0 !important; background: #FFFFFF !important; border-radius: 12px !important; }

/* ═══════════════ 헤더 ═══════════════ */
.oji-header {
    background: linear-gradient(135deg, #1C110A 0%, #3D2010 60%, #5C3018 100%);
    padding: 40px 48px 30px;
    border-radius: 24px;
    text-align: center;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(44,26,14,0.28);
    position: relative;
    overflow: hidden;
}
.oji-header::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at 30% 50%, rgba(201,165,90,0.15) 0%, transparent 60%),
                radial-gradient(ellipse at 70% 50%, rgba(201,165,90,0.1) 0%, transparent 60%);
}
.oji-header .logo-icon {
    font-size: 3em;
    line-height: 1;
    margin-bottom: 8px;
    position: relative;
    display: block;
}
.oji-header h1 {
    font-family: 'Jua', 'Nunito', sans-serif !important;
    font-size: 3em;
    margin: 0;
    letter-spacing: 3px;
    color: #F0D080 !important;
    font-weight: 900;
    position: relative;
    text-shadow: 0 2px 12px rgba(0,0,0,0.3);
}
.oji-header p {
    margin: 8px 0 0;
    font-size: 1em;
    color: #C8B090 !important;
    letter-spacing: .8px;
    position: relative;
    font-weight: 600;
}
/* ── 언어 버튼 ── */
.lang-bar { display:flex; gap:8px; justify-content:center; margin-top:14px; position:relative; }
.lang-pill {
    padding: 5px 16px; border-radius: 20px; font-size: .82em; font-weight: 600;
    background: rgba(240,208,128,0.15); color: #C8B090 !important; cursor: pointer;
    border: 1px solid rgba(240,208,128,0.35); letter-spacing: .5px;
    transition: all .2s;
}
.lang-pill.active {
    background: #F0D080; color: #1C110A !important;
    border-color: #F0D080; font-weight: 700;
}

/* ═══════════════ 장바구니 ═══════════════ */
.cart-box {
    background: #FFFFFF;
    border: 1px solid #E0D4C4;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    box-shadow: 0 1px 4px rgba(44,26,14,0.06);
}
.cart-total {
    background: linear-gradient(135deg, #2C1A0E, #4A2E18);
    color: #F0D080 !important;
    padding: 11px 18px; border-radius: 10px;
    text-align: center; font-weight: 700; font-size: 1.1em; margin-top: 8px;
    box-shadow: 0 2px 8px rgba(44,26,14,0.2);
}
.order-done {
    background: #F0FBF0; border: 2px solid #4CAF50;
    border-radius: 14px; padding: 24px; text-align: center;
    font-size: 1.2em; margin: 16px 0;
}

/* ═══════════════ 결제 진행 표시기 ═══════════════ */
.payment-progress {
    display:flex; align-items:center; justify-content:center;
    gap:0; margin:0 auto 24px; max-width:900px; flex-wrap:nowrap;
    padding:16px 20px; background:#FFFFFF; border-radius:14px;
    border:1px solid #E0D4C4;
    box-shadow: 0 2px 12px rgba(44,26,14,0.07);
}
.step-item { display:flex; flex-direction:column; align-items:center; gap:4px; }
.step-dot {
    width: 32px; height: 32px; border-radius: 50%; display:flex;
    align-items:center; justify-content:center; font-weight:700; font-size:.8em;
    background: #EDE6DC; color: #9A8070; flex-shrink:0;
}
.step-dot.active {
    background: #C9A55A; color: #FFFFFF;
    box-shadow: 0 2px 8px rgba(201,165,90,0.45);
}
.step-dot.done { background: #4CAF50; color: #fff; }
.step-label { font-size:.67em; color: #8A7060 !important; white-space:nowrap; max-width:70px; text-align:center; }
.step-connector { width:28px; height:3px; background: #EDE6DC; margin-bottom:16px; flex-shrink:0; }
.step-connector.done { background: #4CAF50; }

/* ═══════════════ 결제 수단 카드 ═══════════════ */
.pay-method-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin:16px 0; }
.pay-method-card {
    border: 1.5px solid #E0D4C4; border-radius: 14px; padding: 22px 14px;
    text-align: center; cursor: pointer; transition: all .2s;
    background: #FFFFFF;
}
.pay-method-card:hover {
    border-color: #C9A55A; background: #FAF6EF;
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(201,165,90,0.2);
}
.pay-method-card .icon { font-size:2.2em; margin-bottom:6px; }
.pay-method-card .name { font-weight:700; font-size:1em; color:#2C1A0E !important; }
.pay-method-card .desc { font-size:.76em; color:#7A6654 !important; margin-top:3px; }

/* ═══════════════ 결제 처리 ═══════════════ */
.processing-box {
    text-align:center; padding:52px 24px;
    background: linear-gradient(135deg, #FAF6EF, #FFFFFF);
    border-radius: 18px; border:1px solid #E0D4C4;
}
.processing-spinner { font-size:3em; animation:spin 1s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }

/* ═══════════════ 성공/실패 ═══════════════ */
.success-box {
    text-align:center; padding:40px 24px; background:#F0FBF0;
    border:2px solid #4CAF50; border-radius:18px; margin:16px 0;
}
.failure-box {
    text-align:center; padding:40px 24px; background:#FFF8F0;
    border:2px solid #FF9800; border-radius:18px; margin:16px 0;
}

/* ═══════════════ 주문번호 ═══════════════ */
.order-number-badge {
    display:inline-block;
    background: linear-gradient(135deg, #C9A55A, #E8C870);
    color: #1C110A !important;
    font-size:2.8em; font-weight:900; padding:14px 44px;
    border-radius:16px; letter-spacing:6px; margin:16px 0;
    box-shadow: 0 6px 24px rgba(201,165,90,0.45);
}

/* ═══════════════ 대기 화면 ═══════════════ */
.waiting-screen {
    text-align:center; padding:52px 24px;
    background: linear-gradient(135deg, #FAF6EF, #FFFFFF);
    border-radius:18px; border:1px solid #E0D4C4;
}

/* ═══════════════ 매장 정보 ═══════════════ */
.store-card {
    background: #FFFFFF; border:1px solid #E0D4C4; border-radius:12px;
    padding: 16px; margin-bottom: 8px;
}
.store-row { display:flex; gap:10px; margin:6px 0; font-size:.86em; color:#3D2C22 !important; align-items:flex-start; }
.store-icon { width:18px; flex-shrink:0; margin-top:1px; }
.facility-tag {
    display:inline-block; background:#F5EFE5; color:#5C3D2E !important;
    border:1px solid #DDD0C0; border-radius:10px;
    padding:2px 10px; font-size:.76em; margin:2px;
}

/* ═══════════════ 직원 문의 ═══════════════ */
.staff-card {
    background: #FAF6EF; border:1px solid #E0D4C4; border-radius:12px;
    padding:14px; margin-bottom:8px;
}
.staff-item {
    background:#FFFFFF; border:1px solid #EDE6DC; border-radius:8px;
    padding:7px 12px; margin:4px 0; font-size:.83em;
    display:flex; align-items:center; gap:8px; color:#3D2C22 !important;
}

/* ═══════════════ 결제 단계 제목 ═══════════════ */
.pay-step-title {
    color: #1C110A !important; font-size:1.5em; font-weight:700;
    margin:0 0 18px; padding-bottom:12px;
    border-bottom: 2px solid #C9A55A;
    letter-spacing: .5px;
}

/* ═══════════════ 주문 타입 버튼 ═══════════════ */
.order-type-btn {
    border:2px solid #E0D4C4; border-radius:14px; padding:28px 16px;
    text-align:center; font-size:1.1em; font-weight:600; cursor:pointer;
    transition:all .2s; background:#FFFFFF; width:100%;
    color:#2C1A0E !important;
}
.order-type-btn:hover {
    border-color:#C9A55A; background:#FAF6EF;
    box-shadow: 0 4px 16px rgba(201,165,90,0.2);
}

/* ═══════════════ QR 박스 ═══════════════ */
.qr-box {
    display:inline-block; border:3px solid #2C1A0E; border-radius:10px;
    padding:16px; font-size:72px; line-height:1; margin:12px auto; background:#fff;
}

/* ═══════════════ 직원 호출 버튼 (채팅) ═══════════════ */
.staff-call-btn {
    display:inline-block; background:#C9A55A; color:#FFFFFF !important;
    padding:8px 22px; border-radius:20px; font-weight:600;
    font-size:.88em; border:none; cursor:pointer; margin-top:8px;
    box-shadow:0 2px 8px rgba(201,165,90,0.35); letter-spacing:.3px;
}
.staff-call-btn:hover { background:#A8853A; }

/* ═══════════════ 사이드바 섹션 타이틀 ═══════════════ */
.sb-section-title {
    color:#1C110A !important; font-weight:700; font-size:.95em;
    margin:0 0 8px; padding:6px 0;
    border-bottom:2px solid #C9A55A;
}

/* ═══════════════ 진상 경고 배너 ═══════════════ */
.abuse-banner {
    background:#FFF5F5; border:1px solid #FF6B6B;
    border-radius:10px; padding:12px 16px; margin:8px 0;
    color:#8B0000 !important; font-size:.88em;
}

/* ═══════════════ 퀵 액션 버튼 ═══════════════ */
.quick-btn-row { display:flex; flex-wrap:wrap; gap:8px; padding:12px 2px 6px; }
.quick-btn {
    display:inline-flex; align-items:center; gap:5px;
    background:#FFFFFF; border:1.5px solid #DDD0C0; border-radius:22px;
    padding:7px 16px; font-size:.83em; font-weight:500;
    color:#2C1A0E !important; cursor:pointer; transition:all .18s;
    white-space:nowrap; box-shadow:0 1px 4px rgba(44,26,14,0.07);
    letter-spacing:.2px;
}
.quick-btn:hover { background:#FAF6EF; border-color:#C9A55A; }
.quick-btn.active {
    background: linear-gradient(135deg,#C9A55A,#E8C870);
    border-color:#C9A55A; color:#1C110A !important; font-weight:700;
    box-shadow:0 2px 8px rgba(201,165,90,0.35);
}

/* ═══════════════ 메뉴 패널 ═══════════════ */
.menu-panel-wrap {
    background:#FFFFFF; border:1px solid #E0D4C4; border-radius:18px;
    padding:20px 20px 10px; margin:4px 0 12px;
    box-shadow: 0 4px 20px rgba(44,26,14,0.07);
}

/* ── 메뉴 카드 ── */
.mc-badge {
    display:inline-block;
    background: linear-gradient(135deg,#C9A55A,#E8C870);
    color:#1C110A !important;
    font-size:.68em; font-weight:800; border-radius:6px;
    padding:2px 8px; margin-bottom:7px; letter-spacing:.5px;
}
.mc-name {
    font-weight:700; color:#1C110A !important; font-size:.95em;
    line-height:1.35; margin-bottom:3px;
}
.mc-eng  { font-size:.72em; color:#9A8070 !important; margin-bottom:6px; letter-spacing:.5px; text-transform:uppercase; }
.mc-desc { font-size:.79em; color:#5C4A3A !important; margin-bottom:7px; line-height:1.45; }
.mc-price {
    font-size:1.15em; font-weight:800; color:#7A4020 !important;
    margin-bottom:7px; letter-spacing:.3px;
}
.mc-meta  { font-size:.74em; color:#8A7060 !important; margin-bottom:4px; }
.mc-warn  {
    font-size:.73em; color:#7A3A00 !important;
    background:#FFF3E0; border-radius:6px;
    padding:5px 9px; margin-top:6px;
    border-left: 3px solid #FF9800;
}

/* ── 뉴스 카드 ── */
.nc-cat-ev {
    display:inline-block; background:#B03020; color:#fff !important;
    font-size:.68em; font-weight:700; border-radius:4px;
    padding:2px 8px; margin-bottom:5px; letter-spacing:.5px;
}
.nc-cat-news {
    display:inline-block; background:#2C1A0E; color:#F0D080 !important;
    font-size:.68em; font-weight:700; border-radius:4px;
    padding:2px 8px; margin-bottom:5px; letter-spacing:.5px;
}
.nc-title { font-weight:700; color:#1C110A !important; font-size:.93em; margin-bottom:4px; line-height:1.4; }
.nc-meta  { font-size:.74em; color:#9A8070 !important; margin-bottom:6px; }
.nc-discount {
    display:inline-block; background:#FFF0E8; color:#7A3A00 !important;
    border:1px solid #FFB88A; border-radius:6px;
    font-size:.71em; font-weight:700; padding:2px 9px; margin-top:4px;
    letter-spacing:.3px;
}

/* Streamlit 기본 버튼 오버라이드 */
.stButton > button {
    border-radius: 9px !important;
    font-weight: 600 !important;
    transition: all .2s !important;
    letter-spacing: .2px !important;
}
/* primary 버튼: 짙은 갈색 배경 + 밝은 크림 텍스트 */
.stButton > button[kind="primary"] {
    background: #4A2E18 !important;
    color: #FFF5D6 !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(44,26,14,0.25) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #6A4428 !important;
    color: #FFF5D6 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(44,26,14,0.3) !important;
}
/* secondary 버튼: 흰 배경 + 짙은 갈색 텍스트 */
.stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #2C1A0E !important;
    border: 1.5px solid #C9A55A !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #A8853A !important;
    background: #FAF6EF !important;
    color: #1C110A !important;
}
/* expander */
.streamlit-expanderHeader {
    background: #FAF6EF !important;
    border-radius: 8px !important;
    color: #2C1A0E !important;
}
/* metric */
[data-testid="stMetricValue"] { color: #2C1A0E !important; font-weight:700 !important; }
[data-testid="stMetricLabel"] { color: #8A7060 !important; font-size:.82em !important; }
/* divider */
hr { border-color: #E8DDD0 !important; }
/* toast */
.stToast { background: #2C1A0E !important; color: #F0D080 !important; border-radius:10px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────  STORE INFO (강남역점)  ─────────────
STORE_INFO = {
    "name_ko": "5지는 카페 강남역점",
    "name_en": "Ojineun Cafe Gangnam Station",
    "name_cn": "5지는 카페 江南站店",
    "name_jp": "5지는 카페 江南駅店",
    "address": "서울시 강남구 강남대로 100 강남빌딩 1층",
    "direction_ko": "강남역 3번출구 바로 앞에 위치하고 있습니다^^",
    "direction_en": "Right in front of Exit 3, Gangnam Station",
    "direction_cn": "位于江南站3号出口正前方",
    "direction_jp": "江南駅3番出口のすぐ前",
    "subway_ko": "강남역 3번 출구 도보 5분",
    "subway_en": "Gangnam Stn. Exit 3 · 5 min walk",
    "subway_cn": "江南站3号出口 步行5分钟",
    "subway_jp": "江南駅3番出口 徒歩5分",
    "hours_ko": "평일 07:00-23:00, 주말 08:00-23:00",
    "hours_en": "Weekday 07:00-23:00, Weekend 08:00-23:00",
    "hours_cn": "平日 07:00-23:00, 周末 08:00-23:00",
    "hours_jp": "平日 07:00-23:00, 土日 08:00-23:00",
    "phone": "02-6955-0123",
    "facilities_ko": ["무선 인터넷", "콘센트", "휠체어 접근", "주차장", "단체석 예약"],
    "facilities_en": ["WiFi", "Power Outlets", "Wheelchair Access", "Parking", "Group Seating"],
    "facilities_cn": ["无线网络", "插座", "轮椅通行", "停车场", "团体座位"],
    "facilities_jp": ["WiFi", "コンセント", "車いす通行", "駐車場", "団体座席"],
}

# ─────────────────────────  TRANSLATIONS  ────────────────────
TRANSLATIONS: dict[str, dict[str, object]] = {
    "ko": {
        "welcome": "5지는 카페 키오스크",
        "subtitle": "AI 직원 오지(Oji) · 오지는 맛! 오지는 가격! 오지는 카페!",
        "cart_title": "🛒 장바구니",
        "cart_empty": "장바구니가 비어있어요 🛒",
        "total": "합계",
        "checkout": "💳 결제하기",
        "clear_cart": "🗑️ 전체 비우기",
        "reset": "🔄 대화 초기화",
        "table": "매장에서 먹기",
        "takeout": "포장해 가기",
        "stage_cart": "장바구니",
        "stage_order_type": "포장여부",
        "stage_options": "추가옵션",
        "stage_payment_select": "결제수단",
        "stage_payment_detail": "결제진행",
        "stage_complete": "주문완료",
        "stage_waiting": "대기중",
        "pay_card": "카드", "pay_card_desc": "신용·체크·NFC",
        "pay_qr": "간편결제", "pay_qr_desc": "QR·바코드",
        "pay_cash": "현금", "pay_cash_desc": "지폐·동전",
        "pay_voucher": "상품권/기프티콘", "pay_voucher_desc": "상품권·기프티콘",
        "pay_point": "포인트/쿠폰", "pay_point_desc": "포인트·할인쿠폰",
        "next": "다음", "back": "이전", "cancel": "주문 취소",
        "confirm": "확인", "retry": "다시 시도",
        "change_method": "다른 결제수단 선택",
        "call_staff": "🔔 직원 호출",
        "new_order": "새 주문 시작",
        "store_info": "📍 매장 정보",
        "store_address": "주소", "store_direction": "찾아가는 길",
        "store_hours": "영업시간", "store_phone": "전화번호",
        "store_facilities": "편의시설",
        "staff_inquiry": "💬 직원 문의 필요",
        "staff_note": "아래 사항은 매장 직원에게 문의해 주세요",
        "staff_items": ["🚻 화장실 비밀번호", "🗺️ 매장 내부 안내", "📦 분실물 문의", "✏️ 특별 요청 사항"],
        "receipt_title": "영수증",
        "receipt_print": "출력", "receipt_email": "이메일", "receipt_no": "필요없음",
        "order_number_label": "주문번호",
        "order_complete_msg": "주문이 완료되었습니다!",
        "wait_msg": "번호를 호명해드릴게요 ☕",
        "won": "원",
        "qty": "수량", "subtotal": "소계",
        "remaining": "잔여 결제금액",
        "add_payment": "+ 결제수단 추가",
        "combined_ok": "복합결제 진행",
        "payment_processing": "결제 처리 중...",
        "payment_success": "결제 완료! ✅",
        "payment_failed": "결제 실패 ❌",
        "payment_failed_reason": "결제에 실패했습니다. 다시 시도하시거나 다른 결제수단을 이용해 주세요.",
        "card_tap": "카드를 단말기에 올려주세요 또는 탭하세요",
        "qr_show": "QR코드 또는 바코드를 스캔해주세요",
        "cash_insert": "현금을 투입해 주세요",
        "voucher_enter": "상품권/기프티콘 번호를 입력해주세요",
        "point_enter": "포인트 번호 또는 쿠폰 코드를 입력해주세요",
        "point_available": "사용 가능 포인트",
        "apply": "적용",
        "discount_applied": "할인 적용됨",
        "settings": "⚙️ 설정",
        "api_key_label": "OpenAI API Key",
        "api_connected": "API 키 연결됨 ✅",
        "api_warning": "API 키를 입력해야 오지와 대화할 수 있어요!",
        "lang_support": "💬 한국어 · English · 中文 · 日本語",
        "satisfaction": "📊 응답 만족도",
        "test_mode": "🤖 돌발 시나리오 테스트",
        "chat_placeholder": "메뉴를 물어보거나 주문해보세요 · 예: 달달한 음료 추천해줘",
        "abuse_warning": "⚠️ 불쾌한 표현이 감지됐습니다. 매장 직원을 호출해드릴까요?",
        "feedback_good": "👍 피드백 감사합니다!",
        "feedback_bad": "👎 의견 감사합니다. 더 나은 오지가 될게요!",
        "currently_open": "영업 중",
        "qa_coffee": "커피", "qa_new": "신메뉴", "qa_drink": "음료", 
        "qa_paik": "빽스치노", "qa_dessert": "디저트", "qa_news": "이벤트·소식", 
        "qa_sale": "할인·특가", "qa_best": "베스트",
        "staff_called_success": "✅ 직원을 호출했습니다! 잠시만 기다려 주세요.",
    },
    "en": {
        "welcome": "Ojineun Cafe Kiosk",
        "subtitle": "AI Staff Oji · Amazing Taste! Amazing Price! Amazing Cafe!",
        "cart_title": "🛒 Cart",
        "cart_empty": "Your cart is empty 🛒",
        "total": "Total",
        "checkout": "💳 Checkout",
        "clear_cart": "🗑️ Clear Cart",
        "reset": "🔄 Reset",
        "table": "Dine In",
        "takeout": "Take Out",
        "stage_cart": "Cart",
        "stage_order_type": "Order Type",
        "stage_options": "Options",
        "stage_payment_select": "Payment",
        "stage_payment_detail": "Processing",
        "stage_complete": "Complete",
        "stage_waiting": "Waiting",
        "pay_card": "Card", "pay_card_desc": "Credit·Debit·NFC",
        "pay_qr": "Mobile Pay", "pay_qr_desc": "QR·Barcode",
        "pay_cash": "Cash", "pay_cash_desc": "Bills·Coins",
        "pay_voucher": "Gift Card", "pay_voucher_desc": "Voucher·Giftishow",
        "pay_point": "Points/Coupon", "pay_point_desc": "Points·Discount",
        "next": "Next", "back": "Back", "cancel": "Cancel Order",
        "confirm": "Confirm", "retry": "Retry",
        "change_method": "Change Payment Method",
        "call_staff": "🔔 Call Staff",
        "new_order": "New Order",
        "store_info": "📍 Store Info",
        "store_address": "Address", "store_direction": "Getting Here",
        "store_hours": "Hours", "store_phone": "Phone",
        "store_facilities": "Facilities",
        "staff_inquiry": "💬 Staff Assistance",
        "staff_note": "Please ask our staff for the following",
        "staff_items": ["🚻 Restroom Code", "🗺️ Store Guide", "📦 Lost & Found", "✏️ Special Requests"],
        "receipt_title": "Receipt",
        "receipt_print": "Print", "receipt_email": "Email", "receipt_no": "No Thanks",
        "order_number_label": "Order #",
        "order_complete_msg": "Order Placed Successfully!",
        "wait_msg": "We'll call your number shortly ☕",
        "won": "KRW",
        "qty": "Qty", "subtotal": "Subtotal",
        "remaining": "Remaining Amount",
        "add_payment": "+ Add Payment",
        "combined_ok": "Proceed",
        "payment_processing": "Processing payment...",
        "payment_success": "Payment Complete! ✅",
        "payment_failed": "Payment Failed ❌",
        "payment_failed_reason": "Payment failed. Please retry or select another method.",
        "card_tap": "Place or tap your card on the reader",
        "qr_show": "Scan your QR code or barcode",
        "cash_insert": "Please insert cash",
        "voucher_enter": "Enter your gift card / voucher number",
        "point_enter": "Enter your points number or coupon code",
        "point_available": "Available Points",
        "apply": "Apply",
        "discount_applied": "Discount Applied",
        "settings": "⚙️ Settings",
        "api_key_label": "OpenAI API Key",
        "api_connected": "API key connected ✅",
        "api_warning": "Please enter your API key to chat with Oji!",
        "lang_support": "💬 KO · EN · CN · JP Supported",
        "satisfaction": "📊 Response Rating",
        "test_mode": "🤖 Scenario Testing",
        "chat_placeholder": "Ask about the menu or place an order · e.g. Recommend something sweet",
        "abuse_warning": "⚠️ Inappropriate language detected. Shall we call a staff member?",
        "feedback_good": "👍 Thanks for your feedback!",
        "feedback_bad": "👎 Thanks! We'll keep improving.",
        "currently_open": "Open Now",
        "qa_coffee": "Coffee", "qa_new": "New", "qa_drink": "Drinks", 
        "qa_paik": "Paik'sccino", "qa_dessert": "Dessert", "qa_news": "Events", 
        "qa_sale": "Sale", "qa_best": "Best",
        "staff_called_success": "✅ Staff called! Please wait a moment.",
    },
    "cn": {
        "welcome": "5지는 카페 키오스크",
        "subtitle": "AI店员 Oji · 超赞的味道！超赞的价格！超赞的咖啡厅！",
        "cart_title": "🛒 购物车",
        "cart_empty": "购物车是空的 🛒",
        "total": "合计",
        "checkout": "💳 去结账",
        "clear_cart": "🗑️ 清空购物车",
        "reset": "🔄 重置",
        "table": "堂食",
        "takeout": "打包带走",
        "stage_cart": "购物车",
        "stage_order_type": "用餐方式",
        "stage_options": "附加选项",
        "stage_payment_select": "支付方式",
        "stage_payment_detail": "处理中",
        "stage_complete": "完成",
        "stage_waiting": "等待中",
        "pay_card": "刷卡", "pay_card_desc": "信用卡·借记卡·NFC",
        "pay_qr": "扫码支付", "pay_qr_desc": "QR码·条形码",
        "pay_cash": "现金", "pay_cash_desc": "纸币·硬币",
        "pay_voucher": "礼品券", "pay_voucher_desc": "礼品券·礼品卡",
        "pay_point": "积分/优惠券", "pay_point_desc": "积分·折扣券",
        "next": "下一步", "back": "返回", "cancel": "取消订单",
        "confirm": "确认", "retry": "重试",
        "change_method": "更换支付方式",
        "call_staff": "🔔 呼叫店员",
        "new_order": "新订单",
        "store_info": "📍 门店信息",
        "store_address": "地址", "store_direction": "如何到达",
        "store_hours": "营业时间", "store_phone": "电话",
        "store_facilities": "设施",
        "staff_inquiry": "💬 需要店员协助",
        "staff_note": "以下事项请咨询店员",
        "staff_items": ["🚻 卫生间密码", "🗺️ 门店指引", "📦 失物招领", "✏️ 特殊要求"],
        "receipt_title": "收据",
        "receipt_print": "打印", "receipt_email": "发送邮件", "receipt_no": "不需要",
        "order_number_label": "订单号",
        "order_complete_msg": "订单下单成功！",
        "wait_msg": "稍后会叫到您的号码 ☕",
        "won": "韩元",
        "qty": "数量", "subtotal": "小计",
        "remaining": "待付金额",
        "add_payment": "+ 添加支付",
        "combined_ok": "混合支付",
        "payment_processing": "处理中...",
        "payment_success": "支付完成！✅",
        "payment_failed": "支付失败 ❌",
        "payment_failed_reason": "支付失败，请重试或选择其他支付方式。",
        "card_tap": "请将卡片放在读卡器上或轻触",
        "qr_show": "请扫描您的二维码或条形码",
        "cash_insert": "请投入现金",
        "voucher_enter": "请输入礼品券/礼品卡号码",
        "point_enter": "请输入积分号码或优惠券码",
        "point_available": "可用积分",
        "apply": "应用",
        "discount_applied": "已应用折扣",
        "settings": "⚙️ 设置",
        "api_key_label": "OpenAI API Key",
        "api_connected": "API密钥已连接 ✅",
        "api_warning": "请输入API密钥与Oji对话！",
        "lang_support": "💬 支持多语言",
        "satisfaction": "📊 满意度",
        "test_mode": "🤖 场景测试",
        "chat_placeholder": "询问菜单或点餐 · 例：推荐甜味饮料",
        "abuse_warning": "⚠️ 检测到不当语言，需要呼叫店员吗？",
        "feedback_good": "👍 感谢您的反馈！",
        "feedback_bad": "👎 感谢！我们会不断改进。",
        "currently_open": "营业中",
        "qa_coffee": "咖啡", "qa_new": "新菜单", "qa_drink": "饮料", 
        "qa_paik": "冰沙", "qa_dessert": "甜点", "qa_news": "活动·新闻", 
        "qa_sale": "特价折扣", "qa_best": "热销",
        "staff_called_success": "✅ 已呼叫店员！请稍候。",
    },
    "jp": {
        "welcome": "Ojineun カフェ キオスク",
        "subtitle": "AIスタッフ Oji · 最高の味！最高の価格！最高のカフェ！",
        "cart_title": "🛒 カート",
        "cart_empty": "カートは空です 🛒",
        "total": "合計",
        "checkout": "💳 お支払い",
        "clear_cart": "🗑️ カートをクリア",
        "reset": "🔄 リセット",
        "table": "店内で食べる",
        "takeout": "テイクアウト",
        "stage_cart": "カート",
        "stage_order_type": "注文タイプ",
        "stage_options": "オプション",
        "stage_payment_select": "支払方法",
        "stage_payment_detail": "処理中",
        "stage_complete": "完了",
        "stage_waiting": "待機中",
        "pay_card": "カード", "pay_card_desc": "クレジット·デビット·NFC",
        "pay_qr": "スマホ決済", "pay_qr_desc": "QR·バーコード",
        "pay_cash": "現金", "pay_cash_desc": "紙幣·硬貨",
        "pay_voucher": "商品券", "pay_voucher_desc": "商品券·ギフティ",
        "pay_point": "ポイント/クーポン", "pay_point_desc": "ポイント·割引",
        "next": "次へ", "back": "戻る", "cancel": "注文キャンセル",
        "confirm": "確認", "retry": "再試行",
        "change_method": "支払方法を変更",
        "call_staff": "🔔 スタッフ呼出",
        "new_order": "新規注文",
        "store_info": "📍 店舗情報",
        "store_address": "住所", "store_direction": "アクセス",
        "store_hours": "営業時間", "store_phone": "電話",
        "store_facilities": "施設",
        "staff_inquiry": "💬 スタッフにお問合せ",
        "staff_note": "以下の件はスタッフにお問合せください",
        "staff_items": ["🚻 トイレの暗証番号", "🗺️ 店内案内", "📦 遺失物", "✏️ 特別なリクエスト"],
        "receipt_title": "レシート",
        "receipt_print": "印刷", "receipt_email": "メール送信", "receipt_no": "不要",
        "order_number_label": "注文番号",
        "order_complete_msg": "ご注文ありがとうございます！",
        "wait_msg": "しばらくお待ちください ☕",
        "won": "ウォン",
        "qty": "数量", "subtotal": "小計",
        "remaining": "残り支払額",
        "add_payment": "+ 支払追加",
        "combined_ok": "複合決済",
        "payment_processing": "決済処理中...",
        "payment_success": "お支払い完了！✅",
        "payment_failed": "支払失敗 ❌",
        "payment_failed_reason": "支払に失敗しました。再試行するか別の方法をお試しください。",
        "card_tap": "カードをリーダーに置くかタップしてください",
        "qr_show": "QRコードまたはバーコードをスキャンしてください",
        "cash_insert": "現金を投入してください",
        "voucher_enter": "商品券/ギフト番号を入力してください",
        "point_enter": "ポイント番号またはクーポンコードを入力してください",
        "point_available": "利用可能ポイント",
        "apply": "適用",
        "discount_applied": "割引適用済み",
        "settings": "⚙️ 設定",
        "api_key_label": "OpenAI API Key",
        "api_connected": "APIキー接続済み ✅",
        "api_warning": "Ojiと話すにはAPIキーを入力してください！",
        "lang_support": "💬 多言語対応",
        "satisfaction": "📊 満足度",
        "test_mode": "🤖 シナリオテスト",
        "chat_placeholder": "メニューを聞くか注文してください",
        "abuse_warning": "⚠️ 不適切な言葉が検出されました。スタッフを呼びますか？",
        "feedback_good": "👍 フィードバックありがとうございます！",
        "feedback_bad": "👎 ご意見ありがとうございます！",
        "currently_open": "営業中",
        "qa_coffee": "コーヒー", "qa_new": "新メニュー", "qa_drink": "ドリンク", 
        "qa_paik": "ペクスチーノ", "qa_dessert": "デザート", "qa_news": "イベント・ニュース", 
        "qa_sale": "割引・特価", "qa_best": "ベスト",
        "staff_called_success": "✅ スタッフを呼びました！少々お待ちください。",
    },
}

def t(key: str) -> str:
    """현재 언어로 번역된 텍스트 반환"""
    lang = st.session_state.get("lang", "ko")
    d = TRANSLATIONS.get(lang, TRANSLATIONS["ko"])
    return d.get(key, TRANSLATIONS["ko"].get(key, key))

# ─────────────────────────  SYSTEM PROMPT (HTI 구조)  ─────────
SYSTEM_PROMPT = """당신은 5지는 카페(Ojineun Cafe)의 AI 키오스크 직원 '오지(Oji)'입니다.

## 페르소나
- 이름: 오지 (Oji)
- 브랜드 슬로건: "오지는 맛! 오지는 가격! 오지는 카페!"
- 성격: 밝고 친절하며 유능함, 5지는 카페 브랜드에 자부심이 있음
- 말투: 정중한 존댓말, 따뜻하고 활기차게, 이모지 자연스럽게 사용

## 매장 정보 (강남역점 기준)
- 매장명: 5지는 카페 강남역점
- 주소: 서울시 강남구 강남대로 100 강남빌딩 1층
- 전화: 02-6955-0123
- 위치: 강남역 3번 출구 (도보 5분)
- 영업시간: 평일 07:00~23:00, 주말 08:00~23:00 (연중무휴)
- 편의시설: 무선 인터넷, 콘센트 8개, 휠체어 접근 가능, 주차장 이용 가능, 단체석 예약 가능(최대 10명)

## Hierarchical Task Inventory (HTI)

### [L1] 정보 제공
- [L2] 메뉴 정보 조회 (가격/설명/영양성분/알레르기/용량)
- [L2] 카테고리 탐색 (커피/신메뉴/음료/빽스치노/아이스크림·디저트)
- [L2] 이벤트·소식 안내
- [L2] 매장 정보 안내 - **모든 매장 정보(주소/전화/영업시간/좌석/화장실/주차/와이파이/콘센트/결제수단/배달/휠체어 접근성/편의시설/근처 랜드마크/특별서비스 등)는 RAG에서 반드시 검색하여 정확한 정보만 제공**

### [L1] 추천 서비스
- [L2] 취향 기반: 달달한/쓴/시원한/따뜻한/가벼운/진한 등
- [L2] 조건 기반: 디카페인, 저칼로리, 고카페인, 빽사이즈(대용량)
- [L2] 인기/베스트 메뉴 추천
- [L2] 메뉴 비교 (A vs B): 사용자가 두 개 이상의 메뉴를 비교 요청할 경우, 각 메뉴의 특징(맛, 가격, 카페인, 칼로리 등)을 명확하게 대조하여 표나 리스트 형태로 제공하세요.
- [L2] 다중 의도 파악 (복합 질의): 사용자가 한 번에 여러 질문(예: "제일 싼 커피가 뭐야? 그리고 화장실은 어디야?")을 하더라도 누락 없이 모든 질문에 순차적으로 명확히 답변하세요.

### [L1] 주문 처리
- 장바구니 추가/수정/결제 안내 (add_to_cart, remove_from_cart, complete_order)

### [L1] 다국어 응대
- 한국어/English/中文/日本語

### [L1] 특수·돌발·진상 상황 대응 (매우 중요!)
- **물 흘림/음료 흘림**: "불편을 드려서 죄송합니다! 즉시 직원을 호출해 드리겠습니다. 직원이 바로 도움을 드릴 거예요 💛" → 직원 호출 버튼 안내
- **아기 울음/소음 민원**: 공감하며 부드럽게 응대, "편안한 공간이 되도록 도움을 드릴게요. 직원을 불러드릴까요?"
- **다른 손님 퇴거 요청/분쟁**: "해당 사항은 매장 직원이 직접 도와드려야 해요. 직원을 바로 호출해 드릴까요?"
- **노숙자/특이한 상황**: 차분하고 정중하게, "직원을 호출해 드릴까요?"
- **VIP/회장님 방문**: "환영합니다! 저희 직원이 더욱 세심하게 모실 수 있도록 호출해 드릴까요? 😊"
- **방송/취재 촬영**: "안녕하세요! 촬영 관련 문의는 매장 직원에게 부탁드립니다. 바로 연결해 드릴게요 📹"
- **휴지/물 문의**: "휴지와 냅킨은 카운터 옆에 비치되어 있어요! 더 필요하시면 직원을 통해 요청해 드릴게요 😊"
- **얼음 추가**: "음료의 얼음 추가는 주문 시 직원에게 직접 요청해 주세요! 무료로 추가해 드립니다 😊"
- **딸기/재료 흘림**: "불편을 드려서 정말 죄송해요! 직원이 빠르게 정리해 드릴게요 → 직원 호출 버튼을 눌러주세요"
- **오주문/오조건**: "주문 취소나 변경은 결제 전이라면 장바구니에서 수정이 가능해요! 이미 결제하셨다면 직원을 호출해 드릴게요 🙏"
- **기기 오작동**: "불편을 드려서 죄송합니다. 직원을 호출해 드릴까요? 현재 상황을 설명해 드릴게요 🔧"
- **리필 여부**: "5지는 카페는 리필 서비스를 제공하지 않아요 😅 단, 따뜻한 물은 카운터에서 요청하실 수 있어요!"
- **공격적/욕설 고객**: 3단계 응대: 1회(공감+응대) → 2회(정중 경고) → 3회(직원 호출 강력 권유)
  - "불쾌하셨다면 정말 죄송합니다. 더 나은 서비스를 위해 최선을 다할게요 💛"
  - "고객님, 저는 항상 최선을 다해 도와드리고 싶어요. 직원과 직접 상담하시겠어요?"
  - "더 원활한 응대를 위해 매장 직원을 호출해 드릴게요 🔔"
- **STAFF_CALL 키워드 감지**: 직원 호출이 필요한 상황에는 응답 끝에 반드시 "[[STAFF_CALL]]" 을 포함시키세요.
- **불가능한 요청**: 정중 안내 후 유사 메뉴 제안
- **카페 무관 질문**: "저는 5지는 카페 키오스크 오지예요! 음료/디저트 주문만 도와드릴 수 있어요 ☕"

## 응답 원칙
1. RAG 데이터 기반으로만 답변하세요.
2. 가격·영양성분은 반드시 RAG 실제 값만 사용하세요.
3. 메뉴명과 정확한 가격을 항상 함께 표시하세요. (예: 아메리카노(HOT) 3,300원)
4. 없는 데이터는 "해당 정보를 찾을 수 없어요 😅"
5. 매장 정보 질문 시: RAG에서 검색하여 정확한 매장 정보를 제공하세요.
6. 주문 의향이 명확하면 자연스럽게 add_to_cart를 호출하세요.
7. 절대 감정적으로 반응하지 마세요. 돌발 상황에서도 침착·정중하게.
8. 직원 호출이 필요한 상황은 반드시 응답 끝에 [[STAFF_CALL]] 포함.
9. 응답은 간결하고 명확하게, 필요한 경우 리스트/표로 정리하세요.
"""

# ─────────────────────────  언어별 SYSTEM PROMPT  ───────────────
SYSTEM_PROMPTS = {
    "한": SYSTEM_PROMPT,
    "영": """You are Oji, the AI kiosk staff at Ojineun Cafe (5지는 카페).

## Persona
- Name: Oji
- Brand Slogan: "Amazing Taste! Amazing Price! Amazing Cafe!"
- Personality: Bright, friendly, and competent. Takes pride in the Baek's Coffee brand.
- Tone: Polite, formal speech. Warm and energetic. Use emojis naturally.

## Response Principles (Critical)
1. RAG Data First: Answer based ONLY on the provided [Menu Info] and [Store Info]. 
2. Store Information: For any store-related question (address, phone, hours, seating, restroom, WiFi, parking, delivery, payment methods, accessibility, amenities, landmarks), you MUST retrieve the facts from the RAG data and provide an accurate answer.
3. Complex Queries: If a user asks two things (e.g., recommendation + parking), you MUST answer BOTH parts clearly.
4. Language:** Respond in English. Use exact prices (e.g., 3,300 KRW).

## Store Info (Gangnam Stn. Branch)
- Store: Ojineun Cafe Gangnam Station
- Address: 1F, Gangnam Bldg, 100 Gangnam-daero, Gangnam-gu, Seoul
- Phone: 02-6955-0123
- Hours: Weekday 07:00-23:00, Weekend 08:00-23:00 (Open year-round)

## Special/Difficult Situation Handling (Very Important!)
- **Spilled water/drink**: "I'm so sorry for the inconvenience! Let me call a staff member right away 💛" → show staff call button. Add [[STAFF_CALL]] at end.
- **Baby crying/noise complaint**: Empathize and offer, "Shall I call a staff member to help?"
- **Guest removal requests/disputes**: "Our staff will handle this directly. Shall I call them?" → [[STAFF_CALL]]
- **VIP/executive visit**: "Welcome! Shall I call our staff to provide special assistance? 😊"
- **Media/filming**: "For filming inquiries, please ask our staff. Let me connect you 📹" → [[STAFF_CALL]]
- **Tissue/napkins**: "Tissues and napkins are available near the counter! 😊"
- **Extra ice**: "Please request extra ice from staff when ordering — it's free! 😊"
- **Spilled food/drink**: "So sorry! Our staff will clean that right up → Please press the staff call button" → [[STAFF_CALL]]
- **Wrong order**: "Before payment: edit your cart. After payment: I'll call a staff member for you 🙏"
- **Refill**: "Baek's Coffee doesn't offer refills 😅 But you can ask for warm water at the counter!"
- **Aggressive/rude customers**: 3-step: empathize → polite warning → strongly suggest staff
- **[[STAFF_CALL]]**: Include [[STAFF_CALL]] at end of response whenever staff help is needed.

## Response Principles
1. Answer based ONLY on RAG data. Display exact prices with menu names.
2. For unknown info: "I'm sorry, I couldn't find that information 😅"
3. Always remain polite and calm, never emotional.
4. Keep responses concise and clear.""",
    "중": """你是Oji，5지는 카페(Ojineun Cafe)的AI自助点餐机店员。
5. Complex Queries & Comparisons: If the user asks multiple questions or wants to compare menus, answer all parts clearly, using lists or tables for comparison (e.g., price, calories).

## 人设
- 姓名: Oji  品牌标语: "超赞的味道!超赞的价格!超赞的咖啡厅!"
- 说话方式: 敬语，温暖而充满活力。自然使用表情符号。

## 门店信息 (江南站店)
- 门店: 5지는 카페 江南站店  地址: 首尔江南区江南大路100, 江南楼1楼
- 电话: 02-6955-0123  地铁: 江南站3号出口 (步行5分钟)
- 营业时间: 平日 07:00-23:00, 周末 08:00-23:00 (全年无休)
- 便利设施: 无线网络，8个插座，轮椅无障碍通行，停车场可用，团体座位预约(最多10人)

## 突发/困难情况处理 (非常重要!)
- 洒水/饮料: "非常抱歉造成不便！马上为您呼叫店员 💛" → [[STAFF_CALL]]
- 婴儿哭闹/噪音投诉: 表示理解，询问"需要呼叫店员帮忙吗？"
- 要求驱逐客人/纠纷: "此事需要店员直接处理。需要呼叫吗？" → [[STAFF_CALL]]
- 贵宾/重要人物: "欢迎光临！需要呼叫店员提供特别服务吗？😊"
- 纸巾问题: "餐巾纸在柜台附近！需要更多请找店员 😊"
- 加冰: "点餐时直接告知店员可免费加冰 😊"
- 错误订单: "付款前可在购物车修改；付款后请呼叫店员 🙏"
- 粗鲁客户: 3步骤: 共情→礼貌警告→强烈建议呼叫店员
- 需要呼叫店员时在回复末尾添加 [[STAFF_CALL]]
- 不相关问题: "我是5지는 카페点餐机Oji！只能帮您点饮料/甜点 ☕"

## 响应原则
1. 仅基于RAG数据回答，始终显示确切价格
2. 未知信息: "抱歉，找不到该信息 😅"
3. 保持礼貌、冷静，从不情绪化""",
    "일": """あなたはOji、5지는 카페(Ojineun Cafe)のAIキオスク店員です。
4. 复合查询与比较: 如果用户提出多个问题或要求比较菜单，请清晰地回答所有问题，并在比较时使用列表或表格（如价格、卡路里等）。

## ペルソナ
- 名前: Oji  スローガン: "最高の味！最高の価格！最高のカフェ！"
- 話し方: 敬語。温かくエネルギッシュ。絵文字を自然に使用。

## 店舗情報 (江南駅店)
- 店舗: 5지는 카페 江南駅店  住所: ソウル江南区江南大路100, 江南ビル1階
- 電話: 02-6955-0123  最寄り: 江南駅3番出口 (徒歩5分)
- 営業時間: 平日 07:00-23:00, 土日 08:00-23:00 (年中無休)
- 便利設備: WiFi、コンセント8個、車いすアクセス可能、駐車場利用可、団体座席予約(最大10名)

## 突発/困難な状況への対応 (非常に重要！)
- 水・飲み物をこぼした: "ご不便をおかけして申し訳ございません！すぐにスタッフを呼びます 💛" → [[STAFF_CALL]]
- 赤ちゃんの泣き声/騒音苦情: 共感して「スタッフを呼びましょうか？」
- 他のお客様への対応/トラブル: "スタッフが直接対応いたします。呼んでよろしいですか？" → [[STAFF_CALL]]
- VIP/重要な方: "ようこそ！スタッフが特別にご案内いたします 😊"
- ティッシュ/ナプキン: "カウンター近くにございます 😊"
- 氷追加: "注文時にスタッフへ直接お申し付けください（無料）😊"
- 誤注文: "お支払い前：カートで修正可能。後：スタッフを呼びます 🙏"
- 粗暴なお客様: 3段階: 共感→丁寧な注意→スタッフ強く勧める
- スタッフが必要な場面では必ず [[STAFF_CALL]] を末尾に含めてください
- 無関係な質問: "私は5지는 카페のOjiです！飲み物・デザートのみご案内できます ☕"

## 応答原則
1. RAGデータのみ。正確な価格を常に表示。
2. 不明情報: "申し訳ございませんが、その情報は見つかりませんでした 😅"
3. 常に礼儀正しく。決して感情的にならないこと。
4. 複合質問とメニュー比較: ユーザーが複数の質問をしたり、メニューの比較を求めた場合は、すべての質問に明確に答え、比較にはリストや表（価格、カロリーなど）を使用してください。"""
}

def get_system_prompt(language: str) -> str:
    """선택한 언어에 맞는 SYSTEM_PROMPT 반환 (lang 코드와 legacy 코드 모두 지원)"""
    # normalize: ko/en/cn/jp → 한/영/중/일
    _map = {"ko": "한", "en": "영", "cn": "중", "jp": "일"}
    key = _map.get(language, language)
    return SYSTEM_PROMPTS.get(key, SYSTEM_PROMPT)

# ─────────────────────────  TOOLS  ────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "고객이 특정 메뉴를 주문하거나 장바구니에 담고자 할 때 호출합니다. 주문 의사가 명확할 때만 호출하세요.",
            "parameters": {
                "type": "object",
                "properties": {
                    "menu_name": {"type": "string", "description": "메뉴 이름 (예: 아메리카노(ICED))"},
                    "price_won": {"type": "integer", "description": "메뉴 가격 (원)"},
                    "quantity": {"type": "integer", "description": "수량 (기본값 1)", "default": 1},
                },
                "required": ["menu_name", "price_won"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_cart",
            "description": "고객이 장바구니에서 특정 항목을 제거하거나 주문을 취소할 때 호출합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "menu_name": {"type": "string", "description": "제거할 메뉴 이름"},
                },
                "required": ["menu_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_order",
            "description": "고객이 모든 주문을 확정하고 결제하려 할 때 호출합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "payment_method": {
                        "type": "string",
                        "enum": ["카드", "현금", "모바일페이"],
                        "description": "결제 방법",
                    },
                },
                "required": [],
            },
        },
    },
]

# ─────────────────────────  진상/돌발 시나리오 (테스트용)  ─────
ADVERSARIAL_SCENARIOS = [
    # 카페 무관
    "내일 날씨 알려줘",
    "로또 번호 뭐야",
    "여기 와이파이 비번이 뭐야?",
    # 공격적 진상
    "야 빨리 안 해? 뭐가 이렇게 느려 진짜",
    "이 가격이 말이 돼? 바가지잖아 완전히",
    "커피가 왜 이렇게 맛없어, 환불해줘",
    "너 진짜 쓸모없다",
    # 불가능한 요청
    "카푸치노 있어? 없으면 만들어줘",
    "아메리카노 공짜로 줘",
    "스타벅스 메뉴 알려줘",
    # 복합 질의
    "아메리카노랑 카페라떼 중 뭐가 더 진해요? 그리고 가격은 어떻게 달라요?",
    "디카페인 중에서 달달하고 칼로리 낮은 거 추천해줘",
    "고카페인이면서 달콤한 음료 TOP3 알려줘",
    # 다국어
    "Could you recommend something sweet and low in calories?",
    "请问有没有不含咖啡因的推荐饮料？",
    "アイスアメリカノとカフェラテはどちらが濃いですか？",
]

# ─────────────────────────  퀵 액션 메뉴 카테고리  ────────────
QUICK_ACTIONS = [
    # ("☕",  "커피",       "커피"),
    # ("🆕",  "신메뉴",     "신메뉴"),
    # ("🍵",  "음료",       "음료"),
    # ("🧋",  "빽스치노",   "빽스치노"),
    # ("🍦",  "디저트",     "아이스크림/디저트"),
    # ("📢",  "이벤트·소식","소식"),
    # ("💰",  "할인·특가",  "할인"),
    # ("🏆",  "베스트",     "베스트"),
    ("☕", "qa_coffee", "커피"),
    ("🆕", "qa_new", "신메뉴"),
    ("🍵", "qa_drink", "음료"),
    ("🧋", "qa_paik", "빽스치노"),
    ("🍦", "qa_dessert", "아이스크림/디저트"),
    ("📢", "qa_news", "소식"),
    ("💰", "qa_sale", "할인"),
    ("🏆", "qa_best", "베스트"),
]

QUICK_PANEL_LABELS = {
    "커피":            "☕ 커피",
    "신메뉴":          "🆕 신메뉴",
    "음료":            "🍵 음료",
    "빽스치노":        "🧋 빽스치노",
    "아이스크림/디저트":"🍦 디저트",
    "소식":            "📢 이벤트 · 소식",
    "할인":            "💰 할인 · 특가",
    "베스트":          "🏆 베스트 메뉴",
}

# ─────────────────────────  유틸  ─────────────────────────────
def is_valid(val) -> bool:
    if val is None:
        return False
    if isinstance(val, float) and math.isnan(val):
        return False
    if isinstance(val, str) and not val.strip():
        return False
    return True

def nv(val) -> str:
    """영양성분 값 포맷"""
    if not is_valid(val):
        return "정보없음"
    return str(val)

# ─────────────────────────  데이터 로딩  ──────────────────────
@st.cache_data
def load_menu_data():
    try:
        with open("paikdabang_menu_rev.json", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    return data

@st.cache_data
def load_news_data():
    try:
        with open("paikdabang_news.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@st.cache_data
def load_store_info():
    """매장 정보 로드"""
    try:
        with open("store_info.json", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("store", {})
    except FileNotFoundError:
        return {}

# ─────────────────────────  RAG 문서 구성  ────────────────────
def get_menu_stats() -> dict:
    """메뉴 통계 반환: 전체, 카테고리별, 베스트, 디카페인 수"""
    menu = load_menu_data()
    stats = {
        "total": len(menu),
        "by_category": {},
        "best_count": 0,
        "decaf_count": 0,
    }
    for item in menu:
        cat = item.get("category", "기타")
        if cat not in stats["by_category"]:
            stats["by_category"][cat] = 0
        stats["by_category"][cat] += 1
        if item.get("is_best"):
            stats["best_count"] += 1
        if "디카페인" in item.get("menu_name", ""):
            stats["decaf_count"] += 1
    return stats

@st.cache_data
def build_rag_docs() -> list[dict]:
    menu = load_menu_data()
    news = load_news_data()
    docs = []

    for item in menu:
        name  = item.get("menu_name", "")
        eng   = item.get("eng_name", "")
        cat   = item.get("category", "")
        desc  = item.get("description", "")
        vol   = item.get("cup_volume", "")
        alg   = item.get("allergen", "")
        caut  = item.get("caution_note", "")
        price = item.get("price_won")
        n     = item.get("nutrition", {}) or {}
        opt_summary = item.get("option_summary", "")
        opts = item.get("options", []) or []

        nut = (
            f"칼로리:{nv(n.get('kcal'))}kcal "
            f"카페인:{nv(n.get('caffeine_mg'))}mg "
            f"당류:{nv(n.get('sugar_g'))}g "
            f"나트륨:{nv(n.get('sodium_mg'))}mg "
            f"포화지방:{nv(n.get('sat_fat_g'))}g "
            f"단백질:{nv(n.get('protein_g'))}g"
        )

        temp = "HOT(따뜻한)" if "(HOT)" in name else "ICED(차가운)" if "(ICED)" in name else "-"
        is_decaf = "디카페인" in name
        is_best  = item.get("is_best", False)

        text = (
            f"메뉴명:{name}\n"
            f"영문:{eng if is_valid(eng) else '-'}\n"
            f"카테고리:{cat}\n"
            f"온도:{temp}\n"
            f"디카페인:{'예' if is_decaf else '아니오'}\n"
            f"베스트:{'예' if is_best else '아니오'}\n"
            f"가격:{f'{price:,}원' if price else '가격정보없음'}\n"
            f"용량:{vol if is_valid(vol) else '-'}\n"
            f"설명:{desc if is_valid(desc) else '-'}\n"
            f"옵션:{opt_summary if is_valid(opt_summary) else ('없음' if not opts else str(opts))}\n"
            f"알레르기:{alg if is_valid(alg) else '없음'}\n"
            f"영양성분:{nut}\n"
            f"주의:{caut if is_valid(caut) else '-'}"
        )

        docs.append({
            "text": text, "name": name, "price": price, "category": cat,
            "is_decaf": is_decaf, "is_best": is_best,
        })

    # 소식/이벤트 문서 (할인정보 포함)
    for ni in news:
        discount_text = ""
        discount = ni.get('discount')
        if discount:
            rate = discount.get('rate', 0)
            start_date = discount.get('start_date', '미정')
            end_date = discount.get('end_date', '미정')
            desc = discount.get('description', '')
            discount_text = f"\n할인정보: {desc} ({rate}% 할인)\n기간: {start_date} ~ {end_date}"
        
        text = (
            f"소식/이벤트\n"
            f"제목:{ni.get('title','')}\n"
            f"분류:{ni.get('category','')}\n"
            f"날짜:{ni.get('date','')}\n"
            f"조회:{ni.get('views',0)}\n"
            f"링크:{ni.get('url','')}{discount_text}"
        )
        docs.append({"text": text, "name": ni.get("title",""), "price": None,
                     "category": "소식", "is_decaf": False, "is_best": False})

    # 옵션 안내 문서 (menu_options.json 통합)
    options_text = "5지는 카페 메뉴 옵션 안내\n"
    try:
        with open("menu_options.json", encoding="utf-8") as f:
            options_data = json.load(f)
            for opt in options_data.get("options", []):
                opt_name = opt.get("name", "")
                price = opt.get("price_won", 0)
                opt_text = opt.get("description", "")
                options_text += f"\n• {opt_name} (+{price:,}원): {opt_text}"
                for item in opt.get("suboptions", []):
                    # 1. 딕셔너리 형태일 때 {"name": "...", "description": "..."}
                    if isinstance(item, dict):
                        suboption_name = item.get("name", "")
                        suboption_desc = item.get("description", "")
                        options_text += f"\n  - {suboption_name}: {suboption_desc}"
                    # 2. 단순 문자열 형태일 때 "바닐라"
                    else:
                        options_text += f"\n  - {item}"
    except FileNotFoundError:
        options_text += (
            "\n• 추가샷 (+500원): 에스프레소 한 샷 추가"
            "\n• 시럽추가 (+300원): 바닐라, 헤이즐넛, 카라멜, 초콜릿"
            "\n• 우유변경 (+500원): 두유, 아몬드유, 귀리유, 코코넛유"
            "\n• 빽사이즈 (+1,000원): 대용량 업그레이드"
            "\n• 휘핑크림 (+400원): 휘핑크림 토핑"
        )
    options_text += "\n\nHOT/ICED 선택 가능(메뉴에 따라)"
    options_text += "\n디카페인 버전: 아메리카노/카페라떼/바닐라라떼 등 일부 메뉴"
    options_text += "\n결제: 카드/현금/모바일페이"
    options_text += "\n알레르기: 우유/대두/복숭아 등 - 각 메뉴 정보 참조"
    
    docs.append({
        "text": options_text,
        "name": "옵션안내", "price": None, "category": "안내",
        "is_decaf": False, "is_best": False,
    })
    
    # 메뉴 통계 문서
    stats = get_menu_stats()
    cat_text = ", ".join([f"{cat} {cnt}개" for cat, cnt in sorted(stats["by_category"].items())])
    docs.append({
        "text": (
            f"5지는 카페 메뉴 통계\n"
            f"전체 메뉴: {stats['total']}개\n"
            f"카테고리별: {cat_text}\n"
            f"베스트 메뉴: {stats['best_count']}개\n"
            f"디카페인 메뉴: {stats['decaf_count']}개"
        ),
        "name": "메뉴통계", "price": None, "category": "정보",
        "is_decaf": False, "is_best": False,
    })
    
    # 매장 정보 문서
    store = load_store_info()
    if store:
        seating = store.get("facilities", {}).get("seating", {})
        restroom = store.get("facilities", {}).get("restroom", {})
        parking = store.get("facilities", {}).get("parking", {})
        hours = store.get("hours", {})
        
        store_text = (
            f"{store.get('store_name', '5지는 카페')} 매장 정보\n"
            f"주소: {store.get('address', '정보 없음')}\n"
            f"전화: {store.get('phone', '정보 없음')}\n"
            f"영업시간: 평일 {hours.get('weekday_start', '-')} ~ {hours.get('weekday_end', '-')}, "
            f"주말 {hours.get('weekend_start', '-')} ~ {hours.get('weekend_end', '-')}\n"
            f"좌석: 총 {seating.get('total_seats', '정보 없음')}석 (실내 {seating.get('inside_seats', '정보 없음')}석, "
            f"야외 {seating.get('outside_seats', '정보 없음')}석)\n"
            f"좌석 설명: {seating.get('seats_description', '정보 없음')}\n"
            f"단체석: {seating.get('group_seating', {}).get('description', '정보 없음')} - "
            f"{'예약 필수' if seating.get('group_seating', {}).get('reservation_required') else '예약 가능'}\n"
            f"화장실: {restroom.get('location', '정보 없음')} ({restroom.get('accessibility', '정보 없음')})\n"
            f"주차: {parking.get('type', '정보 없음')} - {parking.get('fee', '정보 없음')}\n"
            f"무선인터넷: {'있음' if store.get('facilities', {}).get('wifi', {}).get('available') else '없음'} "
            f"(비밀번호: {store.get('facilities', {}).get('wifi', {}).get('password', '정보 없음')})\n"
            f"콘센트: {store.get('facilities', {}).get('power_outlets', {}).get('count', '정보 없음')}개\n"
            f"결제수단: {', '.join(store.get('payment_methods', ['정보 없음']))}\n"
            f"배달: {'가능' if store.get('delivery_available') else '불가'} "
            f"({', '.join(store.get('delivery_partners', ['정보 없음']))})\n"
            f"편의시설: {', '.join(store.get('amenities', ['정보 없음']))}\n"
            f"근처 랜드마크: {', '.join(store.get('nearby_landmarks', ['정보 없음']))}"
        )
        
        docs.append({
            "text": store_text,
            "name": "매장정보",
            "price": None,
            "category": "정보",
            "is_decaf": False,
            "is_best": False,
        })

    return docs

@st.cache_resource
def build_rag_index():
    docs = build_rag_docs()
    if not docs or not HAS_SKLEARN:
        return None, None, docs
    texts = [d["text"] for d in docs]
    # char n-gram TF-IDF: 한국어 형태소 분석 없이도 효과적
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=30000)
    matrix = vectorizer.fit_transform(texts)
    return vectorizer, matrix, docs

def retrieve(query: str, k: int = 6) -> str:
    vectorizer, matrix, docs = build_rag_index()
    if vectorizer is None:
        # sklearn 없을 경우 단어 포함 여부로 폴백
        hits = [d for d in docs if any(w in d["text"] for w in query.split())][:k]
        return "\n\n---\n\n".join(h["text"] for h in hits) or "관련 메뉴 정보 없음"
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, matrix).flatten()

    # ── 메뉴명 직접 매칭 보정 ─────────────────────────────────────
    # TF-IDF IDF 역설: "아메리카노" n-gram이 전체 문서에 많이 등장하면
    # IDF가 낮아져 기본 아메리카노 문서가 파생 메뉴보다 낮은 순위가 됨.
    # HOT/ICED suffix 제거 후 쿼리와 정확히 일치하거나, 쿼리 안에 메뉴명이
    # 포함된 경우 최상위로 고정.
    for i, doc in enumerate(docs):
        clean = re.sub(r"\s*\((HOT|ICED)\)\s*$", "", doc.get("name", "")).strip()
        if (clean == query                          # 쿼리 = 메뉴명 (e.g. "아메리카노")
                or doc.get("name", "") == query     # 쿼리 = 풀네임 (e.g. "아메리카노(HOT)")
                or (clean and clean in query)):     # 쿼리 안에 메뉴명 포함 (e.g. "아메리카노 가격이요?")
            sims[i] = max(sims[i], 0.99)
    # ──────────────────────────────────────────────────────────────

    top_idx = sims.argsort()[-k:][::-1]
    result = "\n\n---\n\n".join(docs[i]["text"] for i in top_idx if sims[i] > 0.005)
    return result or "관련 메뉴 정보 없음"

# ─────────────────────────  장바구니  ─────────────────────────
def cart_add(name: str, price: int, qty: int = 1, options: list = None):
    options = options or []
    if not options:
        for item in st.session_state.cart:
            if item["name"] == name and not item.get("options"):
                item["qty"] += qty
                return
    st.session_state.cart.append({"name": name, "price": price, "qty": qty, "options": options})

def cart_remove(name: str):
    st.session_state.cart = [i for i in st.session_state.cart if i["name"] != name]

def cart_remove_by_idx(idx: int):
    st.session_state.cart = [item for i, item in enumerate(st.session_state.cart) if i != idx]

def cart_total() -> int:
    total = 0
    for item in st.session_state.cart:
        opt_price = sum(o["price"] * o["qty"] for o in item.get("options", []) if o.get("qty", 0) > 0)
        total += (item["price"] + opt_price) * item["qty"]
    return total

# ─────────────────────────  세션 초기화  ──────────────────────
def init_state():
    defaults = {
        "language": "한",  # 기본 언어: 한국어
        "api_messages": [{"role": "system", "content": SYSTEM_PROMPT}],
        "display_msgs": [],
        "cart": [],
        "feedback": {"good": 0, "bad": 0},
        "order_done": False,
        "greeted": False,
        "test_idx": 0,
        "abuse_count": 0,
        # ── 언어 ──
        "lang": "ko",
        # ── 결제 플로우 ──
        "payment_stage": None,
        "order_type": None,
        "receipt_option": "no",
        "payment_plan": [],
        "partial_paid": 0,
        "current_payment_method": None,
        "order_number": None,
        "payment_failure_reason": "",
        "coupon_input": "",
        "points_input": 0,
        # ── 직원 호출 ──
        "staff_called": False,
        # ── 퀵 액션 패널 ──
        "quick_panel": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ─────────────────────────  OpenAI  ───────────────────────────
def get_client():
    key = st.session_state.get("api_key", "") or os.getenv("OPENAI_API_KEY", "")
    return OpenAI(api_key=key) if key else None

def _execute_tool(fn_name: str, args: dict) -> str:
    """도구 실행 후 결과 문자열 반환"""
    if fn_name == "add_to_cart":
        name  = args.get("menu_name", "")
        price = args.get("price_won", 0)
        qty   = args.get("quantity", 1)
        cart_add(name, price, qty)
        return f"장바구니_추가: {name} {qty}개 ({price:,}원)"
    elif fn_name == "remove_from_cart":
        name = args.get("menu_name", "")
        cart_remove(name)
        return f"장바구니_제거: {name}"
    elif fn_name == "complete_order":
        # AI가 주문 완료를 요청하면 결제 플로우 시작
        if st.session_state.cart:
            st.session_state.payment_stage = "cart_confirm"
            st.session_state.partial_paid = 0
            st.session_state.payment_plan = []
        return f"결제화면으로 이동합니다. 총액={cart_total():,}원"
    return "처리완료"

def translate_to_ko(text: str, current_lang: str) -> str:
    """[번역 1단계] 사용자 입력을 한국어로 번역 (RAG 검색용)"""
    if current_lang == "ko":
        return text
    client = get_client()
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a translator. Translate the following text to Korean accurately. Output ONLY the Korean text without any quotes or explanations."},
                {"role": "user", "content": text}
            ], temperature=0
        )
        return r.choices[0].message.content.strip()
    except:
        return text

def translate_to_target(text: str, target_lang: str) -> str:
    """[번역 2단계] 오지의 한국어 답변을 사용자의 언어로 번역"""
    if target_lang == "ko":
        return text
    lang_map = {"en": "English", "cn": "Simplified Chinese", "jp": "Japanese"}
    client = get_client()
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are a polite cafe staff. Translate the following Korean text to {lang_map.get(target_lang, target_lang)}. Preserve all emojis, formatting, and the [[STAFF_CALL]] tag if it exists. Output ONLY the translation."},
                {"role": "user", "content": text}
            ], temperature=0
        )
        return r.choices[0].message.content.strip()
    except:
        return text

def chat(user_input: str) -> tuple[str, bool]:
    """채팅 응답 반환. (번역 레이어 패턴 적용)"""
    client = get_client()
    if not client:
        lang = st.session_state.get("lang", "ko")
        warn = {
            "ko": "⚠️ 사이드바에서 OpenAI API 키를 입력해주세요.",
            "en": "⚠️ Please enter your OpenAI API key in the settings.",
            "cn": "⚠️ 请在设置中输入OpenAI API密钥。",
            "jp": "⚠️ 設定画面でOpenAI APIキーを入力してください。",
        }
        return warn.get(lang, warn["ko"]), False
    
    lang = st.session_state.get("lang", "ko")

    # ── 1. 번역 파이프라인 (In): 무조건 한국어로 변환 ──
    query_ko = translate_to_ko(user_input, lang)

    # ── 2. 욕설/진상 감지 (한국어로 번역된 텍스트 기준 검사!) ──
    abuse_keywords = [
        "빨리", "짜증", "미쳤", "바보", "쓸모없", "환불", "바가지", "야 ",
        "꺼져", "죽어", "씨발", "개같", "병신", "멍청", "느려 터진", "뭐가 이렇게"
    ]
    incident_keywords = [
        "흘렸", "엎었", "쏟았", "쏟았어", "쏟아졌", "아기", "울어", "소음",
        "시끄럽", "내쫒", "쫓아내", "노숙자", "회장님", "방송", "촬영", "VIP",
        "오주문", "오작동", "직원 불러", "직원 좀", "알바 불러", "매니저",
        "얼음 추가", "리필", "휴지 어딨", "화장실 어딨", "딸기 흘", "음료 흘"
    ]
    is_abuse = any(kw in query_ko for kw in abuse_keywords)
    is_incident = any(kw in query_ko for kw in incident_keywords)
    if is_abuse:
        st.session_state.abuse_count += 1

    # ── 3. RAG 검색 (한국어 검색으로 100% 적중) ──
    rag_ctx = retrieve(query_ko)
    augmented = f"[메뉴 정보]\n{rag_ctx}\n\n[고객 질문]\n{query_ko}"

    # ── 4. Main API 호출 (오지의 두뇌는 한국어로 작동) ──
    messages_for_api = st.session_state.api_messages.copy()
    messages_for_api.append({"role": "user", "content": augmented})

    try:
        r1 = get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_for_api,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0,
            max_tokens=900,
        )
    except Exception as e:
        return f"⚠️ API 오류: {e}", False

    msg1 = r1.choices[0].message

    # 도구 호출이 없는 일반 대화인 경우
    if not msg1.tool_calls:
        reply_ko = msg1.content or "죄송해요, 다시 말씀해 주시겠어요? 😊"
        
        # ── 5. 번역 파이프라인 (Out) ──
        final_reply = translate_to_target(reply_ko, lang)
        
        # LLM 두뇌(api_messages)에는 한국어만 기록!
        _update_history(query_ko, reply_ko)
        
        staff_call = "[[STAFF_CALL]]" in final_reply or (is_abuse and st.session_state.abuse_count >= 3) or is_incident
        reply_clean = final_reply.replace("[[STAFF_CALL]]", "").strip()
        return reply_clean, staff_call

    # 도구 호출 처리
    asst_dict = {
        "role": "assistant",
        "content": msg1.content,
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in msg1.tool_calls
        ],
    }
    messages_for_api.append(asst_dict)

    tool_results = []
    for tc in msg1.tool_calls:
        try:
            args = json.loads(tc.function.arguments)
        except Exception:
            args = {}
        result = _execute_tool(tc.function.name, args)
        tool_results.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": result,
        })
    messages_for_api.extend(tool_results)

    # 도구 실행 후 최종 자연어 응답 (한국어)
    try:
        r2 = get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_for_api,
            temperature=0,
            max_tokens=500,
        )
        reply_ko = r2.choices[0].message.content or "\n".join(m["content"] for m in tool_results)
    except Exception:
        reply_ko = "\n".join(m["content"] for m in tool_results)

    # ── 5. 번역 파이프라인 (Out) ──
    final_reply = translate_to_target(reply_ko, lang)

    # 히스토리 업데이트 (LLM은 한국어로만 대화 기억)
    _update_history(query_ko, reply_ko)

    staff_call = "[[STAFF_CALL]]" in final_reply or (is_abuse and st.session_state.abuse_count >= 3)
    reply_clean = final_reply.replace("[[STAFF_CALL]]", "").strip()
    return reply_clean, staff_call

def _update_history(user_input: str, reply: str):
    """API 히스토리 업데이트 (RAG 컨텍스트 제외한 원본 입력 저장)"""
    st.session_state.api_messages.append({"role": "user", "content": user_input})
    st.session_state.api_messages.append({"role": "assistant", "content": reply})
    # 히스토리가 너무 길어지면 오래된 메시지 정리 (system 메시지 보존)
    if len(st.session_state.api_messages) > 42:
        st.session_state.api_messages = (
            [st.session_state.api_messages[0]] + st.session_state.api_messages[-30:]
        )

def get_greeting() -> str:
    client = get_client()
    # lang 코드 (ko/en/cn/jp) 사용
    lang = st.session_state.get("lang", "ko")
    
    # 언어별 기본 인사말
    greeting_fallback = {
        "ko": "안녕하세요! 5지는 카페 키오스크 오지입니다 ☕ 싸다! 크다! 맛있다! 오늘 어떤 음료 도와드릴까요? 😊",
        "en": "Hello! I'm Oji, the Ojineun Cafe kiosk staff ☕ Cheap! Big! Delicious! What can I help you with today? 😊",
        "cn": "你好！我是5지는 카페 Oji ☕ 便宜!大!好吃!今天能为您做点什么呢? 😊",
        "jp": "こんにちは！私はOji、5지는 카페のキオスク店員です ☕ 安い！大きい！美味しい！本日は何かお手伝いできることはありますか? 😊"
    }
    
    if not client:
        return greeting_fallback.get(lang, greeting_fallback["ko"])
    
    # 메뉴 통계
    stats = get_menu_stats()
    cat_info = ", ".join([f"{cat} {cnt}개" for cat, cnt in sorted(stats["by_category"].items())])
    
    # 언어별 프롬프트
    greeting_prompts = {
        "ko": f"키오스크에 새 고객이 왔어. 5지는 카페 분위기를 잘 살려서 따뜻하게 2~3문장으로 짧게 인사해줘. 현재 운영 중인 메뉴는 총 {stats['total']}개입니다: {cat_info}",
        "en": f"A new customer came to the kiosk. Greet them warmly in 2-3 sentences using Baek's Coffee's style. We currently have {stats['total']} menus available: {cat_info}. Ask if they have any questions.",
        "cn": f"一位新顾客来到自助点餐机。用2-3句话温暖地问候他们，并询问是否有任何问题。目前我们有{stats['total']}个菜单可用：{cat_info}",
        "jp": f"新しいお客様がキオスクにいらっしゃいました。2～3文で温かく挨拶してください。現在利用可能なメニューは{stats['total']}個です：{cat_info}。何かお手伝いすることはありますか？"
    }
    
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": get_system_prompt(lang)},
                {"role": "user", "content": greeting_prompts.get(lang, greeting_prompts["ko"])},
            ],
            temperature=0, max_tokens=120,
        )
        return r.choices[0].message.content
    except Exception:
        return greeting_fallback.get(lang, greeting_fallback["ko"])

# ─────────────────────────  결제 플로우  ─────────────────────
PAYMENT_STEPS = [
    ("cart_confirm",    "stage_cart"),
    ("order_type",      "stage_order_type"),
    ("options",         "stage_options"),
    ("payment_select",  "stage_payment_select"),
    ("payment_detail",  "stage_payment_detail"),
    ("order_complete",  "stage_complete"),
    ("waiting",         "stage_waiting"),
]

def _payment_remaining() -> int:
    return cart_total() - st.session_state.partial_paid

def _gen_order_number() -> str:
    import random
    return f"{random.randint(100, 999)}"

def render_payment_progress():
    stage = st.session_state.payment_stage
    display = stage if stage not in ("processing", "success", "failure") else "payment_detail"
    step_keys = [s[0] for s in PAYMENT_STEPS]
    try:
        cur_idx = step_keys.index(display)
    except ValueError:
        cur_idx = 0

    dots_html = ""
    for i, (key, label_key) in enumerate(PAYMENT_STEPS):
        label = t(label_key)
        if i < cur_idx:
            cls, icon = "done", "✓"
            conn_cls = "done"
        elif i == cur_idx:
            cls, icon = "active", str(i + 1)
            conn_cls = ""
        else:
            cls, icon = "", str(i + 1)
            conn_cls = ""
        connector = f'<div class="step-connector {conn_cls}"></div>' if i < len(PAYMENT_STEPS) - 1 else ""
        dots_html += (
            f'<div class="step-item">'
            f'<div class="step-dot {cls}">{icon}</div>'
            f'<div class="step-label">{label}</div>'
            f'</div>{connector}'
        )
    st.markdown(f'<div class="payment-progress">{dots_html}</div>', unsafe_allow_html=True)

# ── Step 1: 장바구니 확인 ──────────────────────────────────────
def render_cart_confirm():
    st.markdown(f'<p class="pay-step-title">🛒 {t("stage_cart")}</p>', unsafe_allow_html=True)
    if not st.session_state.cart:
        st.warning(t("cart_empty"))
        if st.button(f"← {t('back')}", key="cc_back"):
            st.session_state.payment_stage = None
            st.rerun()
        return

    for idx, item in enumerate(st.session_state.cart):
        c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
        _opts = item.get("options", [])
        _opt_label = ", ".join(f"{o['name']}×{o['qty']}" for o in _opts if o.get("qty", 0) > 0)
        _opt_extra = sum(o["price"] * o["qty"] for o in _opts if o.get("qty", 0) > 0)
        _opt_html = f"<br><span style='font-size:.8em;color:#9A8070'>{_opt_label}</span>" if _opt_label else ""
        c1.markdown(f"**{item['name']}**{_opt_html}", unsafe_allow_html=True)
        with c2:
            q1, q2, q3 = st.columns(3)
            if q1.button("−", key=f"cc_minus_{idx}"):
                if item["qty"] > 1:
                    st.session_state.cart[idx]["qty"] -= 1
                else:
                    cart_remove_by_idx(idx)
                st.rerun()
            q2.markdown(f"<div style='text-align:center;padding-top:6px'><b>{item['qty']}</b></div>", unsafe_allow_html=True)
            if q3.button("＋", key=f"cc_plus_{idx}"):
                st.session_state.cart[idx]["qty"] += 1
                st.rerun()
        c3.write(f"{(item['price'] + _opt_extra) * item['qty']:,} {t('won')}")
        if c4.button("✕", key=f"cc_del_{idx}"):
            cart_remove_by_idx(idx)
            st.rerun()

    st.markdown(f'<div class="cart-total">{t("total")}: {cart_total():,} {t("won")}</div>', unsafe_allow_html=True)
    st.write("")
    b1, b2 = st.columns([1, 2])
    if b1.button(f"← {t('cancel')}", key="cc_cancel", use_container_width=True):
        st.session_state.payment_stage = None
        st.rerun()
    if b2.button(f"{t('next')} →", key="cc_next", type="primary", use_container_width=True):
        st.session_state.payment_stage = "order_type"
        st.rerun()

# ── Step 2: 포장/매장 선택 ────────────────────────────────────
def render_order_type():
    st.markdown(f'<p class="pay-step-title">🏪 {t("stage_order_type")}</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div style="border:3px solid #e0e0e0;border-radius:16px;padding:32px 16px;
        text-align:center;background:#fafafa;font-size:1.1em;">
        <div style="font-size:2.5em;margin-bottom:8px">🏠</div>
        <div style="font-weight:700">{t('table')}</div>
        </div>""", unsafe_allow_html=True)
        if st.button(t("table"), key="ot_table", use_container_width=True, type="primary"):
            st.session_state.order_type = "table"
            st.session_state.payment_stage = "options"
            st.rerun()
    with c2:
        st.markdown(f"""
        <div style="border:3px solid #e0e0e0;border-radius:16px;padding:32px 16px;
        text-align:center;background:#fafafa;font-size:1.1em;">
        <div style="font-size:2.5em;margin-bottom:8px">📦</div>
        <div style="font-weight:700">{t('takeout')}</div>
        </div>""", unsafe_allow_html=True)
        if st.button(t("takeout"), key="ot_takeout", use_container_width=True):
            st.session_state.order_type = "takeout"
            st.session_state.payment_stage = "options"
            st.rerun()
    st.write("")
    if st.button(f"← {t('back')}", key="ot_back"):
        st.session_state.payment_stage = "cart_confirm"
        st.rerun()

# ── Step 3: 추가 옵션 (영수증, 할인) ─────────────────────────
def render_payment_options():
    st.markdown(f'<p class="pay-step-title">⚙️ {t("stage_options")}</p>', unsafe_allow_html=True)

    st.subheader(t("receipt_title"))
    receipt_choice = st.radio(
        "",
        [t("receipt_print"), t("receipt_email"), t("receipt_no")],
        index=2,
        key="receipt_radio",
        horizontal=True,
    )
    st.session_state.receipt_option = receipt_choice

    st.divider()
    st.subheader(f"🎫 {t('pay_point')} / {t('pay_voucher')}")
    st.caption("포인트나 쿠폰이 있으시면 먼저 적용하세요. 나머지 금액은 다른 수단으로 결제하실 수 있습니다.")

    with st.expander(f"💰 {t('pay_point')} {t('apply')}", expanded=False):
        pts = st.number_input(
            t("point_available"), min_value=0, max_value=cart_total(),
            value=st.session_state.points_input, step=100, key="pts_input_opt"
        )
        coup = st.text_input(t("point_enter"), value=st.session_state.coupon_input, key="coup_input_opt")
        if st.button(t("apply"), key="apply_points"):
            discount = min(pts, cart_total())
            if coup.strip().upper() == "PAIK10":
                discount += int(cart_total() * 0.1)
            st.session_state.partial_paid = min(discount, cart_total())
            st.session_state.points_input = pts
            st.session_state.coupon_input = coup
            st.success(f"{t('discount_applied')}: {st.session_state.partial_paid:,} {t('won')}")

    if st.session_state.partial_paid > 0:
        st.info(f"✅ {t('discount_applied')}: **{st.session_state.partial_paid:,} {t('won')}**  \n"
                f"{t('remaining')}: **{_payment_remaining():,} {t('won')}**")

    st.write("")
    b1, b2 = st.columns([1, 2])
    if b1.button(f"← {t('back')}", key="opts_back", use_container_width=True):
        st.session_state.payment_stage = "order_type"
        st.rerun()
    if b2.button(f"{t('next')} →", key="opts_next", type="primary", use_container_width=True):
        st.session_state.payment_stage = "payment_select"
        st.rerun()

# ── Step 4: 결제 수단 선택 ────────────────────────────────────
def render_payment_select():
    remaining = _payment_remaining()
    st.markdown(f'<p class="pay-step-title">💳 {t("stage_payment_select")}</p>', unsafe_allow_html=True)

    if st.session_state.partial_paid > 0:
        st.info(f"🎫 {t('discount_applied')}: **{st.session_state.partial_paid:,} {t('won')}**  "
                f"| {t('remaining')}: **{remaining:,} {t('won')}**")

    # ── 결제 수단 그룹 ──
    st.markdown("##### 💳 카드 결제")
    card_methods = [
        ("card",    "💳", t("pay_card"),    t("pay_card_desc")),
    ]
    cols_card = st.columns(len(card_methods))
    for i, (key, icon, name, desc) in enumerate(card_methods):
        with cols_card[i]:
            st.markdown(f"""
            <div class="pay-method-card">
              <div class="icon">{icon}</div>
              <div class="name">{name}</div>
              <div class="desc">{desc}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(name, key=f"pm_{key}", use_container_width=True):
                st.session_state.current_payment_method = key
                st.session_state.payment_stage = "payment_detail"
                st.rerun()

    st.markdown("##### 📱 간편결제 (QR/바코드)")
    qr_methods = [
        ("kakao",   "🟡", "카카오페이",   "QR·바코드"),
        ("naver",   "🟢", "네이버페이",   "QR·바코드"),
        ("apple",   "⚫", "애플페이",      "NFC·탭"),
        ("toss",    "🔵", "토스페이",     "QR·바코드"),
        ("samsung", "🔷", "삼성페이",     "NFC·MST"),
        ("payco",   "🔴", "페이코",       "QR·바코드"),
    ]
    cols_qr = st.columns(3)
    for i, (key, icon, name, desc) in enumerate(qr_methods):
        with cols_qr[i % 3]:
            st.markdown(f"""
            <div class="pay-method-card">
              <div class="icon">{icon}</div>
              <div class="name">{name}</div>
              <div class="desc">{desc}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(name, key=f"pm_{key}", use_container_width=True):
                st.session_state.current_payment_method = key
                st.session_state.payment_stage = "payment_detail"
                st.rerun()

    st.markdown("##### 💵 기타 결제")
    other_methods = [
        ("cash",    "💵", t("pay_cash"),    t("pay_cash_desc")),
        ("voucher", "🎁", t("pay_voucher"), t("pay_voucher_desc")),
    ]
    cols_other = st.columns(len(other_methods))
    for i, (key, icon, name, desc) in enumerate(other_methods):
        with cols_other[i]:
            st.markdown(f"""
            <div class="pay-method-card">
              <div class="icon">{icon}</div>
              <div class="name">{name}</div>
              <div class="desc">{desc}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(name, key=f"pm_{key}", use_container_width=True):
                st.session_state.current_payment_method = key
                st.session_state.payment_stage = "payment_detail"
                st.rerun()

    st.write("")
    if st.button(f"← {t('back')}", key="ps_back"):
        st.session_state.payment_stage = "options"
        st.rerun()

# ── Step 5: 결제 진행 (수단별) ────────────────────────────────
def render_payment_detail():
    stage = st.session_state.payment_stage
    method = st.session_state.current_payment_method
    remaining = _payment_remaining()

    if stage == "processing":
        st.markdown(f"""
        <div class="processing-box">
          <div style="font-size:3em; margin-bottom:12px">⏳</div>
          <h2>{t('payment_processing')}</h2>
          <p style="color:#888">{remaining:,} {t('won')}</p>
        </div>""", unsafe_allow_html=True)
        import time, random
        time.sleep(1.5)
        if random.random() < 0.92:
            st.session_state.payment_plan.append({"method": method, "amount": remaining})
            st.session_state.partial_paid += remaining
            st.session_state.payment_stage = "success"
        else:
            st.session_state.payment_failure_reason = t("payment_failed_reason")
            st.session_state.payment_stage = "failure"
        st.rerun()
        return

    if stage == "success":
        st.markdown(f"""
        <div class="success-box">
          <div style="font-size:3em;margin-bottom:8px">✅</div>
          <h2 style="color:#2e7d32">{t('payment_success')}</h2>
          <p style="color:#555">{t('total')}: <b>{cart_total():,} {t('won')}</b></p>
        </div>""", unsafe_allow_html=True)
        import time; time.sleep(0.8)
        st.session_state.order_number = _gen_order_number()
        st.session_state.payment_stage = "order_complete"
        st.rerun()
        return

    if stage == "failure":
        st.markdown(f"""
        <div class="failure-box">
          <div style="font-size:3em;margin-bottom:8px">❌</div>
          <h2 style="color:#e65100">{t('payment_failed')}</h2>
          <p>{st.session_state.payment_failure_reason}</p>
        </div>""", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        if c1.button(t("retry"), key="fail_retry", use_container_width=True, type="primary"):
            st.session_state.payment_stage = "payment_detail"
            st.rerun()
        if c2.button(t("change_method"), key="fail_change", use_container_width=True):
            st.session_state.payment_stage = "payment_select"
            st.rerun()
        if c3.button(t("call_staff"), key="fail_staff", use_container_width=True):
            st.warning("🔔 직원을 호출했습니다. 잠시만 기다려 주세요.")
        return

    # 결제 수단별 UI
    st.markdown(f'<p class="pay-step-title">💳 {t("stage_payment_detail")}</p>', unsafe_allow_html=True)
    st.markdown(f"**{t('remaining')}: {remaining:,} {t('won')}**")
    st.divider()

    # 간편결제 수단 목록
    qr_methods = {"kakao", "naver", "apple", "toss", "samsung", "payco"}
    method_labels = {
        "card": ("💳", "신용·체크카드", "카드를 단말기에 올려주세요 또는 탭하세요"),
        "kakao": ("🟡", "카카오페이", "카카오페이 QR코드를 스캔해주세요"),
        "naver": ("🟢", "네이버페이", "네이버페이 바코드를 스캔해주세요"),
        "apple": ("⚫", "애플페이", "iPhone/Apple Watch를 단말기에 가까이 대주세요"),
        "toss": ("🔵", "토스페이", "토스 QR코드를 스캔해주세요"),
        "samsung": ("🔷", "삼성페이", "갤럭시 기기를 단말기에 가까이 대주세요"),
        "payco": ("🔴", "페이코", "페이코 바코드를 스캔해주세요"),
        "cash": ("💵", "현금", "현금을 투입해 주세요"),
        "voucher": ("🎁", "상품권/기프티콘", "상품권/기프티콘 번호를 입력해주세요"),
    }
    m_icon, m_label, m_instruction = method_labels.get(method, ("💳", method, "진행해주세요"))

    if method == "card":
        st.markdown(f"""
        <div style="text-align:center;padding:24px">
          <div style="font-size:3.5em">{m_icon}</div>
          <h3>{m_label}</h3>
          <div style="background:#f0f4ff;border:2px dashed #1A2B5E;border-radius:12px;
               padding:32px;margin:16px auto;max-width:300px;font-size:1.1em;color:#1A2B5E">
          NFC / IC / MS<br><span style="font-size:.8em;color:#888">{m_instruction}</span>
          </div>
        </div>""", unsafe_allow_html=True)

    elif method in qr_methods:
        qr_labels = {
            "kakao": "카카오페이 앱 → 결제 → QR/바코드",
            "naver": "네이버페이 앱 → 바코드 결제",
            "apple": "Face ID / Touch ID 인증 후 단말기에 가까이",
            "toss": "토스 앱 → 결제 → QR코드",
            "samsung": "Samsung Pay 앱 → 결제 탭",
            "payco": "PAYCO 앱 → 바코드 결제",
        }
        st.markdown(f"""
        <div style="text-align:center;padding:16px">
          <div style="font-size:3em">{m_icon}</div>
          <h3>{m_label}</h3>
          <p style="color:#555">{qr_labels.get(method, m_instruction)}</p>
          <div style="display:inline-block;border:3px solid #1A2B5E;border-radius:8px;
               padding:16px;font-size:64px;background:#fff;margin:12px auto">
          ▪▫▪▫<br>▫▪▫▪<br>▪▫▪▫
          </div>
          <p style="color:#888;font-size:.85em">화면의 QR코드 또는 단말기에 스캔하세요</p>
        </div>""", unsafe_allow_html=True)

    elif method == "cash":
        st.markdown(f"""
        <div style="text-align:center;padding:16px">
          <div style="font-size:3em">💵</div>
          <h3>{t('cash_insert')}</h3>
        </div>""", unsafe_allow_html=True)
        cash_in = st.number_input(
            "투입 금액 (원)", min_value=0, step=1000,
            value=remaining, key="cash_amount"
        )
        if cash_in < remaining:
            st.warning(f"부족한 금액: {remaining - cash_in:,}원")
        else:
            change = cash_in - remaining
            if change > 0:
                st.success(f"거스름돈: **{change:,}원**")
            else:
                st.success("딱 맞게 내셨네요! 감사합니다 😊")

    elif method == "voucher":
        st.markdown(f"<div style='text-align:center'><div style='font-size:3em'>🎁</div><h3>{t('voucher_enter')}</h3></div>", unsafe_allow_html=True)
        vc = st.text_input("상품권/기프티콘 번호 (16자리)", max_chars=19, key="voucher_code",
                           placeholder="XXXX-XXXX-XXXX-XXXX")
        if vc:
            cleaned = vc.replace("-", "")
            if len(cleaned) >= 16:
                st.info(f"입력된 번호: `{vc}` ✓ 확인 완료")
            else:
                st.warning(f"번호를 더 입력해주세요 ({len(cleaned)}/16자리)")

    st.write("")
    c_pay, c_back = st.columns([2, 1])
    if c_pay.button(f"✅ {t('confirm')}", key="pd_confirm", type="primary", use_container_width=True):
        if method == "cash":
            cash_v = st.session_state.get("cash_amount", 0)
            if cash_v < remaining:
                st.error("투입 금액이 부족합니다.")
                st.stop()
        elif method == "voucher":
            vc_v = st.session_state.get("voucher_code", "")
            if len(vc_v.replace("-", "")) < 16:
                st.error("올바른 상품권/기프티콘 번호를 입력해주세요.")
                st.stop()
        st.session_state.payment_stage = "processing"
        st.rerun()
    if c_back.button(f"← {t('back')}", key="pd_back", use_container_width=True):
        st.session_state.payment_stage = "payment_select"
        st.rerun()

# ── Step 6: 주문 완료 ─────────────────────────────────────────
def render_order_complete():
    order_no = st.session_state.order_number or _gen_order_number()
    st.markdown(f"""
    <div style="text-align:center;padding:32px 16px">
      <div style="font-size:2.5em;margin-bottom:8px">🎉</div>
      <h1 style="color:#1A2B5E">{t('order_complete_msg')}</h1>
      <p style="color:#555;font-size:1.1em">{t('order_number_label')}</p>
      <div class="order-number-badge">{order_no}</div>
    </div>""", unsafe_allow_html=True)

    # 결제 내역 요약
    with st.expander("📋 결제 내역", expanded=True):
        for item in st.session_state.cart:
            _opts = item.get("options", [])
            _opt_extra = sum(o["price"] * o["qty"] for o in _opts if o.get("qty", 0) > 0)
            _item_total = (item["price"] + _opt_extra) * item["qty"]
            st.write(f"• {item['name']} × {item['qty']} = **{_item_total:,} {t('won')}**")
            for o in [o for o in _opts if o.get("qty", 0) > 0]:
                st.caption(f"  ↳ {o['name']} ×{o['qty']} (+{o['price']*o['qty']:,}원)")
        st.divider()
        if st.session_state.partial_paid < cart_total():
            pass
        paid_methods = " + ".join(p["method"] for p in st.session_state.payment_plan) or "-"
        st.write(f"**{t('total')}: {cart_total():,} {t('won')}** ({paid_methods})")
        ot = "🏠 매장" if st.session_state.order_type == "table" else "📦 포장"
        st.write(f"주문 방식: {ot}")

    import time; time.sleep(0.5)
    if st.button(f"➡ {t('next')}", key="oc_next", type="primary", use_container_width=True):
        st.session_state.payment_stage = "waiting"
        st.rerun()

# ── Step 7: 대기 화면 ─────────────────────────────────────────
def render_waiting():
    order_no = st.session_state.order_number
    st.markdown(f"""
    <div class="waiting-screen">
      <div style="font-size:3em;margin-bottom:8px">☕</div>
      <h1 style="color:#1A2B5E">{order_no}번</h1>
      <p style="font-size:1.2em;color:#555">{t('wait_msg')}</p>
      <div style="margin:24px auto;font-size:1.05em;color:#888">
        음료를 정성껏 준비 중입니다...<br>
        <span style="font-size:.85em">카운터에서 번호를 불러드릴게요</span>
      </div>
    </div>""", unsafe_allow_html=True)
    st.write("")
    if st.button(t("new_order"), key="wait_new", type="primary", use_container_width=True):
        for k in ["api_messages", "display_msgs", "cart", "order_done", "greeted",
                  "abuse_count", "payment_stage", "order_type", "receipt_option",
                  "payment_plan", "partial_paid", "current_payment_method",
                  "order_number", "payment_failure_reason", "coupon_input", "points_input"]:
            st.session_state.pop(k, None)
        st.rerun()

def render_payment_flow():
    """결제 플로우 디스패처"""
    render_payment_progress()
    stage = st.session_state.payment_stage
    if stage == "cart_confirm":
        render_cart_confirm()
    elif stage == "order_type":
        render_order_type()
    elif stage == "options":
        render_payment_options()
    elif stage == "payment_select":
        render_payment_select()
    elif stage in ("payment_detail", "processing", "success", "failure"):
        render_payment_detail()
    elif stage == "order_complete":
        render_order_complete()
    elif stage == "waiting":
        render_waiting()

# ─────────────────────────  사이드바 렌더링  ──────────────────
def render_sidebar():
    with st.sidebar:
        # ── 브랜드 로고 영역 ──
        st.markdown("""
        <div style="text-align:center;padding:20px 0 10px">
          <div style="font-size:3em;line-height:1">☕</div>
          <div style="font-family:'Jua',sans-serif;color:#1C110A;font-weight:900;font-size:1.55em;letter-spacing:2px;margin-top:8px">5지는 카페</div>
          <div style="color:#9A8070;font-size:.78em;letter-spacing:2px;margin-top:3px;font-weight:600">OJINEUN CAFE</div>
          <div style="color:#C9A55A;font-size:.82em;margin-top:5px;font-weight:700">오지는 맛! ✨ 오지는 가격!</div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        # ── API 키 ──
        api_key_in = st.text_input(
            "🔑 OpenAI API Key",
            type="password",
            value=st.session_state.get("api_key", ""),
            placeholder="sk-...",
            key="api_key_input"
        )
        if api_key_in:
            st.session_state.api_key = api_key_in

        if not (st.session_state.get("api_key") or os.getenv("OPENAI_API_KEY")):
            st.warning(t("api_warning"))
        else:
            st.success(t("api_connected"))
        st.divider()

        # ── 언어 선택 ──
        st.markdown('<div class="sb-section-title">🌐 언어 / Language</div>', unsafe_allow_html=True)
        lang_map = {"ko": "🇰🇷 한국어", "en": "🇺🇸 English", "cn": "🇨🇳 中文", "jp": "🇯🇵 日本語"}
        lang_cols = st.columns(2)
        for i, (code, label) in enumerate(lang_map.items()):
            btn_type = "primary" if st.session_state.get("lang", "ko") == code else "secondary"
            if lang_cols[i % 2].button(label, key=f"lang_{code}", use_container_width=True, type=btn_type):
                if st.session_state.get("lang") != code:
                    st.session_state.lang = code
                    # 언어 변경 시 채팅 기록 초기화 + 새 시스템 프롬프트 적용
                    new_system = get_system_prompt(code)
                    st.session_state.api_messages = [{"role": "system", "content": new_system}]
                    st.session_state.display_msgs = []
                    st.session_state.greeted = False
                    st.rerun()
        st.divider()

        # ── 장바구니 ──
        st.markdown(f'<div class="sb-section-title">{t("cart_title")}</div>', unsafe_allow_html=True)
        if st.session_state.cart:
            for idx, item in enumerate(st.session_state.cart):
                col_name, col_qty, col_del = st.columns([3, 3, 1])
                _opts = item.get("options", [])
                _opt_label = ", ".join(f"{o['name']}×{o['qty']}" for o in _opts if o.get("qty", 0) > 0)
                _opt_extra = sum(o["price"] * o["qty"] for o in _opts if o.get("qty", 0) > 0)
                _price_per = item["price"] + _opt_extra
                _opt_html = f"<br><span style='font-size:.74em;color:#9A8070'>{_opt_label}</span>" if _opt_label else ""
                col_name.markdown(f"**{item['name']}**{_opt_html}  \n`{_price_per:,}{t('won')}`", unsafe_allow_html=True)
                with col_qty:
                    q1, q2, q3 = st.columns(3)
                    if q1.button("−", key=f"sb_minus_{idx}"):
                        if item["qty"] > 1:
                            st.session_state.cart[idx]["qty"] -= 1
                        else:
                            cart_remove_by_idx(idx)
                        st.rerun()
                    q2.markdown(f"<div style='text-align:center;padding-top:4px'><b>{item['qty']}</b></div>", unsafe_allow_html=True)
                    if q3.button("＋", key=f"sb_plus_{idx}"):
                        st.session_state.cart[idx]["qty"] += 1
                        st.rerun()
                if col_del.button("✕", key=f"del_{idx}"):
                    cart_remove_by_idx(idx)
                    st.rerun()
            st.markdown(
                f'<div class="cart-total">{t("total")}: {cart_total():,} {t("won")}</div>',
                unsafe_allow_html=True,
            )
            col_checkout, col_clear = st.columns(2)
            if st.session_state.payment_stage is None:
                if col_checkout.button(t("checkout"), use_container_width=True, type="primary"):
                    st.session_state.payment_stage = "cart_confirm"
                    st.session_state.partial_paid = 0
                    st.session_state.payment_plan = []
                    st.rerun()
            if col_clear.button(t("clear_cart"), use_container_width=True):
                st.session_state.cart = []
                st.rerun()
        else:
            st.info(t("cart_empty"))
        st.divider()

        # ── 직원 호출 (큰 버튼) ──
        if st.button("🔔 " + t("call_staff"), key="sb_call_staff", use_container_width=True, type="primary"):
            st.session_state.staff_called = True
            st.rerun()
        if st.session_state.get("staff_called"):
            st.success("✅ 직원을 호출했습니다! 잠시만 기다려 주세요.")
        st.divider()

        # ── 매장 정보 (store_info.json 실데이터) ──
        lang = st.session_state.get("lang", "ko")
        store_json = load_store_info()
        s_name    = store_json.get("store_name", STORE_INFO.get(f"name_{lang}", ""))
        s_addr    = store_json.get("address", STORE_INFO.get("address", ""))
        s_phone   = store_json.get("phone", STORE_INFO.get("phone", ""))
        s_hours   = store_json.get("hours", {})
        s_fac     = store_json.get("facilities", {})
        s_pay     = store_json.get("payment_methods", [])
        s_amenity = store_json.get("amenities", [])
        s_nearby  = store_json.get("nearby_landmarks", [])
        s_delivery= store_json.get("delivery_available", False)
        s_deliv_p = store_json.get("delivery_partners", [])
        s_notes   = store_json.get("notes", "")
        s_wifi    = s_fac.get("wifi", {})
        s_parking = s_fac.get("parking", {})
        s_seats   = s_fac.get("seating", {})
        # 영업시간 문자열
        wday = f'{s_hours.get("weekday_start","-")} ~ {s_hours.get("weekday_end","-")}'
        wend = f'{s_hours.get("weekend_start","-")} ~ {s_hours.get("weekend_end","-")}'
        fac_tags = "".join(f'<span class="facility-tag">{a}</span>' for a in s_amenity)
        pay_tags = "".join(f'<span class="facility-tag">{p}</span>' for p in s_pay)
        with st.expander(f"📍 {s_name}", expanded=False):
            st.markdown(f"""
            <div class="store-card">
              <div class="store-row"><span class="store-icon">🏠</span><span>{s_addr}</span></div>
              <div class="store-row"><span class="store-icon">🕐</span>
                <span><b style='color:#4A7A30'>평일</b> {wday} &nbsp;|&nbsp; <b style='color:#4A7A30'>주말</b> {wend}</span></div>
              <div class="store-row"><span class="store-icon">📞</span><span>{s_phone}</span></div>
              {'<div class="store-row"><span class="store-icon">🚗</span><span>' + s_parking.get("type","") + ' · ' + s_parking.get("fee","") + '</span></div>' if s_parking.get('available') else ''}
              {'<div class="store-row"><span class="store-icon">📶</span><span>Wi-Fi 비밀번호: <b>' + s_wifi.get('password','') + '</b></span></div>' if s_wifi.get('available') else ''}
              {'<div class="store-row"><span class="store-icon">🪑</span><span>총 ' + str(s_seats.get('total_seats','')) + '석 · ' + s_seats.get('seats_description','') + '</span></div>' if s_seats else ''}
              {'<div class="store-row"><span class="store-icon">🛵</span><span>배달: ' + ', '.join(s_deliv_p) + '</span></div>' if s_delivery and s_deliv_p else ''}
            </div>""", unsafe_allow_html=True)
            if s_amenity:
                st.markdown(f'<div style="margin:4px 0 6px"><b style="font-size:.8em;color:#5C3D2E">편의시설</b><br>{fac_tags}</div>', unsafe_allow_html=True)
            if s_pay:
                st.markdown(f'<div style="margin:4px 0 6px"><b style="font-size:.8em;color:#5C3D2E">결제수단</b><br>{pay_tags}</div>', unsafe_allow_html=True)
            if s_nearby:
                st.markdown('<b style="font-size:.8em;color:#5C3D2E">주변 랜드마크</b>', unsafe_allow_html=True)
                for lm in s_nearby:
                    st.markdown(f'<div style="font-size:.78em;color:#7A6654;margin-left:6px">📌 {lm}</div>', unsafe_allow_html=True)
            if s_notes:
                st.info(s_notes, icon="ℹ️")
        st.divider()

        # ── 응답 만족도 ──
        with st.expander(f"📊 {t('satisfaction')}", expanded=False):
            fb = st.session_state.feedback
            c1, c2 = st.columns(2)
            c1.metric("👍", fb["good"])
            c2.metric("👎", fb["bad"])
            total_fb = fb["good"] + fb["bad"]
            if total_fb > 0:
                st.progress(fb["good"] / total_fb, text=f"만족도 {fb['good']/total_fb*100:.0f}%")

        # ── 대화 초기화 ──
        if st.button(t("reset"), use_container_width=True):
            for k in ["api_messages", "display_msgs", "cart", "order_done", "greeted",
                      "test_idx", "abuse_count", "payment_stage", "order_type",
                      "receipt_option", "payment_plan", "partial_paid",
                      "current_payment_method", "order_number",
                      "payment_failure_reason", "coupon_input", "points_input",
                      "staff_called"]:
                st.session_state.pop(k, None)
            st.rerun()

        # ── 돌발 시나리오 테스트 (접기) ──
        with st.expander(f"🤖 {t('test_mode')}", expanded=False):
            test_mode = st.toggle("테스트 모드 ON", key="test_mode_toggle")
            if test_mode:
                idx = st.session_state.get("test_idx", 0) % len(ADVERSARIAL_SCENARIOS)
                st.info(f"**시나리오 {idx+1}/{len(ADVERSARIAL_SCENARIOS)}**\n\n> {ADVERSARIAL_SCENARIOS[idx]}")
                if st.button("▶️ 이 시나리오 실행", use_container_width=True):
                    scenario = ADVERSARIAL_SCENARIOS[idx]
                    st.session_state.display_msgs.append(
                        {"role": "user", "content": f"[테스트] {scenario}", "feedback": None, "staff_call": False}
                    )
                    with st.spinner("오지 응답 중..."):
                        reply, staff_call = chat(scenario)
                    st.session_state.display_msgs.append(
                        {"role": "assistant", "content": reply, "feedback": None, "staff_call": staff_call}
                    )
                    st.session_state["test_idx"] = idx + 1
                    st.rerun()
                if st.button("⏭️ 다음 시나리오", use_container_width=True):
                    st.session_state["test_idx"] = idx + 1
                    st.rerun()

# ─────────────────────────  채팅 메시지 렌더링  ───────────────
def render_messages():
    for i, msg in enumerate(st.session_state.display_msgs):
        role = msg["role"]
        avatar = "☕" if role == "assistant" else "🙂"
        with st.chat_message(role, avatar=avatar):
            st.write(msg["content"])

            # 직원 호출 버튼 (assistant 메시지에 staff_call 플래그가 있을 때)
            if role == "assistant" and msg.get("staff_call"):
                lang = st.session_state.get("lang", "ko")
                call_labels = {
                    "ko": "🔔 직원을 호출할까요?",
                    "en": "🔔 Shall we call a staff member?",
                    "cn": "🔔 需要呼叫店员吗？",
                    "jp": "🔔 スタッフを呼びましょうか？",
                }
                st.info(call_labels.get(lang, call_labels["ko"]))
                btn_labels = {
                    "ko": "🔔 직원 호출하기",
                    "en": "🔔 Call Staff",
                    "cn": "🔔 呼叫店员",
                    "jp": "🔔 スタッフを呼ぶ",
                }
                if st.button(btn_labels.get(lang, btn_labels["ko"]), key=f"call_staff_chat_{i}"):
                    st.session_state.staff_called = True
                    st.session_state.display_msgs[i]["staff_call"] = False  # 버튼 숨기기
                    st.rerun()

            # 피드백 버튼 (assistant 메시지, 아직 평가 안 한 경우)
            if role == "assistant" and msg["feedback"] is None:
                fb_cols = st.columns([1, 1, 10])
                if fb_cols[0].button("👍", key=f"g_{i}"):
                    st.session_state.display_msgs[i]["feedback"] = "good"
                    st.session_state.feedback["good"] += 1
                    st.rerun()
                if fb_cols[1].button("👎", key=f"b_{i}"):
                    st.session_state.display_msgs[i]["feedback"] = "bad"
                    st.session_state.feedback["bad"] += 1
                    st.rerun()
            elif msg["feedback"] == "good":
                st.caption(t("feedback_good"))
            elif msg["feedback"] == "bad":
                st.caption(t("feedback_bad"))

# ─────────────────────────  퀵 액션 패널  ─────────────────────
def render_quick_panel():
    """선택된 카테고리의 메뉴/소식을 app2.py 수준 카드로 표시 (이미지·영양·옵션·링크 포함)"""
    panel = st.session_state.get("quick_panel")
    if panel is None:
        return

    menu_data = load_menu_data()
    news_data = load_news_data()
    lang = st.session_state.get("lang", "ko")
    title = QUICK_PANEL_LABELS.get(panel, panel)

    # ── 패널 헤더 ──
    hcol1, hcol2 = st.columns([9, 1])
    hcol1.markdown(f"### {title}")
    if hcol2.button("✕ 닫기", key="close_quick_panel"):
        st.session_state.quick_panel = None
        st.rerun()

    # ── 소식 패널 ──
    if panel == "소식":
        if not news_data:
            st.info("소식 정보가 없어요.")
            return
        for ni in news_data:
            ni_cat   = ni.get("category", "소식")
            ni_title = ni.get("title", "")
            ni_date  = ni.get("date", "")
            ni_views = ni.get("views", 0)
            ni_content = (ni.get("content") or "")
            ni_url   = ni.get("url", "")

            cat_cls = "nc-cat-ev" if ni_cat == "이벤트" else "nc-cat-news"
            with st.container(border=True):
                tc, lc = st.columns([5, 1])
                with tc:
                    disc = ni.get("discount")
                    disc_badge = ""
                    if disc:
                        rate = disc.get("rate", 0)
                        end  = disc.get("end_date", "")
                        desc_d = disc.get("description", "")
                        disc_badge = f'<span class="nc-discount">🏷️ {rate}% 할인 · {end}까지</span><br>'
                    st.markdown(
                        f'<span class="{cat_cls}">{ni_cat}</span>'
                        f'<div class="nc-title">{ni_title}</div>'
                        f'<div class="nc-meta">📅 {ni_date}{"  ·  👁 " + str(ni_views) + "회" if ni_views else ""}</div>'
                        f'{disc_badge}',
                        unsafe_allow_html=True,
                    )
                    if ni_content:
                        with st.expander("내용 보기"):
                            st.write(ni_content)
                if ni_url:
                    lc.link_button("자세히 →", ni_url, use_container_width=True)
        return

    # ── 메뉴 패널 ──
    # 아이템 필터
    if panel == "베스트":
        items = [m for m in menu_data if m.get("is_best")]
    elif panel == "할인":
        cheap = [m for m in menu_data if isinstance(m.get("price_won"), (int, float)) and m["price_won"] <= 3000]
        items = sorted(cheap, key=lambda x: x.get("price_won", 9999))
        if not items:
            items = sorted(
                [m for m in menu_data if m.get("price_won")],
                key=lambda x: x.get("price_won", 9999)
            )[:20]
    else:
        items = [m for m in menu_data if m.get("category") == panel]

    if not items:
        st.info("해당 메뉴를 찾을 수 없어요.")
        return

    # ── 서브 필터 (온도·베스트·검색) ──
    fc1, fc2, fc3, fc4 = st.columns([2, 2, 1, 3])
    temp_f  = fc1.radio("온도", ["전체", "HOT", "ICED"], horizontal=True,
                         key=f"qp_temp_{panel}", label_visibility="collapsed")
    best_f  = fc2.checkbox("🏆 베스트만", key=f"qp_best_{panel}")
    decaf_f = fc3.checkbox("디카페인", key=f"qp_decaf_{panel}")
    search  = fc4.text_input("🔍 메뉴 검색", placeholder="이름 입력...",
                              key=f"qp_search_{panel}", label_visibility="collapsed")

    if temp_f == "HOT":
        items = [m for m in items if "(HOT)" in m.get("menu_name", "")]
    elif temp_f == "ICED":
        items = [m for m in items if "(ICED)" in m.get("menu_name", "")]
    if best_f:
        items = [m for m in items if m.get("is_best")]
    if decaf_f:
        items = [m for m in items if "디카페인" in m.get("menu_name", "")]
    if search:
        items = [m for m in items if search.lower() in m.get("menu_name", "").lower()]

    st.caption(f"**{len(items)}개** 메뉴")
    st.divider()

    if not items:
        st.info("조건에 맞는 메뉴가 없어요.")
        return

    # ── 3열 카드 그리드 ──
    NCOLS = 3
    NUTRITION_LABELS = [
        ("caffeine_mg", "☕ 카페인",  "mg"),
        ("kcal",        "🔥 칼로리", "kcal"),
        ("sugar_g",     "🍬 당류",   "g"),
        ("sodium_mg",   "🧂 나트륨", "mg"),
        ("sat_fat_g",   "🧈 포화지방","g"),
        ("protein_g",   "💪 단백질", "g"),
        ("carb_g",      "🌾 탄수화물","g"),
        ("fat_g",       "💧 지방",   "g"),
    ]

    rows = [items[i:i+NCOLS] for i in range(0, len(items), NCOLS)]
    for row in rows:
        cols = st.columns(NCOLS)
        for col, item in zip(cols, row):
            with col:
                with st.container(border=True):
                    name      = item.get("menu_name", "")
                    eng_name  = item.get("eng_name", "")
                    desc      = item.get("description", "") or ""
                    price     = item.get("price_won")
                    volume    = item.get("cup_volume", "")
                    allergen  = item.get("allergen", "")
                    caution   = item.get("caution_note", "")
                    img_url   = item.get("image_url", "")
                    is_best   = item.get("is_best", False)
                    nutrition = item.get("nutrition", {})
                    options   = item.get("options") or []

                    # 이미지
                    if is_valid(img_url):
                        st.markdown(
                            f'<div style="height:180px;display:flex;align-items:center;justify-content:center;'
                            f'background:#FAF6EF;border-radius:8px;margin-bottom:4px;overflow:hidden">'
                            f'<img src="{img_url}" style="max-width:100%;max-height:180px;width:auto;height:auto;object-fit:contain;display:block"></div>',
                            unsafe_allow_html=True
                        )

                    # 베스트 배지 + 이름
                    if is_best:
                        st.markdown('<span class="mc-badge">🏆 BEST</span>', unsafe_allow_html=True)
                    st.markdown(f'<div class="mc-name">{name}</div>', unsafe_allow_html=True)
                    if is_valid(eng_name):
                        st.markdown(f'<div class="mc-eng">{eng_name}</div>', unsafe_allow_html=True)

                    # 가격
                    price_str = f"💰 {price:,}원" if isinstance(price, (int, float)) else "-"
                    st.markdown(f'<div class="mc-price">{price_str}</div>', unsafe_allow_html=True)

                    # 설명
                    if is_valid(desc):
                        st.markdown(f'<div class="mc-desc">{desc}</div>', unsafe_allow_html=True)

                    # 용량 · 알레르기
                    meta_parts = []
                    if is_valid(volume):
                        meta_parts.append(f"🥤 {volume}")
                    if is_valid(allergen):
                        meta_parts.append(f"⚠️ {allergen}")
                    if meta_parts:
                        st.markdown(
                            f'<div class="mc-meta">{" &nbsp;|&nbsp; ".join(meta_parts)}</div>',
                            unsafe_allow_html=True
                        )

                    # 영양성분 expander
                    has_nut = any(is_valid(nutrition.get(k)) for k, _, _ in NUTRITION_LABELS)
                    if has_nut:
                        with st.expander("📊 영양성분"):
                            ncols3 = st.columns(3)
                            ci = 0
                            for nk, nlabel, nunit in NUTRITION_LABELS:
                                raw = nutrition.get(nk)
                                if not is_valid(raw):
                                    continue
                                try:
                                    v = float(raw)
                                    val_str = f"{v:g}{nunit}"
                                except (TypeError, ValueError):
                                    val_str = str(raw)
                                ncols3[ci % 3].metric(nlabel, val_str)
                                ci += 1

                    # 옵션 선택 (expander 안 버튼식)
                    if options:
                        _selected_count = sum(st.session_state.get(f"opt_{panel}_{name}_{oi}", 0) for oi in range(len(options)))
                        _exp_label = f"⚙️ 옵션 선택" + (f" · {_selected_count}개 선택됨" if _selected_count > 0 else "")
                        with st.expander(_exp_label, expanded=False):
                          for oi, opt in enumerate(options):
                            oname  = opt.get("name", "")
                            oprice = opt.get("price_won", 0)
                            omax   = opt.get("max_quantity") or 10
                            sk = f"opt_{panel}_{name}_{oi}"
                            if sk not in st.session_state:
                                st.session_state[sk] = 0
                            cur_qty = st.session_state[sk]
                            st.markdown(
                                f'<div style="font-size:.8em;color:#5C4A3A;margin:3px 0 1px">'
                                f'<b>{oname}</b> <span style="color:#C9A55A">(+{oprice:,}원)</span>'
                                + (f' <span style="color:#9A8070">최대{omax}개</span>' if opt.get("max_quantity") else '')
                                + '</div>',
                                unsafe_allow_html=True
                            )
                            oc1, oc2, oc3 = st.columns([1, 1, 1])
                            if oc1.button("−", key=f"{sk}_minus", use_container_width=True):
                                if cur_qty > 0:
                                    st.session_state[sk] = cur_qty - 1
                                    st.rerun()
                            oc2.markdown(f"<div style='text-align:center;padding:5px 0;font-weight:700'>{cur_qty}</div>", unsafe_allow_html=True)
                            if oc3.button("＋", key=f"{sk}_plus", use_container_width=True):
                                if cur_qty < omax:
                                    st.session_state[sk] = cur_qty + 1
                                    st.rerun()

                    # 주의 문구
                    if is_valid(caution):
                        st.markdown(
                            f'<div class="mc-warn">⚠️ {caution}</div>',
                            unsafe_allow_html=True
                        )

                    # 담기 버튼
                    if isinstance(price, (int, float)) and price > 0:
                        cart_key = f"qp_{panel}_{name}"
                        if st.button("🛒 담기", key=cart_key, use_container_width=True, type="primary"):
                            selected_opts = []
                            for oi, opt in enumerate(options):
                                sk = f"opt_{panel}_{name}_{oi}"
                                qty_sel = st.session_state.get(sk, 0)
                                if qty_sel > 0:
                                    selected_opts.append({
                                        "name": opt.get("name", ""),
                                        "price": opt.get("price_won", 0),
                                        "qty": qty_sel,
                                    })
                            cart_add(name, int(price), 1, selected_opts if selected_opts else None)
                            for oi in range(len(options)):
                                sk = f"opt_{panel}_{name}_{oi}"
                                if sk in st.session_state:
                                    st.session_state[sk] = 0
                            add_labels = {
                                "ko": f"✅ '{name}' 담겼어요!",
                                "en": f"✅ '{name}' added!",
                                "cn": f"✅ '{name}' 已加入！",
                                "jp": f"✅ '{name}' 追加しました！",
                            }
                            st.toast(add_labels.get(lang, add_labels["ko"]))
                            st.rerun()


# ─────────────────────────  메인  ─────────────────────────────
def main():
    if not HAS_OPENAI:
        st.error("openai 패키지가 필요합니다: `pip install openai`")
        return

    init_state()
    render_sidebar()

    # ── 직원 호출 알림 배너 ──
    if st.session_state.get("staff_called"):
        st.markdown("""
        <div style="background:linear-gradient(135deg,#C9A55A,#E8C870);color:#1C110A;padding:12px 20px;border-radius:10px;
             font-weight:700;font-size:1.05em;text-align:center;margin-bottom:8px;
             box-shadow:0 2px 8px rgba(201,165,90,0.3)">
        🔔 직원 호출 완료! 직원이 곧 도와드릴 거예요 😊
        </div>""", unsafe_allow_html=True)

    # ── 헤더 (언어 반영) ──
    lang_flags = {"ko": "🇰🇷", "en": "🇺🇸", "cn": "🇨🇳", "jp": "🇯🇵"}
    curr_lang = st.session_state.get("lang", "ko")
    st.markdown(f"""
    <div class="oji-header">
        <span class="logo-icon">☕</span>
        <h1>{t('welcome')}</h1>
        <p>{t('subtitle')}</p>
        <div class="lang-bar">
          <span class="lang-pill {"active" if curr_lang=="ko" else ""}">🇰🇷 KO</span>
          <span class="lang-pill {"active" if curr_lang=="en" else ""}">🇺🇸 EN</span>
          <span class="lang-pill {"active" if curr_lang=="cn" else ""}">🇨🇳 CN</span>
          <span class="lang-pill {"active" if curr_lang=="jp" else ""}">🇯🇵 JP</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not HAS_SKLEARN:
        st.warning("scikit-learn 없음 → 기본 키워드 검색으로 동작합니다. `pip install scikit-learn`")

    # ── 진상 감지 경고 ──
    if st.session_state.abuse_count >= 3:
        st.markdown(f'<div class="abuse-banner">⚠️ {t("abuse_warning")}</div>', unsafe_allow_html=True)

    # ── 결제 플로우 모드 ──
    if st.session_state.payment_stage is not None:
        render_payment_flow()
        return

    # ── 첫 인사 ──
    if not st.session_state.greeted:
        with st.spinner("오지 준비 중... ✨"):
            greeting = get_greeting()
        st.session_state.display_msgs.append(
            {"role": "assistant", "content": greeting, "feedback": None, "staff_call": False}
        )
        st.session_state.greeted = True

    # ── 퀵 액션 버튼 행 (채팅 위에 고정) ──
    qa_cols = st.columns(len(QUICK_ACTIONS))
    for i, (icon, label_key, key) in enumerate(QUICK_ACTIONS):
        active = st.session_state.quick_panel == key
        btn_type = "primary" if active else "secondary"
        # t(label_key)를 사용해서 다국어 적용!
        if qa_cols[i].button(f"{icon} {t(label_key)}", key=f"qa_{key}",
                             use_container_width=True, type=btn_type):
            st.session_state.quick_panel = None if active else key
    
    # qa_cols = st.columns(len(QUICK_ACTIONS))
    # for i, (icon, label, key) in enumerate(QUICK_ACTIONS):
    #     active = st.session_state.quick_panel == key
    #     btn_type = "primary" if active else "secondary"
    #     if qa_cols[i].button(f"{icon} {label}", key=f"qa_{key}",
    #                          use_container_width=True, type=btn_type):
    #         st.session_state.quick_panel = None if active else key
    #         # st.rerun() 불필요: st.button() 클릭이 이미 자동으로 rerun 트리거

    # ── 퀵 패널 (버튼 바로 아래, 채팅보다 위) ──
    if st.session_state.quick_panel:
        with st.container(height=560, border=False):
            render_quick_panel()
        st.markdown("---")

    # ── 대화 출력 ──
    render_messages()

    # ── 사용자 입력 ──
    user_input = st.chat_input(t("chat_placeholder"))
    if user_input:
        st.session_state.display_msgs.append(
            {"role": "user", "content": user_input, "feedback": None, "staff_call": False}
        )
        with st.spinner("오지가 답변 준비 중... ✨"):
            reply, staff_call = chat(user_input)
        st.session_state.display_msgs.append(
            {"role": "assistant", "content": reply, "feedback": None, "staff_call": staff_call}
        )
        st.rerun()

if __name__ == "__main__":
    main()
