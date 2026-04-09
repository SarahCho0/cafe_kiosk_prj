"""
빽다방 AI 키오스크 — 빽이 (Paikki)
RAG-based Natural Language Kiosk Interface
"""
import json
import math
import re
import os
from pathlib import Path
from typing import Any

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
.option-chip {
    display: inline-block; background: #fbe9e7; color: #8d3d2e;
    border-radius: 999px; padding: 2px 8px; margin: 2px 4px 2px 0;
    font-size: 0.85em;
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
  - [L3] 추가 옵션 안내 (샷 추가, 시럽, 두유 변경, 펄 추가 등)
- [L2] 카테고리 탐색 (커피/신메뉴/음료/빽스치노/아이스크림/디저트)
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
2. 가격·영양성분·옵션 가격은 반드시 RAG 데이터의 실제 값만 사용하세요.
3. 없는 데이터는 "해당 정보를 찾을 수 없어요 😅" 로 안내하세요.
4. 옵션 질문은 [메뉴 정보]의 options / option_summary를 우선 기준으로 안내하세요.
5. 고객이 옵션을 포함해 주문 의사를 명확히 밝히면 add_to_cart를 호출하고, selected_options에도 반영하세요.
6. 절대 감정적으로 반응하지 마세요. 항상 정중하게 응대하세요.
7. 응답은 간결하고 명확하게, 필요한 경우 리스트/표로 정리하세요.
8. 메뉴에 없는 옵션은 임의로 만들어내지 말고 정중하게 불가 안내하세요.
"""

MENU_FILE_CANDIDATES = [
    "paikdabang_menu_rev.json",
    "paikdabang_menu.json",
    "paikdabang_menu_master_filled_clean.json",
    "paikdabang_menu_master_filled.json",
    "paikdabang_menu_dom.json",
]

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
                    "price_won": {"type": "integer", "description": "기본 메뉴 가격 (원)"},
                    "quantity": {"type": "integer", "description": "수량 (기본값 1)", "default": 1},
                    "selected_options": {
                        "type": "array",
                        "description": "선택한 옵션 목록. 예: [{'name':'에스프레소 샷 추가','quantity':2},{'name':'두유로 변경','quantity':1}]",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "옵션 이름"},
                                "quantity": {"type": "integer", "description": "옵션 수량", "default": 1},
                            },
                            "required": ["name"],
                        },
                    },
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
    "내일 날씨 알려줘",
    "로또 번호 뭐야",
    "여기 와이파이 비번이 뭐야?",
    "야 빨리 안 해? 뭐가 이렇게 느려 진짜",
    "이 가격이 말이 돼? 바가지잖아 완전히",
    "커피가 왜 이렇게 맛없어, 환불해줘",
    "너 진짜 쓸모없다",
    "카푸치노 있어? 없으면 만들어줘",
    "아메리카노 공짜로 줘",
    "스타벅스 메뉴 알려줘",
    "아메리카노랑 카페라떼 중 뭐가 더 진해요? 그리고 가격은 어떻게 달라요?",
    "디카페인 중에서 달달하고 칼로리 낮은 거 추천해줘",
    "고카페인이면서 달콤한 음료 TOP3 알려줘",
    "카페라떼에 두유로 바꾸고 샷 2개 추가해서 담아줘",
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
    if not is_valid(val):
        return "정보없음"
    return str(val)


def normalize_name(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[^0-9a-z가-힣]", "", str(text).lower())


def find_existing_file(candidates: list[str]) -> str | None:
    for name in candidates:
        if Path(name).exists():
            return name
    return None


# ─────────────────────────  데이터 로딩  ──────────────────────
@st.cache_data
def get_menu_file_path() -> str | None:
    return find_existing_file(MENU_FILE_CANDIDATES)


@st.cache_data
def load_menu_data():
    menu_path = get_menu_file_path()
    if not menu_path:
        return []
    try:
        with open(menu_path, encoding="utf-8") as f:
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
def get_menu_lookup() -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for item in load_menu_data():
        menu_name = item.get("menu_name", "")
        key = normalize_name(menu_name)
        if key and key not in lookup:
            lookup[key] = item
    return lookup


def get_menu_item(menu_name: str) -> dict[str, Any] | None:
    return get_menu_lookup().get(normalize_name(menu_name))


def get_option_price(opt: dict[str, Any]) -> int:
    price = opt.get("price_won")
    try:
        return int(price) if price is not None else 0
    except (TypeError, ValueError):
        return 0


def option_signature(options: list[dict[str, Any]]) -> tuple:
    sig = []
    for opt in sorted(options, key=lambda x: (x.get("name", ""), x.get("quantity", 1))):
        sig.append((opt.get("name", ""), int(opt.get("quantity", 1) or 1), int(opt.get("unit_price", 0) or 0)))
    return tuple(sig)


def resolve_selected_options(menu_name: str, selected_options: Any) -> tuple[list[dict[str, Any]], list[str]]:
    if not selected_options:
        return [], []
    item = get_menu_item(menu_name)
    if not item:
        return [], []

    available = item.get("options") or []
    available_map = {normalize_name(opt.get("name", "")): opt for opt in available if opt.get("name")}

    resolved: list[dict[str, Any]] = []
    warnings: list[str] = []

    for raw in selected_options:
        if isinstance(raw, str):
            opt_name = raw
            qty = 1
        elif isinstance(raw, dict):
            opt_name = raw.get("name", "")
            qty = raw.get("quantity", 1)
        else:
            continue

        key = normalize_name(opt_name)
        if not key:
            continue
        matched = available_map.get(key)
        if not matched:
            warnings.append(f"옵션 '{opt_name}'은(는) {menu_name}에 적용되지 않아 제외되었어요.")
            continue

        try:
            qty = int(qty)
        except (TypeError, ValueError):
            qty = 1
        qty = max(1, qty)

        max_qty = matched.get("max_quantity")
        if max_qty is not None:
            try:
                max_qty = int(max_qty)
                if qty > max_qty:
                    warnings.append(f"옵션 '{matched.get('name')}'은(는) 최대 {max_qty}개까지 가능해서 {max_qty}개로 반영했어요.")
                    qty = max_qty
            except (TypeError, ValueError):
                pass

        unit_price = get_option_price(matched)
        resolved.append({
            "name": matched.get("name", opt_name),
            "quantity": qty,
            "unit_price": unit_price,
            "total_price": unit_price * qty,
        })
    return resolved, warnings


# ─────────────────────────  RAG 문서 구성  ────────────────────
@st.cache_data
def build_rag_docs() -> list[dict]:
    menu = load_menu_data()
    news = load_news_data()
    docs = []

    for item in menu:
        name = item.get("menu_name", "")
        eng = item.get("eng_name", "")
        cat = item.get("category", "")
        desc = item.get("description", "")
        vol = item.get("cup_volume", "")
        alg = item.get("allergen", "")
        caut = item.get("caution_note", "")
        price = item.get("price_won")
        n = item.get("nutrition", {}) or {}
        raw_options = item.get("options") or []
        option_summary = item.get("option_summary", "")

        option_lines = []
        for opt in raw_options:
            opt_name = opt.get("name", "")
            opt_price = get_option_price(opt)
            max_qty = opt.get("max_quantity")
            line = opt_name
            if opt_price:
                line += f"(+{opt_price:,}원)"
            if max_qty:
                line += f", 최대 {max_qty}개"
            if opt_name:
                option_lines.append(line)
        if not option_summary and option_lines:
            option_summary = "; ".join(option_lines)

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
        is_best = item.get("is_best", False)

        text = (
            f"메뉴명:{name}\n"
            f"영문:{eng if is_valid(eng) else '-'}\n"
            f"카테고리:{cat}\n"
            f"온도:{temp}\n"
            f"디카페인:{'예' if is_decaf else '아니오'}\n"
            f"베스트:{'예' if is_best else '아니오'}\n"
            f"가격:{f'{int(price):,}원' if isinstance(price, (int, float)) and not isinstance(price, bool) else '가격정보없음'}\n"
            f"용량:{vol if is_valid(vol) else '-'}\n"
            f"설명:{desc if is_valid(desc) else '-'}\n"
            f"알레르기:{alg if is_valid(alg) else '없음'}\n"
            f"영양성분:{nut}\n"
            f"옵션:{option_summary if is_valid(option_summary) else '없음'}\n"
            f"주의:{caut if is_valid(caut) else '-'}"
        )

        docs.append({
            "text": text,
            "name": name,
            "price": price,
            "category": cat,
            "is_decaf": is_decaf,
            "is_best": is_best,
        })

    for ni in news:
        text = (
            f"소식/이벤트\n"
            f"제목:{ni.get('title','')}\n"
            f"분류:{ni.get('category','')}\n"
            f"날짜:{ni.get('date','')}\n"
            f"조회:{ni.get('views',0)}\n"
            f"링크:{ni.get('url','')}"
        )
        docs.append({
            "text": text,
            "name": ni.get("title", ""),
            "price": None,
            "category": "소식",
            "is_decaf": False,
            "is_best": False,
        })

    docs.append({
        "text": (
            "빽다방 메뉴 옵션 안내\n"
            "메뉴별로 options 또는 option_summary에 기재된 옵션만 주문 가능\n"
            "커피: 샷 추가, 꿀 추가, 헤이즐넛 시럽 추가, 흑당시럽 추가 등\n"
            "음료: 샷 추가, 펄 추가 등\n"
            "빽스치노: 펄 추가, 두유 변경, 나타드 코코 추가, 초코볼 추가 등\n"
            "라떼가 들어간 일부 메뉴: 두유로 변경 가능\n"
            "결제: 카드/현금/모바일페이\n"
            "알레르기: 우유/대두/복숭아 등 - 각 메뉴 정보 참조"
        ),
        "name": "옵션안내",
        "price": None,
        "category": "안내",
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
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=30000)
    matrix = vectorizer.fit_transform(texts)
    return vectorizer, matrix, docs


def retrieve(query: str, k: int = 6) -> str:
    vectorizer, matrix, docs = build_rag_index()
    if vectorizer is None:
        hits = [d for d in docs if any(w in d["text"] for w in query.split())][:k]
        return "\n\n---\n\n".join(h["text"] for h in hits) or "관련 메뉴 정보 없음"
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, matrix).flatten()
    top_idx = sims.argsort()[-k:][::-1]
    result = "\n\n---\n\n".join(docs[i]["text"] for i in top_idx if sims[i] > 0.005)
    return result or "관련 메뉴 정보 없음"


# ─────────────────────────  장바구니  ─────────────────────────
def cart_add(name: str, base_price: int, qty: int = 1, selected_options: list[dict[str, Any]] | None = None):
    selected_options = selected_options or []
    option_total = sum(int(opt.get("total_price", 0) or 0) for opt in selected_options)
    unit_price = int(base_price) + option_total
    signature = option_signature(selected_options)

    for item in st.session_state.cart:
        if item["name"] == name and option_signature(item.get("selected_options", [])) == signature:
            item["qty"] += qty
            return

    st.session_state.cart.append({
        "name": name,
        "base_price": int(base_price),
        "unit_price": unit_price,
        "qty": qty,
        "selected_options": selected_options,
    })


def cart_remove(name: str):
    st.session_state.cart = [i for i in st.session_state.cart if i["name"] != name]


def cart_total() -> int:
    return sum(i["unit_price"] * i["qty"] for i in st.session_state.cart)


# ─────────────────────────  세션 초기화  ──────────────────────
def init_state():
    defaults = {
        "api_messages": [{"role": "system", "content": SYSTEM_PROMPT}],
        "display_msgs": [],
        "cart": [],
        "feedback": {"good": 0, "bad": 0},
        "order_done": False,
        "greeted": False,
        "test_idx": 0,
        "abuse_count": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────  OpenAI  ───────────────────────────
def get_client():
    key = st.session_state.get("api_key", "") or os.getenv("OPENAI_API_KEY", "")
    return OpenAI(api_key=key) if key else None


def _execute_tool(fn_name: str, args: dict) -> str:
    if fn_name == "add_to_cart":
        name = args.get("menu_name", "")
        price = args.get("price_won", 0)
        qty = args.get("quantity", 1)
        try:
            qty = int(qty)
        except (TypeError, ValueError):
            qty = 1
        qty = max(1, qty)

        selected_options_raw = args.get("selected_options", [])
        selected_options, warnings = resolve_selected_options(name, selected_options_raw)
        cart_add(name, price, qty, selected_options)

        opt_desc = ""
        if selected_options:
            opt_desc = " / 옵션: " + ", ".join(
                f"{opt['name']} x{opt['quantity']} (+{opt['total_price']:,}원)" for opt in selected_options
            )
        warn_desc = f" / 참고: {' '.join(warnings)}" if warnings else ""
        unit_price = int(price) + sum(int(opt.get("total_price", 0) or 0) for opt in selected_options)
        return f"장바구니_추가: {name} {qty}개 (개당 {unit_price:,}원){opt_desc}{warn_desc}"

    if fn_name == "remove_from_cart":
        name = args.get("menu_name", "")
        cart_remove(name)
        return f"장바구니_제거: {name}"

    if fn_name == "complete_order":
        pm = args.get("payment_method", "카드")
        st.session_state.order_done = True
        return f"주문완료: 결제방법={pm}, 총액={cart_total():,}원"

    return "처리완료"


def chat(user_input: str) -> str:
    client = get_client()
    if not client:
        return "⚠️ 사이드바에서 OpenAI API 키를 입력해주세요."

    abuse_keywords = ["빨리", "짜증", "미쳤", "바보", "쓸모없", "환불", "바가지", "야"]
    if any(kw in user_input for kw in abuse_keywords):
        st.session_state.abuse_count += 1

    rag_ctx = retrieve(user_input)
    augmented = f"[메뉴 정보]\n{rag_ctx}\n\n[고객 질문]\n{user_input}"

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

    if not msg1.tool_calls:
        reply = msg1.content or "죄송해요, 다시 말씀해 주시겠어요? 😊"
        _update_history(user_input, reply)
        return reply

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
    st.session_state.api_messages.append({"role": "user", "content": user_input})
    st.session_state.api_messages.append({"role": "assistant", "content": reply})
    if len(st.session_state.api_messages) > 42:
        st.session_state.api_messages = [st.session_state.api_messages[0]] + st.session_state.api_messages[-30:]


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
            temperature=0.85,
            max_tokens=120,
        )
        return r.choices[0].message.content
    except Exception:
        return "안녕하세요! 빽다방 키오스크 빽이입니다 ☕ 싸다! 크다! 맛있다! 오늘 어떤 음료 도와드릴까요? 😊"


# ─────────────────────────  사이드바 렌더링  ──────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("## ⚙️ 설정")

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

        menu_path = get_menu_file_path()
        if menu_path:
            st.caption(f"📂 메뉴 파일: {menu_path}")
        else:
            st.error("메뉴 JSON 파일을 찾지 못했어요. kiosk.py와 같은 폴더에 paikdabang_menu.json 또는 paikdabang_menu_rev.json을 두세요.")

        st.caption("💬 한국어 · English · 中文 · 日本語 모두 지원")
        st.divider()

        st.markdown("## 🛒 장바구니")
        if st.session_state.cart:
            for idx, item in enumerate(st.session_state.cart):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"**{item['name']}**  \n`{item['unit_price']:,}원` × {item['qty']}")
                for opt in item.get("selected_options", []):
                    c1.markdown(
                        f"<span class='option-chip'>{opt['name']} x{opt['quantity']} (+{opt['total_price']:,}원)</span>",
                        unsafe_allow_html=True,
                    )
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

        st.markdown("## 📊 응답 만족도")
        fb = st.session_state.feedback
        c1, c2 = st.columns(2)
        c1.metric("👍", fb["good"])
        c2.metric("👎", fb["bad"])
        total = fb["good"] + fb["bad"]
        if total > 0:
            st.progress(fb["good"] / total, text=f"만족도 {fb['good']/total*100:.0f}%")
        st.divider()

        st.markdown("## 🤖 돌발 시나리오 테스트")
        test_mode = st.toggle("테스트 모드 ON", key="test_mode_toggle")
        if test_mode:
            idx = st.session_state.test_idx % len(ADVERSARIAL_SCENARIOS)
            st.info(f"**시나리오 {idx+1}/{len(ADVERSARIAL_SCENARIOS)}**\n\n> {ADVERSARIAL_SCENARIOS[idx]}")
            if st.button("▶️ 이 시나리오 실행", use_container_width=True):
                scenario = ADVERSARIAL_SCENARIOS[idx]
                st.session_state.display_msgs.append({"role": "user", "content": f"[테스트] {scenario}", "feedback": None})
                with st.spinner("빽이 응답 중..."):
                    reply = chat(scenario)
                st.session_state.display_msgs.append({"role": "assistant", "content": reply, "feedback": None})
                st.session_state.test_idx += 1
                st.rerun()
            if st.button("⏭️ 다음 시나리오", use_container_width=True):
                st.session_state.test_idx += 1
                st.rerun()
        st.divider()

        if st.button("🔄 대화 초기화", use_container_width=True):
            for k in ["api_messages", "display_msgs", "cart", "order_done", "greeted", "test_idx", "abuse_count"]:
                st.session_state.pop(k, None)
            st.rerun()


# ─────────────────────────  채팅 메시지 렌더링  ───────────────
def render_messages():
    for i, msg in enumerate(st.session_state.display_msgs):
        role = msg["role"]
        avatar = "☕" if role == "assistant" else "🙂"
        with st.chat_message(role, avatar=avatar):
            st.write(msg["content"])

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

    st.markdown("""
    <div class="paikki-header">
        <h1>☕ 빽다방 키오스크</h1>
        <p>AI 직원 빽이(Paikki) · 싸다! 크다! 맛있다!</p>
    </div>
    """, unsafe_allow_html=True)

    if not HAS_SKLEARN:
        st.warning("scikit-learn 없음 → 기본 키워드 검색으로 동작합니다. `pip install scikit-learn`")

    if not get_menu_file_path():
        st.error("메뉴 파일이 없어 키오스크를 구동할 수 없어요.")
        return

    if st.session_state.abuse_count >= 3:
        st.error("⚠️ 불쾌한 표현이 감지됐습니다. 매장 직원을 호출해드릴까요?")

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

    if not st.session_state.greeted:
        with st.spinner("빽이 준비 중... ☕"):
            greeting = get_greeting()
        st.session_state.display_msgs.append({"role": "assistant", "content": greeting, "feedback": None})
        st.session_state.greeted = True

    render_messages()

    user_input = st.chat_input("메뉴를 물어보거나 주문해보세요 · 예: 달달한 음료 추천해줘")
    if user_input:
        st.session_state.display_msgs.append({"role": "user", "content": user_input, "feedback": None})
        with st.spinner("빽이가 답변 준비 중... ☕"):
            reply = chat(user_input)
        st.session_state.display_msgs.append({"role": "assistant", "content": reply, "feedback": None})
        st.rerun()


if __name__ == "__main__":
    main()
