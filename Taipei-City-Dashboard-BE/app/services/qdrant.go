package services

import (
	"TaipeiCityDashboardBE/app/models"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings" // Added for string manipulation
	"sync/atomic"

	"TaipeiCityDashboardBE/global" // Added this import
)

// isQdrantRebuilding is an atomic boolean to prevent concurrent rebuilds.
var isQdrantRebuilding atomic.Bool

// qdrantPoint represents a single point to be upserted to Qdrant.
type qdrantPoint struct {
	// The ID is an interface{} to accommodate both integer and UUID string IDs.
	ID      interface{}            `json:"id"`
	Vector  []float32              `json:"vector"`
	Payload map[string]interface{} `json:"payload"`
}

// RebuildQdrantPublicCollection fetches the latest public component data, generates vectors, and rebuilds the Qdrant collection.
// It is designed to be run asynchronously and is concurrency-safe.
func RebuildQdrantPublicCollection() ([]models.QuertChartAndConponentForQdrant, error) {
	// Use CompareAndSwap to ensure only one instance runs at a time.
	if !isQdrantRebuilding.CompareAndSwap(false, true) {
		log.Println("Qdrant rebuild is already in progress. Skipping.")
		return nil, fmt.Errorf("qdrant rebuild is already in progress")
	}
	// Ensure the flag is reset when the function exits.
	defer isQdrantRebuilding.Store(false)

	log.Println("Starting Qdrant public collection rebuild...")
	ctx := context.Background()

	// 1. Fetch data from PostgreSQL using the model function
	data, err := fetchPublicComponentData()
	if err != nil {
		log.Printf("Error fetching public component data: %v", err)
		return nil, err
	}
	if len(data) == 0 {
		log.Println("No public component data found. Aborting Qdrant rebuild.")
		return data, nil
	}
	
	// 2. Generate vectors for each data point	points, vectorSize, err := generateVectors(data)
	points, vectorSize, err := generateVectors(data)
	if err != nil {
		log.Printf("Error generating vectors: %v", err)
		return data, err
	}

	// 3. Recreate Qdrant collection
	collectionName := os.Getenv("QDRANT_COLLECTION_NAME")
	if collectionName == "" {
		collectionName = "query_charts" // Default collection name
	}

	err = recreateCollection(ctx, collectionName, uint64(vectorSize))
	if err != nil {
		log.Printf("Error recreating Qdrant collection: %v", err)
		return data, err
	}
	// 4. Upsert new points to Qdrant
	err = upsertPoints(ctx, collectionName, points)
	if err != nil {
		log.Printf("Error upserting points to Qdrant: %v", err)
		return data, err
	}

	log.Printf("Successfully rebuilt Qdrant collection '%s' with %d points.", collectionName, len(points))
	return data, nil
}

// fetchPublicComponentData now calls the model function.
func fetchPublicComponentData() ([]models.QuertChartAndConponentForQdrant, error) {
	return models.GetPublicComponentsForQdrant()
}

func generateVectors(data []models.QuertChartAndConponentForQdrant) ([]qdrantPoint, int, error) {
	var points []qdrantPoint
	var vectorSize int

	for _, item := range data {
		// Combine text fields for vector generation
		combinedText := item.LongDesc
		if item.UseCase != "" {
			if combinedText != "" {
				combinedText += " "
			}
			combinedText += item.UseCase
		}

		// Sanitize newline characters, as suspected by the user.
		// Replace all `\r\n`, `\r`, and `\n` with a single space.
		combinedText = strings.ReplaceAll(combinedText, "\r\n", " ")
		combinedText = strings.ReplaceAll(combinedText, "\r", " ")
		combinedText = strings.ReplaceAll(combinedText, "\n", " ")
		
		if combinedText == "" {
			log.Printf("Skipping item ID %d (%s) due to empty combined text for vector generation.", item.ID, item.Name)
			continue
		}

		// Generate vector
		vector, err := models.GenVector(combinedText)
		if err != nil {
			return nil, 0, fmt.Errorf("failed to generate vector for item %s/%s: %w", item.Index, item.Name, err)
		}

		// Set vector size if not already set
		if vectorSize == 0 {
			vectorSize = len(vector)
		}

		// Create payload
		payload := map[string]interface{}{
			"id":        item.ID,
			"index":     item.Index,
			"name":      item.Name,
			"city":      item.City,
			"long_desc": item.LongDesc,
			"use_case":  item.UseCase,
		}

		// Handle point ID type: Qdrant accepts integer or UUID string.
		// Since item.ID is now int64, we can use it directly as a uint64 point ID.
		points = append(points, qdrantPoint{
			ID:      uint64(item.ID),
			Vector:  vector,
			Payload: payload,
		})
	}

	return points, vectorSize, nil
}

// recreateCollection deletes and then creates a new Qdrant collection.
func recreateCollection(ctx context.Context, collectionName string, vectorSize uint64) error {
	qdrantConfig := global.Qdrant
	qdrantURL := qdrantConfig.Url

	// 1. Try to delete the existing collection
	log.Printf("Attempting to delete Qdrant collection '%s'...", collectionName)
	deleteURL := fmt.Sprintf("%s/collections/%s", qdrantURL, collectionName)
	deleteReq, err := http.NewRequestWithContext(ctx, http.MethodDelete, deleteURL, nil)
	if err != nil {
		return fmt.Errorf("failed to create delete collection request: %w", err)
	}
	if qdrantConfig.ApiKey != "" {
		deleteReq.Header.Set("api-key", qdrantConfig.ApiKey)
	}

	deleteResp, err := http.DefaultClient.Do(deleteReq)
	if err != nil {
		return fmt.Errorf("failed to send delete collection request for '%s': %w", collectionName, err)
	} else {
		defer deleteResp.Body.Close()
		if deleteResp.StatusCode == http.StatusOK {
			log.Printf("Collection '%s' deleted successfully.", collectionName)
		} else {
			// Log other statuses (like 404 Not Found) as info, not as a hard error.
			bodyBytes, _ := io.ReadAll(deleteResp.Body)
			log.Printf("Info: Qdrant delete collection returned status %s, body: %s", deleteResp.Status, string(bodyBytes))
		}
	}

	// 2. Create the new collection
	log.Printf("Creating new Qdrant collection '%s' with vector size %d.", collectionName, vectorSize)
	createURL := fmt.Sprintf("%s/collections/%s?timeout=30", qdrantURL, collectionName)
	createBody := map[string]interface{}{
		"vectors": map[string]interface{}{
			"size":     vectorSize,
			"distance": "Cosine",
		},
	}
	createBodyBytes, err := json.Marshal(createBody)
	if err != nil {
		return fmt.Errorf("failed to marshal create collection request body: %w", err)
	}

	createReq, err := http.NewRequestWithContext(ctx, http.MethodPut, createURL, bytes.NewBuffer(createBodyBytes))
	if err != nil {
		return fmt.Errorf("failed to create create-collection request: %w", err)
	}
	createReq.Header.Set("Content-Type", "application/json")
	if qdrantConfig.ApiKey != "" {
		createReq.Header.Set("api-key", qdrantConfig.ApiKey)
	}

	createResp, err := http.DefaultClient.Do(createReq)
	if err != nil {
		return fmt.Errorf("failed to send create-collection request: %w", err)
	}
	defer createResp.Body.Close()

	if createResp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(createResp.Body)
		return fmt.Errorf("qdrant create collection returned status %s, body: %s", createResp.Status, string(bodyBytes))
	}

	log.Printf("Collection '%s' created successfully.", collectionName)
	return nil
}

// upsertPoints uploads the generated vector points to the Qdrant collection.
func upsertPoints(ctx context.Context, collectionName string, points []qdrantPoint) error {
	if len(points) == 0 {
		log.Println("No points to upsert. Skipping.")
		return nil
	}

	qdrantConfig := global.Qdrant
	qdrantURL := qdrantConfig.Url

	// Define the structure for the upsert request body
	type upsertRequest struct {
		Points []qdrantPoint `json:"points"`
	}

	reqBody := upsertRequest{
		Points: points,
	}

	bodyBytes, err := json.Marshal(reqBody)
	if err != nil {
		return fmt.Errorf("failed to marshal upsert request body: %w", err)
	}

	// Use wait=true to ensure the operation is indexed before returning
	upsertURL := fmt.Sprintf("%s/collections/%s/points?wait=true", qdrantURL, collectionName)

	req, err := http.NewRequestWithContext(ctx, http.MethodPut, upsertURL, bytes.NewBuffer(bodyBytes))
	if err != nil {
		return fmt.Errorf("failed to create upsert points request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	if qdrantConfig.ApiKey != "" {
		req.Header.Set("api-key", qdrantConfig.ApiKey)
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Printf("Error sending upsert points request for '%s': %v", collectionName, err)
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("qdrant upsert points returned status %s, body: %s", resp.Status, string(bodyBytes))
	}

	log.Printf("Successfully upserted %d points to collection '%s'.", len(points), collectionName)
	return nil
}
