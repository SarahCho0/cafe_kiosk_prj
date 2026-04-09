import json
import math
import streamlit as st

st.set_page_config(
    page_title="빽다방 전체 메뉴",
    page_icon="☕",
    layout="wide",
)


# ── 유틸 ─────────────────────────────────────────────────
def is_valid(val) -> bool:
    """NaN / None / 빈문자열 검사"""
    if val is None:
        return False
    if isinstance(val, float) and math.isnan(val):
        return False
    if isinstance(val, str) and val.strip() == "":
        return False
    return True


def to_float(val) -> float | None:
    if not is_valid(val):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ── 데이터 로드 ─────────────────────────────────────────
@st.cache_data
def load_news():
    try:
        with open("paikdabang_news.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


@st.cache_data
def load_menu():
    with open("paikdabang_menu_rev.json", encoding="utf-8") as f:
        return json.load(f)

all_menu = load_menu()

CATEGORIES = ["커피", "신메뉴", "음료", "빽스치노", "아이스크림/디저트", "소식 📢"]

# ── 헤더 ────────────────────────────────────────────────
st.title("☕ 빽다방 메뉴판")
st.caption(f"총 {len(all_menu)}개 메뉴 수록")

# ── 사이드바 필터 ────────────────────────────────────────
with st.sidebar:
    st.header("필터")

    # 온도
    temp_filter = st.radio("온도", ["전체", "HOT", "ICED"], horizontal=True)

    # 디카페인
    decaf_filter = st.checkbox("디카페인만 보기")
    regular_filter = st.checkbox("일반(카페인)만 보기")

    # 베스트 메뉴
    best_filter = st.checkbox("🏆 베스트 메뉴만 보기")

    # 검색
    search = st.text_input("메뉴 검색", placeholder="예: 아메리카노")

    st.divider()

    # 정렬
    sort_by = st.selectbox(
        "정렬 기준",
        ["기본 순서", "가격 낮은 순", "가격 높은 순", "칼로리 낮은 순", "칼로리 높은 순", "카페인 낮은 순", "카페인 높은 순"],
    )

    st.divider()

    # 카페인 범위 슬라이더
    st.markdown("**카페인 범위 (mg)**")
    caffeine_values = [
        to_float(m["nutrition"].get("caffeine_mg"))
        for m in all_menu
        if to_float(m["nutrition"].get("caffeine_mg")) is not None
    ]
    if caffeine_values:
        caf_min, caf_max = int(min(caffeine_values)), int(max(caffeine_values))
        caffeine_range = st.slider(
            "카페인 범위",
            min_value=caf_min,
            max_value=caf_max,
            value=(caf_min, caf_max),
            label_visibility="collapsed",
        )
    else:
        caffeine_range = None


# ── 카테고리 탭 ───────────────────────────────────────────
tabs = st.tabs(CATEGORIES)

for tab, category in zip(tabs, CATEGORIES):
    with tab:
        # 카테고리 필터
        filtered = [m for m in all_menu if m.get("category") == category]

        # 소식 탭은 별도 렌더링
        if category == "소식 📢":
            news_list = load_news()
            if not news_list:
                st.info("소식 데이터가 없습니다.")
                continue
            for news_item in news_list:
                cat_color = "🔴" if news_item.get("category") == "이벤트" else "🔵"
                with st.container(border=True):
                    col_l, col_r = st.columns([5, 1])
                    col_l.markdown(
                        f"{cat_color} **[{news_item.get('category')}]** "
                        f"{news_item.get('title')}"
                    )
                    col_l.caption(f"📅 {news_item.get('date')}  ·  👁 {news_item.get('views', 0):,}")
                    if news_item.get("url"):
                        col_r.link_button("자세히", news_item["url"])
            continue

        # 온도 필터 (HOT/ICED 명시된 항목만 엄격 매칭)
        if temp_filter == "HOT":
            filtered = [m for m in filtered if "(HOT)" in m["menu_name"]]
        elif temp_filter == "ICED":
            filtered = [m for m in filtered if "(ICED)" in m["menu_name"]]

        # 디카페인 필터
        if decaf_filter:
            filtered = [m for m in filtered if "디카페인" in m["menu_name"]]
        elif regular_filter:
            filtered = [m for m in filtered if "디카페인" not in m["menu_name"]]

        # 베스트 필터
        if best_filter:
            filtered = [m for m in filtered if m.get("is_best") is True]

        # 검색
        if search:
            filtered = [m for m in filtered if search.lower() in m["menu_name"].lower()]

        # 카페인 범위
        if caffeine_range:
            lo, hi = caffeine_range
            def in_range(m):
                val = to_float(m["nutrition"].get("caffeine_mg"))
                if val is None:
                    return True  # 카페인 정보 없으면 표시
                return lo <= val <= hi
            filtered = [m for m in filtered if in_range(m)]

        # 정렬
        if sort_by == "가격 낮은 순":
            filtered = sorted(filtered, key=lambda m: m.get("price_won") or float("inf"))
        elif sort_by == "가격 높은 순":
            filtered = sorted(filtered, key=lambda m: m.get("price_won") or 0, reverse=True)
        elif sort_by == "칼로리 낮은 순":
            filtered = sorted(filtered, key=lambda m: to_float(m["nutrition"].get("kcal")) or float("inf"))
        elif sort_by == "칼로리 높은 순":
            filtered = sorted(filtered, key=lambda m: to_float(m["nutrition"].get("kcal")) or 0, reverse=True)
        elif sort_by == "카페인 낮은 순":
            filtered = sorted(filtered, key=lambda m: to_float(m["nutrition"].get("caffeine_mg")) or float("inf"))
        elif sort_by == "카페인 높은 순":
            filtered = sorted(filtered, key=lambda m: to_float(m["nutrition"].get("caffeine_mg")) or 0, reverse=True)

        st.markdown(f"**{len(filtered)}개** 메뉴")
        st.divider()

        if not filtered:
            st.info("조건에 맞는 메뉴가 없습니다.")
            continue

        # ── 메뉴 카드 (3열) ──────────────────────────────
        COLS = 3
        rows = [filtered[i : i + COLS] for i in range(0, len(filtered), COLS)]

        for row in rows:
            cols = st.columns(COLS)
            for col, item in zip(cols, row):
                with col:
                    # 이미지
                    if is_valid(item.get("image_url")):
                        st.image(item["image_url"], width="stretch")

                    # 베스트 배지 + 이름
                    name_display = item["menu_name"]
                    if item.get("is_best"):
                        st.markdown(f"🏆 **{name_display}**")
                    else:
                        st.markdown(f"**{name_display}**")

                    if is_valid(item.get("eng_name")):
                        st.caption(item["eng_name"])

                    # 설명
                    if is_valid(item.get("description")):
                        st.write(item["description"])

                    # 가격 / 용량 / 알레르기
                    price_won = item.get("price_won")
                    if price_won:
                        st.markdown(f"### 💰 {price_won:,}원")

                    meta_cols = st.columns(2)
                    if is_valid(item.get("cup_volume")):
                        meta_cols[0].markdown(f"🥤 `{item['cup_volume']}`")
                    if is_valid(item.get("allergen")):
                        meta_cols[1].markdown(f"⚠️ 알레르기: `{item['allergen']}`")

                    # 영양성분
                    nutrition = item.get("nutrition", {})
                    NUTRITION_LABELS = [
                        ("caffeine_mg",  "☕ 카페인",   "mg"),
                        ("kcal",         "🔥 칼로리",   "kcal"),
                        ("sugar_g",      "🍬 당류",     "g"),
                        ("sodium_mg",    "🧂 나트륨",   "mg"),
                        ("sat_fat_g",    "🧈 포화지방", "g"),
                        ("protein_g",    "💪 단백질",   "g"),
                        ("carb_g",       "🌾 탄수화물", "g"),
                        ("fat_g",        "💧 지방",     "g"),
                    ]

                    has_nutrition = any(
                        is_valid(nutrition.get(k)) for k, _, _ in NUTRITION_LABELS
                    )
                    if has_nutrition:
                        with st.expander("영양성분 보기"):
                            n_cols = st.columns(3)
                            col_idx = 0
                            for key, label, unit in NUTRITION_LABELS:
                                raw = nutrition.get(key)
                                if not is_valid(raw):
                                    continue
                                val = to_float(raw)
                                if val is not None:
                                    val_str = f"{val:g}{unit}"
                                else:
                                    val_str = str(raw)
                                n_cols[col_idx % 3].metric(label, val_str)
                                col_idx += 1

                    # 주의 문구
                    if is_valid(item.get("caution_note")):
                        st.warning(f"⚠️ {item['caution_note']}")

                    st.divider()
