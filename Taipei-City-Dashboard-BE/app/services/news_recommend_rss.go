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
	"slices"
	"strings"
	"time"
	"unicode"
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

// tokenRunsLower splits loosely on non-letter/non-digit runes so Chinese phrases stay as blocks.
func tokenRunsLower(src string, minRunes int) []string {
	var out []string
	var b strings.Builder
	flush := func() {
		if b.Len() == 0 {
			b.Reset()
			return
		}
		t := strings.TrimSpace(strings.ToLower(b.String()))
		n := utf8.RuneCountInString(t)
		if n >= minRunes && n <= 48 {
			out = append(out, t)
		}
		b.Reset()
	}
	for _, r := range src {
		if unicode.IsLetter(r) || unicode.IsDigit(r) {
			b.WriteRune(r)
		} else {
			flush()
		}
	}
	flush()
	return out
}

func keywordOverlapScore(newsLower string, c models.PublicComponentForNewsMatch) int {
	tokenSet := make(map[string]struct{})
	for _, part := range []string{c.Name, c.ShortDesc, c.Index} {
		for _, t := range tokenRunsLower(strings.TrimSpace(part), 2) {
			tokenSet[t] = struct{}{}
		}
	}

	score := 0

	nameLower := strings.ToLower(strings.TrimSpace(c.Name))
	if nameLower != "" && utf8.RuneCountInString(nameLower) >= 4 && strings.Contains(newsLower, nameLower) {
		score += utf8.RuneCountInString(nameLower) * 2
	}

	for t := range tokenSet {
		if strings.Contains(newsLower, t) {
			score += utf8.RuneCountInString(t)
		}
	}
	return score
}

type scoredPick struct {
	story rssStory
	score int
	comp  models.PublicComponentForNewsMatch
}

func pickDistinctTopStories(scored []scoredPick, minScore int, limit int) []scoredPick {
	seenTitles := map[string]struct{}{}
	out := make([]scoredPick, 0, limit)
	for _, p := range scored {
		if p.score < minScore {
			continue
		}
		key := strings.ToLower(strings.TrimSpace(p.story.title))
		if _, ok := seenTitles[key]; ok {
			continue
		}
		seenTitles[key] = struct{}{}
		out = append(out, p)
		if len(out) >= limit {
			break
		}
	}
	return out
}

// FetchSimpleRSSNewsRecommendations pulls default RSS URLs, merges items, picks up to three with strongest keyword overlap to public components.
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
			"無法取得 RSS 資料。請確認：1) 伺服器對外 HTTPS 可走；2) 設環境變數 NEWS_RSS_FEEDS 為可用的 RSS／Atom URL（可多個逗號分隔）。預設已含中央社 FeedBurner 鏈結；若環境會擋媒體站，請換成可被貴環境抓取之來源；3) 請檢視應用程式日誌中 RSS fetch / parse 訊息",
		)
	}

	var allScored []scoredPick
	for _, st := range stories {
		txt := strings.ToLower(st.title + " " + st.description)
		best := 0
		var chosen models.PublicComponentForNewsMatch
		for _, c := range comps {
			sc := keywordOverlapScore(txt, c)
			if sc > best {
				best = sc
				chosen = c
			}
		}
		allScored = append(allScored, scoredPick{story: st, score: best, comp: chosen})
	}

	slices.SortFunc(allScored, func(a, b scoredPick) int {
		if a.score != b.score {
			return b.score - a.score
		}
		return 0
	})

	uniq := pickDistinctTopStories(allScored, 8, 3)
	if len(uniq) < 1 {
		uniq = pickDistinctTopStories(allScored, 4, 3)
	}
	if len(uniq) < 1 {
		uniq = pickDistinctTopStories(allScored, 1, 3)
	}

	out := make([]map[string]any, 0, len(uniq))

	for _, p := range uniq {
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
