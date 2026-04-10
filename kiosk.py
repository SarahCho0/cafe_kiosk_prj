"""
빽다방 AI 키오스크 — 빽이 (Paikki)
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
    page_title="빽다방 키오스크 ☕",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────  CSS  ──────────────────────────────
st.markdown("""
<style>
/* ── 헤더 ── */
.paikki-header {
    background: linear-gradient(135deg, #C62828 0%, #E53935 100%);
    color: white; padding: 22px 40px 16px; border-radius: 18px;
    text-align: center; margin-bottom: 16px;
    box-shadow: 0 6px 20px rgba(198,40,40,0.35);
}
.paikki-header h1 { font-size: 2.4em; margin: 0; letter-spacing: 3px; }
.paikki-header p  { margin: 4px 0 0; font-size: 1em; opacity: 0.92; }
/* ── 언어 버튼 ── */
.lang-bar { display:flex; gap:8px; justify-content:center; margin-top:10px; }
.lang-pill {
    padding:4px 14px; border-radius:20px; font-size:.88em; font-weight:700;
    background:rgba(255,255,255,0.22); color:#fff; cursor:pointer;
    border:2px solid transparent;
}
.lang-pill.active { background:#fff; color:#C62828; border-color:#fff; }
/* ── 장바구니 ── */
.cart-box {
    background: #fff8f8; border: 1px solid #ffcdd2;
    border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
}
.cart-total {
    background: #C62828; color: white;
    padding: 10px 18px; border-radius: 8px;
    text-align: center; font-weight: bold; font-size: 1.15em; margin-top: 8px;
}
.order-done {
    background: #e8f5e9; border: 2px solid #43a047;
    border-radius: 12px; padding: 20px; text-align: center;
    font-size: 1.2em; margin: 16px 0;
}
/* ── 결제 진행 표시기 ── */
.payment-progress {
    display:flex; align-items:center; justify-content:center;
    gap:0; margin:0 auto 24px; max-width:900px; flex-wrap:nowrap;
    padding:16px; background:#fff8f8; border-radius:12px;
    border:1px solid #ffcdd2;
}
.step-item { display:flex; flex-direction:column; align-items:center; gap:4px; }
.step-dot {
    width:32px; height:32px; border-radius:50%; display:flex;
    align-items:center; justify-content:center; font-weight:700; font-size:.82em;
    background:#e0e0e0; color:#999; flex-shrink:0;
}
.step-dot.active { background:#C62828; color:#fff; box-shadow:0 2px 8px rgba(198,40,40,0.4); }
.step-dot.done   { background:#43a047; color:#fff; }
.step-label { font-size:.68em; color:#666; white-space:nowrap; max-width:70px; text-align:center; }
.step-connector { width:28px; height:3px; background:#e0e0e0; margin-bottom:16px; flex-shrink:0; }
.step-connector.done { background:#43a047; }
/* ── 결제 수단 카드 ── */
.pay-method-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin:16px 0; }
.pay-method-card {
    border:2px solid #e0e0e0; border-radius:14px; padding:20px 14px;
    text-align:center; cursor:pointer; transition:all .2s;
    background:#fafafa;
}
.pay-method-card:hover { border-color:#C62828; background:#fff5f5; transform:translateY(-2px); }
.pay-method-card .icon { font-size:2.2em; margin-bottom:6px; }
.pay-method-card .name { font-weight:700; font-size:1.05em; color:#333; }
.pay-method-card .desc { font-size:.78em; color:#888; margin-top:2px; }
/* ── 결제 처리 ── */
.processing-box {
    text-align:center; padding:48px 24px;
    background:linear-gradient(135deg,#fff8f8,#fff); border-radius:16px;
    border:1px solid #ffcdd2;
}
.processing-spinner { font-size:3em; animation:spin 1s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
/* ── 성공/실패 ── */
.success-box {
    text-align:center; padding:40px 24px; background:#e8f5e9;
    border:2px solid #43a047; border-radius:16px; margin:16px 0;
}
.failure-box {
    text-align:center; padding:40px 24px; background:#fff3e0;
    border:2px solid #ff9800; border-radius:16px; margin:16px 0;
}
/* ── 주문번호 ── */
.order-number-badge {
    display:inline-block; background:#C62828; color:#fff;
    font-size:2.8em; font-weight:900; padding:14px 40px;
    border-radius:16px; letter-spacing:6px; margin:16px 0;
    box-shadow:0 4px 16px rgba(198,40,40,0.35);
}
/* ── 대기 화면 ── */
.waiting-screen {
    text-align:center; padding:48px 24px;
    background:linear-gradient(135deg,#fff8f8,#fff);
    border-radius:16px; border:1px solid #ffcdd2;
}
/* ── 매장 정보 ── */
.store-card {
    background:#fff; border:1px solid #ffcdd2; border-radius:12px;
    padding:16px; margin-bottom:10px;
}
.store-card h3 { color:#C62828; margin:0 0 10px; font-size:1.1em; }
.store-row { display:flex; gap:8px; margin:5px 0; font-size:.88em; }
.store-icon { width:20px; flex-shrink:0; }
.facility-tag {
    display:inline-block; background:#fff0f0; color:#C62828;
    border:1px solid #ffcdd2; border-radius:12px;
    padding:2px 10px; font-size:.78em; margin:2px;
}
/* ── 직원 문의 ── */
.staff-card {
    background:#fffde7; border:1px solid #f9a825; border-radius:12px;
    padding:14px; margin-bottom:10px;
}
.staff-card h3 { color:#f57f17; margin:0 0 8px; font-size:.98em; }
.staff-item {
    background:#fff; border:1px solid #ffe082; border-radius:8px;
    padding:6px 12px; margin:4px 0; font-size:.84em; cursor:default;
    display:flex; align-items:center; gap:8px;
}
/* ── 결제 단계 제목 ── */
.pay-step-title {
    color:#C62828; font-size:1.5em; font-weight:800;
    margin:0 0 18px; padding-bottom:10px;
    border-bottom:2px solid #ffcdd2;
}
/* ── 주문타입 버튼 ── */
.order-type-btn {
    border:3px solid #e0e0e0; border-radius:16px; padding:28px 16px;
    text-align:center; font-size:1.15em; font-weight:700; cursor:pointer;
    transition:all .2s; background:#fafafa; width:100%;
}
.order-type-btn:hover { border-color:#C62828; background:#fff5f5; }
/* ── QR 코드 흉내 ── */
.qr-box {
    display:inline-block; border:3px solid #333; border-radius:8px;
    padding:16px; font-size:72px; line-height:1; margin:12px auto;
    background:#fff;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────  STORE INFO (낙성점)  ─────────────
STORE_INFO = {
    "name_ko": "빽다방 낙성점",
    "name_en": "Paik's Coffee Nakseong",
    "name_cn": "白咖啡 洛星店",
    "name_jp": "ペクコーヒー 洛星店",
    "address": "서울 관악구 남부순환로 1919 1층",
    "direction_ko": "낙성대역 5번출구 바로 앞에 위치하고 있습니다^^",
    "direction_en": "Right in front of Exit 5, Nakseongdae Station",
    "direction_cn": "位于落星台站5号出口正前方",
    "direction_jp": "落星台駅5番出口のすぐ前",
    "subway_ko": "2호선 낙성대역 5번 출구 34m",
    "subway_en": "Line 2 Nakseongdae Stn. Exit 5 · 34m",
    "subway_cn": "2号线落星台站5号出口 34m",
    "subway_jp": "2号線落星台駅5番出口 34m",
    "hours_ko": "22:00 라스트오더",
    "hours_en": "Last Order 22:00",
    "hours_cn": "最后点单 22:00",
    "hours_jp": "ラストオーダー 22:00",
    "phone": "02-884-5585",
    "facilities_ko": ["단체 이용 가능", "포장", "주차"],
    "facilities_en": ["Group Use", "Takeout", "Parking"],
    "facilities_cn": ["团体使用", "打包", "停车"],
    "facilities_jp": ["団体利用可", "テイクアウト", "駐車場"],
}

# ─────────────────────────  TRANSLATIONS  ────────────────────
TRANSLATIONS: dict[str, dict[str, object]] = {
    "ko": {
        "welcome": "빽다방 키오스크",
        "subtitle": "AI 직원 빽이(Paikki) · 싸다! 크다! 맛있다!",
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
        "api_warning": "API 키를 입력해야 빽이와 대화할 수 있어요!",
        "lang_support": "💬 한국어 · English · 中文 · 日本語",
        "satisfaction": "📊 응답 만족도",
        "test_mode": "🤖 돌발 시나리오 테스트",
        "chat_placeholder": "메뉴를 물어보거나 주문해보세요 · 예: 달달한 음료 추천해줘",
        "abuse_warning": "⚠️ 불쾌한 표현이 감지됐습니다. 매장 직원을 호출해드릴까요?",
        "feedback_good": "👍 피드백 감사합니다!",
        "feedback_bad": "👎 의견 감사합니다. 더 나은 빽이가 될게요!",
        "currently_open": "영업 중",
    },
    "en": {
        "welcome": "Paik's Coffee Kiosk",
        "subtitle": "AI Staff Paikki · Affordable! Big! Delicious!",
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
        "api_warning": "Please enter your API key to chat with Paikki!",
        "lang_support": "💬 KO · EN · CN · JP Supported",
        "satisfaction": "📊 Response Rating",
        "test_mode": "🤖 Scenario Testing",
        "chat_placeholder": "Ask about the menu or place an order · e.g. Recommend something sweet",
        "abuse_warning": "⚠️ Inappropriate language detected. Shall we call a staff member?",
        "feedback_good": "👍 Thanks for your feedback!",
        "feedback_bad": "👎 Thanks! We'll keep improving.",
        "currently_open": "Open Now",
    },
    "cn": {
        "welcome": "白咖啡自助点餐机",
        "subtitle": "AI店员小白 · 便宜！大杯！好喝！",
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
        "api_warning": "请输入API密钥以与小白对话！",
        "lang_support": "💬 支持多语言",
        "satisfaction": "📊 满意度",
        "test_mode": "🤖 场景测试",
        "chat_placeholder": "询问菜单或点餐 · 例：推荐甜味饮料",
        "abuse_warning": "⚠️ 检测到不当语言，需要呼叫店员吗？",
        "feedback_good": "👍 感谢您的反馈！",
        "feedback_bad": "👎 感谢！我们会不断改进。",
        "currently_open": "营业中",
    },
    "jp": {
        "welcome": "ペクコーヒー キオスク",
        "subtitle": "AIスタッフ・ペッキ · 安い！大きい！美味しい！",
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
        "api_warning": "ペッキと話すにはAPIキーを入力してください！",
        "lang_support": "💬 多言語対応",
        "satisfaction": "📊 満足度",
        "test_mode": "🤖 シナリオテスト",
        "chat_placeholder": "メニューを聞くか注文してください",
        "abuse_warning": "⚠️ 不適切な言葉が検出されました。スタッフを呼びますか？",
        "feedback_good": "👍 フィードバックありがとうございます！",
        "feedback_bad": "👎 ご意見ありがとうございます！",
        "currently_open": "営業中",
    },
}

def t(key: str) -> str:
    """현재 언어로 번역된 텍스트 반환"""
    lang = st.session_state.get("lang", "ko")
    d = TRANSLATIONS.get(lang, TRANSLATIONS["ko"])
    return d.get(key, TRANSLATIONS["ko"].get(key, key))

# ─────────────────────────  SYSTEM PROMPT (HTI 구조)  ─────────
SYSTEM_PROMPT = """당신은 빽다방(Baek's Coffee)의 AI 키오스크 직원 '빽이(Paikki)'입니다.

## 페르소나
- 이름: 빽이 (Paikki)
- 브랜드 슬로건: "싸다! 크다! 맛있다!"
- 성격: 밝고 친절하며 유능함, 빽다방 브랜드에 자부심이 있음
- 말투: 정중한 존댓말, 따뜻하고 활기차게, 이모지 자연스럽게 사용

## Hierarchical Task Inventory (HTI)

### [L1] 정보 제공
- [L2] 메뉴 정보 조회
  - [L3] 가격 안내
  - [L3] 메뉴 설명 및 특징
  - [L3] 영양성분 (칼로리, 카페인, 당류, 나트륨, 단백질)
  - [L3] 알레르기 정보
  - [L3] 용량/사이즈
- [L2] 카테고리 탐색 (커피/신메뉴/음료/빽스치노/아이스크림·디저트)
- [L2] 이벤트·소식 안내
- [L2] 매장 정보 안내
  - [L3] 주소, 전화번호, 영업시간
  - [L3] 좌석 정보 (총 좌석 수, 실내/야외 구분)
  - [L3] 화장실 위치 및 편의시설
  - [L3] 주차, 배달, 결제수단 등

### [L1] 추천 서비스
- [L2] 취향 기반: 달달한/쓴/시원한/따뜻한/가벼운/진한 등
- [L2] 조건 기반: 디카페인, 저칼로리, 고카페인, 빽사이즈(대용량)
- [L2] 메뉴 비교: A vs B 비교 요청
- [L2] 인기/베스트 메뉴 추천

### [L1] 주문 처리
- [L2] 장바구니 추가 (add_to_cart 함수)
- [L2] 장바구니 수정 (remove_from_cart 함수)
- [L2] 주문 완료 및 결제 안내 (complete_order 함수)

### [L1] 다국어 응대
- [L2] 한국어 (기본)
- [L2] English: detect and respond in English
- [L2] 中文: 检测到中文时用中文回复
- [L2] 日本語: 日本語が検出されたら日本語で返答

### [L1] 특수·돌발 상황
- [L2] 공격적/무례한 고객 (진상): 침착·정중하게 응대, 3회 반복 시 매장 직원 호출 제안
- [L2] 불가능한 요청 (메뉴에 없는 것): 정중 안내 후 유사 메뉴 제안
- [L2] 카페 무관 질문: "저는 빽다방 키오스크 빽이예요! 음료/디저트 주문만 도와드릴 수 있어요 ☕" 로 부드럽게 전환
- [L2] 이해 불가 입력: 친절하게 재질문
- [L2] 시스템 한계: "매장 직원을 호출해드릴까요?"

## 응답 원칙
1. [메뉴 정보]에 제공된 RAG 데이터만 기반으로 답변하세요.
2. **가격·영양성분은 반드시 RAG 데이터의 실제 값만 사용하세요.**
3. **가격 안내 시 필수**: 메뉴명과 정확한 가격을 항상 함께 표시하세요. (예: 아메리카노(HOT) 3,300원)
4. 없는 데이터는 "해당 정보를 찾을 수 없어요 😅" 로 안내하세요.
5. 추가 옵션(샷 추가, 시럽, 두유 변경, 펄 추가 등)은 [메뉴 정보]의 options 또는 option_summary에 있는 값만 기준으로 안내하세요.
6. **매장 정보 질문** (화장실, 좌석, 주차, 영업시간 등): RAG에서 검색하여 정확한 정보 제공하세요.
7. 주문 의향이 명확하면 자연스럽게 add_to_cart를 호출하세요.
8. 절대 감정적으로 반응하지 마세요. 항상 정중하게 응대하세요.
9. 응답은 간결하고 명확하게, 필요한 경우 리스트/표로 정리하세요.
"""

# ─────────────────────────  언어별 SYSTEM PROMPT  ───────────────
SYSTEM_PROMPTS = {
    "한": SYSTEM_PROMPT,
    "영": """You are Paikki, the AI kiosk staff at Baek's Coffee (빽다방).

## Persona
- Name: Paikki
- Brand Slogan: "Cheap! Big! Delicious!"
- Personality: Bright, friendly, and competent. Takes pride in the Baek's Coffee brand.
- Tone: Polite, formal speech. Warm and energetic. Use emojis naturally.

## Hierarchical Task Inventory (HTI)

### [L1] Information Provision
- [L2] Menu Information Inquiry
  - [L3] Price guidance
  - [L3] Menu description and features
  - [L3] Nutrition info (calories, caffeine, sugar, sodium, protein)
  - [L3] Allergen information
  - [L3] Volume/size
- [L2] Category exploration
- [L2] Event/news announcements
- [L2] Store information (location, hours, seating, restroom, parking, etc.)

### [L1] Recommendation Service
- [L2] Preference-based: sweet/bitter/cold/hot/light/rich
- [L2] Condition-based: decaf, low-calorie, high-caffeine, large size
- [L2] Popular menu recommendations

### [L1] Order Processing
- [L2] Add to cart, remove from cart, complete order

### [L1] Multilingual Support
- [L2] English (current)
- [L2] 한국어, 中文, 日本語 supported

## Response Principles
1. Answer based ONLY on RAG data provided in [Menu Info].
2. **Always display exact prices with menu names.**
3. For unknown info: "I'm sorry, I couldn't find that information 😅"
4. Detailed option questions: "Please ask our staff"
5. Always remain polite, never emotional.
6. Keep responses concise and clear. Use lists/tables when helpful.""",
    "중": """你是Paikki，Baek's Coffee(빽다방)的AI自动售货员。

## 人设
- 姓名: Paikki
- 品牌标语: "便宜!大!好吃!"
- 性格: 开朗、友好、能干。为Baek's Coffee品牌感到自豪。
- 说话方式: 敬语，温暖而充满活力。自然使用表情符号。

## 分层任务库(HTI)

### [L1] 信息提供
- [L2] 菜单查询
  - [L3] 价格指导
  - [L3] 菜单描述和特点
  - [L3] 营养信息(卡路里、咖啡因、糖、钠、蛋白质)
  - [L3] 过敏原信息
  - [L3] 容量/规格

### [L1] 推荐服务
- [L2] 基于偏好的建议
- [L2] 基于条件的建议(无咖啡因、低热量等)
- [L2] 流行菜单推荐

### [L1] 订单处理
- 加入购物车、移除、完成订单

## 响应原则
1. 仅基于RAG数据回答
2. **始终显示确切的价格**
3. 对于未知信息："抱歉，我找不到那个信息 😅"
4. 详细问题咨询员工
5. 保持礼貌，从不情绪化
6. 简洁清晰，必要时使用列表或表格""",
    "일": """あなたはPaikki、Baek's Coffee(빽다방)のAIキオスク店員です。

## ペルソナ
- 名前: Paikki
- ブランドスローガン: "安い!大きい!美味しい!"
- 性格: 明るく、親切で有能です。Baek's Coffeeブランドを誇りに思っています。
- 話し方: 敬語。温かくエネルギッシュ。絵文字を自然に使用します。

## 階層的タスクインベントリ(HTI)

### [L1] 情報提供
- [L2] メニュー情報問い合わせ
  - [L3] 価格ガイダンス
  - [L3] メニューの説明と特徴
  - [L3] 栄養情報(カロリー、カフェイン、砂糖、ナトリウム、タンパク質)
  - [L3] アレルギー情報
  - [L3] ボリューム/サイズ

### [L1] 推奨サービス
- [L2] 好みに基づいた推奨
- [L2] 条件に基づいた推奨
- [L2] 人気メニュー推奨

### [L1] 注文処理
- カートに追加、削除、注文完了

## 応答原則
1. 提供されたRAGデータのみに基づいて答えてください
2. **常に正確な価格をメニュー名と共に表示してください**
3. 未知の情報："申し訳ございませんが、その情報は見つかりませんでした 😅"
4. 詳細な質問はスタッフにお問い合わせください
5. 常に礼儀正しく、感情的にならないこと
6. 簡潔で明確に。必要に応じてリストまたはテーブルを使用"""
}

def get_system_prompt(language: str) -> str:
    """선택한 언어에 맞는 SYSTEM_PROMPT 반환"""
    return SYSTEM_PROMPTS.get(language, SYSTEM_PROMPT)

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
    options_text = "빽다방 메뉴 옵션 안내\n"
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
            f"빽다방 메뉴 통계\n"
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
            f"빽다방 낙성점 매장 정보\n"
            f"주소: {store.get('address', '정보 없음')}\n"
            f"전화: {store.get('phone', '정보 없음')}\n"
            f"영업시간: 평일 {hours.get('weekday_start', '-')} ~ {hours.get('weekday_end', '-')}, "
            f"주말 {hours.get('weekend_start', '-')} ~ {hours.get('weekend_end', '-')}\n"
            f"좌석: 총 {seating.get('total_seats', '정보 없음')}석 (실내 {seating.get('inside_seats', '정보 없음')}석, "
            f"야외 {seating.get('outside_seats', '정보 없음')}석)\n"
            f"좌석 설명: {seating.get('seats_description', '정보 없음')}\n"
            f"화장실: {restroom.get('location', '정보 없음')} ({restroom.get('accessibility', '정보 없음')})\n"
            f"주차: {parking.get('type', '정보 없음')} - {parking.get('fee', '정보 없음')}\n"
            f"무선인터넷: {'있음' if store.get('facilities', {}).get('wifi', {}).get('available') else '없음'}\n"
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
    top_idx = sims.argsort()[-k:][::-1]
    result = "\n\n---\n\n".join(docs[i]["text"] for i in top_idx if sims[i] > 0.005)
    return result or "관련 메뉴 정보 없음"

# ─────────────────────────  장바구니  ─────────────────────────
def cart_add(name: str, price: int, qty: int = 1):
    for item in st.session_state.cart:
        if item["name"] == name:
            item["qty"] += qty
            return
    st.session_state.cart.append({"name": name, "price": price, "qty": qty})

def cart_remove(name: str):
    st.session_state.cart = [i for i in st.session_state.cart if i["name"] != name]

def cart_total() -> int:
    return sum(i["price"] * i["qty"] for i in st.session_state.cart)

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
        # None | "cart_confirm" | "order_type" | "options"
        # | "payment_select" | "payment_detail"
        # | "processing" | "success" | "failure"
        # | "order_complete" | "waiting"
        "payment_stage": None,
        "order_type": None,          # "table" | "takeout"
        "receipt_option": "no",      # "print" | "email" | "no"
        "payment_plan": [],          # [{"method": str, "amount": int}]
        "partial_paid": 0,           # 복합결제 시 이미 처리된 금액
        "current_payment_method": None,
        "order_number": None,
        "payment_failure_reason": "",
        "coupon_input": "",
        "points_input": 0,
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

def chat(user_input: str) -> str:
    client = get_client()
    if not client:
        return "⚠️ 사이드바에서 OpenAI API 키를 입력해주세요."

    # ── 욕설/진상 간단 감지 ──
    abuse_keywords = ["빨리", "짜증", "미쳤", "바보", "쓸모없", "환불", "바가지", "야"]
    if any(kw in user_input for kw in abuse_keywords):
        st.session_state.abuse_count += 1

    # ── RAG 검색 ──
    rag_ctx = retrieve(user_input)
    augmented = f"[메뉴 정보]\n{rag_ctx}\n\n[고객 질문]\n{user_input}"

    # ── 1차 API 호출 (with tools) ──
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
        return f"⚠️ API 오류: {e}"

    msg1 = r1.choices[0].message

    # ── 도구 호출 없으면 바로 반환 ──
    if not msg1.tool_calls:
        reply = msg1.content or "죄송해요, 다시 말씀해 주시겠어요? 😊"
        _update_history(user_input, reply)
        return reply

    # ── 도구 호출 처리 ──
    # assistant 메시지 (tool_calls 포함) 직렬화
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

    # ── 2차 API 호출 (최종 자연어 응답) ──
    try:
        r2 = get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_for_api,
            temperature=0,
            max_tokens=500,
        )
        reply = r2.choices[0].message.content or "\n".join(m["content"] for m in tool_results)
    except Exception:
        reply = "\n".join(m["content"] for m in tool_results)

    _update_history(user_input, reply)
    return reply

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
    language = st.session_state.get("language", "한")
    
    # 언어별 기본 인사말
    greeting_fallback = {
        "한": "안녕하세요! 빽다방 키오스크 빽이입니다 ☕ 싸다! 크다! 맛있다! 오늘 어떤 음료 도와드릴까요? 😊",
        "영": "Hello! I'm Paikki, the Baek's Coffee kiosk staff ☕ Cheap! Big! Delicious! What can I help you with today? 😊",
        "중": "你好！我是빽다방自动售货员Paikki ☕ 便宜!大!好吃!今天能为您做点什么呢? 😊",
        "일": "こんにちは！私はPaikki、빽다방のキオスク店員です ☕ 安い！大きい！美味しい！本日は何かお手伝いできることはありますか? 😊"
    }
    
    if not client:
        return greeting_fallback[language]
    
    # 메뉴 통계
    stats = get_menu_stats()
    cat_info = ", ".join([f"{cat} {cnt}개" for cat, cnt in sorted(stats["by_category"].items())])
    
    # 언어별 프롬프트
    greeting_prompts = {
        "한": f"키오스크에 새 고객이 왔어. 빽다방스럽고 따뜻하게 2~3문장으로 짧게 인사해줘. 현재 운영 중인 메뉴는 총 {stats['total']}개입니다: {cat_info}",
        "영": f"A new customer came to the kiosk. Greet them warmly in 2-3 sentences using Baek's Coffee's style. We currently have {stats['total']} menus available: {cat_info}. Ask if they have any questions.",
        "중": f"一位新顾客来到自动售货机。用2-3句话温暖地问候他们，并询问是否有任何问题。目前我们有{stats['total']}个菜单可用：{cat_info}",
        "일": f"新しいお客様がキオスクにいらっしゃいました。2～3文で温かく挨拶してください。現在利用可能なメニューは{stats['total']}個です：{cat_info}。何かお手伝いすることはありますか？"
    }
    
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": get_system_prompt(language)},
                {"role": "user", "content": greeting_prompts.get(language, greeting_prompts["한"])},
            ],
            temperature=0, max_tokens=120,
        )
        return r.choices[0].message.content
    except Exception:
        return greeting_fallback[language]

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
        c1.write(f"**{item['name']}**")
        with c2:
            q1, q2, q3 = st.columns(3)
            if q1.button("−", key=f"cc_minus_{idx}"):
                if item["qty"] > 1:
                    st.session_state.cart[idx]["qty"] -= 1
                else:
                    cart_remove(item["name"])
                st.rerun()
            q2.markdown(f"<div style='text-align:center;padding-top:6px'><b>{item['qty']}</b></div>", unsafe_allow_html=True)
            if q3.button("+", key=f"cc_plus_{idx}"):
                st.session_state.cart[idx]["qty"] += 1
                st.rerun()
        c3.write(f"{item['price'] * item['qty']:,} {t('won')}")
        if c4.button("✕", key=f"cc_del_{idx}"):
            cart_remove(item["name"])
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

    methods = [
        ("card",    "💳", t("pay_card"),    t("pay_card_desc")),
        ("qr",      "📱", t("pay_qr"),      t("pay_qr_desc")),
        ("cash",    "💵", t("pay_cash"),     t("pay_cash_desc")),
        ("voucher", "🎁", t("pay_voucher"),  t("pay_voucher_desc")),
    ]
    st.write("##### 결제 수단을 선택하세요")
    cols = st.columns(2)
    for i, (key, icon, name, desc) in enumerate(methods):
        with cols[i % 2]:
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

    if method == "card":
        st.markdown(f"""
        <div style="text-align:center;padding:24px">
          <div style="font-size:3.5em">💳</div>
          <h3>{t('card_tap')}</h3>
          <div style="background:#f5f5f5;border:2px dashed #C62828;border-radius:12px;
               padding:32px;margin:16px auto;max-width:300px;font-size:1.1em;color:#C62828">
          NFC / IC / MS<br><span style="font-size:.8em;color:#888">단말기에 올려주세요</span>
          </div>
        </div>""", unsafe_allow_html=True)

    elif method == "qr":
        st.markdown(f"""
        <div style="text-align:center;padding:16px">
          <h3>{t('qr_show')}</h3>
          <div style="display:inline-block;border:3px solid #333;border-radius:8px;
               padding:16px;font-size:64px;background:#fff;margin:12px auto">
          ▪▫▪▫<br>▫▪▫▪<br>▪▫▪▫
          </div>
          <p style="color:#888">카카오페이 · 네이버페이 · 토스 · 페이코</p>
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
            st.success(f"거스름돈: **{change:,}원**")

    elif method == "voucher":
        st.markdown(f"<div style='text-align:center'><div style='font-size:3em'>🎁</div><h3>{t('voucher_enter')}</h3></div>", unsafe_allow_html=True)
        vc = st.text_input("상품권 번호 (16자리)", max_chars=19, key="voucher_code",
                           placeholder="XXXX-XXXX-XXXX-XXXX")
        if vc:
            st.info(f"입력된 번호: `{vc}` · 확인 중...")

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
                st.error("올바른 상품권 번호를 입력해주세요.")
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
      <h1 style="color:#C62828">{t('order_complete_msg')}</h1>
      <p style="color:#555;font-size:1.1em">{t('order_number_label')}</p>
      <div class="order-number-badge">{order_no}</div>
    </div>""", unsafe_allow_html=True)

    # 결제 내역 요약
    with st.expander("📋 결제 내역", expanded=True):
        for item in st.session_state.cart:
            st.write(f"• {item['name']} × {item['qty']} = **{item['price']*item['qty']:,} {t('won')}**")
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
      <h1 style="color:#C62828">{order_no}번</h1>
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
        st.markdown(f"## {t('settings')}")
        st.divider()

        # ── API 키 ──
        api_key_in = st.text_input(
            t("api_key_label"),
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

        st.caption(t("lang_support"))
        st.divider()

        # ── 언어 선택 ──
        lang_map = {"ko": "🇰🇷 한국어", "en": "🇺🇸 English", "cn": "🇨🇳 中文", "jp": "🇯🇵 日本語"}
        st.markdown("**🌐 Language**")
        lang_cols = st.columns(4)
        for i, (code, label) in enumerate(lang_map.items()):
            btn_type = "primary" if st.session_state.get("lang", "ko") == code else "secondary"
            if lang_cols[i].button(label, key=f"lang_{code}", use_container_width=True, type=btn_type):
                st.session_state.lang = code
                st.session_state.api_messages[0]["content"] = get_system_prompt(code) # 시스템 프롬프트 업데이트 추가
                st.session_state.greeted = False
                st.rerun()
        st.divider()

        # ── 장바구니 ──
        st.markdown(f"## {t('cart_title')}")
        if st.session_state.cart:
            for idx, item in enumerate(st.session_state.cart):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"**{item['name']}**  \n`{item['price']:,}{t('won')}` × {item['qty']}")
                if c2.button("✕", key=f"del_{idx}", help="제거"):
                    cart_remove(item["name"])
                    st.rerun()
            st.markdown(
                f'<div class="cart-total">{t("total")}: {cart_total():,} {t("won")}</div>',
                unsafe_allow_html=True,
            )
            if st.session_state.payment_stage is None:
                if st.button(t("checkout"), use_container_width=True, type="primary"):
                    st.session_state.payment_stage = "cart_confirm"
                    st.session_state.partial_paid = 0
                    st.session_state.payment_plan = []
                    st.rerun()
            if st.button(t("clear_cart"), use_container_width=True):
                st.session_state.cart = []
                st.rerun()
        else:
            st.info(t("cart_empty"))
        st.divider()

        # ── 응답 만족도 ──
        st.markdown(f"## {t('satisfaction')}")
        fb = st.session_state.feedback
        c1, c2 = st.columns(2)
        c1.metric("👍", fb["good"])
        c2.metric("👎", fb["bad"])
        total_fb = fb["good"] + fb["bad"]
        if total_fb > 0:
            st.progress(fb["good"] / total_fb, text=f"만족도 {fb['good']/total_fb*100:.0f}%")
        st.divider()

        # ── 매장 정보 ──
        lang = st.session_state.get("lang", "ko")
        store_name = STORE_INFO.get(f"name_{lang}", STORE_INFO["name_ko"])
        direction  = STORE_INFO.get(f"direction_{lang}", STORE_INFO["direction_ko"])
        subway     = STORE_INFO.get(f"subway_{lang}", STORE_INFO["subway_ko"])
        hours      = STORE_INFO.get(f"hours_{lang}", STORE_INFO["hours_ko"])
        facilities = STORE_INFO.get(f"facilities_{lang}", STORE_INFO["facilities_ko"])
        fac_tags   = "".join(f'<span class="facility-tag">{f}</span>' for f in facilities)
        st.markdown(f"""
        <div class="store-card">
          <h3>📍 {store_name}</h3>
          <div class="store-row"><span class="store-icon">🏠</span><span>{STORE_INFO['address']}</span></div>
          <div class="store-row"><span class="store-icon">🚇</span><span>{subway}</span></div>
          <div class="store-row"><span class="store-icon">ℹ️</span><span>{direction}</span></div>
          <div class="store-row"><span class="store-icon">🕐</span>
            <span><b style="color:#43a047">{t('currently_open')}</b> · {hours}</span></div>
          <div class="store-row"><span class="store-icon">📞</span><span>{STORE_INFO['phone']}</span></div>
          <div class="store-row"><span class="store-icon">🏪</span><div>{fac_tags}</div></div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        # ── 직원 문의 영역 ──
        staff_items_html = "".join(
            f'<div class="staff-item">👤 {item}</div>'
            for item in t("staff_items")
        )
        st.markdown(f"""
        <div class="staff-card">
          <h3>{t('staff_inquiry')}</h3>
          <p style="font-size:.82em;color:#795548;margin:0 0 8px">{t('staff_note')}</p>
          {staff_items_html}
        </div>
        """, unsafe_allow_html=True)
        if st.button(t("call_staff"), key="sb_call_staff", use_container_width=True):
            st.warning("🔔 직원을 호출했습니다! 잠시만 기다려 주세요.")
        st.divider()

        # ── 돌발 시나리오 테스트 ──
        st.markdown(f"## {t('test_mode')}")
        test_mode = st.toggle("테스트 모드 ON", key="test_mode_toggle")
        if test_mode:
            idx = st.session_state.test_idx % len(ADVERSARIAL_SCENARIOS)
            st.info(f"**시나리오 {idx+1}/{len(ADVERSARIAL_SCENARIOS)}**\n\n> {ADVERSARIAL_SCENARIOS[idx]}")
            if st.button("▶️ 이 시나리오 실행", use_container_width=True):
                scenario = ADVERSARIAL_SCENARIOS[idx]
                st.session_state.display_msgs.append(
                    {"role": "user", "content": f"[테스트] {scenario}", "feedback": None}
                )
                with st.spinner("빽이 응답 중..."):
                    reply = chat(scenario)
                st.session_state.display_msgs.append(
                    {"role": "assistant", "content": reply, "feedback": None}
                )
                st.session_state.test_idx += 1
                st.rerun()
            if st.button("⏭️ 다음 시나리오", use_container_width=True):
                st.session_state.test_idx += 1
                st.rerun()
        st.divider()

        # ── 초기화 ──
        if st.button(t("reset"), use_container_width=True):
            for k in ["api_messages", "display_msgs", "cart", "order_done", "greeted",
                      "test_idx", "abuse_count", "payment_stage", "order_type",
                      "receipt_option", "payment_plan", "partial_paid",
                      "current_payment_method", "order_number",
                      "payment_failure_reason", "coupon_input", "points_input"]:
                st.session_state.pop(k, None)
            st.rerun()

# ─────────────────────────  채팅 메시지 렌더링  ───────────────
def render_messages():
    for i, msg in enumerate(st.session_state.display_msgs):
        role = msg["role"]
        avatar = "☕" if role == "assistant" else "🙂"
        with st.chat_message(role, avatar=avatar):
            st.write(msg["content"])

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

# ─────────────────────────  메인  ─────────────────────────────
def main():
    if not HAS_OPENAI:
        st.error("openai 패키지가 필요합니다: `pip install openai`")
        return

    init_state()
    render_sidebar()

    # ── 헤더 (언어 반영) ──
    lang_flags = {"ko": "🇰🇷", "en": "🇺🇸", "cn": "🇨🇳", "jp": "🇯🇵"}
    curr_flag  = lang_flags.get(st.session_state.get("lang", "ko"), "")
    st.markdown(f"""
    <div class="paikki-header">
        <h1>☕ {t('welcome')}</h1>
        <p>{t('subtitle')}</p>
        <div class="lang-bar">
          <span class="lang-pill {"active" if st.session_state.lang=="ko" else ""}">🇰🇷 KO</span>
          <span class="lang-pill {"active" if st.session_state.lang=="en" else ""}">🇺🇸 EN</span>
          <span class="lang-pill {"active" if st.session_state.lang=="cn" else ""}">🇨🇳 CN</span>
          <span class="lang-pill {"active" if st.session_state.lang=="jp" else ""}">🇯🇵 JP</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not HAS_SKLEARN:
        st.warning("scikit-learn 없음 → 기본 키워드 검색으로 동작합니다. `pip install scikit-learn`")

    # ── 진상 감지 경고 ──
    if st.session_state.abuse_count >= 3:
        st.error(t("abuse_warning"))

    # ── 결제 플로우 모드 ──
    if st.session_state.payment_stage is not None:
        render_payment_flow()
        return

    # ── 첫 인사 ──
    if not st.session_state.greeted:
        with st.spinner("빽이 준비 중... ☕"):
            greeting = get_greeting()
        st.session_state.display_msgs.append(
            {"role": "assistant", "content": greeting, "feedback": None}
        )
        st.session_state.greeted = True

    # ── 대화 출력 ──
    render_messages()

    # ── 사용자 입력 ──
    user_input = st.chat_input(t("chat_placeholder"))
    if user_input:
        st.session_state.display_msgs.append(
            {"role": "user", "content": user_input, "feedback": None}
        )
        with st.spinner("빽이가 답변 준비 중... ☕"):
            reply = chat(user_input)
        st.session_state.display_msgs.append(
            {"role": "assistant", "content": reply, "feedback": None}
        )
        st.rerun()

if __name__ == "__main__":
    main()
