import os
import shutil
# 1. 更改 import：改用 PyPDFLoader
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader 
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

DATA_PATH = "./data"          
DB_PATH = "./chroma_db"       

def create_vector_db():
    # --- 檢查資料夾 ---
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
        print(f"❌ 找不到 {DATA_PATH} 資料夾。已建立，請放入 PDF 檔。")
        return

    # 檢查是否有 PDF
    files = [f for f in os.listdir(DATA_PATH) if f.lower().endswith(".pdf")]
    if not files:
        print(f"❌ 錯誤: 在 {DATA_PATH} 裡找不到任何 .pdf 檔案！")
        return

    print(f"📄 正在讀取 {len(files)} 份 PDF 文件...")

    try:
        # 2. 修改 Loader 設定
        loader = DirectoryLoader(
            DATA_PATH, 
            glob="*.pdf",             # 改抓 PDF
            loader_cls=PyPDFLoader,   # 改用 PDF 讀取器
            use_multithreading=True   # 加速讀取
        )
        documents = loader.load()
    except Exception as e:
        print(f"❌ 讀取 PDF 失敗: {e}")
        return

    if not documents:
        print("❌ 錯誤: PDF 內容讀取為空 (可能是掃描檔或加密檔)！")
        return

    print(f"   -> 成功載入 {len(documents)} 頁內容")

    # --- 切分文本 ---
    print("✂️  正在切分文本...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    
    # 注入檔名 Metadata (方便知道是哪份 PDF)
    for chunk in chunks:
        source_name = chunk.metadata.get('source', '').split(os.sep)[-1]
        chunk.page_content = f"【來源文件: {source_name}】\n{chunk.page_content}"

    # --- 寫入 DB ---
    if os.path.exists(DB_PATH):
        try:
            shutil.rmtree(DB_PATH)
            print("🗑️  舊資料庫已清除")
        except PermissionError:
            print("⚠️  無法刪除舊資料庫，請先關閉 main.py！")
            return

    print("💾 正在寫入向量資料庫...")
    try:
        embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
        Chroma.from_documents(
            documents=chunks,
            embedding=embedding_model,
            persist_directory=DB_PATH
        )
        print(f"✅ 資料庫建立完成！儲存於: {DB_PATH}")
        
    except Exception as e:
        print(f"❌ 寫入錯誤: {e}")

if __name__ == "__main__":
    create_vector_db()