import os
import asyncio
from dotenv import load_dotenv
from nemoguardrails import LLMRails, RailsConfig
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma

# 1. 載入環境變數
load_dotenv()

# --- 設定資料庫 ---
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
DB_PATH = "./chroma_db"

vector_store = None
if os.path.exists(DB_PATH):
    try:
        vector_store = Chroma(
            persist_directory=DB_PATH,
            embedding_function=embedding_model
        )
        print(f"✅ 已連接至向量資料庫: {DB_PATH}")
    except Exception as e:
        print(f"❌ 資料庫連接失敗: {e}")
else:
    print("⚠️  警告：找不到 chroma_db 資料夾！")

# --- Action 1: 檢索資料 (Retrieve) ---
async def retrieve_knowledge(query: str):
    print(f"\n[RAG Action] 正在搜尋: {query}")
    
    if not vector_store:
        return "資料庫尚未連接。"

    try:
        results_with_score = vector_store.similarity_search_with_score(query, k=3)
        valid_results = []
        for doc, score in results_with_score:
            print(f"   - 片段分數 (Distance): {score:.4f}") 
            if score < 1.8: 
                valid_results.append(doc.page_content)
        
        if not valid_results:
            return "沒有找到相關的金融數據。"

        context_text = "\n\n".join(valid_results)
        print("   -> ✅ 已找到高相關性資訊。")
        return context_text
        
    except Exception as e:
        print(f"檢索發生錯誤: {e}")
        return "檢索錯誤"

async def generate_answer(context: str, question: str):
    print("   -> 🤖 正在生成回答 (LLM)...")
    
    # 初始化 LLM
    llm = ChatOpenAI(temperature=0.5, model="gpt-4o") # 稍微調高溫度讓對話自然點
    
    # 修改 Prompt：允許在沒有 Context 時使用通用知識
    prompt = f"""
    你是一位專業的金融 AI 助理。請回答使用者的問題。
    
    邏輯判斷：
    1. 請先閱讀下方的「已知資訊 (Context)」。
    2. 如果「已知資訊」包含問題的答案，請**優先**根據資訊回答。
    3. 如果「已知資訊」與問題無關，或者問題只是打招呼（如 Hi, 你好）或通用概念，**請使用你自己的知識回答**，不要死板地拒絕。
    
    限制：
    - **必須** 使用繁體中文 (Traditional Chinese) 回答。
    
    已知資訊 (Context):
    {context}
    
    使用者問題 (Question): {question}
    
    回答:
    """
    
    response = await llm.ainvoke(prompt)
    return response.content

# --- 主程式 ---
async def main():
    config = RailsConfig.from_path("./config")
    rails = LLMRails(config)

    # ⭐️ 關鍵：註冊兩個 Action
    rails.register_action(retrieve_knowledge, name="retrieve_knowledge")
    rails.register_action(generate_answer, name="generate_answer")

    print("\n🚀 --- 金融指引 RAG 系統啟動 ---")
    
    while True:
        try:
            user_input = input("\nUser: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Bye!")
                break
            
            response = await rails.generate_async(prompt=user_input)
            
            if hasattr(response, "response"):
                print(f"Bot: {response.response}")
            else:
                print(f"Bot: {response}")

        except Exception as e:
            print(f"❌ 發生錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(main())