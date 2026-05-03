

本專案使用 Python 語言，除了部分因 Airflow 所做的調整（如 import level）　以及排版使用　Black　風格外，其餘撰寫規範以 PEP8 風格為準。

> **i01**
> `PEP8` 風格的官方文件可以在[這裡](https://peps.python.org/pep-0008/)找到。

> **i02**
> Black 風格排版可以視為 PEP8 的嚴格子集，它的官方文件可以在[這裡](https://black.readthedocs.io/en/stable/the_black_code_style/index.html)找到。

## 程式碼檢查

以 VSCode IDE 為例，開發者在開啟 pull request 之前，應盡可能排除 Pylint 擴充套件的提示，使用 Isort 擴充套件對引用進行排序，最後使用 Black Formater 擴充套件整理排版。開啟 pull request 的流程將在[此處](/data-end/open-as-request)詳細說明。

> **w01**
> 本文僅涵蓋資料端的程式碼撰寫規範。如果你也將開發我們的前端，請參閱[前端程式碼撰寫規範](/front-end/code-style)。如果你也將開發我們的後端，請參閱[前端程式碼撰寫規範](/back-end/code-style)


## 撰寫風格舉例

### 縮排

使用 4 個空白，而不是 2 個空白或 tab。

### 最大長度

使用 100 個字，而不是 79 個字。VSCode 的設定請參考[這裡](https://stackoverflow.com/questions/71078751/vs-code-python-formatting-change-max-line-length-with-autopep8-yapf-black)。

### 換行策略

一般而言，程式碼一行僅執行一個動作，且不超過最大長度。

當程式碼超過最大長度時，需對程式碼換行。換行以調整括號內表達式的內容為主，將外部括號換行並維持於同一縮排，將表達式內內容換行並後退一個縮排。

當表達式內容可在一行內表達時，列於同一行。

``` python
# Correct:
ImportantClass.important_method_but_too_long(
    exc, limit, lookup_lines, capture_locals, extra_argument
)

# Wrong:
ImportantClass.important_method_but_too_long(exc, limit, lookup_lines, capture_locals, extra_argument)
```

當表達式內容無法在一行內表達時，以逗號分隔。

``` python
# Correct:
def very_important_function(
    template: str,
    *variables,
    file: os.PathLike,
    engine: str,
    header: bool = True,
    debug: bool = False,
):
    """Applies `variables` to the `template` and writes to `file`."""
    with open(file, "w") as f:
        ...

# Wrong:
def very_important_function(template: str, *variables, file: os.PathLike, engine: str, header: bool = True, debug: bool = False):
    """Applies `variables` to the `template` and writes to `file`."""
    with open(file, 'w') as f:
        ...
```

當程式碼超過最大長度卻沒有括號時，不要使用反斜線，請加上括號來進行換行。

``` python
# Correct:
if (
    some_long_rule1
    and some_long_rule2
):
    ...

# Wrong:
if some_long_rule1 \
  and some_long_rule2:
    ...
```

> **w02**
> 避免在任何情況下使用反斜線換行。反斜線換行在某些設定中會造成解析錯誤，請使用括號等其他方案換行。

### 行內注釋

`#` 後隔一個空格，`#` 與程式碼間至少要隔兩個空格。

``` python
# Correct:
x = x + 1  # comment

# Wrong:
x = x + 1 #comment
```

### 空格

在逗號、分號、冒號之後添加空格

``` python
# Correct:
if x == 4: print(x, y); x, y = y, x

# Wrong:
if x == 4 : print(x , y) ; x , y = y , x
```

關鍵字參數中的 `=` 旁不需要使用空格

``` python
# Correct:
def complex(real, imag=0.0):
    return magic(r=real, i=imag)

# Wrong:
def complex(real, imag = 0.0):
    return magic(r=real, i=imag)

# Wrong:
def complex(real, imag=0.0):
    return magic(r = real, i = imag)
```


### 命名規則

所有的變數和檔案名稱都應該是具有意義的。

#### 資料夾、檔案、一般變數、函式

一般情況下，請遵循 snake_case 命名方式。全小寫，並以英文開頭，以底線分隔單字，如 `this_is_snake_case`。

#### Class

請遵循 Upper Camel Case 命名方式。以大寫英文開頭，單字間不分隔，但首字大寫，例如 `ThisIsUpperCamelCase`。

#### 常數

常數是在程式中不應被修改的固定值。
一般情況下，應置於 module 層級，並使用全大寫字母並用底線分隔單字，如 `THIS_IS_CONSTANT`。
