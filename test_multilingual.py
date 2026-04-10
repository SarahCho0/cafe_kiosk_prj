#!/usr/bin/env python3
"""
다국어 기능 테스트
"""
import sys
sys.path.insert(0, '/Users/jinjukim/Documents/GitHub/cafe_kiosk_prj')

try:
    print("[1] kiosk.py import 테스트...")
    from kiosk import get_system_prompt, SYSTEM_PROMPTS
    print("✅ kiosk.py imports OK")
    
    print("\n[2] 언어별 SYSTEM_PROMPT 확인...")
    for lang, prompt in SYSTEM_PROMPTS.items():
        print(f"  ✅ {lang} PROMPT: {len(prompt)} chars, 첫 50글자: {prompt[:50]}...")
        
    print("\n[3] get_system_prompt() 함수 테스트...")
    for lang in ["한", "영", "중", "일"]:
        p = get_system_prompt(lang)
        print(f"  ✅ get_system_prompt('{lang}'): {len(p)} chars")
        
    print("\n[4] 메뉴 통계 함수 테스트...")
    from kiosk import get_menu_stats, load_menu_data
    print("  ✅ get_menu_stats import OK")
    print("  ✅ load_menu_data import OK")
    
    print("\n[5] 매장 정보 로드 테스트...")
    from kiosk import load_store_info
    store = load_store_info()
    if store:
        print(f"  ✅ store_info 로드 OK: {store.get('store_name', '정보 없음')}")
        print(f"     - 좌석: {store['facilities']['seating']['total_seats']}석")
        print(f"     - 주소: {store.get('address', '정보 없음')}")
    else:
        print("  ⚠️  store_info 파일이 없거나 비어있음")
        
    print("\n" + "="*60)
    print("✅ 모든 다국어 기능 테스트 완료!")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
