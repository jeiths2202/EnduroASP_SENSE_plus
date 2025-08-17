#!/usr/bin/env python3
"""
Simple SearXNG Test
"""

import requests
import json

def test_searxng():
    base_url = "http://localhost:3006"
    
    print("Testing SearXNG Service...")
    
    # Test status
    try:
        response = requests.get(f"{base_url}/api/searxng-search/status", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            status = response.json()
            print(f"RAG: {status['status']['rag_available']}")
            print(f"Web: {status['status']['web_search_available']}")
            print(f"Service Type: {status.get('service_type')}")
    except Exception as e:
        print(f"Status error: {e}")
    
    # Test search
    print("\nTesting search...")
    try:
        response = requests.post(
            f"{base_url}/api/searxng-search",
            json={"query": "Python tutorial", "max_results": 3},
            timeout=30
        )
        print(f"Search status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Route: {result['route_used']}")
            print(f"Results: {result['total_results']}")
            print(f"Time: {result['search_time']:.2f}s")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Search error: {e}")

if __name__ == "__main__":
    test_searxng()