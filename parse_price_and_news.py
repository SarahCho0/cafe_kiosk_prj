import json
import re
from bs4 import BeautifulSoup

# ── 1) price.html 파싱 ─────────────────────────────────────────
with open("price.html", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

price_data = {}  # {name: {category, description, price_won}}
sections = soup.find_all("div", class_="single-menu")
for sec in sections:
    cat_tag = sec.find("div", class_="title-wrapper")
    category = cat_tag.get_text(strip=True) if cat_tag else "기타"
    for item in sec.find_all("div", class_="menuitem"):
        name_div = item.find("div", class_="itemtitle-wrapper")
        if not name_div:
            continue
        name = name_div.get_text(strip=True)
        full_text = item.get_text(separator=" ", strip=True)
        full_text = re.sub(r"^(BEST\s*)+", "", full_text).strip()
        desc_raw = full_text.replace(name, "", 1).strip()
        desc_raw = re.sub(r"\s*[\d,]+원.*", "", desc_raw).strip()
        price_match = re.search(r"([\d,]+)원", full_text)
        price_won = int(price_match.group(1).replace(",", "")) if price_match else None
        price_data[name] = {
            "category": category,
            "description": desc_raw or None,
            "price_won": price_won,
        }

print(f"[가격] 추출된 메뉴 수: {len(price_data)}개")
for n, v in price_data.items():
    print(f"  {repr(n)}: {v['price_won']}원")

# ── 2) paikdabang_menu_dom.json에 가격 추가 ─────────────────────
def normalize(name: str) -> str:
    return re.sub(r"\s*\(", "(", name)

try:
    with open("paikdabang_menu_dom.json", encoding="utf-8") as f:
        all_menu = json.load(f)
    
    matched_dom = 0
    unmatched = []
    
    for menu in all_menu:
        menu_name = menu.get("menu_name", "")
        norm_name = normalize(menu_name)
        
        # 정확히 일치하는 이름 찾기
        found_price = None
        for p_name, p_data in price_data.items():
            if normalize(p_name) == norm_name:
                found_price = p_data["price_won"]
                matched_dom += 1
                break
        
        if found_price:
            menu["price_won"] = found_price
        else:
            if menu.get("price_won") is None:
                unmatched.append(menu_name)
    
    print(f"\n[DOM 매칭] {matched_dom}개 / {len(all_menu)}개")
    if unmatched:
        print(f"[가격 미정] {len(unmatched)}개 메뉴:")
        for um in unmatched[:10]:  # 처음 10개만 표시
            print(f"  - {um}")
    
    with open("paikdabang_menu_dom.json", "w", encoding="utf-8") as f:
        json.dump(all_menu, f, ensure_ascii=False, indent=2)
    print("저장 완료 → paikdabang_menu_dom.json")
except FileNotFoundError:
    print("[경고] paikdabang_menu_dom.json 파일 없음")

# ── 3) paikdabang_coffee_menu.json에 가격 추가 (기존 코드 유지) ─────
try:
    with open("paikdabang_coffee_menu.json", encoding="utf-8") as f:
        coffee = json.load(f)

    matched_coffee = 0
    for menu in coffee:
        if menu["name"] in price_data:
            menu["price_won"] = price_data[menu["name"]]["price_won"]
            matched_coffee += 1

    print(f"\n[Coffee 매칭] 정확히 일치: {matched_coffee}개 / {len(coffee)}개")

    with open("paikdabang_coffee_menu.json", "w", encoding="utf-8") as f:
        json.dump(coffee, f, ensure_ascii=False, indent=2)
    print("저장 완료 → paikdabang_coffee_menu.json")
except FileNotFoundError:
    print("[경고] paikdabang_coffee_menu.json 파일 없음")
