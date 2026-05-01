"""
test_transform_utils.py
驗證 transform_utils 修正是否對齊官方規範。
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from transform_utils import (
    convert_str_to_time_format,
    add_point_wkbgeometry_column_to_df,
    transform_single,
    TAIPEI_TZ,
)


def test_convert_str_to_time_format():
    """data_time 必須帶有時區 +08:00"""
    s = pd.Series(["2024-03-01 14:46:51", "2023-06-06 09:53:08"])
    result = convert_str_to_time_format(s)
    for val in result:
        assert val is not None, "不應回傳 None"
        assert val.tzinfo is not None, f"必須帶有時區，實際：{val}"
    print("[OK] convert_str_to_time_format: timezone correct")


def test_convert_roc_year():
    """民國年轉換測試"""
    s = pd.Series(["112/03/15"])
    result = convert_str_to_time_format(s, from_format="%TY/%m/%d")
    assert result[0] is not None
    assert result[0].year == 2023, f"民國 112 = 西元 2023，實際：{result[0].year}"
    print("[OK] convert_str_to_time_format: ROC year conversion correct")


def test_wkb_geometry_present():
    """wkb_geometry 欄位必須存在"""
    data = pd.DataFrame({
        "name": ["台北車站", "新莊市政府"],
        "lng": [121.517, 121.465],
        "lat": [25.048, 25.012],
    })
    gdf = add_point_wkbgeometry_column_to_df(data, x=data["lng"], y=data["lat"], from_crs=4326)
    assert "wkb_geometry" in gdf.columns, "缺少 wkb_geometry 欄位"
    assert gdf["wkb_geometry"].notna().all(), "wkb_geometry 不應有 NaN"
    print("[OK] add_point_wkbgeometry_column_to_df: wkb_geometry present, no nulls")


def test_geometry_removed_after_transform_single():
    """transform_single 後不應有 geometry 欄位（官方警告）"""
    df = pd.DataFrame({
        "name": ["測試地點"],
        "lng": [121.517],
        "lat": [25.048],
        "_id": [1],
    })
    config = {"keep_cols": ["name", "lng", "lat", "wkb_geometry"]}
    result = transform_single(df, "2024-03-01 14:46:51", config)
    assert "geometry" not in result.columns, "geometry 欄位必須被移除"
    assert "wkb_geometry" in result.columns, "wkb_geometry 必須存在"
    assert "_id" not in result.columns, "_id 必須被移除"
    assert "data_time" in result.columns, "data_time 必須存在"
    print("[OK] transform_single: geometry removed, wkb_geometry present, system cols cleared")


def test_data_time_has_timezone():
    """transform_single 產生的 data_time 必須帶有時區"""
    df = pd.DataFrame({"val": [1, 2]})
    config = {}
    result = transform_single(df, "2024-03-01 14:46:51", config)
    for val in result["data_time"]:
        if val is not None:
            assert val.tzinfo is not None, f"data_time 必須帶有時區，實際：{val}"
    print("[OK] transform_single: data_time has timezone")


if __name__ == "__main__":
    test_convert_str_to_time_format()
    test_convert_roc_year()
    test_wkb_geometry_present()
    test_geometry_removed_after_transform_single()
    test_data_time_has_timezone()
    print("\n[PASS] All tests passed")
