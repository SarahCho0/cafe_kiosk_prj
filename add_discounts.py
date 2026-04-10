# add_discounts.py

import json

# 뉴스 파일 읽기
with open('paikdabang_news.json', 'r', encoding='utf-8') as f:
    news_data = json.load(f)

# 할인 정보 추가
discounts = {
    85: None,
    84: {"rate": 10, "start_date": "2026-03-26", "end_date": "2026-04-30", "description": "건강음식 신메뉴 10% 할인"},
    83: {"rate": 15, "start_date": "2026-03-26", "end_date": "2026-05-31", "description": "제로슈거 신메뉴 15% 할인"},
    82: {"rate": 20, "start_date": "2026-03-19", "end_date": "2026-04-30", "description": "에어폼 신메뉴 20% 할인"},
    81: None,
    80: {"rate": 12, "start_date": "2026-02-26", "end_date": "2026-04-30", "description": "망고피치 신메뉴 12% 할인"},
    79: {"rate": 18, "start_date": "2026-02-05", "end_date": "2026-04-30", "description": "크런키 콜라보 신메뉴 18% 할인"},
    78: None,
    77: None,
    76: {"rate": 25, "start_date": "2026-01-02", "end_date": "2026-02-28", "description": "말차 관련 메뉴 25% 할인 (앱 픽업오더 전용)"}
}

# 각 뉴스 항목에 할인 필드 추가
for item in news_data:
    item_id = item['id']
    item['discount'] = discounts.get(item_id)

# 파일에 쓰기
with open('paikdabang_news.json', 'w', encoding='utf-8') as f:
    json.dump(news_data, f, ensure_ascii=False, indent=2)

print("✅ [완료] paikdabang_news.json에 할인정보 추가: 6개 이벤트 적용")
print("   - 건강음식 신메뉴: 10% (ID 84)")
print("   - 제로슈거 신메뉴: 15% (ID 83)")
print("   - 에어폼 신메뉴: 20% (ID 82)")
print("   - 망고피치 신메뉴: 12% (ID 80)")
print("   - 크런키 콜라보: 18% (ID 79)")
print("   - 말차 메뉴: 25% (ID 76)")
