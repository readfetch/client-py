"""Published routes — keep in sync with catalog.json (published + integrator)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import quote

Method = Literal["GET", "POST"]
_PATH_PARAM = re.compile(r"\{(\w+)\}")
MAX_PATH_PARAM_LEN = 512


@dataclass(frozen=True)
class EndpointSpec:
    name: str
    method: Method
    path: str
    free: bool
    accept: tuple[int, ...] = ()


CATALOG_ENDPOINTS: tuple[EndpointSpec, ...] = (
    EndpointSpec("text", "POST", "/v1/text", False),
    EndpointSpec("map", "POST", "/v1/map", False),
    EndpointSpec("scrape", "POST", "/v1/scrape", False),
    EndpointSpec("residential", "POST", "/v1/scrape/residential", False),
    EndpointSpec("fetch", "POST", "/v1/fetch", False),
    EndpointSpec("batch", "POST", "/v1/batch", False),
    EndpointSpec("pdf", "POST", "/v1/pdf", False),
    EndpointSpec("section", "POST", "/v1/section", False),
    EndpointSpec("diff", "POST", "/v1/diff", False),
    EndpointSpec("screenshot", "POST", "/v1/screenshot", False),
    EndpointSpec("search", "POST", "/v1/search", False),
    EndpointSpec("crawl", "POST", "/v1/crawl", False),
    EndpointSpec("crawl_status", "GET", "/v1/crawl/{id}", True),
    EndpointSpec("probe", "POST", "/v1/probe", True),
)

INTEGRATOR_ENDPOINTS: tuple[EndpointSpec, ...] = (
    EndpointSpec("feedback", "POST", "/v1/feedback", True, (202,)),
    EndpointSpec("claims", "POST", "/v1/claims", True),
)

BY_NAME: dict[str, EndpointSpec] = {
    spec.name: spec for spec in (*CATALOG_ENDPOINTS, *INTEGRATOR_ENDPOINTS)
}


def endpoint_path(name: str, path_params: dict[str, str] | None = None) -> str:
    spec = BY_NAME.get(name)
    if spec is None:
        known = ", ".join(sorted(BY_NAME))
        raise ValueError(f"unknown endpoint `{name}`; known: {known}")
    path_params = path_params or {}
    out = spec.path
    for key in _PATH_PARAM.findall(spec.path):
        raw = path_params.get(key)
        if raw is None:
            raise ValueError(f"`{name}` requires path_params {key}")
        value = str(raw).strip()
        if not value:
            raise ValueError(f"`{name}` requires path_params {key}")
        if len(value) > MAX_PATH_PARAM_LEN:
            raise ValueError(
                f"`{name}` path_params.{key} exceeds {MAX_PATH_PARAM_LEN} characters"
            )
        out = out.replace(f"{{{key}}}", quote(value, safe=""))
    if "{" in out:
        raise ValueError(f"`{name}` has unresolved path template")
    return out


def export_name(name: str) -> str:
    parts = name.split("_")
    return "readfetch" + "".join(part[:1].upper() + part[1:] for part in parts)
