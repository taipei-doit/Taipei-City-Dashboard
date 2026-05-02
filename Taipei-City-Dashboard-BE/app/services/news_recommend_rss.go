package services

import (
	"TaipeiCityDashboardBE/app/models"
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

var rssTagStripper = regexp.MustCompile(`(?is)<[^>]+>`)

type rssEnvelope struct {
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
		"https://rss.cna.com.tw/list/aall.xml",
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
		req.Header.Set("User-Agent", "TaipeiCityDashboard/1.1 news-recommend-rss (+https://github.com/taipei-city-dashboard)")
		resp, err := client.Do(req)
		if err != nil || resp == nil || resp.StatusCode >= http.StatusBadRequest {
			if resp != nil && resp.Body != nil {
				_ = resp.Body.Close()
			}
			continue
		}
		bodyBytes, readErr := io.ReadAll(io.LimitReader(resp.Body, 4<<20))
		_ = resp.Body.Close()
		if readErr != nil {
			continue
		}

		var env rssEnvelope
		if err := xml.Unmarshal(bodyBytes, &env); err != nil || len(env.Channel.Items) == 0 {
			continue
		}
		chTitle := strings.TrimSpace(env.Channel.Title)

		maxItemsPerFeed := 15
		for i, it := range env.Channel.Items {
			if i >= maxItemsPerFeed {
				break
			}
			title := strings.TrimSpace(strings.TrimPrefix(it.Title, "\ufeff"))
			link := strings.TrimSpace(it.Link)
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
				description: truncateRunes(stripRSSHTML(it.Description), 320),
				pubDate:     strings.TrimSpace(it.PubDate),
				source:      rssSourceLabel(chTitle, link),
			})
		}
	}

	if len(stories) == 0 {
		return nil, fmt.Errorf("無法取得 RSS 資料，請確認 NEWS_RSS_FEEDS 或可連線來源網址")
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
