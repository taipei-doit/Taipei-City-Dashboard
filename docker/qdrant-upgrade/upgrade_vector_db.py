import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
import os
from sqlalchemy import create_engine

def main():
    print("開始向量資料庫升級...")
    
    # === 環境變數 ===
    DB_HOST = os.getenv("DB_MANAGER_HOST", "postgres-manager")
    DB_PORT = os.getenv("DB_MANAGER_PORT", "5432")
    DB_USER = os.getenv("DB_MANAGER_USER")
    DB_PASSWORD = os.getenv("DB_MANAGER_PASSWORD")
    DB_NAME = os.getenv("DB_MANAGER_DBNAME")
    QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "gogosecurity")
    COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "query_charts")
    
    # === 1. 從 PostgreSQL 讀取資料 ===
    # Encode special characters for connection string
    from urllib.parse import quote_plus
    encoded_user = quote_plus(DB_USER) if DB_USER else ""
    encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
    
    print(f"連接資料庫：{DB_HOST}:{DB_PORT}/{DB_NAME}")
    connection_string = f"postgresql://{encoded_user}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    # 執行 SQL 查詢（query_charts JOIN components）
    query = """
			SELECT
				c.id,
				qc.index,
				c.name,
				qc.city,
				qc.long_desc,
				qc.use_case
			FROM query_charts qc
			INNER JOIN components c ON qc.index = c.index
			where id in (select distinct unnest(components) from dashboards d where id
			in (select distinct dashboard_id  from dashboard_groups dg where group_id  in (select distinct id from "groups" g where is_personal is false))
			)
    """
    
    print("執行 SQL 查詢並讀取資料...")
    df = pd.read_sql(query, engine)
    print(f"成功讀取 {len(df)} 筆資料")
    
    # 組合描述文字
    df["long_desc"] = df["long_desc"].fillna("")
    df["use_case"] = df["use_case"].fillna("")
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
    collections = client.get_collections().collections
    if any(c.name == COLLECTION_NAME for c in collections):
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
            id=row["id"],
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
        for v, row in zip(embeddings, df.to_dict(orient="records"))
    ]
    
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"成功上傳 {len(points)} 筆向量至 Qdrant")
    print("向量資料庫升級完成！")

if __name__ == "__main__":
    main()
