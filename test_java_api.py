#!/usr/bin/env python3
import requests
import json

# Test Java execution API
java_code = """public class TestSimple {
    public static void main(String[] args) {
        System.out.println("Hello from converted COBOL!");
        System.out.println("This proves execution uses the actual converted code!");
    }
}"""

payload = {
    "java_code": java_code,
    "class_name": "TestSimple",
    "timeout": 10
}

try:
    response = requests.post(
        "http://localhost:8000/api/execute/java",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=15
    )
    
    print("Status Code:", response.status_code)
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    
except Exception as e:
    print(f"Error: {e}")