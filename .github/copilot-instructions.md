# Copilot Instructions for cafe_kiosk_prj

This repository is a small Streamlit-based cafe menu project with three main UI entrypoints and supporting HTML parsing scripts.

## What this project is
- `app.py`: simple coffee menu viewer using `paikdabang_menu.json`.
- `app2.py`: full menu viewer using parsed DOM data from `paikdabang_menu_dom.json`, price extraction from `price.html`, and news from `paikdabang_news.json`.
- `kiosk.py`: AI kiosk chat interface using OpenAI + RAG over menu/news data.
- `parse_paikdabang_coffee.py`: parses raw HTML into JSON menu items.
- `parse_price_and_news.py`: extracts price info from `price.html` and merges it into `paikdabang_coffee_menu.json`.

## Key project patterns
- Streamlit apps are the primary user-facing code and are launched with `streamlit run <file>`.
- JSON is treated as the canonical menu/news data source; the apps read from JSON files in the repository root.
- `price.html` and `Paik's_news.html` are source HTML files used by parsing scripts, not by the UI directly.
- `kiosk.py` uses a local RAG index built from menu and news documents:
  - `TfidfVectorizer(analyzer="char_wb", ngram_range=(2,4), max_features=30000)`
  - if `scikit-learn` is absent, it falls back to simple keyword matching.
- `kiosk.py` uses OpenAI tool-style function calls for cart operations: `add_to_cart`, `remove_from_cart`, `complete_order`.
- `st.session_state` in `kiosk.py` stores chat history, cart state, order completion, feedback counts, and abuse count.

## Important implementation details
- `app2.py` normalizes menu names before matching price values from `price.html`.
- `kiosk.py` builds RAG docs from:
  - menu items in `paikdabang_menu_dom.json`
  - prices parsed from `price.html`
  - news items in `paikdabang_news.json`
  - a fixed option guidance block for hot/iced, decaf, big-size, and payment methods.
- The assistant prompt in `kiosk.py` is a strong HTI-style persona with explicit role, language support, and failure handling.
- `kiosk.py` expects OpenAI API access via `OPENAI_API_KEY` or sidebar input.
- There is no automated test suite in this repository; manual `streamlit run ...` is the main validation path.

## Developer workflow
- Install dependencies manually:
  - `pip install streamlit beautifulsoup4 scikit-learn openai`
- Run UI apps:
  - `streamlit run app.py`
  - `streamlit run app2.py`
  - `streamlit run kiosk.py`
- Parse or refresh data files using:
  - `python parse_paikdabang_coffee.py <html-file>` or no argument for crawling
  - `python parse_price_and_news.py`
- `kiosk.py` will still work without `scikit-learn`, but the RAG retrieval quality is lower.

## What to preserve
- Keep the JSON schemas intact; menu items include fields such as `name`, `name_en`, `image_url`, `description`, `caution`, `allergen`, `volume`, `nutrition`, `notice`, `category`, `price_won`.
- Maintain `kiosk.py`’s tool interface semantics when modifying the chatbot flow.
- Preserve the specific filtering behavior in `app.py` and `app2.py` around HOT/ICED, decaf, and best menu items.

## When editing AI behavior
- In `kiosk.py`, follow the existing prompt and tool-based order flow.
- Use the menu/news docs as the only source for factual responses.
- For unknown menu details, respond with the repository’s current fallback style:
  - "해당 정보를 찾을 수 없어요 😅"
- Do not invent prices or nutrition values beyond what is available in `paikdabang_price.json`, `paikdabang_menu_dom.json`, or parsed HTML.

## Notes for Copilot agents
- No CI/test config was found, so do not assume GitHub Actions or pytest are present.
- This repository is primarily local, file-based, and Streamlit-driven, not a packaged Python application.
- If asked to add features, prefer extending existing Streamlit files rather than introducing a new web server.
- Avoid changing the root data file structure unless the user explicitly requests a data schema update.
