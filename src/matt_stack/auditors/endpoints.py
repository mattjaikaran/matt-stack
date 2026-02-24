"""Endpoint auditor — static route analysis + optional live probing."""

from __future__ import annotations

import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

from matt_stack.auditors.base import AuditFinding, AuditType, BaseAuditor, Severity
from matt_stack.parsers.django_routes import Route, find_route_files, parse_routes_file


class EndpointAuditor(BaseAuditor):
    audit_type = AuditType.ENDPOINTS

    def run(self) -> list[AuditFinding]:
        project = self.config.project_path
        routes = self._parse_all_routes(project)

        if not routes:
            self.add_finding(
                Severity.INFO,
                Path("."),
                0,
                "No route definitions found",
                "Routes are expected in api.py, routes.py, controllers.py, etc.",
            )
            return self.findings

        self._check_duplicates(routes)
        self._check_stubs(routes)
        self._check_auth(routes)
        self._check_naming(routes)

        if self.config.live:
            self._live_probe(routes)

        return self.findings

    def _parse_all_routes(self, project: Path) -> list[Route]:
        routes: list[Route] = []
        for f in find_route_files(project):
            routes.extend(parse_routes_file(f))
        return routes

    def _check_duplicates(self, routes: list[Route]) -> None:
        """Find duplicate method+path combinations."""
        counter: Counter[tuple[str, str]] = Counter()
        route_map: dict[tuple[str, str], list[Route]] = {}

        for r in routes:
            key = (r.method, r.path)
            counter[key] += 1
            route_map.setdefault(key, []).append(r)

        for key, count in counter.items():
            if count > 1:
                method, path = key
                dupes = route_map[key]
                files = ", ".join(f"{self._rel(r.file)}:{r.line}" for r in dupes)
                self.add_finding(
                    Severity.ERROR,
                    self._rel(dupes[0].file),
                    dupes[0].line,
                    f"Duplicate route: {method} {path} defined {count} times ({files})",
                    "Remove duplicate or use unique paths",
                )

    def _check_stubs(self, routes: list[Route]) -> None:
        """Find routes with stub implementations."""
        for r in routes:
            if r.is_stub:
                self.add_finding(
                    Severity.WARNING,
                    self._rel(r.file),
                    r.line,
                    f"Stub endpoint: {r.method} {r.path} ({r.function_name})",
                    "Implement the endpoint handler",
                )

    def _check_auth(self, routes: list[Route]) -> None:
        """Find write endpoints without explicit auth."""
        write_methods = {"POST", "PUT", "DELETE", "PATCH"}
        for r in routes:
            if r.method in write_methods and not r.has_auth:
                self.add_finding(
                    Severity.WARNING,
                    self._rel(r.file),
                    r.line,
                    f"No auth on write endpoint: {r.method} {r.path}",
                    "Add auth=... parameter to protect write operations",
                )

    def _check_naming(self, routes: list[Route]) -> None:
        """Check route naming conventions."""
        for r in routes:
            # Flag routes with no leading slash
            if not r.path.startswith("/"):
                self.add_finding(
                    Severity.INFO,
                    self._rel(r.file),
                    r.line,
                    f"Route path missing leading slash: '{r.path}'",
                    f"Use '/{r.path}' for consistency",
                )

            # Flag routes ending with slash inconsistency
            if r.path != "/" and r.path.endswith("/"):
                self.add_finding(
                    Severity.INFO,
                    self._rel(r.file),
                    r.line,
                    f"Trailing slash on route: '{r.path}'",
                    "Consider removing trailing slash for consistency",
                )

    def _live_probe(self, routes: list[Route]) -> None:
        """GET-probe discovered endpoints (safe, read-only)."""
        base_url = self.config.base_url

        for r in routes:
            if r.method != "GET":
                continue

            url = f"{base_url}{r.path}"
            # Skip parameterized routes
            if "{" in url or "<" in url:
                continue

            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    status = resp.status
                    if status >= 500:
                        self.add_finding(
                            Severity.ERROR,
                            self._rel(r.file),
                            r.line,
                            f"Live probe {r.method} {r.path} returned {status}",
                            "Check server logs for the error",
                        )
            except urllib.error.HTTPError as e:
                if e.code >= 500:
                    self.add_finding(
                        Severity.ERROR,
                        self._rel(r.file),
                        r.line,
                        f"Live probe {r.method} {r.path} returned {e.code}",
                        "Check server logs for the error",
                    )
                elif e.code == 404:
                    self.add_finding(
                        Severity.WARNING,
                        self._rel(r.file),
                        r.line,
                        f"Live probe {r.method} {r.path} returned 404",
                        "Route may not be registered or server isn't running",
                    )
            except (urllib.error.URLError, TimeoutError, OSError):
                # Server not running or not reachable — skip silently
                self.add_finding(
                    Severity.INFO,
                    Path("."),
                    0,
                    f"Could not reach {base_url} — is the server running?",
                    "Start the backend with 'make backend-dev' before using --live",
                )
                break  # No point probing more
