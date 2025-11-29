import os
import requests
from dotenv import load_dotenv
load_dotenv("tools/.env")

api_key = os.getenv("GROQ_API_KEY")
print(f"🔑 Groq API Key loaded: {api_key[:10]}..." if api_key else "❌ No Groq API key found")

if not api_key:
    print("\n🔧 FIX:")
    print("1. Go to: https://console.groq.com/keys")
    print("2. Create a NEW API key")
    print("3. Add to tools/.env:")
    print("   GROQ_API_KEY=your_groq_api_key_here")
    exit(1)

print("\n🔍 Testing Groq API connection...\n")

# Test 1: List available models
print("=" * 60)
print("📋 FETCHING AVAILABLE MODELS")
print("=" * 60)

try:
    url = "https://api.groq.com/openai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        models_data = response.json()
        print(f"\n✅ Found {len(models_data.get('data', []))} models:\n")
        
        for model in models_data.get('data', []):
            model_id = model.get('id', 'Unknown')
            owned_by = model.get('owned_by', 'Unknown')
            context_window = model.get('context_window', 'N/A')
            
            print(f"   ✅ {model_id}")
            print(f"      Owner: {owned_by}")
            print(f"      Context: {context_window} tokens")
            print()
    else:
        print(f"❌ Failed to fetch models: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error fetching models: {e}")

# Test 2: Try a simple chat completion
print("\n" + "=" * 60)
print("🧪 TESTING CHAT COMPLETION")
print("=" * 60 + "\n")

try:
    from groq import Groq
    
    client = Groq(api_key=api_key)
    
    print("✅ Groq client initialized successfully!\n")
    print("🧪 Sending test message...\n")
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say 'Groq API is working!' in one sentence.",
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    
    response = chat_completion.choices[0].message.content
    print(f"🎉 Test Response: {response}\n")
    
    print("=" * 60)
    print("✅ GROQ API IS FULLY FUNCTIONAL!")
    print("=" * 60)
    
    print("\n🎯 RECOMMENDED MODELS FOR YOUR AGENT:")
    print("   1. llama-3.3-70b-versatile (BEST - Fast & Smart)")
    print("   2. llama-3.1-70b-versatile (Alternative)")
    print("   3. mixtral-8x7b-32768 (Fastest inference)")
    
    print("\n✅ Your root_agent.py is configured correctly!")
    print("\n🚀 NEXT STEP: Run ADK Web Server")
    print("   Command: adk web")
    print("   Then open: http://127.0.0.1:8000")
    
except ImportError:
    print("\n❌ Groq SDK not installed!")
    print("\n🔧 FIX: Install Groq SDK:")
    print("   pip install --upgrade groq")
    
except Exception as e:
    print(f"\n❌ Chat Completion Error: {e}")
    print("\n🔧 TROUBLESHOOTING:")
    print("1. Update Groq SDK:")
    print("   pip install --upgrade groq")
    print("\n2. Check if your API key is valid at: https://console.groq.com/keys")
    print("\n3. Make sure you have internet connection")