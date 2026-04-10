#!/usr/bin/env python3
# 빽이/빽다방 → 오지/5지는 카페 일괄 치환
import re

path = "/Users/hyeonjucho/Downloads/cafe_kiosk_prj/kiosk.py"
c = open(path, encoding="utf-8").read()

subs = [
    # --- 한국어 시스템 프롬프트 ---
    ("당신은 빽다방(Baek's Coffee)의 AI 키오스크 직원 '빽이(Paikki)'입니다.",
     "당신은 5지는 카페(Ojineun Cafe)의 AI 키오스크 직원 '오지(Oji)'입니다."),
    ("- 이름: 빽이 (Paikki)", "- 이름: 오지 (Oji)"),
    ('- 브랜드 슬로건: "싸다! 크다! 맛있다!"', '- 브랜드 슬로건: "오지는 맛! 오지는 가격! 오지는 카페!"'),
    ("- 매장명: 빽다방 낙성점", "- 매장명: 5지는 카페 낙성점"),
    ("저는 빽다방 키오스크 빽이예요! 음료/디저트 주문만 도와드릴 수 있어요 ☕",
     "저는 5지는 카페 키오스크 오지예요! 음료/디저트 주문만 도와드릴 수 있어요 ☕"),
    # --- 영어 시스템 프롬프트 ---
    ("You are Paikki, the AI kiosk staff at Baek's Coffee (빽다방).",
     "You are Oji, the AI kiosk staff at Ojineun Cafe (5지는 카페)."),
    ("- Name: Paikki", "- Name: Oji"),
    ('- Brand Slogan: "Cheap! Big! Delicious!"', '- Brand Slogan: "Amazing Taste! Amazing Price! Amazing Cafe!"'),
    ("- Store: Baek's Coffee Nakseongdae", "- Store: Ojineun Cafe Nakseongdae"),
    ("I'm Paikki, the Baek's Coffee kiosk staff", "I'm Oji, the Ojineun Cafe kiosk staff"),
    # --- 중국어 시스템 프롬프트 ---
    ("你是Paikki，Baek's Coffee(빽다방)的AI自助点餐机店员。",
     "你是Oji，5지는 카페(Ojineun Cafe)的AI自助点餐机店员。"),
    ('- 姓名: Paikki  品牌标语: "便宜!大!好吃!"',
     '- 姓名: Oji  品牌标语: "超赞的味道!超赞的价格!超赞的咖啡厅!"'),
    ("- 门店: 빽다방 落星店", "- 门店: 5지는 카페 落星店"),
    ("我是빽다방点餐机Paikki！只能帮您点饮料/甜点 ☕",
     "我是5지는 카페点餐机Oji！只能帮您点饮料/甜点 ☕"),
    ("我是빽다방自助点餐机Paikki ☕", "我是5지는 카페 Oji ☕"),
    # --- 일본어 시스템 프롬프트 ---
    ("あなたはPaikki、Baek's Coffee(빽다방)のAIキオスク店員です。",
     "あなたはOji、5지는 카페(Ojineun Cafe)のAIキオスク店員です。"),
    ('- 名前: Paikki  スローガン: "安い！大きい！美味しい！"',
     '- 名前: Oji  スローガン: "最高の味！最高の価格！最高のカフェ！"'),
    ("- 店舗: 빽다방 落星店", "- 店舗: 5지는 카페 落星店"),
    ("私はPaik'sキオスクのPaikkiです！飲み物・デザートのみご案内できます ☕",
     "私は5지는 카페のOjiです！飲み物・デザートのみご案内できます ☕"),
    ("こんにちは！私はPaikki、빽다방のキオスク店員",
     "こんにちは！私はOji、5지는 카페のキオスク店員"),
    # --- 인사말 fallbacks ---
    ('"ko": "안녕하세요! 빽다방 키오스크 빽이입니다',
     '"ko": "안녕하세요! 5지는 카페 키오스크 오지입니다'),
    ('"en": "Hello! I\'m Paikki, the Baek\'s Coffee kiosk staff',
     '"en": "Hello! I\'m Oji, the Ojineun Cafe kiosk staff'),
    ('"cn": "你好！我是빽다방自助点餐机Paikki',
     '"cn": "你好！我是5지는 카페 Oji'),
    # --- 스피너/응답 메시지 ---
    ("빽이 응답 중...", "오지 응답 중..."),
    ("빽이 준비 중... ☕", "오지 준비 중... ✨"),
    ("빽이가 답변 준비 중... ☕", "오지가 답변 준비 중... ✨"),
    # --- 사이드바 브랜드 ---
    ('<div style="color:#FFD600;font-weight:900;font-size:1.3em;letter-spacing:2px">빽다방</div>',
     '<div style="color:#1A2B5E;font-weight:900;font-size:1.15em;letter-spacing:2px">5지는 카페 ✨</div>'),
    ('<div style="color:#aab4d8;font-size:.75em">Paik\'s Coffee</div>',
     '<div style="color:#5A73A8;font-size:.75em">Ojineun Cafe</div>'),
    # --- 기타 잔여 빽이/Paikki ---
    ("빽이", "오지"),
    ("Paikki", "Oji"),
]

count = 0
for old, new in subs:
    if old in c:
        c = c.replace(old, new)
        count += 1
    else:
        print(f"NOT FOUND: {old[:60]}")

open(path, "w", encoding="utf-8").write(c)
print(f"완료: {count}개 치환됨. '오지' 등장 횟수: {c.count('오지')}")
