import os
from dotenv import load_dotenv
load_dotenv("tools/.env")

import google.generativeai as genai

api_key = os.getenv("GOOGLE_API_KEY")
print(f"🔑 API Key loaded: {api_key[:10]}..." if api_key else "❌ No API key found")

if not api_key:
    print("\n❌ No GOOGLE_API_KEY found in tools/.env")
    exit(1)

genai.configure(api_key=api_key)

print("\n" + "=" * 70)
print("📋 LISTING ALL AVAILABLE GEMINI MODELS")
print("=" * 70 + "\n")

try:
    models = genai.list_models()
    
    working_models = []
    
    for model in models:
        # Check if model supports generateContent (required for ADK)
        if 'generateContent' in model.supported_generation_methods:
            model_name = model.name.replace('models/', '')
            working_models.append(model_name)
            
            print(f"✅ {model_name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description[:80]}...")
            print(f"   Input Token Limit: {model.input_token_limit:,}")
            print(f"   Output Token Limit: {model.output_token_limit:,}")
            print()
    
    print("=" * 70)
    print(f"✅ FOUND {len(working_models)} WORKING MODELS")
    print("=" * 70)
    
    if working_models:
        print("\n🎯 RECOMMENDED FOR ADK (copy one of these to root_agent.py):\n")
        for i, model_name in enumerate(working_models[:3], 1):
            print(f"   {i}. model=\"{model_name}\"")
        
        print("\n📝 UPDATE YOUR root_agent.py:")
        print(f"\n   root_agent = LlmAgent(")
        print(f"       model=\"{working_models[0]}\",  # ← Use this!")
        print(f"       name=\"MediSyncIntelligentSystem\",")
        print(f"       ...")
        print(f"   )")
    else:
        print("\n❌ NO MODELS FOUND!")
        print("\n🔧 POSSIBLE ISSUES:")
        print("1. API key might be invalid")
        print("2. Account might not have access to Gemini API")
        print("3. Need to enable Gemini API in Google Cloud Console")
        print("\n🆕 GET A NEW API KEY:")
        print("   https://aistudio.google.com/apikey")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\n🔧 TROUBLESHOOTING:")
    print("1. Check API key at: https://aistudio.google.com/apikey")
    print("2. Make sure generative-ai SDK is installed:")
    print("   pip install --upgrade google-generativeai")
    print("3. Check if you have internet connection")
    print("4. Try getting a NEW API key")