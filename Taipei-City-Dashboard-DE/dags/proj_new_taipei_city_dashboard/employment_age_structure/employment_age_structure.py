from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import NewTaipeiAPIClient
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.get_time import get_tpe_now_time_str

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    RID= "c285509a-7fb2-434f-8542-0b4986c337a8"
    client = NewTaipeiAPIClient(RID, input_format="json")
    res = client.get_all_data(size=1000)
    raw_data = pd.DataFrame(res)
    print(f"raw data =========== {raw_data.head()}")
    data = raw_data.copy()
    data = data.rename(
        columns={
            "field1": "year",
            "percent2": "15-24_male",
            "percent3": "15-24_female",
            "percent4": "25-29_male",
            "percent5": "25-29_female",
            "percent6": "30-34_male",
            "percent7": "30-34_female",
            "percent8": "35-39_male",
            "percent9": "35-39_female",
            "percent10": "40-44_male",
            "percent11": "40-44_female",
            "percent12": "45-49_male",
            "percent13": "45-49_female",
            "percent14": "50-54_male",
            "percent15": "50-54_female",
            "percent16": "55-59_male",
            "percent17": "55-59_female",
            "percent18": "60-64_male",
            "percent19": "60-64_female",
            "percent20": "65_above_male",
            "percent21": "65_above_female",
        }
    )

    # 轉換成與台北市資料相同的結構
    melted_data = data.melt(id_vars=["year"], var_name="age_gender", value_name="percentage")

    # 解析 `age_gender` 欄位來對應 `age_structure` 和 `gender`
    age_mapping = {
        "15-24_male": "就業人口按年齡別/15-24歲",
        "15-24_female": "就業人口按年齡別/15-24歲",
        "25-29_male": "就業人口按年齡別/25-29歲",
        "25-29_female": "就業人口按年齡別/25-29歲",
        "30-34_male": "就業人口按年齡別/30-34歲",
        "30-34_female": "就業人口按年齡別/30-34歲",
        "35-39_male": "就業人口按年齡別/35-39歲",
        "35-39_female": "就業人口按年齡別/35-39歲",
        "40-44_male": "就業人口按年齡別/40-44歲",
        "40-44_female": "就業人口按年齡別/40-44歲",
        "45-49_male": "就業人口按年齡別/45-49歲",
        "45-49_female": "就業人口按年齡別/45-49歲",
        "50-54_male": "就業人口按年齡別/50-54歲",
        "50-54_female": "就業人口按年齡別/50-54歲",
        "55-59_male": "就業人口按年齡別/55-59歲",
        "55-59_female": "就業人口按年齡別/55-59歲",
        "60-64_male": "就業人口按年齡別/60-64歲",
        "60-64_female": "就業人口按年齡別/60-64歲",
        "65_above_male": "就業人口按年齡別/65歲以上",
        "65_above_female": "就業人口按年齡別/65歲以上",
    }

    # 提取 `age_structure` 和 `gender`
    melted_data["age_structure"] = melted_data["age_gender"].map(age_mapping)
    melted_data["gender"] = melted_data["age_gender"].apply(lambda x: "男" if "male" in x else "女")

    # 民國年份轉換為西元（例如 67 年 → 1978 年）
    melted_data["year"] = melted_data["year"].astype(int) + 1911

    # 移除不需要的欄位
    melted_data = melted_data.drop(columns=["age_gender"])

    # 重新排列欄位順序
    melted_data = melted_data[["year", "gender", "age_structure", "percentage"]]
    melted_data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    print(f"ready_data =========== {melted_data.head()}")

    
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=melted_data,
        load_behavior=load_behavior,
        default_table=default_table,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, melted_data["data_time"].max()
        )

dag = CommonDag(proj_folder="proj_new_taipei_city_dashboard", dag_folder="employment_age_structure")
dag.create_dag(etl_func=_transfer)
