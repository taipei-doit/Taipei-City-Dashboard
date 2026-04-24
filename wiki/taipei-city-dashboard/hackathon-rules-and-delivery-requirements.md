# Hackathon Rules and Delivery Requirements

> Sources: Taipei City Government Department of Information Technology, 2026-04-11; Taipei City Government Department of Information Technology, 2026-04-10
> Raw: [2026雙北程式設計節競賽工作坊 競賽規則簡報](../../raw/2026雙北程式設計節競賽工作坊 競賽規則簡報.pdf); [2026雙北程式設計節競賽工作坊 開發團隊工作坊指南編V2](../../raw/2026雙北程式設計節競賽工作坊 開發團隊工作坊指南編V2.pdf)

## Overview

The 2026 Twin Cities Codefest City Dashboard Hackathon asks teams to build scenario-specific Taipei/New Taipei dashboard improvements using open data and the official dashboard architecture. The core delivery requirement is at least four dual-city components, including at least one component with a map layer, with judging weighted toward application value rather than component count or AI depth.

## Event Format

The hackathon runs from May 2 to May 3, 2026 at New Taipei City Hall, 6F auditorium. The documented schedule spans roughly 32 hours, with more than 24 hours of development and two judging stages.

Day 1 includes registration, opening and rule explanation, the official start, meals, hacking time, and coding clinic support. Day 2 includes breakfast, file submission, first-round selection, finalist announcement and equipment testing, final presentations, awards, and closing.

## Themes

Teams choose from six application themes:

- Smart commute: traffic, public transit, commuting behavior, congestion, transfers, travel time, and route alternatives.
- Disaster resilience: weather, water, risk zones, historical disaster distribution, warnings, shelters, and response resources.
- Sustainable environment: air quality, energy use, emissions, green facilities, environmental resources, indicators, and policy effects.
- Food safety and health: inspection results, violations, disease trends, health indicators, medical resources, and service access.
- Labor and welfare: employment structure, labor conditions, unemployment trends, welfare resources, and vulnerable-group care.
- Cultural inclusion: cultural activities, tourism resources, group participation, business districts, and cultural policy support.

## Required Deliverables

Every team must complete at least four dual-city components. At least one of those components must include a map layer.

A dual-city component is considered valid when users can switch between Taipei City and the Taipei/New Taipei combined view through a dropdown and see corresponding chart information. A dual-city map layer is valid when the dropdown can switch between Taipei City and Taipei/New Taipei and show corresponding layer information.

Submissions cannot directly reuse existing sample components. Components must be presented through the system database.

## Data Rules

Datasets must be open, legal, transparent, and verifiable. Recommended sources include `data.taipei` and `data.ntpc.gov.tw`, with other public sources such as weather, environment, water, disaster alert, transport, culture, disease-control, food and drug, and agriculture open-data platforms also listed.

The workshop guide emphasizes data quality over data quantity. It recommends CSV import, UTF-8 encoding, clear source provenance, and avoiding excessive mock data because source review may occur during later judging.

## Technical Constraints

Teams must work from a fork of the official project in their own repository and develop locally with version control so the competition can inspect work.

The recommended stack is Vue 3, Vite, Pinia, Mapbox, Go/Gin, and Redis. Windows users should support WSL2. Docker users should avoid port conflicts, and teams should avoid rerunning database initialization commands because existing data can be cleared.

Third-party package use is restricted to the whitelist. Teams may not introduce unauthorized external libraries, and chart optimization may not use chart packages other than ApexCharts. Data formats are limited to the existing dashboard formats: two-dimensional, three-dimensional, time series, percentage, and map legend data.

## Scoring

Judging weights are:

- Application value: 40%, focused on whether components actually solve a problem.
- Technical quality: 30%, focused on optimization, integration, and extension.
- Creativity: 30%, focused on new features or breakthroughs.

The guide explicitly notes that judging is not about producing the most components. It is about the depth and value of the application scenario. AI usage is optional and is not the main scoring target.

## AI and Resource Rules

Teams may use AI, but if they use AI compute they must use the designated Taiwan AI Cloud model and API service. The authorized model is `llama3.3-ffm-70b-16k-chat`. Each team receives one dedicated API key on competition day, with a strict 30 RPM limit. Abnormal behavior can result in service suspension.

The rules warn against relying on pure vibe coding. Teams must be able to maintain and modify their source code. If a winning team cannot complete required official integration work, it may lose prize eligibility.

## Rights, Licensing, and Post-Award Duties

Competition works are expected to remain under AGPL terms, and the dashboard fork must not be taken down without authorization for three years. Teams must ensure their work does not infringe intellectual property rights or violate laws.

Winning teams must authorize the organizers to use their results and collaborate with the organizers to integrate selected work into the official repository. The organizers will contact winners within two weeks after the competition to discuss collaboration items.

## Development Strategy

The workshop recommends focusing Day 1 on an MVP that closes the core functional loop and validates the usage scenario. Day 2 should prioritize submission documents, integration testing, demo rehearsal, and stability. Teams are encouraged to use mock data to parallelize front-end/back-end development, but final data must have legitimate and verifiable sources.

## See Also

- [AI Model and Tool Calling Integration](ai-model-and-tool-calling-integration.md)
- [Data and Visualization Formats](data-and-visualization-formats.md)
- [Design and Code Standards](design-and-code-standards.md)
- [Platform Model](platform-model.md)
