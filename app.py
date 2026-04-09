import json
import streamlit as st

st.set_page_config(
    page_title="빽다방 커피 메뉴",
    page_icon="☕",
    layout="wide",
)

# ── 데이터 로드 ─────────────────────────────────────────
@st.cache_data
def load_menu():
    with open("paikdabang_coffee_menu.json", encoding="utf-8") as f:
        return json.load(f)

menu = load_menu()

# ── 헤더 ────────────────────────────────────────────────
st.title("☕ 빽다방 커피 메뉴")
st.caption(f"총 {len(menu)}개 메뉴")

# ── 사이드바 필터 ────────────────────────────────────────
with st.sidebar:
    st.header("필터")

    # 온도 필터
    temp_options = ["전체", "HOT", "ICED"]
    temp_filter = st.radio("온도", temp_options, horizontal=True)

    # 디카페인 필터
    decaf_filter = st.checkbox("디카페인만 보기")
    regular_filter = st.checkbox("일반(카페인)만 보기")

    # 검색
    search = st.text_input("메뉴 검색", placeholder="예: 아메리카노")

    # 영양성분 정렬
    sort_by = st.selectbox(
        "정렬 기준",
        ["기본 순서", "칼로리 낮은 순", "칼로리 높은 순", "카페인 낮은 순", "카페인 높은 순"],
    )

# ── 필터 적용 ────────────────────────────────────────────
filtered = menu[:]

if temp_filter == "HOT":
    filtered = [m for m in filtered if "(HOT)" in m["name"] or
                ("(ICED)" not in m["name"] and "(HOT)" not in m["name"] and
                 "스무디" not in m["name"] and "쉐이크" not in m["name"])]
    # 더 명확하게: HOT 포함 or 둘 다 없는 경우
    filtered = [m for m in menu if "(HOT)" in m["name"] or
                ("(HOT)" not in m["name"] and "(ICED)" not in m["name"])]
elif temp_filter == "ICED":
    filtered = [m for m in menu if "(ICED)" in m["name"] or
                ("(HOT)" not in m["name"] and "(ICED)" not in m["name"])]
else:
    filtered = menu[:]

if decaf_filter:
    filtered = [m for m in filtered if "디카페인" in m["name"]]
if regular_filter and not decaf_filter:
    filtered = [m for m in filtered if "디카페인" not in m["name"]]

if search:
    filtered = [m for m in filtered if search.lower() in m["name"].lower()]

# ── 정렬 ─────────────────────────────────────────────────
def get_nutrition_val(item, key):
    val = item.get("nutrition", {}).get(key)
    return val if val is not None else float("inf")

if sort_by == "칼로리 낮은 순":
    filtered = sorted(filtered, key=lambda m: get_nutrition_val(m, "calories_kcal"))
elif sort_by == "칼로리 높은 순":
    filtered = sorted(filtered, key=lambda m: get_nutrition_val(m, "calories_kcal"), reverse=True)
elif sort_by == "카페인 낮은 순":
    filtered = sorted(filtered, key=lambda m: get_nutrition_val(m, "caffeine_mg"))
elif sort_by == "카페인 높은 순":
    filtered = sorted(filtered, key=lambda m: get_nutrition_val(m, "caffeine_mg"), reverse=True)

st.markdown(f"**{len(filtered)}개** 메뉴 표시 중")
st.divider()

# ── 메뉴 카드 ─────────────────────────────────────────────
COLS = 3
rows = [filtered[i : i + COLS] for i in range(0, len(filtered), COLS)]

for row in rows:
    cols = st.columns(COLS)
    for col, item in zip(cols, row):
        with col:
            # 이미지
            if item.get("image_url"):
                st.image(item["image_url"], width="stretch")
            else:
                st.markdown("🖼️ 이미지 없음")

            # 이름
            st.markdown(f"### {item['name']}")
            if item.get("name_en"):
                st.caption(item["name_en"])

            # 설명
            if item.get("description"):
                st.write(item["description"])

            # 용량
            if item.get("volume"):
                st.markdown(f"🥤 `{item['volume']}`")

            # 영양성분 expander
            nutrition = item.get("nutrition", {})
            if nutrition:
                with st.expander("영양성분 보기"):
                    n_cols = st.columns(3)
                    labels = {
                        "caffeine_mg": ("☕ 카페인", "mg"),
                        "calories_kcal": ("🔥 칼로리", "kcal"),
                        "sugar_g": ("🍬 당류", "g"),
                        "sodium_mg": ("🧂 나트륨", "mg"),
                        "saturated_fat_g": ("🧈 포화지방", "g"),
                        "protein_g": ("💪 단백질", "g"),
                    }
                    items_list = list(labels.items())
                    for i, (key, (label, unit)) in enumerate(items_list):
                        val = nutrition.get(key)
                        val_str = f"{val}{unit}" if val is not None else "-"
                        n_cols[i % 3].metric(label, val_str)

            # 고카페인 경고
            if item.get("caution"):
                st.warning(f"⚠️ {item['caution']}", icon=None)

            st.divider()
