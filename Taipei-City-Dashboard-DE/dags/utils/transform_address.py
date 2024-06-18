import concurrent.futures
import json
import re
import time
import warnings

import numpy as np
import pandas as pd
import requests
from airflow.models import Variable
from requests.adapters import HTTPAdapter
from settings.global_config import DAG_PATH

# Config
warnings.filterwarnings("ignore")
OPENDATA_PATH = f"{DAG_PATH}/utils/opendata"
PREPROCESS_PATH = f"{DAG_PATH}/utils/preprocess"


# Load necessary data
def load_dim_data():
    """
    Load preprocess knowledge data.
    """
    # 各種清單
    # 縣市
    citys = ["台北市", "臺北市"]
    # 第一個來源，內政部公開資料
    road_table1 = pd.read_csv(
        f"{PREPROCESS_PATH}/dict/taipei_road.csv", encoding="UTF-8"
    )
    roads1 = set(road_table1["road"])
    # 第二個來源，崇恩給的
    road_table2 = pd.read_csv(f"{OPENDATA_PATH}/街道/road.csv")
    roads2 = list(set(road_table2["ROADNAME"].dropna().tolist()))
    not_road_list = [
        "匝道",
        "交流道",
        "高架道路",
        "高速公路",
        "快速道路",
        "便道",
        "交流",
    ]
    for nroad in not_road_list:
        roads2 = [road for road in roads2 if not road.endswith(nroad)]
    # 合併
    roads = list(roads1.union(set(roads2)))

    # 行政區
    districts = list(set(road_table1["site"]))

    # 郵政區號對應
    postcode_table = pd.read_csv(
        f"{OPENDATA_PATH}/郵政/郵政3+2對應表.csv", encoding="UTF-8"
    )
    postcode_table["Zip5"] = postcode_table["Zip5"].astype(str)
    postcode3 = list(set(postcode_table["Zip5"].str.slice(0, 3)))
    postcode5 = list(set(postcode_table["Zip5"]))
    # 區里對應表
    village_table = pd.read_csv(
        f"{OPENDATA_PATH}/行政區/區里對應表.csv", encoding="UTF-8"
    )
    villages = village_table["里"].to_list()

    return postcode3, postcode5, citys, districts, villages, roads


def cut_edge(data):
    """
    Filter out rows and columns with a high proportion of missing values.

    Args:
        data (pd.DataFrame): The input DataFrame containing the data.

    Returns:
        pd.DataFrame: A cleaned DataFrame with rows and columns filtered out if they contain
        more than 90% missing values in rows and 98% missing values in columns.
    """
    is_row_notna = [
        True if (row[1].isna().sum() / row[1].shape[0]) < 0.9 else False
        for row in data.iterrows()
    ]
    is_col_notna = [
        True if (data[colname].isna().sum() / data[colname].shape[0]) < 0.98 else False
        for colname in data
    ]
    clean_data = data.loc[is_row_notna, is_col_notna]
    return clean_data


def chnumber_to_number(ch_num):
    """
    Convert Chinese numerals to Arabic numerals, with many lines of code just for aesthetics
    """
    ch_num = ch_num.replace("一", "1").replace("二", "2").replace("三", "3")
    ch_num = ch_num.replace("四", "4").replace("五", "5").replace("六", "6")
    ch_num = ch_num.replace("七", "7").replace("八", "8").replace("九", "9")
    ch_num = ch_num.replace("零", "0")
    if "十" in ch_num:
        if re.findall("[1-9]十", ch_num):
            ch_num = ch_num.replace("十", "0")
        else:
            ch_num = ch_num.replace("十", "10")
    return ch_num


def is_address(address):
    """
    先篩去明顯不是地址的資料
    區分是地址還是地段
    地段的特色: 結尾是段 出現兩次段
    地址的特色: 以號、樓、數字、旁結尾
    """
    if (address.find("台北市") < 0) and (address.find("臺北市") < 0):
        return False
    elif address.endswith("號"):
        return True
    elif address.endswith("旁"):
        return True
    elif address.endswith("樓"):
        return True
    elif address.endswith("0"):
        return True
    elif address.endswith("1"):
        return True
    elif address.endswith("2"):
        return True
    elif address.endswith("3"):
        return True
    elif address.endswith("4"):
        return True
    elif address.endswith("5"):
        return True
    elif address.endswith("6"):
        return True
    elif address.endswith("7"):
        return True
    elif address.endswith("8"):
        return True
    elif address.endswith("9"):
        return True
    elif address.endswith("小段"):
        return False
    elif address.endswith("大段"):
        return False
    elif address.endswith("基"):
        return False
    elif address.endswith("市"):
        return False
    elif address.endswith("區"):
        return False
    elif address.endswith("里"):
        return False
    elif address.endswith("站"):
        return False
    elif address.endswith("所"):
        return False
    elif address.endswith("步道"):
        return False
    elif (address.count("段") > 1) and (address.count("路") == 0):
        # 沒有路，有兩個段，如'臺北市信義區信義段四段'
        return False
    else:
        global process_log
        process_log += "is_address func with else condtion!\n"
        return True


def is_tpe(address):
    """
    Check if the address is in Taipei city.
    """
    if (address.find("台北市") < 0) and (address.find("臺北市") < 0):
        return False
    else:
        return True


def fulltohalf(string):
    """
    Convert full-width to half-width characters.
    """
    try:
        temp = "".join(
            [chr(ord(ss) - 65248) if ord(ss) >= 65281 else ss for ss in string]
        )
        return temp
    except:
        return string


def clean_data(addr):
    """
    Clean address data.

    Example:
        ``` python
        from utils.transform_address import clean_data
        import pandas as pd

        addres = pd.Series(['台北市信義區3民路四段３00號-1(3室)', '信義路-８號之之5樓'])
        ca = clean_data(addres)
        print(ca)
        ```
        ```
        >>> print(ca)
        0    台北市信義區三民路四段300號之1
        1             信義路之8號5樓
        dtype: object
        ```
    """
    if type(addr) == list:
        addr = pd.Series(addr)
    addr = addr.apply(fulltohalf)
    addr1 = addr.str.replace("-", "之")  # 因為後面會刪掉dash，先替換掉
    addr1 = addr1.str.replace("之之", "")
    addr1 = addr1.str.replace(r"\(.*\)", "", regex=True)
    addr1 = addr1.str.replace(r"\(.*", "", regex=True)
    addr1 = addr1.str.replace("~", "至")
    addr1 = addr1.str.replace("１", "1")
    addr1 = addr1.str.replace("２", "2")
    addr1 = addr1.str.replace("３", "3")
    addr1 = addr1.str.replace("４", "4")
    addr1 = addr1.str.replace("５", "5")
    addr1 = addr1.str.replace("６", "6")
    addr1 = addr1.str.replace("７", "7")
    addr1 = addr1.str.replace("８", "8")
    addr1 = addr1.str.replace("９", "9")
    addr1 = addr1.str.replace("０", "0")
    addr1 = addr1.str.replace("Ｏ", "0")
    addr1 = addr1.str.replace("Ｏ", "0")
    addr1 = addr1.str.replace("3民", "三民")
    addr1 = addr1.str.replace("8德", "八德")
    addr1 = addr1.str.replace("廈門街", "厦門街")
    addr1 = addr1.str.replace("梧洲[路街]", "梧州街")
    addr1 = addr1.str.replace("汀洲[路街]", "汀州街")
    addr1 = addr1.str.replace("徐洲[路街]", "徐州路")
    addr1 = addr1.str.replace("舊庄里", "舊莊里")
    addr1 = addr1.str.replace("糖.{1}里", "糖廍里")
    addr1 = addr1.str.replace("汕頭街", "艋舺大道")
    _bool = addr1.str.find("北投區") >= 0  # 有北投區
    addr1.loc[_bool] = addr1.loc[_bool].str.replace(
        "公館", "公舘"
    )  # 同時又有公館，改成公舘
    addr1 = addr1.str.replace("1路", "一路")
    addr1 = addr1.str.replace("2路", "二路")
    addr1 = addr1.str.replace("3路", "三路")
    addr1 = addr1.str.replace("4路", "四路")
    addr1 = addr1.str.replace("5路", "五路")
    addr1 = addr1.str.replace("6路", "六路")
    addr1 = addr1.str.replace("7路", "七路")
    addr1 = addr1.str.replace("8路", "八路")
    addr1 = addr1.str.replace("9路", "九路")
    addr1 = addr1.str.replace("1段", "一段")
    addr1 = addr1.str.replace("2段", "二段")
    addr1 = addr1.str.replace("3段", "三段")
    addr1 = addr1.str.replace("4段", "四段")
    addr1 = addr1.str.replace("5段", "五段")
    addr1 = addr1.str.replace("6段", "六段")
    addr1 = addr1.str.replace("7段", "七段")
    addr1 = addr1.str.replace("8段", "八段")
    addr1 = addr1.str.replace("9段", "九段")
    addr1 = addr1.str.replace("1小段", "一小段")
    addr1 = addr1.str.replace("2小段", "二小段")
    addr1 = addr1.str.replace("3小段", "三小段")
    addr1 = addr1.str.replace("4小段", "四小段")
    addr1 = addr1.str.replace("5小段", "五小段")
    addr1 = addr1.str.replace("6小段", "六小段")
    addr1 = addr1.str.replace("7小段", "七小段")
    addr1 = addr1.str.replace("8小段", "八小段")
    addr1 = addr1.str.replace("9小段", "九小段")
    addr1 = addr1.str.replace("一號", "1號")
    addr1 = addr1.str.replace("二號", "2號")
    addr1 = addr1.str.replace("三號", "3號")
    addr1 = addr1.str.replace(r"[^\w\s]", "", regex=True)  # 去掉標點符號
    # re.compile(ur"[^a-zA-Z0-9\u4e00-\u9fa5]")  # 好像還有沒去掉的標點符號?
    addr2 = addr1.str.replace(" ", "")  # 去掉空白
    addr1 = addr1.str.replace("糖里", "糖廍里")
    addr3 = addr2.str.replace("ㄧ", "一")
    addr4 = addr3.fillna("")  # nan會造成dtype為float，需處理掉
    addr_cleaned = addr4

    return addr_cleaned


def seg_sample(
    address: str, seg_target: str, keyword: str, str_len: int, target_list: list
):
    """
    string: 要處理的地址
    seg_target: 要正規化的部分，例如'city' or 'dist'
    keyword: 做簡單判斷所使用的關鍵字，例如city就是'縣市'
    str_len: 例如市、區、里都是3個字
    """
    new_address = address
    seg_string = ""
    unexpected_string = ","
    global process_log

    have_target = re.search(f"[{keyword}]", address)
    # 簡易判斷
    if have_target:  # 限制式1: 地址裡有縣或市
        target_end_index = have_target.end()  # should be 3
        target_start_index = target_end_index - str_len  # should be 0
        # 嚴謹判斷
        if target_end_index > 2 and target_start_index >= 0:  # 限制式2: 所有市都是3個字
            # 限制式3: 這3個字必須在縣市清單裡
            if address[target_start_index:target_end_index] in target_list:
                # 成功狀況的處理
                seg_string = address[target_start_index:target_end_index]
                if target_start_index > 0:  # 匹配到的字串前面還有其他字不合理
                    unexpected_string = address[:target_start_index] + ","
                    process_log += f"There is unexpected words before {seg_target}!\n"
                new_address = address[target_end_index:]  # 匹配到的字串刪掉
            else:
                process_log += f"{seg_target} seg fail: Not in {seg_target} list!\n"
        else:
            process_log += f"""
                {seg_target} seg fail: Wrong length with str_len:{str_len}
                target_start_index:{target_start_index}, target_end_index:{target_end_index}!\n
            """
    else:
        process_log += f"{seg_target} seg fail: No keyword!\n"

    return new_address, seg_string, unexpected_string


def seg_only_by_regexp(address: str, seg_target: str, pattern: str):
    """
    address: 要處理的地址
    seg_target: 要正規化的目標名稱，例如'city' or 'dist'
    pattern: 要匹配的字串
    """
    new_address = address
    seg_string = ""
    unexpected_string = ","
    global process_log

    have_target = re.search(pattern, address)
    if have_target:
        target_end_index = have_target.end()
        target_start_index = have_target.start()
        # 成功狀況的處理
        seg_string = address[target_start_index:target_end_index]
        if target_start_index > 0:
            unexpected_string = address[:target_start_index] + ","
            process_log += f"There is unexpected words before {seg_target}!\n"
        new_address = address[target_end_index:]
    else:
        process_log += f"{seg_target} seg fail: Can't find pattern!\n"

    return new_address, seg_string, unexpected_string


def road_seg(address: str, target_list: list):
    """
    Regular expression matching for street names.
    """
    new_addr = address
    seg_str = ""
    other_str = ","
    global process_log

    have_target = re.findall("(街|路|大道)", address)
    if len(have_target) > 0:  # 限制式1: 有找到關鍵字
        target_end_index = address.rfind(have_target[-1]) + len(have_target[-1]) - 1
        target = address[: target_end_index + 1]
        if target in target_list:  # 限制式2: 提取的字必須在清單裡
            # 成功狀況的處理
            seg_str = target
            new_addr = address.replace(seg_str, "")  # 匹配到的字串刪掉
        else:
            process_log += "road seg fail: Not in road list!\n"
    else:
        process_log += "road seg fail: No keyword!\n"

    if seg_str != "":  # 把段納入
        have_section = re.search("[0-9一二三四五六七八九十]段", new_addr)
        if have_section:  # 有段
            if have_section.start() == 0:  # 且是從0開始
                new_addr = new_addr.replace(have_section[0], "")
                seg_str += have_section[0]

    return new_addr, seg_str, other_str


def edit_distance(word1: str, word2: str):
    """
    word1, word2: 比較的兩個字

    note:
    目前看來edit_dist是不夠的，不能顯示出兩個相像的字更可能這件事。例如在edit_dist當中州 -> 洲 是1，
    州 -> 五 也是1。真的要準的話，需要在edit一樣的時候，比對兩個字的替換機率。
    """
    M = len(word1)
    N = len(word2)
    output = [[0] * (N + 1) for i in range(M + 1)]
    for i in range(M + 1):
        for j in range(N + 1):
            if i == 0 and j == 0:
                output[i][j] = 0
            elif i == 0 and j != 0:
                output[i][j] = j
            elif i != 0 and j == 0:
                output[i][j] = i
            elif word1[i - 1] == word2[j - 1]:
                output[i][j] = min(
                    output[i - 1][j - 1], output[i - 1][j] + 1, output[i][j - 1] + 1
                )
            else:
                output[i][j] = min(
                    output[i - 1][j - 1] + 1, output[i - 1][j] + 1, output[i][j - 1] + 1
                )
    return output[M][N]


def road_guessing(address, target_list):
    """
    路名邊界不確定的匹配
    有考慮過利用最小編輯距離來計算，但問題是邊界不確定，變成需要用多種邊界測試。
    或著我可以簡單的用前綴樹來搜尋，然後回傳匹配到 node，而且是最長的那個。
    但前綴樹會無法解決錯別字的問題，所以好像是用最小編輯距離來做會比較好。
    目前的想法是，街道名去掉"路、街"，用它的長度去匹配，看edit的dist
    """
    min_dist = 9
    max_len = 1
    road_name = ""
    raw_road = ""

    # 地址當中如果沒[街道路]，卻有段，優先處理
    section_margin = address.find("段")

    if section_margin > 0:  # 有幾段幾段的
        # 這邊有一個假設是，"X段"就只有兩個字
        raw_road = address[: (section_margin + 1)]
        addr = address[: (section_margin - 1)]
        section = address[(section_margin - 1) : (section_margin + 1)]
        for road in roads:
            edit_dist = edit_distance(road, addr)
            if edit_dist < min_dist:  # 出現更近的距離
                min_dist = edit_dist
                road_name = road + section
    else:  # 沒有幾段幾段，不知道邊界在哪
        for road in roads:
            str_len = len(road)
            addr = address[:str_len]  # 動態邊界的路名
            edit_dist = edit_distance(road, addr)
            if edit_dist <= (str_len - 1):  # 最低門檻
                # 避免像"前街"，去掉街只剩1個字，任何字的edit_dist都是1
                if edit_dist < min_dist:  # 出現更近的距離
                    min_dist = edit_dist
                    max_len = str_len
                    road_name = road
                    raw_road = addr
                elif edit_dist == min_dist:  # 距離一樣但字更長
                    if str_len > max_len:
                        min_dist = edit_dist
                        max_len = str_len
                        road_name = road
                        raw_road = addr
                else:
                    pass

    # 設立門檻，不能什麼都要
    if min_dist > 1:
        road_name = ""
        raw_road = ""

    return road_name, raw_road


def except_rule_for_road(address, target_list):
    """
    路名特殊處理方式，目前用edit_distance
    address: 要處理的地址
    target_list: 用來比對的清單
    """
    new_address = address
    seg_string = ""
    unexpected_string = ","
    new_road = ""
    global process_log

    if re.search(r"[^\d]+", address.replace("號", "")):
        # 成功狀況的處理
        new_road, raw_road = road_guessing(address, target_list)
        seg_string = new_road
        new_address = address.replace(raw_road, "")
        unexpected_string = ""
    else:
        process_log += (
            "road seg fail: Edit distance still can't deal broken road name!\n"
        )
    return new_address, seg_string, unexpected_string


def num_fix(address_num):
    r"""
    修正門牌非單一數字(僅"\d+號" or "\d+之\d+號" or "\d+"不須修正)。

    test
    ----
    num_fix('151至200號')
    """
    global process_log

    try:  # 檢查門牌是否為單一數字
        address_clean = address_num.replace("號", "").replace("之", "")
        int(address_clean)
        new_address_num = address_num
    except ValueError:
        if address_num.find("之") > 0 and address_num.find("至") > 0:  # XX之XX至XX號
            clean_addr_num = address_num.replace("號", "").split("至")
            first_num = int(
                re.search(r"\d+", clean_addr_num[0].split("之")[0]).group(0)
            )
            second_num = int(
                re.search(r"\d+", clean_addr_num[1].split("之")[0]).group(0)
            )
            new_address_num = str(round((first_num + second_num) / 2))
            process_log += (
                "number fix success: Choose median number cause number is an range.\n"
            )
        elif address_num.find("至") > 0:  # 用"至"表示模糊門牌號:
            num_range = address_num.split("號")[0].split("至")
            num_range = [re.search(r"\d+", temp).group(0) for temp in num_range]
            first_num = int(num_range[0])
            second_num = int(num_range[1])
            new_address_num = round((first_num + second_num) / 2)
            process_log += (
                "number fix success: Choose median number cause number is an range.\n"
            )
        else:
            new_address_num = address_num
            process_log += (
                "number fix fail: Address number is not a integer, but cant fix.\n"
            )

    # 格式修正
    if not str(new_address_num).endswith("號"):
        new_address_num = str(new_address_num) + "號"

    return new_address_num


def decide_confidence(addr_dict):
    "衡量可信度"
    # 路與號都沒缺
    is_road_and_num_not_empty = (addr_dict["road"] != "") and (addr_dict["num"] != "")
    # 路與區里符合(未使用)
    # (is_road_and_dist_match = addr_dict['dist'] in road_table1.loc[road_table1['road']
    #  == re.sub('[1-9一二三四五六七八九十]段', '', addr_dict['road']), 'site'].tolist())
    # 解析發生異常，暫時只管road解析的部分
    road_parse_log = addr_dict["other"].split(",")[4]
    if road_parse_log.find("road_guessing") >= 0:
        road_parse_status = "guessing"
    elif road_parse_log.find("road_change") >= 0:
        road_parse_status = "change"
    else:  # 這裡只管解析方式，所以不管有沒有殘留，只要沒標註特別解析方式，都是正常解析
        road_parse_status = "good"
    # 殘留多少字
    parse_remained = addr_dict["other"].replace(",", "").replace("road_guessing", "")
    parse_remained = parse_remained.replace("road_change", "").replace(
        "room_comple", ""
    )
    is_parse_perfect = parse_remained == ""
    is_parse_remained_more_than_two_words = len(parse_remained) > 2
    global process_log

    if is_road_and_num_not_empty:  # 路與號都有值
        if road_parse_status == "good":  # 路名用什麼方式解析成功的
            if is_parse_perfect:  # 無殘留的未解析成功的字串
                confidence_level = "perfect"
            else:  # 有殘留字串
                if is_parse_remained_more_than_two_words:  # 有殘留且多於2字
                    confidence_level = "becareful"
                    process_log += "conf level: more than 2 words remained"
                else:  # 有殘留但小於等於2
                    confidence_level = "trustworthy"
                    process_log += "conf level: less than 2 words remained"
        elif road_parse_status == "change":  # 路名是用pattern匹配的
            if is_parse_perfect:  # 無殘留的未解析成功的字串
                confidence_level = "trustworthy"
                process_log += "conf level: only change road and street"
            else:  # 有殘留字串
                confidence_level = "becareful"
                process_log += (
                    "conf level: change road and street and still words remained"
                )
        else:  # 路名是用edit_dist猜的
            confidence_level = "becareful"
            process_log += "conf level: road name not found, use edit_dist"
    else:  # 不可用地址
        confidence_level = "unavailable"

    return confidence_level


def main_process(addr_cleaned):
    """
    Expected to provide several output results with one strict format behind them.
    """
    # 預計提供數個output結果，但背後有一個最嚴謹的格式
    # 0.用dict存正規化後的結果
    # 1.根據0，輸出沒分隔的字串(100台北市中正區...)
    # 2.根據0，輸出用逗點隔開的字串(100,台北市,中正區,...)
    # 3.根據0，輸出該地址可被識別的部分({postcode}{city}{dist}...)
    standard_addr_list = []
    # num_pattern = '[0-9一二三四五六七八九十百bB]*[之至]*[0-9一二三四五六七八九十百bB]+'
    num_pattern = "[0-9bB]*[之至]*[0-9bB]+"
    num1_pattern = "[0-9bB一二三四五六七八九十]*[之至]*[0-9bB一二三四五六七八九十]+"
    cn_lane = ["怡和巷", "銀光巷", "杏林巷"]
    for i, raw_adc in enumerate(addr_cleaned):
        global process_log
        process_log = ""
        process_log += f"data row {i}:\n"
        addr_dict = {
            "status": "not null",
            "conf_level": "unavailable",
            "postcode": "",
            "city": "",
            "dist": "",
            "vil": "",
            "nebd": "",
            "road": "",
            "lane": "",
            "alley": "",
            "sub_alley": "",
            "num": "",
            "floor": "",
            "room": "",
            "other": "",
            "output": raw_adc,
            "log": "",
        }
        # raw_adc = '台北市萬華區新圯里貴陽街二段17巷2弄3號3樓'
        adc = raw_adc  # 複製一份用來處理的

        # 非地址-NaN的直接跳過
        if adc == "" or adc is np.nan or adc is None:
            addr_dict["status"] = "null"
            standard_addr_list.append(addr_dict)
            continue

        # 非地址-無法辨識、非臺北市
        if not is_address(adc):
            if not is_tpe(adc):
                addr_dict["status"] = "not taipei"
            else:
                addr_dict["status"] = "not address"
            standard_addr_list.append(addr_dict)
            continue

        # 非地址-兩個地址
        roads_count = adc.count("路") + adc.count("街") + adc.count("大道")
        and_count = adc.count("與") + adc.count("及")
        num_count = adc.count("號")
        floor_count = adc.count("樓")
        if (roads_count > 1) and (num_count > 1) and (floor_count > 1):
            addr_dict["status"] = "two addrs"
            standard_addr_list.append(addr_dict)
            continue

        # 非地址-兩條道路的路口
        if (roads_count > 1) and (and_count > 0):  # XX路及OO路
            addr_dict["status"] = "crossroad"
            standard_addr_list.append(addr_dict)
            continue
        elif (roads_count > 1) and (adc.endswith("口")):  # XX路OO路口
            addr_dict["status"] = "crossroad"
            standard_addr_list.append(addr_dict)
            continue

        # segment的過程有一定順序，同時會假設字串內包含此順序，因為地址是有順序的!
        # seg_postcode
        if adc[0:3].isnumeric():
            if adc[0:5].isnumeric():  # 5碼郵遞區號
                if adc[0:5] in postcode5:
                    addr_dict["postcode"] += adc[:5]
                    adc = adc[5:]
            else:  # 3碼郵遞區號
                if adc[0:3] in postcode3:
                    addr_dict["postcode"] += adc[:3]
                    adc = adc[3:]
        else:  # 無郵遞區號
            process_log += "postcode seg fail: Can't find pattern!\n"

        # seg city
        new_addr, seg_str, other_str = seg_sample(adc, "city", "縣市", 3, citys)
        adc = new_addr
        adc = adc.replace("台北市", "").replace("臺北市", "")  # 清除重複出現的縣市
        addr_dict["city"] += seg_str
        addr_dict["other"] += other_str

        # seg dist.
        new_addr, seg_str, other_str = seg_sample(
            adc, "district", "鄉鎮市區", 3, districts
        )
        adc = new_addr
        adc = adc.replace(seg_str, "")  # 清除重複出現的鄉鎮市區
        addr_dict["dist"] += seg_str
        addr_dict["other"] += other_str

        # seg vil.
        new_addr, seg_str, other_str = seg_sample(adc, "village", "里", 3, villages)
        if (seg_str == "") and (
            new_addr.find("里") == 2
        ):  # 如果找不到是什麼里，但又有寫XX里，直接丟掉那個XX里
            new_addr = new_addr[3:]
        adc = new_addr
        adc = adc.replace(seg_str, "")  # 清除重複出現的村里
        addr_dict["vil"] += seg_str
        addr_dict["other"] += other_str

        # seg nebd.
        pattern = f"{num_pattern}鄰"
        new_addr, seg_str, other_str = seg_only_by_regexp(adc, "neighberhood", pattern)
        # 到鄰這邊，為了讓路更好做，所有在鄰之前還有任何字，全部刪掉
        adc = new_addr
        addr_dict["nebd"] += chnumber_to_number(seg_str)
        addr_dict["other"] += other_str

        # seg lane
        # 特別的中文巷名
        new_addr, seg_str, other_str = seg_only_by_regexp(
            adc, "lane", f'{"|".join(cn_lane)}'
        )
        if seg_str == "":
            pattern = "[0-9一二三四五六七八九十]+巷"
            new_addr, seg_str, other_str = seg_only_by_regexp(adc, "lane", pattern)
        if (seg_str == "") and (
            new_addr.find("巷") == 2
        ):  # 如果找不到是什麼巷，但又有寫XX巷，直接丟掉那個XX巷
            new_addr = new_addr[3:]
        adc = new_addr
        addr_dict["lane"] += chnumber_to_number(seg_str)
        addr_dict["other"] += other_str

        # seg alley
        pattern = f"{num_pattern}弄"
        new_addr, seg_str, other_str = seg_only_by_regexp(adc, "alley", pattern)
        adc = new_addr
        addr_dict["alley"] += chnumber_to_number(seg_str)
        addr_dict["other"] += other_str

        # seg sub_alley
        pattern = f"{num_pattern}衖"
        new_addr, seg_str, other_str = seg_only_by_regexp(adc, "sub_alley", pattern)
        adc = new_addr
        addr_dict["sub_alley"] += chnumber_to_number(seg_str)
        addr_dict["other"] += other_str

        # seg number
        pattern = f"[0-9bB]*[之至]*{num1_pattern}號"
        new_addr, seg_str, other_str = seg_only_by_regexp(adc, "number", pattern)
        adc = new_addr
        addr_dict["num"] += chnumber_to_number(seg_str)
        addr_dict["other"] += other_str

        # seg floor
        pattern = "[0-9bB一二三四五六七八九十]*[之至]*[0-9bB一二三四五六七八九十]+樓"
        new_addr, seg_str, other_str = seg_only_by_regexp(adc, "floor", pattern)
        adc = new_addr
        addr_dict["floor"] += chnumber_to_number(seg_str)
        addr_dict["other"] += other_str

        # seg room
        pattern = f"(之{num_pattern})|({num_pattern}室)"
        new_addr, seg_str, other_str = seg_only_by_regexp(adc, "room", pattern)
        adc = new_addr
        addr_dict["room"] += chnumber_to_number(seg_str)
        addr_dict["other"] += other_str

        # seg road
        adcr = ""
        clean_others = []
        others = addr_dict["other"].split(",")
        for other in others:
            if len(other) > 1:
                adcr += other
                clean_others.append("")
            else:
                clean_others.append(other)
        addr_dict["other"] = ",".join(clean_others)
        # 最嚴謹的，用已有清單比對
        new_addr, seg_str, other_str = road_seg(adcr, roads)
        # 把街、路互換，這是地址最容易寫錯的東西
        if seg_str == "":
            if adcr.rfind("路") > 0:  # 路換成街
                adc_changed = (
                    adcr[: adcr.rfind("路")] + "街" + adcr[adcr.rfind("路") + 1 :]
                )
                new_addr, seg_str, other_str = road_seg(adc_changed, roads)
                other_str = "road_change" + other_str
            elif adcr.rfind("街") > 0:  # 街換成路
                adc_changed = (
                    adcr[: adcr.rfind("街")] + "路" + adcr[adcr.rfind("街") + 1 :]
                )
                new_addr, seg_str, other_str = road_seg(adc_changed, roads)
                other_str = "road_change" + other_str
            else:  # 跳過
                pass
        # 配對不到的路名，用edit_dist猜是什麼路
        if seg_str == "":
            new_addr, seg_str, other_str = except_rule_for_road(adcr, roads)
            other_str = "road_guessing" + other_str
        # 還是沒有接近的，就放棄
        if seg_str == "":
            cut_index = max(adcr.rfind("路"), adcr.rfind("街"), adcr.rfind("大道"))
            new_addr, seg_str, other_str = (
                adcr[cut_index + 1 :],
                "",
                adcr[: cut_index + 1],
            )
            other_str = "road_guessing" + other_str + ","
        addr_dict["road"] += seg_str
        addr_dict["other"] += new_addr + other_str

        # seg others
        addr_dict["other"] += adc
        adc = ""

        # complement 遺留值嘗試補完
        else_value = addr_dict["other"].split(",")
        if else_value[-1].isnumeric():  # 在最後面剩下純數字，放到室
            addr_dict["room"] += else_value[-1]
            else_value[-1] = "room_comple"
        elif else_value[-1] == "旁":
            # 在最後面剩下一個"旁"，直接去掉
            else_value[-1] = "旁_del"
        else:
            pass
        addr_dict["other"] = ",".join(else_value)

        # fix 檢查各個parse內容是否正確
        # fix_num 門牌號
        if addr_dict["num"] != "":
            addr_dict["num"] = num_fix(addr_dict["num"])

        # 中文數字轉阿拉伯數字
        addr_dict["lane"] = chnumber_to_number(addr_dict["lane"])
        addr_dict["nebd"] = chnumber_to_number(addr_dict["nebd"])
        addr_dict["num"] = chnumber_to_number(addr_dict["num"])

        # confidence level 信心水準
        addr_dict["conf_level"] = decide_confidence(addr_dict)

        # 處理過程紀錄
        addr_dict["log"] = process_log

        # 輸出格式
        addr_dict["output"] = "".join(
            [
                addr_dict["postcode"],
                addr_dict["city"],
                addr_dict["dist"],
                addr_dict["vil"],
                addr_dict["nebd"],
                addr_dict["road"],
                addr_dict["lane"],
                addr_dict["alley"],
                addr_dict["sub_alley"],
                addr_dict["num"],
            ]
        )

        # save
        standard_addr_list.append(addr_dict)

    return standard_addr_list


def save_data(addr, addr_cleaned, standard_addr_list):
    """
    與main_process配套使用，將結果轉換為df，方便使用。
    
    Example:
        ``` python
        import pandas as pd
        from utils.transform_address import (
            clean_data,
            main_process,
            save_data
        )

        addres = pd.Series(['台北市信義區3民路四段３00號-1(3室)', '信義路-８號之之5樓'])
        addr_cleaned = clean_data(addres)
        standard_addr_list = main_process(addr_cleaned)
        result, output = save_data(addres, addr_cleaned, standard_addr_list)
        ```
        ```
        >>> print(result.iloc[0])
        status                                                 not null
        conf_level                                              perfect
        postcode
        city                                                        台北市
        dist                                                        信義區
        vil
        nebd
        road                                                      三民路四段
        lane
        alley
        sub_alley
        num                                                        300號
        floor
        room                                                         之1
        other                                               ,,,,,,,,,,,
        output                                          台北市信義區三民路四段300號
        log           data row 0:\npostcode seg fail: Can't find pat...
        raw                                       台北市信義區3民路四段３00號-1(3室)
        cleaned                                       台北市信義區三民路四段300號之1
        Name: 0, dtype: object
        ```
    """
    # 轉成df方便輸出
    stnd_addr = pd.DataFrame(standard_addr_list)
    stnd_addr["raw"] = addr
    stnd_addr["cleaned"] = addr_cleaned

    # 簡略版
    simple_output = stnd_addr[["status", "conf_level", "output", "raw", "cleaned"]]

    # 最最最簡單版
    output = stnd_addr[["output", "floor"]]
    output.loc[simple_output["conf_level"] == "unavailable", "output"] = (
        simple_output.loc[simple_output["conf_level"] == "unavailable", "cleaned"]
    )
    output.loc[simple_output["conf_level"] == "becareful", "output"] = (
        simple_output.loc[simple_output["conf_level"] == "becareful", "cleaned"]
    )

    return stnd_addr, output["output"]


def transfer_land_num(land_num):
    """
    7月17日(00170007)
    Aug-81(00810008)
    21(00210000)
    121(01210000)
    335-3(03350003)
    0923-0000(09230000)
    0386-2(03860002)
    """
    e_month = {
        "Jan": "1",
        "Feb": "2",
        "Mar": "3",
        "Apr": "4",
        "May": "5",
        "Jun": "6",
        "Jul": "7",
        "Aug": "8",
        "Sep": "9",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12",
    }
    land_num = str(land_num)
    try:
        if "月" and "日" in land_num:
            land_num = land_num.strip("日").split("月")
            land_num[0] = land_num[0].zfill(4)
            land_num[1] = land_num[1].zfill(4)
            land_num = land_num[1] + land_num[0]
            return land_num
        if len(land_num) > 3:
            if land_num[:3] in e_month:
                land_num = land_num.split("-")
                land_num[0] = e_month[land_num[0]].zfill(4)
                land_num[1] = land_num[1].zfill(4)
                land_num = land_num[1] + land_num[0]
                return land_num
        if "-" in land_num:
            land_num = land_num.split("-")
            land_num[0] = land_num[0].zfill(4)
            land_num[1] = land_num[1].zfill(4)
            land_num = land_num[0] + land_num[1]
            return land_num

        if len(land_num) <= 4:
            land_num = land_num.zfill(4) + "0000"
            return land_num
    except:
        print({"msg": "no rule match"})


def get_addr_xy(addrs):
    """
    Input multiple addresses, return multiple coordinates.
    """
    url = "https://map.tpgos.gov.taipei/embed/webapi.cfm"
    params = {
        "SERVICE": "KEYWORDSEARCH",
        "KEYWORD": "",
        "APIKEY": Variable.get("TPGOS_GET_ADDR_XY"),
        "ITEM_LIST": "TPGOS_CA_ADDR:30",
        "SRS_T": "WGS84",
    }
    x = []
    y = []
    for addr in addrs:
        try:
            # !!! add retry process
            params["KEYWORD"] = addr
            response = requests.get(url, params).json()

            if len(response) > 0:
                if response[0]["QUERYTYPE"] == "完全比對":
                    # print('完全比對')
                    x.append(response[0]["X"])
                    y.append(response[0]["Y"])
                else:
                    # print('未找到完全符合者!')
                    x.append(None)
                    y.append(None)
            else:
                # print('No results return!')
                x.append(None)
                y.append(None)
        except json.decoder.JSONDecodeError:
            print("JSONDecodeError! You mught input a empty addr.")
            x.append(None)
            y.append(None)

    return x, y


# =====multi thread=====
def get_single_addr_xy(addr):
    """
    Input an address and return a coordinate.
    """
    url = "https://map.tpgos.gov.taipei/embed/webapi.cfm"
    params = {
        "SERVICE": "KEYWORDSEARCH",
        # 'SERVICE':'ADDRESS',
        "KEYWORD": addr,
        "APIKEY": Variable.get("TPGOS_GET_ADDR_XY"),
        "ITEM_LIST": "TPGOS_CA_ADDR:30",
        "SRS_T": "WGS84",
    }
    x = None
    y = None
    s = requests.Session()
    s.mount("http://", HTTPAdapter(max_retries=5))
    s.mount("https://", HTTPAdapter(max_retries=5))
    response = s.get(url, params=params)
    try:
        res_json = response.json()
        if len(res_json) > 0:
            if res_json[0]["QUERYTYPE"] == "完全比對":
                print("完全比對 = " + addr)
                x = res_json[0]["X"]
                y = res_json[0]["Y"]
            else:
                print("未找到完全符合者! addr = " + addr)
        else:
            print("No results return! addr = " + addr)
    except json.decoder.JSONDecodeError:
        print("JSONDecodeError!")
        print(response.text)
    return addr, x, y


def get_addr_xy_parallel(addrs, sleep_time=0.5):
    """
    Input a list of addresses and return a list of coordinates.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = pool.map(get_single_addr_xy, addrs)
        # print(results)
        x = []
        y = []

        for i in results:
            print(i)
            x.append(i[1])
            y.append(i[2])
        time.sleep(sleep_time)
    return x, y


postcode3, postcode5, citys, districts, villages, roads = load_dim_data()