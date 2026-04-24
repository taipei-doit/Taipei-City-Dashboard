# AI Chat and Chatlog Services

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [ai chat apis](../../raw/taipei-dashboard-backend/ai chat apis.md); [chatlog apis](../../raw/taipei-dashboard-backend/chatlog apis.md); [chatlog db](../../raw/taipei-dashboard-backend/chatlog db.md); [vector db apis](../../raw/taipei-dashboard-backend/vector db apis.md)

## Overview

The backend integrates TWCC/TWS large language models through `langchaingo`, exposes an authenticated AI chat API, supports streaming responses and tool calling, logs AI usage to `ai_chatlog`, and separately provides a user-facing `chatlog` API for storing chatbox conversations.

## AI Chat API

`POST /ai/chat/twai` lets logged-in users converse with the TWCC model. Requests use `Authorization: Bearer <JWT_TOKEN>`.

The request body includes a message history plus optional model parameters such as `session`, `stream`, `temperature`, `max_new_tokens`, `top_p`, `top_k`, `frequence_penalty`, `stop_sequences`, `seed`, `tools`, and `tool_choice`.

When `stream` is false, the response returns final content, latency, model, provider, session, tool-use flag, and token usage. When `stream` is true, the backend returns `text/event-stream`.

## Environment Configuration

AI behavior is configured through environment variables:

- `TWCC_API_URL`, defaulting to `https://api-ams.twcc.ai/api`.
- `TWCC_API_KEY`.
- `TWCC_MODEL`, defaulting to `llama3.3-ffm-70b-16k-chat`.
- `TWCC_TIMEOUT`, defaulting to 60 seconds.
- `TWCC_MAX_RETRY`, defaulting to 2 for non-streaming requests.
- `TWCC_MAX_CONCURRENT`, defaulting to 10 concurrent AI requests.

## Tool-Calling Runtime

The controller validates parameters, generates sessions, and prepares SSE responses when streaming. The AI service creates an `aiSession`, injects instructions, controls concurrency with a semaphore, counts tokens, and runs the tool-execution loop.

The TWCC provider converts generic requests into TWCC format, parses XML tool tags, and cleans content. Tool functions are registered in `app/services/ai/tools/registry.go` and executed reflectively.

Tool calls can be represented in JSON or XML format. The backend executes matching Go functions, appends tool results to the conversation as `role: tool`, and asks the model again until a final answer is reached or the maximum of five loops is hit.

## Streaming Guardrails

In streaming mode, the backend buffers the first 64 characters to detect tool instructions. If a tool call is detected, raw tool output is withheld from the client while the backend executes the tool and obtains a final plain-text answer.

The TWCC provider also includes XML cleanup because TWS models may leave invalid XML tags in conversation history, which can break later model requests.

## Logging

The AI API logs provider, model, question, answer, tool use, tool details, token usage, latency, status, error fields, IP address, session, user, and creation time to `ai_chatlog`.

The separate `chatlog` table records chatbox conversation history with session, question, answer, IP address, user ID, and timestamps.

The chatlog API includes:

- `POST /api/v1/chatlog` to create a log entry for a logged-in user.
- `GET /api/v1/chatlog/session/` to list sessions for a logged-in user.
- `GET /api/v1/chatlog/session/:session` to list messages in one session.

## See Also

- [AI Model and Tool Calling Integration](../taipei-city-dashboard/ai-model-and-tool-calling-integration.md)
- [Component Data Querying](component-data-querying.md)
