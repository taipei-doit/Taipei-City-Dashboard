## Vector DB

The input query is converted into a vector, and the vector database returns the most similar components.

## APIs

### Search Component

`POST` `/api/v1/vector/component`

| Item     | Description                                                                                                                                                                                                                                                                                                                                                                                         |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Permissions     | `Guest`                                                                                                                                                                                                                                                                                                                                                                                      |
| Query Params | `query` ------------- query string <br> |



**Response:**

```json
{
    "data": [
        {
            "id": 217,
            "index": "bike_map",
            "name": "自行車道路網圖資",
            "city": "taipei",
            "score": 0.8181
        },
        {
            "id": 213,
            "index": "bike_network",
            "name": "自行車道路統計資料",
            "city": "taipei",
            "score": 0.8158
        },
        {
            "id": 212,
            "index": "ebus_percent",
            "name": "電動巴士比例",
            "city": "taipei",
            "score": 0.814
        }
    ],
    "status": "success"
}
```