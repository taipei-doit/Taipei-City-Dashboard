# Gap Analysis

This file is the honest part. The current hackathon prep is directionally good, but several things are still missing before it can become a real pitch or a PR plan.

## What is already done

- We have a staged prep funnel.
- We have a primary topic.
- We have a backup and a stretch topic.
- We have candidate official data sources.
- We have a rule that AI must stay secondary.
- We have a first draft of the PR wedge idea.

That is enough to stop thrashing. It is not enough to ship.

## Remaining gaps, ranked

### 1. Source verification is still partial
We have candidate official sources, but most of them are still only *candidate* level. The plan needs a pass that confirms, for each source:

- the page really exists,
- the dataset is downloadable or queryable in a usable format,
- the fields are actually present,
- the license or reuse terms do not block the work,
- and the source is fresh enough for the story we want to tell.

**Why it matters:** if one of the core tables cannot be pulled cleanly, the whole topic falls apart. Pretty slides do not save a broken source chain.

### 2. Joinability is not proven yet
The current spec says the topic should join on geography, vulnerability, and resource coverage. That is still a theory, not a tested data model.

We still need to verify:

- what the shared geographic unit is,
- whether Taipei and New Taipei can be normalized to the same level,
- whether facility points can be geocoded or matched safely,
- whether the heat / climate layer can align with the population and shelter layers,
- and whether time should even be part of the MVP or stay out of scope.

**Why it matters:** this is the difference between a working dashboard and a pile of mismatched tables.

### 3. The decision user is still too generic
"Public health or social affairs planners" is not a decision user. It is a room with several people in it.

We need one primary user per topic, for example:

- district response lead,
- climate adaptation planner,
- shelter allocation coordinator,
- or social welfare operations planner.

Then we need one sentence that says what that person decides differently because of the dashboard.

**Why it matters:** judges smell generic civic tech immediately. If the user is fuzzy, the product becomes a poster.

### 4. The PR wedge is not attached to the repo yet
We have a good description of a reusable module, but we do not yet know:

- which component family exists in the dashboard repo,
- what the input contract should look like,
- what file or view it would actually touch,
- or how it would be reviewed and merged.

Because this workspace currently has no visible app source tree, the PR wedge is still conceptual.

**Why it matters:** the hackathon wants something that can come back as code. Without a real integration point, it stays a demo.

### 5. The fallback path is still thin
If heat island data or joinability fails, the backup is disaster response. That is good, but the trigger for switching topics is not formalized.

We need a simple rule:

- if source X fails,
- or joinability score falls below Y,
- or the PR wedge cannot be mapped,
- then we switch to the backup topic.

**Why it matters:** without a hard switch rule, the team will keep re-litigating the same topic and burn time.

### 6. Demo evidence is not yet staged
We have a demo script, but not the actual evidence set that will make it feel real:

- sample screenshots,
- sample numbers,
- one or two fixed example districts,
- and the exact story for each step.

**Why it matters:** a script without evidence is a speech. Judges respond to proof.

### 7. Operational ownership is missing
No one has yet been assigned to:

- source harvesting,
- data normalization,
- map layer selection,
- PR wedge scoping,
- or judge Q&A tightening.

**Why it matters:** the plan is good enough to start, but not yet structured enough to survive a short hackathon timeline without drift.

## Cross-cutting gap themes

### Theme A: We have strategy, not proof
The funnel and topic ranking are right. The missing work is verification.

### Theme B: We have a product idea, not a repo target
The PR wedge is described, but the actual code path is not.

### Theme C: We have a candidate, not a lock
Heat island is the current front-runner, not a final selection.

## What to do next, in order

1. Finish the source inventory with real source checks.
2. Prove the join path on one small sample.
3. Narrow the decision user to one role.
4. Write the exact PR wedge contract.
5. Stage a backup-topic switch rule.
6. Then turn the demo script into a real pitch artifact.

## Revisit conditions

Only revisit a parked topic if one of these happens:

- the primary topic fails source verification,
- the join path fails,
- the PR wedge cannot map to the dashboard repo,
- or the judge story becomes weaker than the backup on the same evidence.

