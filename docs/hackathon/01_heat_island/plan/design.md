# Chart and Map Design

## Design goals
- fast to understand,
- easy to explain in a 5-minute demo,
- visible dual-city value,
- reusable in a city dashboard context,
- meaningful even without AI.

## Primary topic views

### 1. Risk map
Show:
- heat exposure,
- vulnerability proxy,
- resource coverage.

Purpose:
- make the risk distribution visible at a glance.

### 2. Priority comparison
Compare districts / zones with a simple ranking table or bar chart.

Purpose:
- answer “where should we act first?”

### 3. Gap explanation panel
Explain why an area is flagged:
- higher exposure,
- higher vulnerability,
- fewer support resources.

Purpose:
- turn the visualization into a decision story.

### 4. Cross-city comparison
Show Taipei vs New Taipei using the same metric set.

Purpose:
- prove the dual-city framing is real, not rhetorical.

## Chart rules
- Every chart must be understandable without AI.
- Every chart must point to a validated dataset.
- Every chart must help a planner make a decision.

## UI anti-patterns
- a “pretty heatmap” with no action,
- too many layers with no legend,
- charts that only work in one city,
- chart explanations that depend on LLM phrasing.

