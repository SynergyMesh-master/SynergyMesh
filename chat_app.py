import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY"),
    base_url=os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL"),
)

def chat():
    print("=" * 50)
    print("AI 助手聊天室")
    print("輸入 'quit' 或 'exit' 結束對話")
    print("=" * 50)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Please respond in the same language the user uses."}
    ]
    
    while True:
        user_input = input("\n您: ").strip()
        
        if user_input.lower() in ['quit', 'exit', '結束', '退出']:
            print("\n再見！感謝使用 AI 助手。")
            break
        
        if not user_input:
            continue
        
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            
            assistant_message = response.choices[0].message.content
            messages.append({"role": "assistant", "content": assistant_message})
            
            print(f"\nAI: {assistant_message}")
            
        except Exception as e:
            print(f"\n發生錯誤: {e}")

if __name__ == "__main__":
    chat()
