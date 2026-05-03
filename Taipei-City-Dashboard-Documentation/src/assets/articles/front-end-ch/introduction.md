<tpl>introduction</tpl>

## 本文件的內容概覽

本文件涵蓋了臺北城市儀表板 3.0 的前端部分，並詳細介紹本專案的各個主要面向。

> **i01**
> 臺北城市儀表板 3.0 的前端部分在本文件中將統一稱為「本專案」。除非另有說明，所有檔案路徑皆以 `/Taipei-City-Dashboard-FE` 為根目錄。

> **t01**
> 請點擊[這裡](/back-end)以參閱後端文件。

如果您有興趣以任何方式使用本專案的程式庫，建議您務必詳閱前四章以瞭解更多資訊。第五章中的第一篇文章則針對不同的需求提供進一步建議。

如果您在本文件中遇到任何問題或錯字，歡迎點擊每篇文章底部的「於 Github 編輯此文章」按鈕並提出修改建議。您也可以透過電子郵件直接聯繫我們。

## 授權和版權

本專案的程式碼是以[AGPL-3 許可證](https://github.com/taipei-doit/Taipei-City-Dashboard/blob/main/LICENSE)下發行，允許任何形式的修改和商業化。但是，如果您使用我們的程式庫，請務必歸屬我們，且您對程式庫進行任何改動後，也必須將您修改的版本公開釋出，供本產品的其他使用者參考。

## 專案貢獻者

_contributors_
[![DOIT](/images/contributors/doit.png)**DOIT**](https://tuic.gov.taipei)
[![何紹宇](https://avatars.githubusercontent.com/u/105908220?v=4)**何紹宇**](https://github.com/igorho2000)
[![游璿達](https://avatars.githubusercontent.com/u/28524902?v=4)**游璿達**](https://github.com/iimahao)
[![施柔安](https://avatars.githubusercontent.com/u/38744279?v=4)**施柔安**](https://github.com/ann125697)
[![陳威竹](https://avatars.githubusercontent.com/u/141092596?v=4)**陳威竹**](https://github.com/Chu-c-git)
[![黃敬皓](https://avatars.githubusercontent.com/u/70930600?v=4)**黃敬皓**](https://github.com/JHH11)
[![黃軒柏](https://avatars.githubusercontent.com/u/87354177?v=4)**黃軒柏**](https://github.com/godspeedhuang)
[![李思澄](https://avatars.githubusercontent.com/u/147133205?v=4)**李思澄**](https://github.com/annieleeeee)
[![吳亞融](https://avatars.githubusercontent.com/u/147133247?v=4)**吳亞融**](https://github.com/Lauren8799)
[![Max Su](https://avatars.githubusercontent.com/u/24913710?v=4)**Max Su**](https://github.com/hsuanchi)
[![許富盈](https://avatars.githubusercontent.com/u/95673941?v=4)**許富盈**](https://github.com/fuyingxx0)
[![張庭梧](https://avatars.githubusercontent.com/u/53422996?v=4)**張庭梧**](https://github.com/tingwoo)
[![梁璿安](https://avatars.githubusercontent.com/u/96676144?v=4)**梁璿安**](https://github.com/NTUBOY)
[![陳又華](https://avatars.githubusercontent.com/u/101912090?v=4)**陳又華**](https://github.com/chenjoachim)
[![李冠儀](https://avatars.githubusercontent.com/u/58414317?v=4)**李冠儀**](https://github.com/gary920209)
[![陳柏睿](https://avatars.githubusercontent.com/u/90591931?v=4)**陳柏睿**](https://github.com/rakechen-0307)
[![吳典叡](https://avatars.githubusercontent.com/u/92157987?v=4)**吳典叡**](https://github.com/dienruei123)
[![劉庭均](https://avatars.githubusercontent.com/u/104571273?v=4)**劉庭均**](https://github.com/Davidliu012)
[![吳承羲](/images/contributors/codefest.png)**吳承羲**](https://codefest.taipei)
[![楊明倫](https://avatars.githubusercontent.com/u/51404102?v=4)**楊明倫**](https://github.com/KevinYang2229)
[![顏佑軒](https://avatars.githubusercontent.com/u/25718375?v=4)**顏佑軒**](https://github.com/chrisyen8341)
[![徐慶怡](https://avatars.githubusercontent.com/u/116020940?v=4)**徐慶怡**](https://github.com/pandaachuitwm)
[![林昭宏](https://avatars.githubusercontent.com/u/8535502?v=4)**林昭宏**](https://github.com/Toma-L)
[![蔡宜秀](https://avatars.githubusercontent.com/u/149913183?v=4)**蔡宜秀**](https://github.com/EllenTsaitw)
[![黃梓睿](https://avatars.githubusercontent.com/u/117844832)**黃梓睿**](https://github.com/11044123)
[![廖偉翔](https://avatars.githubusercontent.com/u/46708687?v=4)**廖偉翔**](https://github.com/XinRed)
[![陳俊嘉](/images/contributors/codefest.png)**陳俊嘉**](https://github.com/11044123/Taipei-City-Dashboard-FE)
[![沈鈺芳](https://avatars.githubusercontent.com/u/118120884?v=4)**沈鈺芳**](https://github.com/YuFangShen)
[![黃愉翔](https://avatars.githubusercontent.com/u/116791891?v=4)**黃愉翔**](https://github.com/huangyyuuu)
[![林育緹](https://avatars.githubusercontent.com/u/66775433?v=4)**林育緹**](https://github.com/oohyuti)
[![王佑豪](https://avatars.githubusercontent.com/u/66046966?v=4)**王佑豪**](https://github.com/vnaticzhock)
[![謝芝嫻](https://avatars.githubusercontent.com/u/95428315?v=4)**謝芝嫻**](https://github.com/pigbearhsien)
[![賴彥良](https://avatars.githubusercontent.com/u/57023743?v=4)**賴彥良**](https://github.com/yenlianglai)
[![蔡立倫](https://avatars.githubusercontent.com/u/45750993?v=4)**蔡立倫**](https://github.com/tsailawrence)
[![林柔安](https://avatars.githubusercontent.com/u/24452337?v=4)**林柔安**](https://github.com/anne030303/)
[![陳宇修](https://avatars.githubusercontent.com/u/27717979?v=4)**陳宇修**](https://github.com/Kenny-Snub-Nose-Monk)
[![黃亘立](https://avatars.githubusercontent.com/u/2591880?v=4)**黃亘立**](https://github.com/j450nhuang)
[![卓易霆](https://avatars.githubusercontent.com/u/148839168?v=4)**卓易霆**](https://github.com/artgistim)
[![林湛](https://avatars.githubusercontent.com/u/68535430?v=4)**林湛**](https://github.com/janlin002)
[![喻雋凱](https://avatars.githubusercontent.com/u/49083781?v=4)**喻雋凱**](https://github.com/Aquilass)
[![方聖傑](https://avatars.githubusercontent.com/u/93846808?v=4)**方聖傑**](https://github.com/Scottman625)
[![楊采維](https://avatars.githubusercontent.com/u/108170764?v=4)**楊采維**](https://github.com/WeiLocus)
[![劉碩亭](https://avatars.githubusercontent.com/u/76770643?v=4)**劉碩亭**](https://github.com/ottovenliu)
[![黃郁涵](https://avatars.githubusercontent.com/u/64198190?v=4)**黃郁涵**](https://github.com/lopthick3)
[![陳庭勛](https://avatars.githubusercontent.com/u/10396434?v=4)**陳庭勛**](https://github.com/RayChenCode)
[![蔡豪軒](https://avatars.githubusercontent.com/u/42313425?v=4)**蔡豪軒**](https://github.com/ttom525tw)
[![高偉倫](https://avatars.githubusercontent.com/u/82998557?v=4)**高偉倫**](https://github.com/AllenKao06)
[![江建輝](https://avatars.githubusercontent.com/u/42363293?v=4)**江建輝**](https://github.com/ChiangArthur)
[![何子斌](https://avatars.githubusercontent.com/u/43328591?v=4)**何子斌**](https://github.com/ntubrian)
[![張哲瑜](https://avatars.githubusercontent.com/u/4507239?v=4)**張哲瑜**](https://github.com/Mark1002)
[![陳泓霖](https://avatars.githubusercontent.com/u/96641400?v=4)**陳泓霖**](https://github.com/Holin5566)
[![蘇詠智](https://avatars.githubusercontent.com/u/43024271?v=4)**蘇詠智**](https://github.com/scott9909041)
[![蔡誌洧](https://avatars.githubusercontent.com/u/103926221?v=4)**蔡誌洧**](https://github.com/robin502071)
[![黃筠涵](https://avatars.githubusercontent.com/u/104147108?v=4)**黃筠涵**](https://github.com/yhanh)
[![房俊傑](https://avatars.githubusercontent.com/u/14208280?v=4)**房俊傑**](https://github.com/fenjj)
[![羅宇成](https://avatars.githubusercontent.com/u/12069248?v=4)**羅宇成**](https://github.com/david855033)
[![謝智正](https://avatars.githubusercontent.com/u/65650108?v=4)**謝智正**](https://github.com/zuchen75)
[![歐家維](https://avatars.githubusercontent.com/u/111524597?v=4)**歐家維**](https://github.com/jwou0406)
[![詹彥杰](https://avatars.githubusercontent.com/u/91727472?v=4)**詹彥杰**](https://github.com/zhanyanjie6796)
[![吳沛樺](https://avatars.githubusercontent.com/u/22194851?v=4)**吳沛樺**](https://github.com/power80203)
[![林耘熙](https://avatars.githubusercontent.com/u/99649841?v=4)**林耘熙**](https://github.com/freetime007)

## 聯絡我們

tuic@gov.taipei（DOIT 官方電子郵件）

