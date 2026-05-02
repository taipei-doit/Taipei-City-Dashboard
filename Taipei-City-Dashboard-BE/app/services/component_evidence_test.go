package services

import (
	"context"
	"fmt"
	"testing"
)

func TestBuildComponentEvidencePackNoQdrantHits(t *testing.T) {
	restore := stubEvidenceDependencies(
		func(ctx context.Context, query string, limit int, scoreThreshold float32) ([]ComponentResult, error) {
			return []ComponentResult{}, nil
		},
		nil,
	)
	defer restore()

	pack, err := BuildComponentEvidencePack(context.Background(), ComponentEvidenceQuery{UserQuestion: "test question"})
	if err != nil {
		t.Fatalf("BuildComponentEvidencePack returned error: %v", err)
	}
	if pack.Answerability.Status != "not_answerable" {
		t.Fatalf("answerability status = %q, want not_answerable", pack.Answerability.Status)
	}
	if pack.Retrieval.CandidateCount != 0 {
		t.Fatalf("candidate count = %d, want 0", pack.Retrieval.CandidateCount)
	}
}

func TestBuildComponentEvidencePackPartialWhenOneComponentFails(t *testing.T) {
	restore := stubEvidenceDependencies(
		func(ctx context.Context, query string, limit int, scoreThreshold float32) ([]ComponentResult, error) {
			return []ComponentResult{
				{ID: 1, Index: "ok_component", Name: "OK Component", City: "taipei", Score: 0.91},
				{ID: 2, Index: "failed_component", Name: "Failed Component", City: "taipei", Score: 0.88},
			}, nil
		},
		func(index string, city string, timeFrom string, timeTo string) (ComponentChartDataResult, error) {
			if index == "failed_component" {
				return ComponentChartDataResult{Index: index, City: city, QueryType: "time"}, fmt.Errorf("database timeout")
			}
			return ComponentChartDataResult{
				Index:     index,
				City:      city,
				QueryType: "time",
				Unit:      "unit",
				Data:      []map[string]interface{}{{"x": "2026-05-01T00:00:00+08:00", "y": 1}},
			}, nil
		},
	)
	defer restore()

	pack, err := BuildComponentEvidencePack(context.Background(), ComponentEvidenceQuery{UserQuestion: "test question"})
	if err != nil {
		t.Fatalf("BuildComponentEvidencePack returned error: %v", err)
	}
	if pack.Answerability.Status != "partial" {
		t.Fatalf("answerability status = %q, want partial", pack.Answerability.Status)
	}
	if len(pack.Components) != 1 {
		t.Fatalf("components len = %d, want 1", len(pack.Components))
	}
	if len(pack.InsufficientComponents) != 1 {
		t.Fatalf("insufficient components len = %d, want 1", len(pack.InsufficientComponents))
	}
	if pack.InsufficientComponents[0].Status != "error" {
		t.Fatalf("failed component status = %q, want error", pack.InsufficientComponents[0].Status)
	}
}

func TestBuildComponentEvidencePackAnswerableWhenAllComponentsSucceed(t *testing.T) {
	restore := stubEvidenceDependencies(
		func(ctx context.Context, query string, limit int, scoreThreshold float32) ([]ComponentResult, error) {
			return []ComponentResult{
				{ID: 1, Index: "component_a", Name: "Component A", City: "taipei", Score: 0.91},
				{ID: 2, Index: "component_b", Name: "Component B", City: "taipei", Score: 0.89},
			}, nil
		},
		func(index string, city string, timeFrom string, timeTo string) (ComponentChartDataResult, error) {
			return ComponentChartDataResult{
				Index:     index,
				City:      city,
				QueryType: "two_d",
				Unit:      "unit",
				Data:      []map[string]interface{}{{"x": "label", "y": 1}},
			}, nil
		},
	)
	defer restore()

	pack, err := BuildComponentEvidencePack(context.Background(), ComponentEvidenceQuery{UserQuestion: "test question"})
	if err != nil {
		t.Fatalf("BuildComponentEvidencePack returned error: %v", err)
	}
	if pack.Answerability.Status != "answerable" {
		t.Fatalf("answerability status = %q, want answerable", pack.Answerability.Status)
	}
	if len(pack.Components) != 2 {
		t.Fatalf("components len = %d, want 2", len(pack.Components))
	}
}

func TestBuildComponentEvidencePackNormalizesLimitsAndCity(t *testing.T) {
	var observedLimit int
	restore := stubEvidenceDependencies(
		func(ctx context.Context, query string, limit int, scoreThreshold float32) ([]ComponentResult, error) {
			observedLimit = limit
			return []ComponentResult{}, nil
		},
		nil,
	)
	defer restore()

	pack, err := BuildComponentEvidencePack(context.Background(), ComponentEvidenceQuery{
		UserQuestion: "test question",
		City:         "invalid",
		TopK:         99,
	})
	if err != nil {
		t.Fatalf("BuildComponentEvidencePack returned error: %v", err)
	}
	if pack.City != "taipei" {
		t.Fatalf("city = %q, want taipei", pack.City)
	}
	if pack.Retrieval.TopK != maxEvidenceTopK {
		t.Fatalf("retrieval top_k = %d, want %d", pack.Retrieval.TopK, maxEvidenceTopK)
	}
	if observedLimit != maxEvidenceTopK {
		t.Fatalf("search limit = %d, want %d", observedLimit, maxEvidenceTopK)
	}
}

func TestBuildComponentEvidencePackKeepsMetrotaipei(t *testing.T) {
	restore := stubEvidenceDependencies(
		func(ctx context.Context, query string, limit int, scoreThreshold float32) ([]ComponentResult, error) {
			return []ComponentResult{}, nil
		},
		nil,
	)
	defer restore()

	pack, err := BuildComponentEvidencePack(context.Background(), ComponentEvidenceQuery{
		UserQuestion: "test question",
		City:         "metrotaipei",
	})
	if err != nil {
		t.Fatalf("BuildComponentEvidencePack returned error: %v", err)
	}
	if pack.City != "metrotaipei" {
		t.Fatalf("city = %q, want metrotaipei", pack.City)
	}
}

func stubEvidenceDependencies(
	search func(context.Context, string, int, float32) ([]ComponentResult, error),
	fetch func(string, string, string, string) (ComponentChartDataResult, error),
) func() {
	oldSearch := searchQdrantComponentsForEvidence
	oldFetch := fetchComponentDataForEvidence
	if search != nil {
		searchQdrantComponentsForEvidence = search
	}
	if fetch != nil {
		fetchComponentDataForEvidence = fetch
	}
	return func() {
		searchQdrantComponentsForEvidence = oldSearch
		fetchComponentDataForEvidence = oldFetch
	}
}
