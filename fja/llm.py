"""LLM wrapper with separate settings for roles 'gen' and 'judge'.

Per role (GEN_* or JUDGE_*):
  {ROLE}_PROVIDER  anthropic (default) | openai_compat
  {ROLE}_BASE_URL  required for openai_compat
  {ROLE}_API_KEY   openai_compat key (Anthropic uses ANTHROPIC_API_KEY)
"""
import json
import os
import re
import time

DRY_RUN = False
_clients = {}


def _get_client(role):
    if role not in _clients:
        R = role.upper()
        if os.getenv(f"{R}_PROVIDER", "anthropic") == "anthropic":
            from anthropic import Anthropic
            _clients[role] = Anthropic()
        else:
            from openai import OpenAI
            _clients[role] = OpenAI(
                base_url=os.environ[f"{R}_BASE_URL"],
                api_key=os.getenv(f"{R}_API_KEY", "none"),
            )
    return _clients[role]


def _call(user, model, system, max_tokens, role):
    c = _get_client(role)
    if os.getenv(f"{role.upper()}_PROVIDER", "anthropic") == "anthropic":
        kwargs = dict(model=model, max_tokens=max_tokens,
                      messages=[{"role": "user", "content": user}])
        if system:
            kwargs["system"] = system
        r = c.messages.create(**kwargs)
        return "".join(b.text for b in r.content if b.type == "text")
    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": "user", "content": user}]
    r = c.chat.completions.create(model=model, messages=msgs, max_tokens=max_tokens)
    return r.choices[0].message.content or ""


def complete(user, model, system=None, max_tokens=2500, role="gen"):
    if DRY_RUN:
        return _stub(user, system)
    last = None
    for attempt in range(5):
        try:
            return _call(user, model, system, max_tokens, role)
        except Exception as e:
            last = e
            status = getattr(e, "status_code", None)
            if status is not None and 400 <= status < 500 and status != 429:
                raise RuntimeError(f"API error (not retrying): {e}") from e
            time.sleep(2 ** attempt * 2)
    raise RuntimeError(f"API call failed after retries: {last}")


def parse_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"No JSON object in judge output: {text[:200]}")
    return json.loads(m.group(0))


def _stub(user, system):
    if "Return ONLY a JSON object" in user:
        return json.dumps({
            "flourishing": 3, "justice": 3, "autonomy": 3,
            "helpfulness": 3, "harmlessness": 4, "honesty": 4,
            "refused": False, "harmful_uplift": False,
            "rationale": "dry-run stub"})
    return "[dry-run response]"
