這份程式碼是一個結合了 NeMo Guardrails 與 LangChain 的 RAG（檢索增強生成）系統。它專門為金融問答設計，具備「安全護欄」與「外部知識庫檢索」雙重功能。

以下是程式碼的詳細說明與使用指南：

核心功能說明

    1. 向量資料庫連線 (ChromaDB)
    程式碼首先嘗試載入位於 ./chroma_db 的本地向量資料庫。這裏儲存了預先處理好的金融文檔片段。

    Embedding: 使用 OpenAI 的 text-embedding-3-small 模型，這是一個高性價比且高效的向量化模型。

    2. 自定義 Action 邏輯
    這段程式的核心在於定義了兩個異步 (async) 函式，並將其註冊到 NeMo Guardrails 中：

    retrieve_knowledge (檢索)：

    計算使用者問題與資料庫中片段的相似度（距離分數）。

    設定了閥值 score < 1.8（注意：Chroma 的距離分數越小越相關），篩選出最相關的資訊。

    generate_answer (生成)：

    這是一個「有條件」的生成邏輯。

    優先權：如果有檢索到 Context，則以此回答；若無相關資訊（如打招呼），則切換到 LLM 的通用知識，避免系統過於死板。

    3. NeMo Guardrails 安全護欄
    程式透過 LLMRails(config) 載入設定。這代表系統的對話流程（Flows）是由外部的 .co (Colang) 文件定義的。

    它不只是簡單的對話，還能控制 LLM 什麼時候該去呼叫檢索、什麼時候該拒絕回答敏感議題。

使用說明報告

    ** 準備工作
    在使用此程式碼之前，請確保環境已準備就緒：

    環境變數：在 .env 檔案中必須設定 OPENAI_API_KEY。

    設定檔目錄：必須存在一個 ./config 資料夾，裡面應包含：

    config.yml: 定義模型與路徑。

    *.co (Colang 檔案): 定義對話流程（例如：當使用者詢問金融問題，執行 retrieve_knowledge）。

    資料庫：需確保 ./chroma_db 已存在且已寫入索引資料。

    ** 執行步驟
    啟動系統：執行 Python 腳本後，系統會自動連接資料庫並加載護欄規則。

    輸入問題：

    金融專業問題：例如「公司 A 的財報表現如何？」，系統會觸發 RAG 流程。

    閒聊/通用問題：例如「你好」、「什麼是通貨膨脹？」，系統會由 LLM 直接回答。

    退出系統：輸入 exit 或 quit 即可關閉程式。

    ** 注意事項與建議
    分數閥值 (score < 1.8)：這是目前過濾相關性的關鍵。如果發現系統一直說「找不到相關數據」，可能需要調大此數值或檢查 Embedding 模型是否一致。

    Action 註冊：如果你在 .co 檔案中定義了新的動作（Action），必須在 main() 中使用 rails.register_action 進行註冊，否則 Guardrails 無法呼叫該 Python 函式。

    安全性：由於使用了 GPT-4o 且設定了 Guardrails，系統能有效防止 AI 產生幻覺或回答非相關領域的問題（視你的 Colang 設定而定）。
