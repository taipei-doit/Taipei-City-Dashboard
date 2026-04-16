# Primary Topic Spec — Heat Island + Vulnerable Groups

## Problem statement
Taipei and New Taipei experience severe heat exposure risks, but the people most affected are not only where the temperature is high. Risk depends on:

- population vulnerability,
- access to cooling or shelter resources,
- green coverage / built-environment heat retention,
- cross-district support capacity,
- and whether the public decision-maker can act on the pattern quickly.

The dashboard should help city staff understand **where to prioritize response, what resource gap exists, and why that matters now**.

## Decision user
Likely users:
- public health or social affairs planners,
- disaster / climate adaptation staff,
- district-level operations teams.

## Decision question
> Which districts should receive the first wave of cooling, outreach, or support resources when heat risk rises?

## Why this is a good hackathon topic
- Real public problem
- Easy to explain in one sentence
- Strong map / chart story
- AI can stay secondary
- Lower privacy risk than health or mental-health topics
- Good chance of becoming a reusable dashboard module

## MVP scope
The MVP should answer only:

1. Where is exposure high?
2. Where is vulnerability high?
3. Where are the resource gaps?
4. Which areas should be prioritized first?

## Core dashboard views
1. **Risk map**
   - show heat exposure + vulnerability proxy
2. **Gap comparison**
   - compare exposure vs resources
3. **Priority list**
   - rank districts / zones for response
4. **Explanation panel**
   - summarize why the area is flagged

## AI boundary
AI may:
- summarize the dashboard,
- compare districts,
- explain why an area is flagged,
- suggest next questions for a planner.

AI may not:
- diagnose people,
- predict personal health outcomes,
- create black-box risk scores,
- replace policy rules,
- make claims that cannot be traced back to the data.

## PR wedge
The smallest reusable module should be something like:

- a heat-risk prioritization panel,
- a vulnerability overlay component,
- a resource-gap comparison card,
- or a map layer + legend + explanation component.

If the module cannot be reused in a city dashboard repo, it is too big.

