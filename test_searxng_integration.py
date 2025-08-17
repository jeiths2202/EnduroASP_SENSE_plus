#!/usr/bin/env python3
"""
Test SearXNG Smart Search Service Integration
"""

import requests
import json
import time

def test_searxng_service():
    """Test SearXNG Smart Search Service"""
    
    print("Testing SearXNG Smart Search Service")
    print("=" * 50)
    
    base_url = "http://localhost:3006"
    
    # Test 1: Service Status
    print("\n1. Testing SearXNG Service Status")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/api/searxng-search/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print("OK SearXNG Service Status:")
            print(f"   Service Type: {status.get('service_type')}")
            print(f"   RAG Available: {status['status']['rag_available']}")
            print(f"   Web Search Available: {status['status']['web_search_available']}")
            print(f"   LLM Available: {status['status']['llm_available']}")
            print(f"   Cache Size: {status['status']['cache_size']}")
            print(f"   SearXNG Engines: {status['status'].get('searxng_engines', [])}")
        else:
            print(f"FAILED Status check failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"ERROR Status check error: {e}")
    
    # Test 2: Query Routing
    print("\n2. Testing SearXNG Query Routing")
    print("-" * 30)
    
    test_queries = [
        "COBOLG 컴파일러 구현 방법",  # Should route to local_rag
        "2025년 최신 AI 뉴스",  # Should route to web_search
        "서울 현재 날씨",  # Should route to web_search
        "시스템 명령어 구현 가이드",  # Should route to hybrid
    ]
    
    for query in test_queries:
        try:
            response = requests.post(
                f"{base_url}/api/searxng-search/route",
                json={"query": query},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                route = result['recommended_route']
                analysis = result['analysis']
                
                print(f"Query: {query}")
                print(f"   📍 Route: {route}")
                print(f"   🕒 Time Sensitive: {analysis['is_time_sensitive']}")
                print(f"   🏠 Local Score: {analysis['local_relevance_score']:.2f}")
                print(f"   📰 Needs Current: {analysis['requires_current_info']}")
                print()
            else:
                print(f"❌ Route test failed for: {query}")
                
        except Exception as e:
            print(f"❌ Route test error for '{query}': {e}")
    
    # Test 3: SearXNG Search (local only first)
    print("\n3. Testing SearXNG Search (Local RAG)")
    print("-" * 30)
    
    local_query = "COBOLG 컴파일러란?"
    try:
        response = requests.post(
            f"{base_url}/api/searxng-search",
            json={
                "query": local_query,
                "max_results": 3
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Query: {local_query}")
            print(f"✅ Route Used: {result['route_used']}")
            print(f"   📊 Results: {result['total_results']}")
            print(f"   ⏱️ Search Time: {result['search_time']:.2f}s")
            
            for i, res in enumerate(result['results'][:2], 1):
                print(f"   Result {i} ({res['source_type']}):") 
                print(f"     Source: {res['source']}")
                print(f"     Score: {res['score']:.3f}")
                print(f"     Content: {res['content'][:100]}...")
        else:
            print(f"❌ SearXNG search failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ SearXNG search error: {e}")
    
    # Test 4: Web Search (if available)
    print("\n4. Testing SearXNG Web Search")
    print("-" * 30)
    
    web_query = "Python programming tutorial 2025"
    try:
        response = requests.post(
            f"{base_url}/api/searxng-search",
            json={
                "query": web_query,
                "max_results": 5
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Query: {web_query}")
            print(f"✅ Route Used: {result['route_used']}")
            print(f"   📊 Results: {result['total_results']}")
            print(f"   ⏱️ Search Time: {result['search_time']:.2f}s")
            
            for i, res in enumerate(result['results'][:3], 1):
                print(f"   Result {i} ({res['source_type']}):") 
                print(f"     Source: {res['source'][:60]}...")
                print(f"     Score: {res['score']:.3f}")
                if res['metadata'].get('title'):
                    print(f"     Title: {res['metadata']['title'][:60]}...")
        else:
            print(f"❌ SearXNG web search failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ SearXNG web search error: {e}")

def test_environment():
    """Test if chat API is running"""
    print("\n🔧 Environment Check")
    print("-" * 20)
    
    try:
        response = requests.get("http://localhost:3006/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Chat API is running")
            return True
        else:
            print("❌ Chat API not responding properly")
            return False
    except Exception as e:
        print(f"❌ Chat API not accessible: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 SearXNG Smart Search Integration Test")
    print("=" * 50)
    
    if not test_environment():
        print("\n❌ Environment check failed. Please start the chat API first.")
        return False
    
    test_searxng_service()
    
    print("\n" + "=" * 50)
    print("✅ SearXNG Integration Tests Completed")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)