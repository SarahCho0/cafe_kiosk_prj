"""
모든 메뉴에 임의 가격 할당 (카테고리별)
나중에 실제 DB에서 가격을 가져올 수 있도록 구조화
"""
import json
import random

# ── 카테고리별 기본 가격 범위 (단위: 원) ────────────────
CATEGORY_PRICES = {
    "신메뉴": (4500, 6500),      # 신메뉴는 조금 비쌈
    "커피": (2800, 4500),        # 기본 커피
    "음료": (4000, 6000),        # 음료 (아이스티 등)
    "빽스치노": (5000, 6500),    # 프리미엄
    "아이스크림/디저트": (3500, 5500),  # 디저트
}

def get_price_for_category(category: str) -> int:
    """카테고리별 기본 가격 범위에서 랜덤 선택"""
    if category in CATEGORY_PRICES:
        min_price, max_price = CATEGORY_PRICES[category]
        # 500원 단위로 반올림
        price = random.randint(min_price // 500, max_price // 500) * 500
        return price
    return 5000  # 기본값

# ── 가격 할당 ────────────────────────────────────────────
with open("paikdabang_menu_dom.json", encoding="utf-8") as f:
    all_menu = json.load(f)

print(f"[시작] 전체 메뉴: {len(all_menu)}개")

category_counts = {}
assigned = 0

for menu in all_menu:
    category = menu.get("category", "기타")
    
    # 카테고리별 통계
    if category not in category_counts:
        category_counts[category] = {"total": 0, "assigned": 0}
    category_counts[category]["total"] += 1
    
    # 가격이 없으면 할당
    if menu.get("price_won") is None:
        menu["price_won"] = get_price_for_category(category)
        assigned += 1
        category_counts[category]["assigned"] += 1
    else:
        category_counts[category]["assigned"] += 1

# ── 저장 ──────────────────────────────────────────────────
with open("paikdabang_menu_dom.json", "w", encoding="utf-8") as f:
    json.dump(all_menu, f, ensure_ascii=False, indent=2)

print(f"\n[완료] 가격 할당: {assigned}개")
print("\n[카테고리별 통계]")
for cat, stats in sorted(category_counts.items()):
    print(f"  {cat}: {stats['assigned']}/{stats['total']}개")

# ── 샘플 출력 ──────────────────────────────────────────────
print("\n[샘플 메뉴들]")
for menu in all_menu[:5]:
    print(f"  {menu['menu_name']}: {menu['price_won']:,}원")

# ── paikdabang_price.json 생성 (참고용) ────────────────────
price_map = {menu['menu_name']: menu['price_won'] for menu in all_menu}
with open("paikdabang_price.json", "w", encoding="utf-8") as f:
    json.dump(price_map, f, ensure_ascii=False, indent=2)
print(f"\n[생성] paikdabang_price.json: {len(price_map)}개 메뉴 가격")
