# ☕ 5지는 카페 키오스크

빽다방 메뉴 데이터 기반의 Streamlit 메뉴 뷰어 및 AI 주문 키오스크 프로젝트입니다.

---

## 파일 구조

```
cafe_kiosk/
├── kiosk.py                     # AI 키오스크 — 오지(Oji)  ← 메인 앱
├── app.py                       # 커피 메뉴 뷰어
├── app2.py                      # 전체 메뉴 뷰어
├── parse_paikdabang_coffee.py   # 메뉴 HTML 파싱 스크립트
├── parse_price_and_news.py      # 가격·뉴스 파싱 스크립트
├── requirements.txt             # 의존성 목록
├── paikdabang_menu_rev.json     # 전체 메뉴 + 가격 (kiosk.py, app2.py)
├── paikdabang_menu_dom.json     # 메뉴 DOM 원본 (파싱 중간 결과물)
├── paikdabang_coffee_menu.json  # 커피 메뉴 (app.py)
├── paikdabang_news.json         # 소식·이벤트
├── menu_options.json            # 추가 옵션 (추가샷/시럽 등)
├── store_info.json              # 매장 정보
├── Paik's_news.html             # 뉴스 HTML 원본 (파싱용)
├── kiosk.md                     # AI 키오스크 기능 명세 →
└── parsing.md                   # 데이터 파싱·RAG 구조 →
```

---

## 설치

```bash
pip install -r requirements.txt
```

`kiosk.py`는 OpenAI API 키가 필요합니다. 환경 변수로 설정하거나 앱 사이드바에서 직접 입력할 수 있습니다.

```bash
export OPENAI_API_KEY="sk-..."
```

---

## 실행

```bash
streamlit run kiosk.py      # AI 키오스크 (오지)
streamlit run app2.py       # 전체 메뉴 뷰어
streamlit run app.py        # 커피 메뉴 뷰어
```

---

## 앱 구성

|  | `kiosk.py` | `app2.py` | `app.py` |
|---|---|---|---|
| **목적** | AI 자연어 주문 | 전체 메뉴 조회 | 커피 메뉴 조회 |
| **AI 챗봇** | ✅ GPT-4o-mini + TF-IDF RAG | ❌ | ❌ |
| **장바구니·결제** | ✅ 옵션 포함, 7단계 결제 | ❌ | ❌ |
| **다국어** | ✅ 한·영·중·일 | ❌ | ❌ |
| **메뉴 수** | 332개 | 332개 | 커피만 |

> 기능 상세 스펙 → [kiosk.md](kiosk.md)
> 데이터 파싱·RAG 구조 → [parsing.md](parsing.md)

---

## 데이터 갱신

```bash
python parse_paikdabang_coffee.py    # 메뉴 HTML 재파싱 → paikdabang_menu_dom.json
python parse_price_and_news.py       # 가격·뉴스 갱신 → paikdabang_menu_rev.json
```
