<div align="center">

<br/>

# ☕ 5지는 카페 키오스크

**AI-powered cafe kiosk · Natural language ordering in 4 languages**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/GPT--4o--mini-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![scikit-learn](https://img.shields.io/badge/TF--IDF_RAG-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)

<br/>

[![📋 Kiosk Features](https://img.shields.io/badge/📋_Kiosk-Features_%26_Spec-6F4E37?style=for-the-badge)](kiosk.md)
[![🗄️ Data & RAG](https://img.shields.io/badge/🗄️_Data-Parsing_%26_RAG-4A86C8?style=for-the-badge)](parsing.md)

<br/>

</div>

---

## Overview

**5지는 카페 키오스크** is a Streamlit-based AI ordering system built on **Paik's Coffee (빽다방)** menu data.
The GPT-4o-mini powered chatbot **Oji (오지)** takes natural language orders, manages a cart, and guides checkout — all in **Korean, English, Chinese, and Japanese**.

| | `kiosk.py` | `app2.py` | `app.py` |
|---|---|---|---|
| **Role** | AI kiosk · main app | Full menu browser | Coffee viewer |
| **AI Chat** | ✅ GPT-4o-mini + TF-IDF RAG | — | — |
| **Cart & Checkout** | ✅ 7-step flow with options | — | — |
| **Languages** | 🇰🇷 🇺🇸 🇨🇳 🇯🇵 | — | — |
| **Menu Count** | 332 items | 332 items | Coffee only |

---

## Quick Start

**1 · Install dependencies**

```bash
pip install -r requirements.txt
```

**2 · Set your OpenAI API key**

```bash
export OPENAI_API_KEY="sk-..."
```

> Or enter it directly in the app sidebar.

**3 · Run**

```bash
streamlit run kiosk.py      # ← AI kiosk (recommended)
streamlit run app2.py       # Full menu browser
streamlit run app.py        # Coffee menu viewer
```

---

## Project Structure

```
cafe_kiosk/
├── kiosk.py                     # AI kiosk — Oji  ← main app
├── app2.py                      # Full menu viewer
├── app.py                       # Coffee menu viewer
├── parse_paikdabang_coffee.py   # Menu HTML parser
├── parse_price_and_news.py      # Price & news parser
├── requirements.txt
├── paikdabang_menu_rev.json     # Full menu + prices  ← kiosk.py & app2.py
├── paikdabang_menu_dom.json     # Raw parsed menu DOM
├── paikdabang_coffee_menu.json  # Coffee-only menu    ← app.py
├── paikdabang_news.json         # Events & news
├── menu_options.json            # Add-on options (shots, syrups…)
├── store_info.json              # Store details
├── kiosk.md                     # ↗ Kiosk feature spec
└── parsing.md                   # ↗ Data & RAG structure
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| AI | OpenAI GPT-4o-mini |
| Retrieval (RAG) | scikit-learn · TF-IDF char n-gram (2–4) · cosine similarity |
| Parsing | BeautifulSoup4 |
| Data | JSON files — no database |

---

## Refresh Menu Data

```bash
python parse_paikdabang_coffee.py   # Re-parse menu HTML  → paikdabang_menu_dom.json
python parse_price_and_news.py      # Update prices & news → paikdabang_menu_rev.json
```

---

<details>
<summary>🇰🇷 &nbsp;한국어 설명 보기</summary>
<br/>

## 개요

**5지는 카페 키오스크**는 빽다방 메뉴 데이터 기반의 Streamlit AI 주문 시스템입니다.
GPT-4o-mini 챗봇 **오지(Oji)**가 자연어로 주문을 받고, 장바구니 관리와 결제 안내를 진행합니다.
**한국어 · 영어 · 중국어 · 일본어** 4개 언어를 지원합니다.

## 빠른 시작

```bash
# 의존성 설치
pip install -r requirements.txt

# OpenAI API 키 설정
export OPENAI_API_KEY="sk-..."

# 실행
streamlit run kiosk.py      # AI 키오스크 (오지) ← 메인 앱
streamlit run app2.py       # 전체 메뉴 뷰어
streamlit run app.py        # 커피 메뉴 뷰어
```

## 데이터 갱신

```bash
python parse_paikdabang_coffee.py   # 메뉴 HTML 재파싱 → paikdabang_menu_dom.json
python parse_price_and_news.py      # 가격·뉴스 갱신   → paikdabang_menu_rev.json
```

</details>
