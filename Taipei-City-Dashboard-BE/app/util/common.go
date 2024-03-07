package util

import (
	"crypto/sha256"
	"fmt"
)

// HashString takes a string as input, hashes it using SHA-256, and returns the hexadecimal representation of the hash.
func HashString(s string) string {
	h := sha256.New()
	h.Write([]byte(s))
	return fmt.Sprintf("%x", h.Sum(nil))
}

// MergeAndRemoveDuplicates merges multiple integer slices and removes duplicates.
func MergeAndRemoveDuplicates(slices ...[]int) []int {
	merged := make(map[int]struct{})

	// Merge two slices and remove duplicates
	for _, slice := range slices {
		for _, item := range slice {
			merged[item] = struct{}{}
		}
	}

	// Convert to slice
	result := make([]int, 0, len(merged))
	for item := range merged {
		result = append(result, item)
	}

	return result
}
