package services

import (
	"bytes"
	"fmt"
	"io"
	"net/http"

	"golang.org/x/net/html"
)

func removeSpecificTag(n *html.Node, tag_name string) {
	if n == nil {
		return
	}

	// 先處理子節點（避免 pointer 失效）
	for c := n.FirstChild; c != nil; {
		next := c.NextSibling

		if c.Type == html.ElementNode && c.Data == tag_name {
			// 從 DOM 移除
			n.RemoveChild(c)
		} else {
			removeSpecificTag(c, tag_name)
		}

		c = next
	}
}

// 遍歷 DOM，移除 class 與 id
func removeSpecificAttribute(n *html.Node, attr_name string) {
	if n == nil {
		return
	}

	if n.Type == html.ElementNode {
		var newAttrs []html.Attribute
		for _, attr := range n.Attr {
			if attr.Key != attr_name {
				newAttrs = append(newAttrs, attr)
			}
		}
		n.Attr = newAttrs
	}

	for c := n.FirstChild; c != nil; c = c.NextSibling {
		removeSpecificAttribute(c, attr_name)
	}
}

// 取得HTML Body
func GetHTMLBody(url string) string {

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		panic(err)
	}

	// 很重要：避免被當成爬蟲擋掉
	req.Header.Set("User-Agent", "Mozilla/5.0")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	fmt.Println("Status:", resp.Status)

	// 讀取 HTML body（也就是 outerHTML）
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}

	doc, err := html.Parse(bytes.NewReader(body))
	if err != nil {
		panic(err)
	}

	// 1. 移除所有 <script>
	remove_tags := []string{
		"script",
		"nav",
		"footer",
		"header",
		"iframe",
		"button",
		"aside",
		"path",
		"source",
		"noscript",
		"ins",
		"style",
	}
	for _, remove_tag := range(remove_tags){
		removeSpecificTag(doc, remove_tag)
	}

	remove_attrs := []string{
		"class",
		"style",
		"href",
		"src",
		"srcset",
		"data-ylk",
		"id",
		"data-yga",
		"alt",
		"data-uuid",
		"data-google-query-id",
		"data-src",
		"title",
		"data",
		"data-id",
		"width",
		"height",
		"onclick",
		"onkeypress",
		"data-toggle",
	}
	for _, remove_attr := range(remove_attrs){
		removeSpecificAttribute(doc, remove_attr)
	}

	// 找 body node
	var bodyNode *html.Node
	var f func(*html.Node)

	f = func(n *html.Node) {
		if n.Type == html.ElementNode && n.Data == "body" {
			bodyNode = n
			return
		}
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			f(c)
		}
	}

	f(doc)

	if bodyNode == nil {
		fmt.Println("no body found")
		return ""
	}

	// 輸出 outerHTML
	var buf bytes.Buffer
	html.Render(&buf, bodyNode)

	// fmt.Println(buf.String())
	return buf.String()
}
