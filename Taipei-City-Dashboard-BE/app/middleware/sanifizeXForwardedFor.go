package middleware

import (
	"net"
	"strings"

	"github.com/gin-gonic/gin"
)

// sanitizeXForwardedFor strips an optional port from the first X-Forwarded-For entry.
// Example: "118.163.65.239:56675, 10.224.0.10" -> "118.163.65.239"
// This helps Gin's ClientIP() work correctly behind proxies that append a source port.
func SanitizeXForwardedFor(c *gin.Context){
	xff := c.GetHeader("X-Forwarded-For")
	if xff != "" {
		first := strings.TrimSpace(strings.Split(xff, ",")[0])
		sanitized := first

		// Handle bracketed IPv6 with port: "[2001:db8::1]:1234"
		if strings.HasPrefix(first, "[") {
			if host, _, err := net.SplitHostPort(first); err == nil {
				sanitized = host
			}
		} else if strings.Count(first, ":") == 1 {
			// Likely IPv4:port
			if host, _, err := net.SplitHostPort(first); err == nil {
				sanitized = host
			}
		}

		// Overwrite with sanitized value so gin.ClientIP() can parse it.
		c.Request.Header.Set("X-Forwarded-For", sanitized)

		// Optional convenience: also populate X-Real-IP if missing.
		if c.GetHeader("X-Real-IP") == "" {
			c.Request.Header.Set("X-Real-IP", sanitized)
		}
	}

	c.Next()
}