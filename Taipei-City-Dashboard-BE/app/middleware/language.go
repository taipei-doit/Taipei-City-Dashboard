package middleware

import (
	"strings"

	"github.com/gin-gonic/gin"
)

// LanguageHandler extracts the target language from the Accept-Language header.
// It prioritizes the first language in the header and falls back to zh-TW.
func LanguageHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 1. Get Accept-Language header (e.g., "en-US,en;q=0.9,zh-TW;q=0.8")
		acceptLang := c.GetHeader("Accept-Language")
		
		targetLang := "zh-TW" // Default

		if acceptLang != "" {
			// Split by comma to get the first preferred language
			parts := strings.Split(acceptLang, ",")
			if len(parts) > 0 {
				// Take the first one and split by semicolon (for q-factor) or hyphen (for region)
				langPart := strings.TrimSpace(parts[0])
				langPart = strings.Split(langPart, ";")[0] // Remove q=0.9
				
				// Map common frontend codes to our internal codes if necessary
				switch {
				case strings.HasPrefix(langPart, "zh-TW"), strings.HasPrefix(langPart, "zh-Hant"):
					targetLang = "zh-TW"
				case strings.HasPrefix(langPart, "en"):
					targetLang = "en"
				case strings.HasPrefix(langPart, "ja"):
					targetLang = "ja"
				case strings.HasPrefix(langPart, "ko"):
					targetLang = "ko"
				case strings.HasPrefix(langPart, "vi"):
					targetLang = "vi"
				case strings.HasPrefix(langPart, "th"):
					targetLang = "th"
				case strings.HasPrefix(langPart, "id"):
					targetLang = "id"
				default:
					// If it's a code we don't recognize, we can either use it directly 
					// or fallback to zh-TW. Let's use the prefix.
					targetLang = langPart
				}
			}
		}

		// 2. Set the language in the context for controllers and services to use
		c.Set("lang", targetLang)

		c.Next()
	}
}
