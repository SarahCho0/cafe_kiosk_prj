# 5지는 카페 키오스크 데이터 파싱 및 RAG 구조 정리

## 1. 전체 흐름 요약

이 프로젝트는 **DB에 저장하지 않고**, 파싱된 JSON 파일을 런타임에 읽어 **TF-IDF 임베딩 벡터**로 변환 후 유사도 검색(RAG)으로 AI 답변을 생성합니다.

```
HTML 소스 파일
  └─ 파싱 스크립트 (BeautifulSoup)
       └─ JSON 파일 (정형 데이터)
            └─ build_rag_docs() → 텍스트 문서 리스트
                 └─ TfidfVectorizer (char n-gram 2~4)
                      └─ cosine_similarity → 상위 k개 문서 검색
                           └─ OpenAI GPT 프롬프트에 컨텍스트로 주입
```

---

## 2. 파싱 스크립트

### 2-1. `parse_paikdabang_coffee.py`
- **입력**: 빽다방 공식 사이트 HTML (크롤링 또는 로컬 `.html` 파일)
- **출력**: `paikdabang_menu_dom.json`
- **파서**: `BeautifulSoup` (html.parser)
- **파싱 대상 HTML 셀렉터**:
  | 필드 | 셀렉터 |
  |---|---|
  | 메뉴명 | `.menu_tit`, `h3.font-bl` |
  | 영문명 | `.menu_tit2` |
  | 이미지 | `.thumb img` |
  | 설명 | `.txt` |
  | 컵 용량 | `.menu_ingredient_basis` (ml/oz 정규식 추출) |
  | 알레르기 | `.menu_ingredient_basis` (알레르기 유발 성분 키워드 매칭) |
  | 영양성분 | `.ingredient_table` li 목록 |
  | 안내 문구 | `.msg` |
- **주의 문구 분리 (`split_caution`)**: 설명 텍스트에서 "고카페인 함유..." 계열 문구를 정규식으로 분리하여 `caution_note` 필드에 저장
- **영양성분 키 매핑**:
  | 원문 | JSON 키 |
  |---|---|
  | 카페인 | `caffeine_mg` |
  | 칼로리 | `kcal` |
  | 나트륨 | `sodium_mg` |
  | 당류 | `sugar_g` |
  | 포화지방 | `sat_fat_g` |
  | 단백질 | `protein_g` |

### 2-2. `parse_price_and_news.py`
- **입력**: `price.html` (로컬 HTML 파일)
- **출력**: `paikdabang_menu_dom.json` 및 `paikdabang_coffee_menu.json`에 `price_won` 필드 추가
- **파싱 방식**:
  1. `div.single-menu` → 카테고리 추출
  2. `div.menuitem` → 메뉴명 + 가격(정규식 `[\d,]+원`) 추출
  3. 메뉴명을 `normalize()` 함수로 정규화 후 JSON과 매칭하여 `price_won` 필드를 덮어씀

---

## 3. 파싱된 데이터 파일 및 필드

### 3-1. `paikdabang_menu_dom.json` — 메인 메뉴 정보 (332개)
| 필드 | 설명 | 예시 |
|---|---|---|
| `brand` | 브랜드명 | `"빽다방"` |
| `category` | 카테고리 | `"신메뉴"`, `"커피"`, `"음료"`, `"아이스크림/디저트"`, `"빽스치노"` |
| `menu_name` | 한국어 메뉴명 | `"에어폼 아메리카노(ICED)"` |
| `eng_name` | 영문 메뉴명 | `"AIR FOAM AMERICANO"` |
| `description` | 메뉴 설명 | `"아메리카노의 깔끔한 풍미는..."` |
| `caution_note` | 고카페인 등 주의 문구 | `"고카페인 함유) 어린이/임산부..."` |
| `allergen` | 알레르기 유발 성분 | `"우유, 대두"` |
| `cup_volume` | 컵 용량 | `"710 ml(24 oz)"` |
| `serving_size` | 1회 제공량 | `NaN` (일부 미정) |
| `availability_notice` | 판매 가능 여부 안내 | `"(매장 상황에 따라 판매하지 않을 수 있습니다.)"` |
| `is_best` | 베스트 메뉴 여부 | `true` / `false` |
| `nutrition` | 영양성분 dict | `{"caffeine_mg": "293", "kcal": "21.9", ...}` |
| `price_won` | 가격 (원) | `3000` |
| `image_url` | 메뉴 이미지 URL | `"https://paikdabang.com/..."` |
| `source_url` | 파싱 소스 URL | `"https://paikdabang.com/menu/..."` |

**카테고리 목록**: 신메뉴 / 커피 / 음료 / 아이스크림·디저트 / 빽스치노

### 3-2. `paikdabang_news.json` — 소식 및 이벤트 (10개)
| 필드 | 설명 |
|---|---|
| `id` | 게시글 ID |
| `category` | `"이벤트"`, `"신메뉴"` 등 |
| `title` | 제목 |
| `date` | 날짜 (`YYYY-MM-DD`) |
| `views` | 조회수 |
| `url` | 원문 링크 |
| `discount` | 할인 정보 dict (`rate`, `start_date`, `end_date`, `description`) 또는 `null` |

### 3-3. `menu_options.json` — 메뉴 옵션 정보
| 옵션 | 가격 | 적용 카테고리 |
|---|---|---|
| 추가 샷 | +500원 | 커피, 빽스치노 |
| 시럽 추가 (바닐라/헤이즐넛/카라멜/초콜릿) | +300원 | 커피, 음료, 빽스치노 |
| 우유 변경 (두유/아몬드유/귀리유 등) | +500원 | 커피, 빽스치노 |
| 빽사이즈 업 | +1,000원 | 커피, 음료 |
| 휘핑크림 추가 | +400원 | 전 메뉴 |

최상위 키: `options` (옵션 목록), `option_groups` (그룹별), `popular_combinations` (인기 조합)

### 3-4. `store_info.json` — 매장 정보
| 필드 | 내용 |
|---|---|
| 매장명 | 5지는 카페 |
| 주소 | 서울시 강남구 강남대로 100 |
| 전화 | 02-6955-0123 |
| 영업시간 | 평일 07:00~23:00, 주말 08:00~23:00 |
| 좌석 | 총 45석 (실내 30석, 야외 15석) |
| 주차 | 무료 2시간 |
| 무선인터넷 | 있음 |
| 콘센트 | 다수 |
| 결제수단 | 카드, 현금, 모바일페이 |
| 배달 | 배달의민족, 요기요 |

---

## 4. RAG 구성 방식 (`kiosk.py`)

### 4-1. `build_rag_docs()` — 텍스트 문서 생성
JSON 파일들을 읽어 검색 가능한 텍스트 문서 리스트(`list[dict]`)로 변환합니다.

| 문서 유형 | 소스 | 포함 정보 |
|---|---|---|
| 메뉴 문서 | `paikdabang_menu_dom.json` | 메뉴명, 영문명, 카테고리, 온도, 디카페인 여부, 베스트 여부, 가격, 용량, 설명, 옵션, 알레르기, 영양성분, 주의사항 |
| 소식/이벤트 문서 | `paikdabang_news.json` | 제목, 분류, 날짜, 조회수, 링크, 할인정보 |
| 옵션 안내 문서 | `menu_options.json` | 추가 가능한 옵션 전체 목록 + 가격 |
| 메뉴 통계 문서 | `paikdabang_menu_dom.json` 집계 | 전체 메뉴 수, 카테고리별 수, 베스트 수, 디카페인 수 |
| 매장 정보 문서 | `store_info.json` | 주소, 전화, 영업시간, 좌석, 화장실, 주차, WiFi, 결제수단, 배달 |

### 4-2. `build_rag_index()` — TF-IDF 인덱스 빌드
```python
TfidfVectorizer(
    analyzer="char_wb",    # 문자 단위 n-gram (한국어 형태소 분석 불필요)
    ngram_range=(2, 4),    # 2~4글자 n-gram
    max_features=30000     # 최대 특성 수
)
```
- `@st.cache_resource` 데코레이터로 **최초 1회만 빌드** 후 메모리에 캐싱
- scikit-learn 미설치 시 단순 키워드 포함 여부로 폴백

### 4-3. `retrieve(query, k=6)` — 유사도 검색
1. 쿼리를 같은 TfidfVectorizer로 변환
2. `cosine_similarity`로 전체 문서와 유사도 계산
3. 상위 `k`개 문서를 `---` 구분자로 이어 반환
4. 임계치 `0.005` 이하 문서는 제외

### 4-4. GPT 프롬프트 주입 방식
```
[시스템 프롬프트: 페르소나/언어/규칙 정의]
  +
[Menu Info]: retrieve(query) 결과 (RAG 검색 문서)
  +
[대화 히스토리]
  +
[사용자 메시지]
```
- 가격·영양성분은 RAG 데이터 값만 사용, 임의 생성 금지
- 정보 없을 시: `"해당 정보를 찾을 수 없어요 😅"` 반환

---

## 5. 데이터 갱신 방법

| 작업 | 명령 |
|---|---|
| 메뉴 HTML 재파싱 | `python parse_paikdabang_coffee.py` (크롤링) 또는 `python parse_paikdabang_coffee.py <html파일>` |
| 가격 정보 갱신 | `python parse_price_and_news.py` (`price.html` 필요) |
| RAG 인덱스 재빌드 | `kiosk.py` 재시작 시 자동 (`@st.cache_resource` 초기화) |
