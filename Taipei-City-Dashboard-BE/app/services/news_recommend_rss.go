package services

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/logs"
	"context"
	"encoding/xml"
	"fmt"
	"html"
	"io"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"strings"
	"time"
	"unicode/utf8"
)

const atomNS = "http://www.w3.org/2005/Atom"

var rssTagStripper = regexp.MustCompile(`(?is)<[^>]+>`)

const browserLikeUserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

type rssDoc struct {
	XMLName xml.Name   `xml:"rss"`
	Channel rssChannel `xml:"channel"`
}

type rssChannel struct {
	Title string    `xml:"title"`
	Items []rssItem `xml:"item"`
}

type rssItem struct {
	Title       string `xml:"title"`
	Link        string `xml:"link"`
	Description string `xml:"description"`
	PubDate     string `xml:"pubDate"`
	GUID        struct {
		IsPermaLink bool   `xml:"isPermaLink,attr"`
		Value       string `xml:",chardata"`
	} `xml:"guid"`
	ContentEncoded string `xml:"http://purl.org/rss/1.0/modules/content encoded"`
}

type atomDecoded struct {
	Title atomInner         `xml:"title"`
	Entry []atomEntryDecoded `xml:"entry"`
}

type atomInner struct {
	Body string `xml:",chardata"`
}

type atomEntryDecoded struct {
	Title     atomInner `xml:"title"`
	Links     []struct {
		HRef string `xml:"href,attr"`
		Rel  string `xml:"rel,attr"`
		Type string `xml:"type,attr"`
	} `xml:"link"`
	Summary   atomInner `xml:"summary"`
	Published string    `xml:"published"`
	Updated   string    `xml:"updated"`
}

type rssStory struct {
	title       string
	link        string
	description string
	pubDate     string
	source      string
}

func defaultRSSFeeds() []string {
	if v := strings.TrimSpace(os.Getenv("NEWS_RSS_FEEDS")); v != "" {
		var out []string
		for _, p := range strings.Split(v, ",") {
			if u := strings.TrimSpace(p); u != "" {
				out = append(out, u)
			}
		}
		if len(out) > 0 {
			return out
		}
	}
	return []string{
		// 衛福部食品藥物管理署（官網 RSS 訂閱頁：https://www.fda.gov.tw/tc/rss.aspx ）
		"https://www.fda.gov.tw/tc/rssAnnouncement.ashx",
		"https://www.fda.gov.tw/tc/rssNews.ashx",
		"https://www.fda.gov.tw/tc/rssNewsAboutRumor.ashx",
		"https://www.fda.gov.tw/tc/rssActivity.ashx",
		// 中央社 FeedBurner（多數環境可被拉取；舊 rss.cna.com.tw 路徑已常 404）
		"https://feeds.feedburner.com/rsscna/cmEe",
		"https://feeds.feedburner.com/rsscna/local",
		"https://feeds.feedburner.com/rsscna/social",
		"https://www.cna.com.tw/rss/aall.xml",
		"https://news.pts.org.tw/xml/newsfeed.xml",
	}
}

func rssSourceLabel(channelTitle string, link string) string {
	if strings.TrimSpace(channelTitle) != "" {
		return channelTitle
	}
	if u, err := url.Parse(link); err == nil && u.Host != "" {
		return u.Host
	}
	return ""
}

func stripRSSHTML(content string) string {
	d := html.UnescapeString(content)
	d = rssTagStripper.ReplaceAllString(d, " ")
	return strings.Join(strings.Fields(d), " ")
}

func truncateRunes(s string, maxLen int) string {
	if utf8.RuneCountInString(s) <= maxLen {
		return s
	}
	rs := []rune(s)
	if len(rs) <= maxLen {
		return s
	}
	return string(rs[:maxLen]) + "…"
}

func effectiveRSSLink(it rssItem) string {
	if u := strings.TrimSpace(it.Link); u != "" {
		return u
	}
	g := strings.TrimSpace(it.GUID.Value)
	if strings.HasPrefix(g, "http://") || strings.HasPrefix(g, "https://") {
		return g
	}
	return ""
}

func descFromRSSItem(it rssItem) string {
	if d := stripRSSHTML(it.Description); strings.TrimSpace(d) != "" {
		return d
	}
	return stripRSSHTML(it.ContentEncoded)
}

func atomEntryLink(e atomEntryDecoded) string {
	var fallback string
	for _, l := range e.Links {
		h := strings.TrimSpace(l.HRef)
		if h == "" {
			continue
		}
		rel := strings.ToLower(strings.TrimSpace(l.Rel))
		if rel == "alternate" || rel == "" {
			if strings.Contains(strings.ToLower(l.Type), "html") || l.Type == "" {
				return h
			}
			fallback = h
		}
	}
	if fallback != "" {
		return fallback
	}
	if len(e.Links) > 0 {
		return strings.TrimSpace(e.Links[0].HRef)
	}
	return ""
}

func parseRSSBody(body []byte) ([]rssStory, string) {
	var doc rssDoc
	if err := xml.Unmarshal(body, &doc); err != nil || len(doc.Channel.Items) == 0 {
		return nil, ""
	}
	ch := strings.TrimSpace(doc.Channel.Title)
	out := make([]rssStory, 0, len(doc.Channel.Items))
	maxItems := 15
	for i, it := range doc.Channel.Items {
		if i >= maxItems {
			break
		}
		title := strings.TrimSpace(strings.TrimPrefix(it.Title, "\ufeff"))
		link := effectiveRSSLink(it)
		if title == "" {
			continue
		}
		out = append(out, rssStory{
			title:       title,
			link:        link,
			description: truncateRunes(descFromRSSItem(it), 320),
			pubDate:     strings.TrimSpace(it.PubDate),
			source:      rssSourceLabel(ch, link),
		})
	}
	if len(out) == 0 {
		return nil, ""
	}
	return out, ch
}

func parseAtomBody(body []byte) ([]rssStory, string) {
	dec := xml.NewDecoder(strings.NewReader(string(body)))
	dec.DefaultSpace = atomNS
	var f atomDecoded
	if err := dec.Decode(&f); err != nil || len(f.Entry) == 0 {
		return nil, ""
	}
	ch := strings.TrimSpace(f.Title.Body)
	out := make([]rssStory, 0, len(f.Entry))
	maxItems := 15
	for i, e := range f.Entry {
		if i >= maxItems {
			break
		}
		title := strings.TrimSpace(e.Title.Body)
		link := atomEntryLink(e)
		if title == "" {
			continue
		}
		desc := strings.TrimSpace(e.Summary.Body)
		pub := e.Published
		if pub == "" {
			pub = e.Updated
		}
		out = append(out, rssStory{
			title:       title,
			link:        link,
			description: truncateRunes(stripRSSHTML(desc), 320),
			pubDate:     strings.TrimSpace(pub),
			source:      rssSourceLabel(ch, link),
		})
	}
	if len(out) == 0 {
		return nil, ""
	}
	return out, ch
}

func storiesFromFeedBytes(body []byte) ([]rssStory, string) {
	sniff := strings.TrimSpace(string(body))
	if strings.HasPrefix(sniff, "\ufeff") {
		sniff = sniff[len("\ufeff"):]
	}
	body = []byte(sniff)
	prefixLen := min(1200, len(sniff))
	low := strings.ToLower(sniff[:prefixLen])
	if strings.Contains(low, "<feed") {
		if s, ch := parseAtomBody(body); len(s) > 0 {
			return s, ch
		}
	}
	if s, ch := parseRSSBody(body); len(s) > 0 {
		return s, ch
	}
	if s, ch := parseAtomBody(body); len(s) > 0 {
		return s, ch
	}
	return nil, ""
}

// FetchSimpleRSSNewsRecommendations 擷取預設 RSS，合併後以系統 TWCC／LLM 判斷與公開組件的關聯，至多回傳 3 則；不相關者不列入。
func FetchSimpleRSSNewsRecommendations(ctx context.Context) ([]map[string]any, error) {
	comps, err := models.ListPublicComponentsForNewsMatch()
	if err != nil {
		return nil, err
	}
	if len(comps) == 0 {
		return []map[string]any{}, nil
	}

	client := &http.Client{Timeout: 22 * time.Second}

	seenLinks := map[string]struct{}{}
	var stories []rssStory

	for _, feedURL := range defaultRSSFeeds() {
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, feedURL, nil)
		if err != nil {
			continue
		}
		req.Header.Set("User-Agent", browserLikeUserAgent)
		req.Header.Set("Accept", "application/rss+xml, application/atom+xml, application/xml;q=0.9, text/xml;q=0.9, */*;q=0.5")
		req.Header.Set("Accept-Language", "zh-TW,zh;q=0.9,en;q=0.8")
		resp, err := client.Do(req)
		if err != nil || resp == nil || resp.StatusCode >= http.StatusBadRequest {
			if resp != nil && resp.Body != nil {
				_ = resp.Body.Close()
			}
			if err != nil {
				logs.FWarn("RSS fetch error %s: %v", feedURL, err)
			} else if resp != nil {
				logs.FWarn("RSS fetch bad status %s: %s", feedURL, resp.Status)
			}
			continue
		}
		bodyBytes, readErr := io.ReadAll(io.LimitReader(resp.Body, 4<<20))
		_ = resp.Body.Close()
		if readErr != nil {
			logs.FWarn("RSS read body %s: %v", feedURL, readErr)
			continue
		}

		items, _ := storiesFromFeedBytes(bodyBytes)
		if len(items) == 0 {
			logs.FWarn("RSS parse 0 items: %s (body prefix %d bytes)", feedURL, len(bodyBytes))
			continue
		}

		maxItemsPerFeed := 15
		for i, st := range items {
			if i >= maxItemsPerFeed {
				break
			}
			title := strings.TrimSpace(st.title)
			link := strings.TrimSpace(st.link)
			if title == "" {
				continue
			}
			if _, dup := seenLinks[link]; dup && link != "" {
				continue
			}
			if link != "" {
				seenLinks[link] = struct{}{}
			}
			stories = append(stories, rssStory{
				title:       title,
				link:        link,
				description: st.description,
				pubDate:     st.pubDate,
				source:      st.source,
			})
		}
	}

	if len(stories) == 0 {
		return nil, fmt.Errorf(
			"無法取得 RSS 資料。請確認：1) 伺服器對外 HTTPS 可走；2) 設環境變數 NEWS_RSS_FEEDS 為可用的 RSS／Atom URL（可多個逗號分隔）。預設已含食藥署與中央社等公開 RSS；若環境會擋特定站點，請換成可被貴環境抓取之來源；3) 請檢視應用程式日誌中 RSS fetch / parse 訊息",
		)
	}

	matched, errLLM := matchRSSStoriesToComponentsViaLLM(ctx, stories, comps, rssLLMRecommendOutputCap)
	if errLLM != nil {
		return nil, errLLM
	}

	out := make([]map[string]any, 0, len(matched))

	for _, p := range matched {
		c := p.comp
		out = append(out, map[string]any{
			"title":         p.story.title,
			"summary":       p.story.description,
			"url":           p.story.link,
			"source":        p.story.source,
			"published_at":  p.story.pubDate,
			"component": map[string]any{
				"id":         c.ID,
				"index":      c.Index,
				"city":       c.City,
				"name":       c.Name,
				"short_desc": c.ShortDesc,
			},
		})
	}

	return out, nil
}
