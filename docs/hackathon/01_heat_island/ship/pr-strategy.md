# PR Wedge

## Goal
Define the smallest reusable module that could plausibly land in the Taipei City Dashboard codebase.

## Good PR wedge characteristics
- narrow scope,
- visually meaningful,
- reusable in other public dashboards,
- easy to review,
- no hard dependency on AI,
- no new data contract that the repo cannot support.

## Candidate wedges
1. **Heat-risk prioritization card**
   - rank areas by exposure + vulnerability + resource gap

2. **Map overlay + legend**
   - show heat risk and cooling-resource access in one reusable layer

3. **Explanation panel**
   - convert validated indicators into a short planner-friendly summary

4. **Comparison table**
   - compare districts side by side with the same indicator set

## Rejection test
If the change is only useful for one demo day and cannot be reused by another city dashboard view, it is not a good wedge.

## What the PR should not be
- a full research report,
- a one-off static webpage,
- an AI prompt demo,
- a complex model training pipeline.

