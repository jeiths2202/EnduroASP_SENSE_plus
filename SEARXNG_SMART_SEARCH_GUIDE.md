# 🔍 SearXNG Smart Search Service 사용 가이드

## 개요
SearXNG + LangChain을 활용한 프라이버시 중심의 지능형 검색 서비스입니다. Tavily API 키 없이도 웹 검색이 가능하며, 쿼리 특성에 따라 로컬 RAG와 웹 검색을 자동으로 선택합니다.

## 주요 장점

### 🔐 프라이버시
- **완전한 프라이버시**: 사용자 추적 없음
- **메타 검색 엔진**: 여러 검색 엔진 결과 통합
- **API 키 불필요**: 무료로 사용 가능

### 🌐 다양한 검색 소스
- Google, Bing, DuckDuckGo, Wikipedia
- GitHub, StackOverflow (기술 검색)
- ArXiv, PubMed (학술 검색)
- 70개 이상의 검색 엔진 지원

### 💰 비용 효율성
- **무료**: API 키 불필요
- **무제한 검색**: 사용량 제한 없음
- **Fallback 지원**: SearXNG 불가시 mock 결과 제공

## API 사용법

### 1. SearXNG Smart Search API
```bash
POST /api/searxng-search
{
    "query": "Python programming tutorial",
    "max_results": 5,
    "searxng_url": "optional_custom_url"
}
```

### 2. Chat API with SearXNG (향후 통합 예정)
```bash
POST /api/chat
{
    "message": "최신 AI 뉴스를 알려줘",
    "model": "Gemma3 270M",
    "use_searxng_search": true
}
```

### 3. 라우팅 테스트
```bash
POST /api/searxng-search/route
{
    "query": "Latest AI developments"
}
```

### 4. 서비스 상태 확인
```bash
GET /api/searxng-search/status
```

## 설정 방법

### 1. 환경 변수 설정 (선택사항)
```bash
# .env 파일에 추가
SEARXNG_URL=https://your-custom-searxng-instance.com
```

### 2. 지원되는 SearXNG 인스턴스
기본적으로 다음 공개 인스턴스들을 자동으로 시도합니다:
- https://search.sapti.me
- https://searx.be  
- https://searx.tiekoetter.com
- https://searx.prvcy.eu

## 쿼리 예시 및 라우팅

### 🏠 로컬 RAG로 라우팅되는 쿼리
- "COBOLG 컴파일러 구현 방법"
- "시스템 명령어 구현 가이드"
- "CALL 프로그램 호출 방법"
- "AS/400 마이그레이션"

### 🌐 웹 검색으로 라우팅되는 쿼리
- "2025년 최신 AI 뉴스"
- "오늘 서울 날씨"
- "현재 주식 시세"
- "Python tutorial 2025"

### 🔄 하이브리드로 라우팅되는 쿼리
- "시스템 명령어 최신 동향"
- "프로그래밍 가이드 업데이트"
- "기술 문서 및 최신 정보"

## 응답 형식

### SearXNG Search API 응답
```json
{
    "success": true,
    "query": "Python tutorial",
    "route_used": "web_search",
    "results": [
        {
            "content": "검색 결과 내용...",
            "source": "https://example.com",
            "score": 0.9,
            "source_type": "web_search",
            "metadata": {
                "title": "Python Tutorial",
                "engine": "searxng",
                "category": "general",
                "searxng_url": "https://search.sapti.me"
            }
        }
    ],
    "total_results": 5,
    "search_time": 2.1,
    "timestamp": "2025-08-17T..."
}
```

### 서비스 상태 응답
```json
{
    "success": true,
    "status": {
        "rag_available": true,
        "web_search_available": true,
        "llm_available": true,
        "cache_size": 0,
        "supported_routes": ["local_rag", "web_search", "hybrid"],
        "searxng_engines": ["google", "bing", "duckduckgo", "wikipedia"]
    },
    "service_type": "searxng",
    "timestamp": 1692181234.567
}
```

## 성능 특징

### ⚡ 속도
- **로컬 RAG**: 0.01-0.03초
- **웹 검색**: 2-5초 (SearXNG 응답 시간)
- **하이브리드**: 1-3초
- **Fallback**: 0.1초 (mock 결과)

### 🎯 정확도
- **로컬 RAG**: 문서 기반 질의에 높은 정확도
- **웹 검색**: 실시간 정보에 최적화
- **하이브리드**: 종합적인 정보 제공
- **Fallback**: 서비스 연속성 보장

### 💾 캐싱
- 웹 검색 결과 5분간 캐시
- 동일 쿼리 재검색 시 즉시 응답

## Fallback 모드

SearXNG 인스턴스가 모두 사용 불가능한 경우:
- Mock 검색 결과 제공
- 서비스 연속성 유지
- 사용자에게 명확한 피드백

## 문제 해결

### 웹 검색이 작동하지 않는 경우
1. 여러 SearXNG 인스턴스 자동 시도
2. Fallback 모드로 서비스 지속
3. 로컬 RAG는 정상 작동

### 로컬 RAG 결과가 없는 경우
1. RAG 문서 인덱싱 확인
2. 쿼리 키워드 조정
3. 웹 검색으로 자동 fallback

## 테스트 방법

### 간단한 테스트
```bash
python simple_searxng_test.py
```

### 상세한 테스트
```bash
python test_searxng_integration.py
```

## 확장 가능성

### 추가 가능한 기능
- **자체 SearXNG 인스턴스**: Docker 또는 로컬 설치
- **커스텀 검색 엔진**: 특정 도메인 검색
- **결과 필터링**: 카테고리별 결과 분류
- **검색 히스토리**: 사용자별 검색 기록

### 통합 가능한 서비스
- **Chat API**: 대화형 검색 지원
- **RAG Pipeline**: 검색 결과 문서화
- **Monitoring**: 검색 패턴 분석

## Tavily vs SearXNG 비교

| 특징 | Tavily | SearXNG |
|------|--------|---------|
| 비용 | API 키 필요 | 무료 |
| 프라이버시 | 제한적 | 완전한 프라이버시 |
| 속도 | 빠름 | 보통 |
| 안정성 | 높음 | 인스턴스 의존적 |
| 설정 | 간단 | 복잡할 수 있음 |
| Fallback | 없음 | Mock 결과 제공 |

## 결론

SearXNG Smart Search는 다음과 같은 장점을 제공합니다:

✅ **프라이버시 우선**: 사용자 데이터 추적 없음  
✅ **무료 사용**: API 키 불필요  
✅ **지능형 라우팅**: 쿼리 특성 자동 분석  
✅ **안정성**: Fallback 모드로 서비스 연속성  
✅ **확장성**: 커스텀 인스턴스 지원  

이제 프라이버시를 보호하면서도 효과적인 웹 검색이 가능합니다!