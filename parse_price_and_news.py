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

# ── 2) 정확히 일치하는 이름에만 가격 추가 ─────────────────────
with open("paikdabang_coffee_menu.json", encoding="utf-8") as f:
    coffee = json.load(f)

matched = 0
for menu in coffee:
    if menu["name"] in price_data:
        menu["price_won"] = price_data[menu["name"]]["price_won"]
        matched += 1

print(f"\n[매칭] 정확히 일치: {matched}개 / {len(coffee)}개")

with open("paikdabang_coffee_menu.json", "w", encoding="utf-8") as f:
    json.dump(coffee, f, ensure_ascii=False, indent=2)
print("저장 완료 → paikdabang_coffee_menu.json")
