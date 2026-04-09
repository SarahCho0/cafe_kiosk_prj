"""
빽다방 커피 메뉴 HTML 파서
- 제공된 HTML 구조를 분석하여 메뉴 데이터를 JSON으로 추출
- 실제 사이트 크롤링 또는 로컬 HTML 파일 파싱 모두 지원
"""

import json
import re
import sys
from bs4 import BeautifulSoup

# ── 영양성분 키 매핑 ─────────────────────────────────────
NUTRITION_KEY_MAP = {
    "카페인": "caffeine_mg",
    "칼로리": "calories_kcal",
    "나트륨": "sodium_mg",
    "당류":   "sugar_g",
    "포화지방": "saturated_fat_g",
    "단백질": "protein_g",
}


def normalize_text(raw: str) -> str:
    """HTML 태그 제거 + 줄바꿈 → 공백 + 공백 정리"""
    text = re.sub(r"<br\s*/?>", " ", raw, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_caution(description: str):
    """
    설명 문자열에서 '고카페인 함유...' 또는 '*...' 주의 문구를 분리.
    분리 성공 시 (desc_clean, caution), 실패 시 (original, None) 반환.
    """
    # 패턴: '*고카페인...' 또는 '고카페인...' 또는 '카페인에 민감...' 계열
    caution_pattern = re.compile(
        r"[\*\s]*(고카페인\s*함유[^\n]*(?:주의[^\n]*)?)$", re.IGNORECASE
    )
    m = caution_pattern.search(description)
    if m:
        caution = m.group(0).strip().lstrip("*").strip()
        desc_clean = description[: m.start()].strip()
        return desc_clean, caution
    return description, None


def parse_volume(basis_tags) -> str | None:
    """컵용량 문자열에서 ml/oz 정보 추출"""
    for tag in basis_tags:
        text = tag.get_text(strip=True)
        m = re.search(r"([\d,]+\s*ml(?:\s*\(\d+\s*oz\))?)", text)
        if m:
            return m.group(1).strip()
    return None


def parse_nutrition(table) -> dict:
    """ingredient_table → 영양성분 dict 변환"""
    nutrition = {}
    if not table:
        return nutrition
    for li in table.find_all("li"):
        divs = li.find_all("div")
        if len(divs) < 2:
            continue
        raw_key = divs[0].get_text(strip=True)
        raw_val = divs[1].get_text(strip=True)

        # 키 정규화 (괄호·단위 제거 후 매핑)
        key_clean = re.sub(r"\s*\([^)]*\)", "", raw_key).strip()
        en_key = None
        for ko, en in NUTRITION_KEY_MAP.items():
            if ko in key_clean:
                en_key = en
                break
        if not en_key:
            continue  # 알 수 없는 항목은 skip

        # 값 숫자 변환
        try:
            val = float(re.sub(r"[^\d.]", "", raw_val)) if raw_val else None
        except ValueError:
            val = None
        nutrition[en_key] = val
    return nutrition


def parse_menu_items(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    seen_names = set()   # 중복 제거용

    for idx, li in enumerate(soup.select("ul li"), start=1):
        # ── 이름 ───────────────────────────────────────────
        name_tag = li.select_one(".menu_tit") or li.select_one("h3.font-bl")
        if not name_tag:
            continue
        name = name_tag.get_text(strip=True)
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        # ── 영어명 ─────────────────────────────────────────
        name_en_tag = li.select_one(".menu_tit2")
        name_en = name_en_tag.get_text(strip=True) if name_en_tag else None
        name_en = name_en if name_en else None

        # ── 이미지 URL ─────────────────────────────────────
        img_tag = li.select_one(".thumb img")
        image_url = img_tag["src"] if img_tag and img_tag.get("src") else None

        # ── 설명 + 주의 ────────────────────────────────────
        desc_tag = li.select_one(".txt")
        if desc_tag:
            raw_desc = str(desc_tag)
            # 태그 내부만 추출
            inner = desc_tag.decode_contents()
            description_full = normalize_text(inner)
        else:
            description_full = None

        description, caution = (
            split_caution(description_full) if description_full else (None, None)
        )
        description = description if description else None

        # ── 컵 용량 ────────────────────────────────────────
        basis_tags = li.select(".menu_ingredient_basis")
        volume = parse_volume(basis_tags)

        # ── 알레르기 ───────────────────────────────────────
        allergen = None
        for tag in basis_tags:
            t = tag.get_text(strip=True)
            if "알레르기" in t:
                m = re.search(r"알레르기\s*유발\s*성분\s*:\s*(.+)", t)
                allergen = m.group(1).strip() if m else None
                break

        # ── 영양성분 ───────────────────────────────────────
        table = li.select_one(".ingredient_table")
        nutrition = parse_nutrition(table)

        # ── 안내 문구 ──────────────────────────────────────
        msg_tag = li.select_one(".msg")
        notice = msg_tag.get_text(strip=True).strip("()") if msg_tag else None

        # ── 조립 ───────────────────────────────────────────
        item = {
            "id": f"menu_{idx:03d}",
            "name": name,
            "name_en": name_en,
            "image_url": image_url,
            "description": description,
            "caution": caution,
            "allergen": allergen,
            "volume": volume,
            "nutrition": nutrition if nutrition else None,
            "notice": notice,
        }
        items.append(item)

    return items


# ── 메인 ─────────────────────────────────────────────────
if __name__ == "__main__":
    # 사용법 1: HTML 파일 경로를 인자로 전달
    # 사용법 2: 인자 없으면 실제 사이트 크롤링 시도
    if len(sys.argv) > 1:
        html_path = sys.argv[1]
        with open(html_path, encoding="utf-8") as f:
            html = f.read()
        print(f"[파일 로드] {html_path}", file=sys.stderr)
    else:
        # 실제 크롤링 (requests 필요)
        try:
            import requests
            url = "https://paikdabang.com/menu/menu_coffee/"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            html = resp.text
            print(f"[크롤링 성공] {url}", file=sys.stderr)
        except Exception as e:
            print(f"[크롤링 실패: {e}] 내장 HTML 샘플을 사용합니다.", file=sys.stderr)
            # 내장 HTML 없을 경우 빈 결과 반환
            html = ""

    menus = parse_menu_items(html)
    output = json.dumps(menus, ensure_ascii=False, indent=2)
    print(output)
    print(f"\n[완료] 총 {len(menus)}개 메뉴 파싱됨", file=sys.stderr)
