"""Typed deployment configuration; config file < environment < CLI overrides."""

from dataclasses import dataclass, replace
import os
from pathlib import Path
import tomllib
from urllib.parse import urlsplit


def exact_origins(raw: str) -> tuple[str, ...]:
    values = []
    for value in raw.split(","):
        value = value.strip()
        if not value:
            continue
        p = urlsplit(value)
        if (
            p.scheme not in {"http", "https"}
            or not p.hostname
            or p.username
            or p.password
            or p.path
            or p.query
            or p.fragment
            or any(c.isspace() for c in value)
            or any(c in value for c in "*;'\\<>\"")
        ):
            raise ValueError(
                "Origins must be exact http(s) origins without path, wildcard or trailing slash"
            )
        _ = p.port
        if value not in values:
            values.append(value)
    return tuple(values)


def frame_sources(raw: str) -> str:
    return " ".join(["'self'", *exact_origins(raw)])


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8000
    public_url: str = ""
    result_dir: Path | None = None
    embed_origins: str = ""
    api_origins: str = ""

    def validate(self):
        if not self.host or any(c.isspace() for c in self.host):
            raise ValueError("host cannot be empty or contain whitespace")
        if type(self.port) is not int or not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        exact_origins(self.embed_origins)
        exact_origins(self.api_origins)
        if self.public_url:
            origin = self.public_url.removesuffix("/")
            if exact_origins(origin) != (origin,):
                raise ValueError(
                    "public_url must be one http(s) origin, optionally ending in /"
                )
        return self

    @classmethod
    def load(cls, path: Path | None = None, environ=None):
        env = os.environ if environ is None else environ
        if path is None and env.get("SAFECAPITAL_CONFIG"):
            path = Path(env["SAFECAPITAL_CONFIG"])
        values = {}
        if path is not None:
            path = path.expanduser().resolve(strict=True)
            values = tomllib.loads(path.read_text("utf-8"))
            unknown = set(values) - set(cls.__dataclass_fields__)
            if unknown:
                raise ValueError(f"Unknown configuration fields: {sorted(unknown)}")
        for name in cls.__dataclass_fields__:
            key = "SAFECAPITAL_" + name.upper()
            if key in env:
                values[name] = env[key]
        if "port" in values:
            if type(values["port"]) not in (int, str):
                raise ValueError("port must be an integer")
            values["port"] = int(values["port"])
        for name in ("host", "public_url", "embed_origins", "api_origins"):
            if name in values and not isinstance(values[name], str):
                raise ValueError(f"{name} must be a string")
        raw = values.get("result_dir")
        if raw is not None and not isinstance(raw, (str, Path)):
            raise ValueError("result_dir must be a string path")
        if raw:
            value = Path(raw).expanduser()
            # Relative paths in config are anchored to that config, not the shell cwd.
            anchor = path.parent if path else Path.cwd()
            values["result_dir"] = (anchor / value).resolve()
        elif "result_dir" in values:
            values["result_dir"] = None
        return cls(**values).validate()

    def override(self, **kwargs):
        return replace(
            self, **{k: v for k, v in kwargs.items() if v is not None}
        ).validate()
