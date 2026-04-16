# Join Test Plan

## Why this exists
The source inventory says the topic is plausible. This file says how we will prove it.

## Working hypothesis

For the primary topic, the MVP should use this shape:

- **vulnerability layer** = district-level age structure
- **resource layer** = shelters + cooling / relief points
- **heat trigger** = citywide high-temperature warning or temperature context
- **geography** = district names, with facility coordinates used for the map

That is the simplest version that still tells a real story.

## Important constraint

We should **not** try to force a district-level heat exposure map before we know the data exists.

If the heat layer turns out to be citywide or station-based only, that is fine. The MVP can still work as a **prioritization and explanation tool**.

## Join questions to answer

### 1. Can we normalize district names?
Need to verify:
- Taipei district labels,
- New Taipei district labels,
- whether the two portals use the same spelling and formatting.

### 2. Can one facility record be mapped cleanly?
Need to verify:
- shelter address,
- cooling-point address,
- or coordinates if already present.

### 3. Can one vulnerability record be mapped cleanly?
Need to verify:
- district age bands,
- aging index,
- and whether the chosen metric is stable enough for a simple map.

### 4. What is the minimum heat signal?
Need to verify:
- high-temperature warning page,
- weather observation catalog,
- or a single daily trigger.

## First sample pair

Pick one district from each city:

- Taipei: a district with both age data and cooling/shelter points
- New Taipei: a district with age data and shelter points

Then test:

1. age proxy exists,
2. resource proxy exists,
3. heat trigger exists,
4. all labels are readable,
5. the story makes sense in one minute.

## What counts as a pass

The join test passes if we can answer all of these with evidence:

- Which district is most exposed or least supported?
- Why?
- What source backs that up?
- What do we do first?

If we cannot answer those, the topic is not ready.

## What counts as a fail

Fail the heat-topic path if any of these happen:

- district names do not normalize,
- the heat layer is too weak to explain anything,
- the resource layer has no usable coordinates or addresses,
- or the resulting map is only pretty, not actionable.

## Fallback rule

If the join test fails, switch to:

1. `災害避難 + 物資收容調度`
2. if that also fails, stop topic work and pick a smaller public problem

No heroics. This is a hackathon, not a migration.

