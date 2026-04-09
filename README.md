# ☕ 빽다방 카페 키오스크 프로젝트

빽다방(Baek's Coffee) 메뉴 데이터를 기반으로 한 Streamlit 웹 앱 및 AI 키오스크 프로젝트입니다.

---

## 📁 파일 구조

```
cafe_kiosk/
├── app.py                        # 커피 메뉴 뷰어 (기본)
├── app2.py                       # 전체 메뉴 뷰어 (확장)
├── kiosk.py                      # AI 키오스크 빽이 (OpenAI)
├── parse_paikdabang_coffee.py    # 커피 메뉴 파싱 스크립트
├── parse_price_and_news.py       # 가격 및 뉴스 파싱 스크립트
├── analyze_price.py              # 가격 분석 스크립트
├── paikdabang_coffee_menu.json   # 커피 메뉴 데이터 (app.py 사용)
├── paikdabang_menu_dom.json      # 전체 메뉴 DOM 파싱 원본 데이터
├── paikdabang_menu_rev.json      # 전체 메뉴 + 가격 통합 데이터 (app2.py, kiosk.py 사용)
├── paikdabang_price.json         # 가격 데이터
├── paikdabang_news.json          # 소식/이벤트 데이터
└── Paik's_news.html              # 뉴스 HTML (파싱용)
```

---

## ⚙️ 설치

```bash
pip install streamlit scikit-learn openai
```

> `kiosk.py`는 OpenAI API 키가 필요합니다. 아래 환경 변수를 설정하세요.
>
> ```bash
> export OPENAI_API_KEY="sk-..."
> ```

---

## 🚀 실행 방법

### app.py — 커피 메뉴 뷰어 (기본)

```bash
streamlit run app.py
```

### app2.py — 전체 메뉴 뷰어 (확장)

```bash
streamlit run app2.py
```

### kiosk.py — AI 키오스크 빽이

```bash
streamlit run kiosk.py
```

---

## 🔍 app.py / app2.py / kiosk.py 차이점

| 항목 | `app.py` | `app2.py` | `kiosk.py` |
|------|----------|-----------|------------|
| **목적** | 커피 메뉴 조회 | 전체 메뉴 조회 | AI 자연어 주문 |
| **데이터 소스** | `paikdabang_coffee_menu.json` | `paikdabang_menu_rev.json` | `paikdabang_menu_rev.json` |
| **가격 표시** | ❌ 없음 | ✅ 전체 메뉴 가격 표시 (332개) | ✅ 있음 |
| **카테고리 탭** | ❌ 없음 (단일 목록) | ✅ 커피/신메뉴/음료/빽스치노/아이스크림·디저트/소식 | ❌ 없음 |
| **소식/이벤트** | ❌ 없음 | ✅ 소식 탭 (`paikdabang_news.json`) | ❌ 없음 |
| **필터** | 온도, 디카페인/일반, 검색 | 온도, 디카페인/일반, 베스트 메뉴, 검색, 카페인 범위 슬라이더 | 채팅으로 자연어 처리 |
| **정렬** | 칼로리·카페인 기준 | 가격·칼로리·카페인 기준 | - |
| **베스트 메뉴 필터** | ❌ | ✅ | - |
| **AI 기능** | ❌ | ❌ | ✅ (OpenAI GPT + RAG) |
| **장바구니** | ❌ | ❌ | ✅ (추가/제거/결제) |
| **다국어 지원** | ❌ | ❌ | ✅ (한/영/중/일) |
| **필요 패키지** | `streamlit` | `streamlit` | `streamlit`, `scikit-learn`, `openai` |

### 간단 요약

- **`app.py`**: 커피 메뉴만 보여주는 심플한 뷰어. 이미지·영양성분·고카페인 경고 제공.
- **`app2.py`**: 전체 메뉴 332개 + 가격 + 소식까지 포함한 완전한 메뉴판. 카테고리 탭과 카페인 슬라이더 등 필터가 더 풍부함.
- **`kiosk.py`**: AI 캐릭터 **빽이(Paikki)**와 채팅으로 주문하는 키오스크. TF-IDF 기반 RAG로 메뉴를 검색하고, OpenAI Function Calling으로 장바구니를 조작함.
