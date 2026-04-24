# AI Model and Tool Calling Integration

> Sources: Taiwan AI Cloud Corporation, 2026-04-08; Taipei City Government Department of Information Technology, 2026-04-10
> Raw: [2026雙北程式設計節競賽工作坊 模型使用說明簡報](../../raw/hackathon/2026雙北程式設計節競賽工作坊 模型使用說明簡報.pdf); [2026雙北程式設計節競賽工作坊 開發團隊工作坊指南編V2](../../raw/hackathon/2026雙北程式設計節競賽工作坊 開發團隊工作坊指南編V2.pdf)

## Overview

The hackathon AI setup uses Taiwan AI Cloud's TWCC model service with the dashboard backend acting as a protected gateway. The intended architecture sends user messages to a backend AI chat endpoint, lets the LLM decide whether to call tools, routes tool calls through backend functions or APIs, and records interactions in `ai_chatlog` for audit, debugging, and resource governance.

## Competition Model

The designated model is `Llama3.3-FFM-70B-16K`, with model name `llama3.3-ffm-70b-16k-chat` and a 16K context length.

For testing from April 11 to May 1, teams can register for Taiwan AI Cloud membership and use trial credits. For competition use on May 2 to May 3, the organizers provide API keys. The competition limit is 30 requests per minute per team API key.

## Taiwan AI Cloud Account and ModelSpace Flow

The model-use slides describe this setup flow:

1. Register or log in through the TWAI website.
2. Choose the A100/V100 GPU service path.
3. Enter the registration email.
4. Accept the personal-data and rights/obligations statement.
5. Fill account, password, and basic information.
6. Set a host password that differs from the member password.
7. Complete email and mobile verification.
8. Enter the TWCC main screen after activation.
9. Open AFS ModelSpace from the TWCC home page.
10. Select Public Mode to use the model through an API key.
11. Retrieve the API endpoint and API key.
12. Follow the API sample documentation and replace the sample model name with `llama3.3-ffm-70b-16k-chat`.

Taiwan AI Cloud support is listed as 24-hour phone support at `(02)8979-6199` and email `service@twcloud.ai`.

## Environment Configuration

The workshop guide requires API secrets to be managed through environment variables rather than hardcoded in source. The stated security pattern is to isolate credentials through environment variables and wrap calls through a proxy server or backend gateway.

Key environment/configuration fields include:

- `TWCC_API_URL`: documented endpoint base `https://api-ams.twcc.ai/api`.
- `TWCC_API_KEY`: the authorization credential.
- `TWCC_MODEL`: the model profile/name.
- `TIMEOUT`: 60.
- `MAX_RETRY`: 2.

## Gateway Endpoint

Developers should call the backend gateway instead of calling the model directly from the client. The documented service endpoint is:

```http
POST /api/v1/ai/chat/twai
```

The basic request sends a `messages` array containing `role` and `content`. In the initial mode, the system returns a plain-text AI answer and does not yet involve tool calling.

## Tool Calling Flow

The AI architecture is organized around four steps:

1. The client sends a user request through the AI chat API.
2. The backend core service integrates with the TWCC LLM for intelligent dialog.
3. `ToolRouter` parses returned `tool_calls` and executes matching functions.
4. Conversation details are written to `AI_ChatLog`.

The core flow is: user request, LLM analysis, tool router execution, and natural-language response. The LLM maps user intent into `tool_calls` containing tool names and arguments. The backend then parses those calls and invokes actual backend functions or APIs. API results are returned to the model, which continues reasoning until it generates a final answer.

## Chat Log and Governance

`ai_chatlog` records token usage and operational behavior. The workshop frames this as both a debugging tool and a governance mechanism. Logs support traffic monitoring, behavior tracking, auditability, anomaly detection, and resource allocation optimization.

The competition platform monitors traffic and behavior in real time. Exceeding the 30 RPM limit returns `Rate limit exceeded`, and abnormal usage can suspend service.

## Competition Boundaries

AI use is optional. If a team uses or modifies the AI architecture, it must stay within the organizer-designated model and compute service. Teams cannot use other AI models or non-designated compute resources when doing so would violate rules or make official integration difficult.

The guide emphasizes that AI should support application value. Judging does not primarily reward AI technical depth; it rewards whether the dashboard and components solve a meaningful scenario.

## See Also

- [Hackathon Rules and Delivery Requirements](hackathon-rules-and-delivery-requirements.md)
- [Authentication, Admin, and Dashboard Operations](auth-admin-and-dashboard-operations.md)
- [Platform Model](platform-model.md)
