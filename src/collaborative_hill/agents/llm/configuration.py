"""Offline configuration and explicit construction of network-backed policies."""

import os
import re
from collections.abc import Mapping
from dataclasses import KW_ONLY, dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from collaborative_hill.engine.hashing import frac_str

if TYPE_CHECKING:
    from collaborative_hill.agents.llm.budget import RequestBudget
    from collaborative_hill.agents.llm.policy import LLMPolicy
    from collaborative_hill.experiments.scenario import NarrativeSkin

_SAMPLING_KEYS = {"max_completion_tokens", "max_tokens", "temperature", "top_p", "seed"}
_CONFIG_KEYS = {"endpoint", "model_id", "api_key_env", "timeout_seconds",
                "rate_limit_retries", "retry_delay_seconds", "max_retries",
                "allow_insecure_localhost"}


def _integer(value: Any, name: str, minimum: int, maximum: int | None = None) -> int:
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"invalid {name}: an integer within the documented bounds is required")
    return value


def _sampling(values: Mapping[str, str | int]) -> Mapping[str, str | int]:
    if not isinstance(values, Mapping) or set(values) - _SAMPLING_KEYS:
        raise ValueError("unsupported provider sampling configuration")
    limits = set(values) & {"max_tokens", "max_completion_tokens"}
    if len(limits) != 1:
        raise ValueError("set exactly one of max_completion_tokens or max_tokens")
    result: dict[str, str | int] = {}
    for name, value in values.items():
        if name in limits:
            result[name] = _integer(value, name, 1)
        elif name == "seed":
            result[name] = _integer(value, name, -(2 ** 63), 2 ** 63 - 1)
        else:
            try:
                if not isinstance(value, str):
                    raise ValueError
                fraction = Fraction(value)
                if not 0 <= fraction <= (2 if name == "temperature" else 1):
                    raise ValueError
            except (ValueError, ZeroDivisionError):
                raise ValueError(f"{name} must be an exact string within its supported range") \
                    from None
            result[name] = frac_str(fraction)
    return MappingProxyType(result)


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    """Non-secret settings; token caps are required and numeric sampling is exact.

    ``max_retries`` controls action-format repair in the policy factory, while
    ``rate_limit_retries`` controls HTTP 429 only. Neither is billing-idempotent.
    """

    endpoint: str
    model_id: str
    sampling: Mapping[str, str | int]
    _: KW_ONLY
    api_key_env: str | None = None
    timeout_seconds: int = 30
    rate_limit_retries: int = 0
    retry_delay_seconds: int = 1
    max_retries: int = 0
    allow_insecure_localhost: bool = False

    def __post_init__(self) -> None:
        if type(self.allow_insecure_localhost) is not bool:
            raise ValueError("allow_insecure_localhost must be a boolean")
        if not isinstance(self.endpoint, str) or any(
            ord(c) <= 32 or c == "\\" for c in self.endpoint
        ):
            raise ValueError("provider endpoint must be a clean absolute URL")
        try:
            url = urlsplit(self.endpoint)
            valid = bool(url.hostname) and url.port != 0
        except ValueError:
            raise ValueError("provider endpoint must be a valid absolute URL") from None
        if (not valid or url.username is not None or url.password is not None
                or url.query or url.fragment):
            raise ValueError("provider endpoint must not contain credentials, query or fragment")
        local_http = (self.allow_insecure_localhost and url.scheme == "http"
                      and url.hostname in {"localhost", "127.0.0.1", "::1"})
        if url.scheme != "https" and not local_http:
            raise ValueError("provider endpoint requires HTTPS or explicitly allowed loopback HTTP")
        if (not isinstance(self.model_id, str) or not self.model_id.strip()
                or any(ord(c) < 32 for c in self.model_id)):
            raise ValueError("provider model_id must be a nonempty printable string")
        if self.api_key_env is not None and (
            not isinstance(self.api_key_env, str)
            or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", self.api_key_env) is None
        ):
            raise ValueError("api_key_env must name an environment variable")
        _integer(self.timeout_seconds, "timeout_seconds", 1, 300)
        _integer(self.rate_limit_retries, "rate_limit_retries", 0, 3)
        _integer(self.retry_delay_seconds, "retry_delay_seconds", 0, 60)
        _integer(self.max_retries, "max_retries", 0, 3)
        object.__setattr__(self, "sampling", _sampling(self.sampling))

    def wire_sampling(self) -> dict[str, int | float]:
        """Only the un-hashed HTTP payload uses binary floating-point ratios."""
        return {key: float(Fraction(value)) if isinstance(value, str) else value
                for key, value in self.sampling.items()}


def validate_provider_params(params: Mapping[str, Any]) -> OpenAICompatibleConfig:
    """Validate flat PolicySpec parameters without reading credentials or networking."""
    if not isinstance(params, Mapping) or set(params) - (_SAMPLING_KEYS | _CONFIG_KEYS):
        raise ValueError("unsupported provider parameter; credentials must use api_key_env")
    if "endpoint" not in params or "model_id" not in params:
        raise ValueError("provider endpoint and model_id must be explicitly configured")
    return OpenAICompatibleConfig(
        endpoint=params["endpoint"], model_id=params["model_id"],
        sampling={key: params[key] for key in _SAMPLING_KEYS if key in params},
        **{key: params[key] for key in _CONFIG_KEYS - {"endpoint", "model_id"} if key in params},
    )


def build_openai_compatible_policy(agent_id: str, skin: "NarrativeSkin",
                                   params: Mapping[str, Any], *,
                                   budget: "RequestBudget | None" = None) -> "LLMPolicy":
    """Explicit construction; callers gate authorization before invoking the factory.

    ``budget`` is an operational admission limit shared by every policy built with it."""
    from collaborative_hill.agents.llm.openai_compatible import OpenAICompatibleProvider
    from collaborative_hill.agents.llm.policy import LLMPolicy

    config = validate_provider_params(params)
    api_key = os.environ.get(config.api_key_env) if config.api_key_env is not None else None
    if config.api_key_env is not None and not api_key:
        raise ValueError("provider credential environment variable is unavailable")
    provider = OpenAICompatibleProvider(config, api_key=api_key, budget=budget)
    return LLMPolicy(agent_id, provider, skin,
                     max_retries=config.max_retries, sampling=dict(config.sampling))
