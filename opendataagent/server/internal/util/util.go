package util

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"math/rand"
	"strconv"
	"strings"
	"time"
)

func Now() string {
	return time.Now().UTC().Format(time.RFC3339)
}

func ParseTime(value string) time.Time {
	trimmed := strings.TrimSpace(value)
	if trimmed == "" {
		return time.Time{}
	}
	parsed, err := time.Parse(time.RFC3339, trimmed)
	if err != nil {
		return time.Time{}
	}
	return parsed.UTC()
}

func IntString(value int) string {
	return strconv.Itoa(value)
}

func NewID(prefix string) string {
	return fmt.Sprintf("%s_%d_%06d", prefix, time.Now().UnixNano(), rand.Intn(1000000))
}

func HashText(value string) string {
	sum := sha256.Sum256([]byte(value))
	return hex.EncodeToString(sum[:])
}

func SplitLines(value string) []string {
	return strings.Split(strings.ReplaceAll(value, "\r\n", "\n"), "\n")
}

func BuildUnifiedDiff(left string, right string) (string, int, int, int) {
	leftLines := SplitLines(left)
	rightLines := SplitLines(right)
	maxLen := len(leftLines)
	if len(rightLines) > maxLen {
		maxLen = len(rightLines)
	}

	var builder strings.Builder
	added := 0
	removed := 0
	changed := 0
	for idx := 0; idx < maxLen; idx++ {
		var l string
		var r string
		if idx < len(leftLines) {
			l = leftLines[idx]
		}
		if idx < len(rightLines) {
			r = rightLines[idx]
		}
		if l == r {
			builder.WriteString(" ")
			builder.WriteString(l)
			builder.WriteByte('\n')
			continue
		}
		changed++
		if l != "" {
			builder.WriteString("-")
			builder.WriteString(l)
			builder.WriteByte('\n')
			removed++
		}
		if r != "" {
			builder.WriteString("+")
			builder.WriteString(r)
			builder.WriteByte('\n')
			added++
		}
	}
	return builder.String(), changed, added, removed
}
