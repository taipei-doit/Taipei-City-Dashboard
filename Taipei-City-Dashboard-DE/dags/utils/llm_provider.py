"""
Generic multi-provider LLM text generation for DAGs.

This project's own deployment defaults to TWCC (Taiwan's national AI cloud service,
gov-only access) — but that's not something a clone of this open-source repo can use.
Self-hosters should set the Airflow Variable `LLM_PROVIDER` to "openai" or "gemini"
instead and fill in that provider's own `*_API_KEYS` Variable; every call site in the
DAGs just calls `generate_text()` and doesn't care which backend is behind it.

Required Airflow Variables (only the ones for your chosen LLM_PROVIDER):
    TWCC_API_KEYS / OPENAI_API_KEYS / GEMINI_API_KEYS
        A single key string, or a JSON/Python list of keys to rotate through if one
        fails or gets rate-limited, e.g. '["key1","key2"]'.
    TWCC_API_URL, TWCC_MODEL / OPENAI_API_URL, OPENAI_MODEL / GEMINI_API_URL, GEMINI_MODEL
        Optional overrides; each has a sane default below.
"""
from ast import literal_eval

import requests
from airflow.models import Variable

DEFAULT_PROVIDER = "twcc"

_DEFAULTS = {
    "twcc": {"api_url": "https://api-ams.twcc.ai/api", "model": "llama3.3-ffm-70b-32k-chat"},
    "openai": {"api_url": "https://api.openai.com/v1", "model": "gpt-4o"},
    "gemini": {"api_url": "https://generativelanguage.googleapis.com", "model": "gemini-1.5-pro"},
}


def _get_api_keys(variable_name):
    raw = Variable.get(variable_name)
    keys = literal_eval(raw) if raw.strip().startswith("[") else [raw]
    return [k for k in keys if k]


def _with_key_rotation(provider_label, api_keys, send_request):
    last_error = None
    for api_key in api_keys:
        try:
            return send_request(api_key)
        except Exception as e:
            last_error = e
            print(f"{provider_label} key ...{api_key[-4:]} failed, rotating to next key: {e}")
    raise RuntimeError(f"All {provider_label} API keys failed: {last_error}")


def _call_twcc(system_prompt, user_prompt, max_tokens, temperature):
    api_keys = _get_api_keys("TWCC_API_KEYS")
    base_url = Variable.get("TWCC_API_URL", _DEFAULTS["twcc"]["api_url"])
    model = Variable.get("TWCC_MODEL", _DEFAULTS["twcc"]["model"])

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "parameters": {"max_new_tokens": max_tokens, "temperature": temperature},
        "stream": False,
    }

    def send(api_key):
        resp = requests.post(
            f"{base_url}/models/conversation",
            json=body,
            headers={"Content-Type": "application/json", "X-API-KEY": api_key},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("generated_text")
        if not content and data.get("choices"):
            content = data["choices"][0]["message"]["content"]
        return content.strip()

    return _with_key_rotation("TWCC", api_keys, send)


def _call_openai(system_prompt, user_prompt, max_tokens, temperature):
    api_keys = _get_api_keys("OPENAI_API_KEYS")
    base_url = Variable.get("OPENAI_API_URL", _DEFAULTS["openai"]["api_url"])
    model = Variable.get("OPENAI_MODEL", _DEFAULTS["openai"]["model"])

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    def send(api_key):
        resp = requests.post(
            f"{base_url}/chat/completions",
            json=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    return _with_key_rotation("OpenAI", api_keys, send)


def _call_gemini(system_prompt, user_prompt, max_tokens, temperature):
    api_keys = _get_api_keys("GEMINI_API_KEYS")
    base_url = Variable.get("GEMINI_API_URL", _DEFAULTS["gemini"]["api_url"])
    model = Variable.get("GEMINI_MODEL", _DEFAULTS["gemini"]["model"])

    body = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
    }

    def send(api_key):
        resp = requests.post(
            f"{base_url}/v1beta/models/{model}:generateContent?key={api_key}",
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

    return _with_key_rotation("Gemini", api_keys, send)


_PROVIDERS = {
    "twcc": _call_twcc,
    "openai": _call_openai,
    "gemini": _call_gemini,
}


def generate_text(system_prompt, user_prompt, max_tokens=600, temperature=0.3):
    """Generate text via whichever provider the `LLM_PROVIDER` Airflow Variable selects."""
    provider = Variable.get("LLM_PROVIDER", DEFAULT_PROVIDER)
    if provider not in _PROVIDERS:
        raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Supported: {list(_PROVIDERS)}")
    return _PROVIDERS[provider](system_prompt, user_prompt, max_tokens, temperature)
