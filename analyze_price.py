# analyze_price.py

import json
import re
from bs4 import BeautifulSoup

# price.html 파싱 -> paikdabang_price.json 저장
with open("price.html", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

price_list = []
sections = soup.find_all("div", class_="single-menu")
for sec in sections:
    cat_tag = sec.find("h3", class_="headingTitle") or sec.find("div", class_="title-wrapper")
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
        price_list.append({
            "category": category,
            "name": name,
            "description": desc_raw or None,
            "price_won": price_won,
        })

with open("paikdabang_price.json", "w", encoding="utf-8") as f:
    json.dump(price_list, f, ensure_ascii=False, indent=2)
print(f"저장 완료: paikdabang_price.json ({len(price_list)}개)")

# 이름 형식 차이 분석
with open("paikdabang_coffee_menu.json", encoding="utf-8") as f:
    coffee = json.load(f)
coffee_names = {m["name"] for m in coffee}

def normalize(n):
    return re.sub(r"\s*\(", "(", n)

normalized_matches = []
for p in price_list:
    norm_p = normalize(p["name"])
    for c_name in coffee_names:
        if normalize(c_name) == norm_p:
            normalized_matches.append((p["name"], c_name, p["price_won"]))
            break

print(f"\n[참고] 괄호 앞 공백 정규화 시 매칭 가능 수: {len(normalized_matches)}개")
for pm in normalized_matches[:20]:
    print(f"  price: {repr(pm[0]):50s}  coffee: {repr(pm[1]):50s}  {pm[2]}원")
