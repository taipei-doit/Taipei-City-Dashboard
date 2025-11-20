import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
import os
from sqlalchemy import create_engine

def main():
    print("開始向量資料庫升級...")
    
    # === 環境變數 ===
    DB_HOST = os.getenv("DB_DASHBOARD_HOST", "postgres-data")
    DB_PORT = os.getenv("DB_DASHBOARD_PORT", "5432")
    DB_USER = os.getenv("DB_DASHBOARD_USER")
    DB_PASSWORD = os.getenv("DB_DASHBOARD_PASSWORD")
    DB_NAME = os.getenv("DB_DASHBOARD_DBNAME")
    QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "gogosecurity")
    COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "query_charts")
    
    # === 1. 從 PostgreSQL 讀取資料 ===
    print(f"連接資料庫：{DB_HOST}:{DB_PORT}/{DB_NAME}")
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    # 執行 SQL 查詢（query_charts JOIN components）
    query = """
        SELECT 
            qc.id,
            qc.index,
            c.name,
            c.city,
            c.long_desc,
            c.use_case
        FROM query_charts qc
        INNER JOIN components c ON qc.index = c.index
    """
    
    print("執行 SQL 查詢並讀取資料...")
    df = pd.read_sql(query, engine)
    print(f"成功讀取 {len(df)} 筆資料")
    
    # 組合描述文字
    df["text"] = df["long_desc"] + " " + df["use_case"]
    
    # 載入模型
    print("載入 SentenceTransformer 模型...")
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    
    # 轉成向量
    print("生成向量嵌入...")
    embeddings = model.encode(df["text"].tolist(), normalize_embeddings=True)
    print(f"成功生成 {len(embeddings)} 個向量嵌入")
    
    # === 2. 連線到 Qdrant ===
    print(f"連線到 Qdrant：{QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    # 刪除舊 collection
    if client.collection_exists(COLLECTION_NAME):
        print(f"刪除舊 collection：{COLLECTION_NAME}")
        client.delete_collection(COLLECTION_NAME)
    
    # === 3. 建立 collection ===
    print(f"建立新 collection：{COLLECTION_NAME}")
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=embeddings.shape[1], distance=Distance.COSINE)
    )
    
    # === 4. 上傳向量 ===
    print("上傳向量資料...")
    points = [
        PointStruct(
            id=i,
            vector=v.tolist(),
            payload={
                "id": row["id"],
                "index": row["index"],
                "name": row["name"],
                "city": row["city"],
                "long_desc": row["long_desc"],
                "use_case": row["use_case"]
            }
        )
        for i, (v, row) in enumerate(zip(embeddings, df.to_dict(orient="records")))
    ]
    
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"成功上傳 {len(points)} 筆向量至 Qdrant")
    print("向量資料庫升級完成！")

if __name__ == "__main__":
    main()
