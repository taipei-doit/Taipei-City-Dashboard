# AI Boundary

## Rule
AI is a helper, not the product.

The dashboard must still be valid if the AI layer is removed.

## Allowed AI behavior
- summarize the current view,
- compare districts or time windows,
- explain why an area is flagged,
- suggest likely next questions,
- translate raw indicators into planner-friendly language.

## Forbidden AI behavior
- diagnosis,
- personal prediction,
- black-box scoring,
- individualized recommendations,
- policy replacement,
- claims that cannot be traced back to validated data.

## Good AI examples
- “This district is flagged because exposure is high and nearby cooling resources are sparse.”
- “Compared with the city average, this area has higher vulnerability and fewer accessible support points.”
- “The likely next question is whether nearby districts can absorb overflow support.”

## Bad AI examples
- “This person will be at risk.”
- “The model predicts a heat emergency next week with certainty.”
- “This area is unsafe because the LLM says so.”

## Review rule
Before shipping, ask:

1. Can a planner understand the dashboard without AI?
2. Can every AI statement point back to the data?
3. Does the AI layer add explanation, not authority?

If any answer is no, the AI layer is too strong.

