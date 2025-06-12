
#!/usr/bin/env python3
"""
Test script to debug weather tool issues
"""
import os
from dotenv import load_dotenv
from weather_tool import create_weather_tool

def test_environment():
    """Test environment variables"""
    load_dotenv(dotenv_path="./config/.env")
    
    print("=== Environment Variable Check ===")
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    weather_key = os.getenv("WEATHER_API_KEY")
    
    print(f"OPENWEATHERMAP_API_KEY: {'SET' if api_key else 'NOT SET'}")
    print(f"WEATHER_API_KEY: {'SET' if weather_key else 'NOT SET'}")
    
    if api_key:
        print(f"API Key (first 10 chars): {api_key[:10]}...")
    elif weather_key:
        print(f"WEATHER_API_KEY found (first 10 chars): {weather_key[:10]}...")
        print("Note: LangChain expects OPENWEATHERMAP_API_KEY, not WEATHER_API_KEY")
    else:
        print("ERROR: No API key found!")
        return False
    
    return True

def test_weather_tool_directly():
    """Test the weather tool directly"""
    print("\n=== Direct Weather Tool Test ===")
    
    try:
        weather_tool = create_weather_tool()
        print(f"Weather tool created: {weather_tool.name}")
        print(f"Weather tool description: {weather_tool.description}")
        
        # Test with Rome
        print("\nTesting with Rome...")
        result = weather_tool.run("Rome")
        print(f"Result: {result}")
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_langchain_wrapper():
    """Test LangChain wrapper directly"""
    print("\n=== LangChain Wrapper Test ===")
    
    try:
        from langchain_community.utilities import OpenWeatherMapAPIWrapper
        
        # Check if API key is available
        api_key = os.getenv("OPENWEATHERMAP_API_KEY") or os.getenv("WEATHER_API_KEY")
        if not api_key:
            print("ERROR: No API key available")
            return False
        
        # Test wrapper
        weather = OpenWeatherMapAPIWrapper(openweathermap_api_key=api_key)
        result = weather.run("Rome")
        print(f"LangChain wrapper result: {result}")
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_api_key_validity():
    """Test API key by making direct request"""
    print("\n=== API Key Validity Test ===")
    
    try:
        import requests
        
        api_key = os.getenv("OPENWEATHERMAP_API_KEY") or os.getenv("WEATHER_API_KEY")
        if not api_key:
            print("ERROR: No API key found")
            return False
        
        url = f"https://api.openweathermap.org/data/2.5/weather?q=Rome&appid={api_key}&units=metric"
        response = requests.get(url, timeout=10)
        
        print(f"API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API working! Temperature in Rome: {data['main']['temp']}°C")
            return True
        elif response.status_code == 401:
            print("ERROR: Invalid API key (401 Unauthorized)")
        elif response.status_code == 404:
            print("ERROR: City not found (404)")
        else:
            print(f"ERROR: API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
        
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("Weather Tool Debug Script")
    print("=" * 50)
    
    # Load environment
    load_dotenv(dotenv_path="./config/.env")
    
    # Run tests
    tests = [
        ("Environment Check", test_environment),
        ("API Key Validity", test_api_key_validity),
        ("LangChain Wrapper", test_langchain_wrapper),
        ("Weather Tool Direct", test_weather_tool_directly),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"EXCEPTION in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    # Recommendations
    print(f"\n{'='*50}")
    print("RECOMMENDATIONS:")
    
    failed_tests = [name for name, success in results if not success]
    if not failed_tests:
        print("✅ All tests passed! Your weather tool should work.")
    else:
        if "Environment Check" in failed_tests:
            print("❌ Fix your .env file - add OPENWEATHERMAP_API_KEY=your_key")
        if "API Key Validity" in failed_tests:
            print("❌ Get a valid API key from openweathermap.org")
        if "LangChain Wrapper" in failed_tests:
            print("❌ Install: pip install langchain-community")
        if "Weather Tool Direct" in failed_tests:
            print("❌ Check your weather_tool.py implementation")

if __name__ == "__main__":
    main()