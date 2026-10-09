"""Model providers and the fallback chain.

Every provider turns (system, user) prompts into a JSON object. The chain
tries providers in order (LT_PROVIDER_CHAIN), validates each answer with the
caller's validator, and records every attempt. Output that fails validation
is dropped and logged, never repaired.

The last rung is always `offline`: deterministic hand-written rules that need
no key. It is labelled as such everywhere it appears, so nobody mistakes it
for a model.
"""
import json
import os
import re
import time
import urllib.error
import urllib.request

HTTP_TIMEOUT_SECONDS = 20   # Vercel functions time out; fail over well before that
TEMPERATURE = 0.4           # some variety in copy, still stable on categorical fields
RETRIES_ON_INVALID = 1      # one second chance per provider, told why its answer was rejected
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"   # 2.5-flash is closed to new keys
FEATHERLESS_BASE_URL = "https://api.featherless.ai/v1"
DEFAULT_FEATHERLESS_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_SOCLAAS_MODEL = "qwen3.5:9b"   # quick, and good enough for short structured JSON


class ProviderError(Exception):
    pass


def _post_json(url, body, headers):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise ProviderError(f"HTTP {e.code}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise ProviderError(f"network: {e}") from e


def parse_json_text(text):
    """Pull one JSON object out of model text, tolerating ``` fences and the
    <think>...</think> blocks that reasoning models (e.g. Qwen3) emit first."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ProviderError("no JSON object in reply")
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        raise ProviderError(f"bad JSON: {e}") from e


class Provider:
    name = "base"

    def available(self):
        return True

    def complete_json(self, task, system, user):
        raise NotImplementedError


class GeminiProvider(Provider):
    name = "gemini"

    def __init__(self):
        self.key = os.environ.get("GEMINI_API_KEY", "")
        self.model = os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL

    def available(self):
        return bool(self.key)

    def complete_json(self, task, system, user):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": TEMPERATURE},
        }
        data = _post_json(url, body, {"x-goog-api-key": self.key})
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise ProviderError("empty Gemini reply") from e
        return parse_json_text(text)


class OpenAICompatibleProvider(Provider):
    """Any server speaking the OpenAI chat-completions API, configured by env prefix.

    {PREFIX}_API_KEY, {PREFIX}_BASE_URL (up to and including /v1 or whatever
    path precedes /chat/completions) and {PREFIX}_MODEL.
    """
    prefix = None
    default_base = None
    default_model = None

    def __init__(self):
        self.key = os.environ.get(f"{self.prefix}_API_KEY", "")
        self.model = os.environ.get(f"{self.prefix}_MODEL") or self.default_model
        self.base = (os.environ.get(f"{self.prefix}_BASE_URL") or self.default_base or "").rstrip("/")

    def available(self):
        return bool(self.key and self.base and self.model)

    def complete_json(self, task, system, user):
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": TEMPERATURE,
            "stream": False,
        }
        data = _post_json(f"{self.base}/chat/completions", body,
                          {"Authorization": f"Bearer {self.key}"})
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError(f"empty {self.name} reply") from e
        return parse_json_text(text or "")


class SoclaasProvider(OpenAICompatibleProvider):
    """NUS SoC's SoCLaaS (OpenAI-compatible, free for students; costs are rate control only)."""
    name = "soclaas"
    prefix = "SOCLAAS"
    default_model = DEFAULT_SOCLAAS_MODEL


class FeatherlessProvider(OpenAICompatibleProvider):
    """Featherless exposes an OpenAI-compatible chat completions API."""
    name = "featherless"
    prefix = "FEATHERLESS"
    default_base = FEATHERLESS_BASE_URL
    default_model = DEFAULT_FEATHERLESS_MODEL


class OfflineProvider(Provider):
    """Deterministic rules registered per task. Not a model."""
    name = "offline"

    def __init__(self, rules=None):
        self.rules = rules or {}

    def complete_json(self, task, system, user, context=None):
        if task not in self.rules:
            raise ProviderError(f"no offline rule for {task}")
        return self.rules[task](context)


class FakeProvider(Provider):
    """For tests: returns canned replies in order, or raises if given an Exception."""

    def __init__(self, replies, name="fake"):
        self.replies = list(replies)
        self.name = name
        self.calls = []

    def complete_json(self, task, system, user):
        self.calls.append((task, system, user))
        r = self.replies.pop(0) if self.replies else ProviderError("no more replies")
        if isinstance(r, Exception):
            raise r
        return r


_REGISTRY = {"soclaas": SoclaasProvider, "gemini": GeminiProvider, "featherless": FeatherlessProvider}
DEFAULT_CHAIN = "soclaas,gemini"


def configured_providers():
    names = [n.strip() for n in os.environ.get("LT_PROVIDER_CHAIN", DEFAULT_CHAIN).split(",")]
    return [_REGISTRY[n]() for n in names if n in _REGISTRY]


class Chain:
    def __init__(self, providers=None, offline=None):
        self.providers = configured_providers() if providers is None else providers
        self.offline = offline

    def ladder(self):
        rungs = [{"provider": p.name, "configured": p.available()} for p in self.providers]
        if self.offline:
            rungs.append({"provider": "offline", "configured": True})
        return rungs

    def run(self, task, system, user, validate, context=None):
        """Return (validated result, provider name, attempts)."""
        attempts = []
        for p in self.providers:
            if not p.available():
                attempts.append({"provider": p.name, "ok": False, "error": "no key"})
                continue
            prompt = user
            for attempt in range(1 + RETRIES_ON_INVALID):
                t0 = time.time()
                try:
                    raw = p.complete_json(task, system, prompt)
                except Exception as e:  # transport failure: asking again won't help, move on
                    attempts.append({"provider": p.name, "ok": False, "error": str(e)[:200]})
                    print(f"[{task}] {p.name} failed: {e}")
                    break
                try:
                    result = validate(raw)
                    attempts.append({"provider": p.name, "ok": True, "ms": int((time.time() - t0) * 1000),
                                     "retry": attempt > 0})
                    return result, p.name, attempts
                except Exception as e:  # invalid answer: drop it, log it, ask again with the reason
                    attempts.append({"provider": p.name, "ok": False, "error": str(e)[:200], "retry": attempt > 0})
                    print(f"[{task}] {p.name} rejected: {e}")
                    prompt = (f"{user}\n\nYour previous reply was rejected: {e}. "
                              "Reply again with corrected JSON only, following every rule and limit.")
        if self.offline:
            try:
                result = validate(self.offline.complete_json(task, system, user, context))
                attempts.append({"provider": "offline", "ok": True})
                return result, "offline", attempts
            except Exception as e:
                attempts.append({"provider": "offline", "ok": False, "error": str(e)[:200]})
        return None, None, attempts
