import os
import time
from dataclasses import dataclass
from typing import Any

import requests
from airflow.models import Variable
from settings.global_config import PROXIES


DEFAULT_TWCC_API_URL = "https://api-ams.twcc.ai/api"
DEFAULT_TWCC_MODEL = "llama3.3-ffm-70b-32k-chat"
DEFAULT_TWCC_TIMEOUT = 60
DEFAULT_TWCC_MAX_RETRY = 2


@dataclass
class TWCCAIResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    raw_response: dict[str, Any]


def _get_config_value(key: str, default: str | None = None) -> str | None:
    try:
        return Variable.get(key, default_var=os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


def _get_int_config_value(key: str, default: int) -> int:
    value = _get_config_value(key, str(default))
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _build_parameters(
    max_new_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    frequence_penalty: float | None = None,
    stop_sequences: list[str] | None = None,
    seed: int | None = None,
    extra_parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    parameters: dict[str, Any] = {"stream": False}
    optional_parameters = {
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "frequence_penalty": frequence_penalty,
        "stop_sequences": stop_sequences,
        "seed": seed,
    }
    parameters.update(
        {key: value for key, value in optional_parameters.items() if value is not None}
    )
    if extra_parameters:
        parameters.update(extra_parameters)
    return parameters


def _extract_content(response_json: dict[str, Any]) -> str:
    if response_json.get("generated_text"):
        return response_json["generated_text"]

    choices = response_json.get("choices") or []
    if choices:
        message = choices[0].get("message") or {}
        return message.get("content", "")

    return ""


def _parse_twcc_response(response_json: dict[str, Any], model: str) -> TWCCAIResponse:
    input_tokens = int(response_json.get("prompt_tokens") or 0)
    output_tokens = int(response_json.get("generated_tokens") or 0)
    total_tokens = int(response_json.get("total_tokens") or input_tokens + output_tokens)

    return TWCCAIResponse(
        content=_extract_content(response_json),
        model=response_json.get("model") or model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        raw_response=response_json,
    )


def call_twcc_ai(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    api_url: str | None = None,
    api_key: str | None = None,
    timeout: int | None = None,
    max_retry: int | None = None,
    max_new_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    frequence_penalty: float | None = None,
    stop_sequences: list[str] | None = None,
    seed: int | None = None,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: Any | None = None,
    extra_parameters: dict[str, Any] | None = None,
    is_proxy: bool = False,
    **kwargs,
) -> TWCCAIResponse:
    """
    Call the same TWCC AFS conversation API used by the backend.

    Args:
        messages: TWCC/OpenAI-style chat messages. Roles should be system, user,
            assistant, or tool.
        model: Override TWCC_MODEL.
        api_url: Override TWCC_API_URL. Defaults to BE's TWCC_API_URL default.
        api_key: Override TWCC_API_KEY.
        timeout: Request timeout in seconds.
        max_retry: Number of retries after the first failed request.
        is_proxy: Use the shared Airflow proxy config. DAGs can also pass a
            `proxies` kwarg, which takes precedence.

    Returns:
        TWCCAIResponse with parsed content, token usage, and the raw response.
    """
    selected_api_url = (
        api_url or _get_config_value("TWCC_API_URL", DEFAULT_TWCC_API_URL)
    ).rstrip("/")
    selected_api_key = api_key or _get_config_value("TWCC_API_KEY")
    selected_model = model or _get_config_value("TWCC_MODEL", DEFAULT_TWCC_MODEL)
    selected_timeout = timeout or _get_int_config_value("TWCC_TIMEOUT", DEFAULT_TWCC_TIMEOUT)
    selected_max_retry = (
        max_retry
        if max_retry is not None
        else _get_int_config_value("TWCC_MAX_RETRY", DEFAULT_TWCC_MAX_RETRY)
    )

    if not selected_api_key:
        raise ValueError("TWCC_API_KEY is required to call TWCC AI.")

    body: dict[str, Any] = {
        "model": selected_model,
        "messages": messages,
        "parameters": _build_parameters(
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            frequence_penalty=frequence_penalty,
            stop_sequences=stop_sequences,
            seed=seed,
            extra_parameters=extra_parameters,
        ),
        "stream": False,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = tool_choice if tool_choice is not None else "auto"
    elif tool_choice is not None:
        body["tool_choice"] = tool_choice

    request_proxies = kwargs.get("proxies", PROXIES if is_proxy else None)
    headers = {"Content-Type": "application/json", "X-API-KEY": selected_api_key}
    endpoint = f"{selected_api_url}/models/conversation"

    last_error = None
    for attempt in range(selected_max_retry + 1):
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=body,
                proxies=request_proxies,
                timeout=selected_timeout,
            )
            if response.status_code != requests.codes.ok:
                raise RuntimeError(
                    f"TWCC API returned error status {response.status_code}: "
                    f"{response.text}"
                )
            return _parse_twcc_response(response.json(), selected_model)
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            last_error = exc
            if attempt < selected_max_retry:
                time.sleep(0.5)

    raise RuntimeError(f"Failed to call TWCC AI: {last_error}") from last_error


def call_twcc_ai_prompt(prompt: str, system_prompt: str | None = None, **kwargs) -> TWCCAIResponse:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    return call_twcc_ai(messages, **kwargs)
