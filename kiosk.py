"""
빽다방 AI 키오스크 — 빽이 (Paikki)
RAG-based Natural Language Kiosk Interface
"""
import json
import math
import re
import os
import streamlit as st
from bs4 import BeautifulSoup

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
.paikki-header {
    background: linear-gradient(135deg, #C62828 0%, #E53935 100%);
    color: white; padding: 28px 40px; border-radius: 18px;
    text-align: center; margin-bottom: 20px;
    box-shadow: 0 6px 20px rgba(198,40,40,0.35);
}
.paikki-header h1 { font-size: 2.6em; margin: 0; letter-spacing: 3px; }
.paikki-header p  { margin: 6px 0 0; font-size: 1.1em; opacity: 0.92; }
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
</style>
""", unsafe_allow_html=True)

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
2. 가격·영양성분은 반드시 RAG 데이터의 실제 값만 사용하세요.
3. 없는 데이터는 "해당 정보를 찾을 수 없어요 😅" 로 안내하세요.
4. 추가 옵션(샷 추가, 시럽 등) 상세는 "매장 직원에게 문의해 주세요" 로 안내하세요.
5. 주문 의향이 명확하면 자연스럽게 add_to_cart를 호출하세요.
6. 절대 감정적으로 반응하지 마세요. 항상 정중하게 응대하세요.
7. 응답은 간결하고 명확하게, 필요한 경우 리스트/표로 정리하세요.
"""

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
def load_price_map() -> dict[str, int]:
    def normalize(name: str) -> str:
        return re.sub(r"\s*\(", "(", name)
    price_map: dict[str, int] = {}
    try:
        with open("price.html", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        for sec in soup.find_all("div", class_="single-menu"):
            for item in sec.find_all("div", class_="menuitem"):
                name_div = item.find("div", class_="itemtitle-wrapper")
                if not name_div:
                    continue
                name = name_div.get_text(strip=True)
                full_text = item.get_text(separator=" ", strip=True)
                m = re.search(r"([\d,]+)원", full_text)
                if m:
                    price_map[normalize(name)] = int(m.group(1).replace(",", ""))
    except FileNotFoundError:
        pass
    return price_map

@st.cache_data
def load_menu_data():
    try:
        with open("paikdabang_menu_dom.json", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    def normalize(n): return re.sub(r"\s*\(", "(", n)
    pm = load_price_map()
    for item in data:
        item["price_won"] = pm.get(normalize(item.get("menu_name", "")))
    return data

@st.cache_data
def load_news_data():
    try:
        with open("paikdabang_news.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# ─────────────────────────  RAG 문서 구성  ────────────────────
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
            f"알레르기:{alg if is_valid(alg) else '없음'}\n"
            f"영양성분:{nut}\n"
            f"주의:{caut if is_valid(caut) else '-'}"
        )

        docs.append({
            "text": text, "name": name, "price": price, "category": cat,
            "is_decaf": is_decaf, "is_best": is_best,
        })

    # 소식/이벤트 문서
    for ni in news:
        text = (
            f"소식/이벤트\n"
            f"제목:{ni.get('title','')}\n"
            f"분류:{ni.get('category','')}\n"
            f"날짜:{ni.get('date','')}\n"
            f"조회:{ni.get('views',0)}\n"
            f"링크:{ni.get('url','')}"
        )
        docs.append({"text": text, "name": ni.get("title",""), "price": None,
                     "category": "소식", "is_decaf": False, "is_best": False})

    # 옵션 안내 문서
    docs.append({
        "text": (
            "빽다방 메뉴 옵션 안내\n"
            "HOT/ICED 선택 가능(메뉴에 따라)\n"
            "디카페인 버전: 아메리카노/카페라떼/바닐라라떼 등 일부 메뉴\n"
            "빽사이즈: 대용량 버전(아메리카노/카페라떼/원조커피 등)\n"
            "추가 샷/시럽/두유 변경 등: 매장 직원 문의\n"
            "결제: 카드/현금/모바일페이\n"
            "알레르기: 우유/대두/복숭아 등 - 각 메뉴 정보 참조"
        ),
        "name": "옵션안내", "price": None, "category": "안내",
        "is_decaf": False, "is_best": False,
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
        "api_messages": [{"role": "system", "content": SYSTEM_PROMPT}],
        "display_msgs": [],   # {"role", "content", "feedback": None/"good"/"bad"}
        "cart": [],
        "feedback": {"good": 0, "bad": 0},
        "order_done": False,
        "greeted": False,
        "test_idx": 0,
        "abuse_count": 0,    # 진상 감지 카운터
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
        pm = args.get("payment_method", "카드")
        st.session_state.order_done = True
        return f"주문완료: 결제방법={pm}, 총액={cart_total():,}원"
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
            temperature=0.75,
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
            temperature=0.75,
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
    if not client:
        return "안녕하세요! 빽다방 키오스크 빽이입니다 ☕ API 키를 입력하시면 대화를 시작할 수 있습니다!"
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "키오스크에 새 고객이 왔어. 빽다방스럽고 따뜻하게 2~3문장으로 짧게 인사해줘."},
            ],
            temperature=0.85, max_tokens=120,
        )
        return r.choices[0].message.content
    except Exception:
        return "안녕하세요! 빽다방 키오스크 빽이입니다 ☕ 싸다! 크다! 맛있다! 오늘 어떤 음료 도와드릴까요? 😊"

# ─────────────────────────  사이드바 렌더링  ──────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("## ⚙️ 설정")

        # API 키
        api_key_in = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.get("api_key", ""),
            placeholder="sk-...",
        )
        if api_key_in:
            st.session_state.api_key = api_key_in

        if not (st.session_state.get("api_key") or os.getenv("OPENAI_API_KEY")):
            st.warning("API 키를 입력해야 빽이와 대화할 수 있어요!")
        else:
            st.success("API 키 연결됨 ✅")

        st.caption("💬 한국어 · English · 中文 · 日本語 모두 지원")
        st.divider()

        # ── 장바구니 ──
        st.markdown("## 🛒 장바구니")
        if st.session_state.cart:
            for idx, item in enumerate(st.session_state.cart):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"**{item['name']}**  \n`{item['price']:,}원` × {item['qty']}")
                if c2.button("✕", key=f"del_{idx}", help="제거"):
                    cart_remove(item["name"])
                    st.rerun()
            st.markdown(
                f'<div class="cart-total">합계: {cart_total():,}원</div>',
                unsafe_allow_html=True,
            )
            if st.button("🗑️ 전체 비우기", use_container_width=True):
                st.session_state.cart = []
                st.rerun()
        else:
            st.info("장바구니가 비어있어요 🛒")
        st.divider()

        # ── 응답 품질 피드백 통계 ──
        st.markdown("## 📊 응답 만족도")
        fb = st.session_state.feedback
        c1, c2 = st.columns(2)
        c1.metric("👍", fb["good"])
        c2.metric("👎", fb["bad"])
        total = fb["good"] + fb["bad"]
        if total > 0:
            st.progress(fb["good"] / total, text=f"만족도 {fb['good']/total*100:.0f}%")
        st.divider()

        # ── 진상 테스트 모드 ──
        st.markdown("## 🤖 돌발 시나리오 테스트")
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
        if st.button("🔄 대화 초기화", use_container_width=True):
            for k in ["api_messages", "display_msgs", "cart", "order_done",
                      "greeted", "test_idx", "abuse_count"]:
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
                st.caption("👍 피드백 감사합니다!")
            elif msg["feedback"] == "bad":
                st.caption("👎 의견 감사합니다. 더 나은 빽이가 될게요!")

# ─────────────────────────  메인  ─────────────────────────────
def main():
    if not HAS_OPENAI:
        st.error("openai 패키지가 필요합니다: `pip install openai`")
        return

    init_state()
    render_sidebar()

    # ── 헤더 ──
    st.markdown("""
    <div class="paikki-header">
        <h1>☕ 빽다방 키오스크</h1>
        <p>AI 직원 빽이(Paikki) · 싸다! 크다! 맛있다!</p>
    </div>
    """, unsafe_allow_html=True)

    if not HAS_SKLEARN:
        st.warning("scikit-learn 없음 → 기본 키워드 검색으로 동작합니다. `pip install scikit-learn`")

    # ── 진상 감지 경고 ──
    if st.session_state.abuse_count >= 3:
        st.error("⚠️ 불쾌한 표현이 감지됐습니다. 매장 직원을 호출해드릴까요?")

    # ── 주문 완료 화면 ──
    if st.session_state.order_done:
        st.markdown(
            f'<div class="order-done">'
            f'🎉 주문이 완료되었습니다!<br>'
            f'총 결제 금액: <b>{cart_total():,}원</b><br>'
            f'잠시 후 음료를 준비해 드릴게요 ☕</div>',
            unsafe_allow_html=True,
        )
        if st.button("🔄 새 주문 시작", use_container_width=True):
            for k in ["api_messages", "display_msgs", "cart", "order_done", "greeted", "abuse_count"]:
                st.session_state.pop(k, None)
            st.rerun()
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
    user_input = st.chat_input(
        "메뉴를 물어보거나 주문해보세요 · 예: 달달한 음료 추천해줘"
    )
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
