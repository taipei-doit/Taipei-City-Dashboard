import csv
import json
import os


def csv_to_geojson(csv_path, output_path, lon_col, lat_col):
    features = []

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        if lon_col not in headers or lat_col not in headers:
            raise ValueError(
                f"找不到欄位：確認經度欄位「{lon_col}」和緯度欄位「{lat_col}」是正確的嗎 \n現有欄位：{headers}"
            )

        for row in reader:
            try:
                lon = float(row[lon_col])
                lat = float(row[lat_col])
            except (ValueError, TypeError):
                continue

            properties = {k: v for k, v in row.items() if k not in (lon_col, lat_col)}

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": properties,
            }
            features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    return len(features)


def main():
    print("=== CSV 轉 GeoJSON  ===\n")

    csv_path = input("輸入CSV檔案路徑：").strip().strip('"')
    if not os.path.isfile(csv_path):
        print(f"error：找不到檔案 {csv_path}")
        return

    output_dir = input("請輸入輸出資料夾路徑：").strip().strip('"')
    if not os.path.isdir(output_dir):
        print(f"error：找不到資料夾 {output_dir}")
        return

    output_name = input("輸入輸出檔名（不含副檔名）：").strip()
    if not output_name:
        print("error：檔名不可以是空的啦")
        return

    output_path = os.path.join(output_dir, output_name + ".geojson")

    lon_col = input("輸入經度欄位名稱：").strip()
    lat_col = input("輸入緯度欄位名稱：").strip()

    try:
        count = csv_to_geojson(csv_path, output_path, lon_col, lat_col)
        print(f"\n完成！轉換 {count} 筆資料，輸出至：{output_path}")
    except ValueError as e:
        print(f"\n錯誤：{e}")
    except Exception as e:
        print(f"\n發生未預期錯誤：{e}")


if __name__ == "__main__":
    main()
