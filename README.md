# ☕ 5지는 카페 키오스크 프로젝트

5지는 카페(Ojineun Cafe) 메뉴 데이터를 기반으로 한 Streamlit 웹 앱 및 AI 키오스크 프로젝트입니다.

---

## 📁 파일 구조

```
cafe_kiosk/
├── app.py                        # 커피 메뉴 뷰어 (기본)
├── app2.py                       # 전체 메뉴 뷰어 (확장)
├── kiosk.py                      # AI 키오스크 오지 (OpenAI + RAG)
├── parse_paikdabang_coffee.py    # 커피 메뉴 파싱 스크립트
├── parse_price_and_news.py       # 가격 및 뉴스 파싱 스크립트
├── analyze_price.py              # 가격 분석 스크립트
├── requirements.txt              # 의존성 목록
├── paikdabang_coffee_menu.json   # 커피 메뉴 데이터 (app.py 사용)
├── paikdabang_menu_dom.json      # 전체 메뉴 DOM 파싱 원본 데이터
├── paikdabang_menu_rev.json      # 전체 메뉴 + 가격 통합 데이터 (app2.py, kiosk.py 사용)
├── paikdabang_price.json         # 가격 데이터
├── paikdabang_news.json          # 소식/이벤트 데이터
├── menu_options.json             # 메뉴 옵션 데이터 (추가샷/시럽 등)
├── store_info.json               # 매장 정보 데이터
├── parsing.md                    # 데이터 파싱 구조 설명
├── kiosk.md                      # 키오스크 기능 명세서
└── Paik's_news.html              # 뉴스 HTML (파싱용)
```

---

## ⚙️ 설치

```bash
pip install -r requirements.txt
```

> `kiosk.py`는 OpenAI API 키가 필요합니다.
>
> ```bash
> export OPENAI_API_KEY="sk-..."
> ```
> 또는 앱 실행 후 사이드바에서 직접 입력할 수 있습니다.

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

### kiosk.py — AI 키오스크 오지

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
| **AI 기능** | ❌ | ❌ | ✅ (OpenAI GPT-4o-mini + TF-IDF RAG) |
| **장바구니** | ❌ | ❌ | ✅ (추가/제거/결제 + 옵션 버튼식) |
| **다국어 지원** | ❌ | ❌ | ✅ (한/영/중/일) |
| **필요 패키지** | `streamlit` | `streamlit` | `streamlit`, `scikit-learn`, `openai` |

### 간단 요약

- **`app.py`**: 커피 메뉴만 보여주는 심플한 뷰어. 이미지·영양성분·고카페인 경고 제공.
- **`app2.py`**: 전체 메뉴 332개 + 가격 + 소식까지 포함한 완전한 메뉴판. 카테고리 탭과 카페인 슬라이더 등 필터가 더 풍부함.
- **`kiosk.py`**: AI 캐릭터 **오지(Oji)**와 채팅으로 주문하는 키오스크. TF-IDF 기반 RAG로 메뉴를 검색하고, OpenAI Function Calling으로 장바구니를 조작함. 옵션 버튼식(expander) 데개, 다언어 지원, 결제 7단계 플로우 포함.
