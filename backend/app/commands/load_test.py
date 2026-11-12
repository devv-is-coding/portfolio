"""A small load test of the public read endpoints (HTTPX, no extra tools).

    uv run python -m app.commands.load_test --base-url http://localhost:8000
    uv run python -m app.commands.load_test --concurrency 100 --requests 1000

For each endpoint it sends `--requests` GETs, `--concurrency` at a time, and prints
p50 / p95 / max latency, requests per second and errors (anything but 200). Endpoints
that don't answer 200 to a first probe (e.g. /profile before one exists) are skipped.
Run `python -m app.commands.seed` first so the lists have realistic sizes.
"""

import argparse
import asyncio
import statistics
import time
from collections import Counter
from dataclasses import dataclass

import httpx

PUBLIC_ENDPOINTS = (
    "/profile",
    "/skills",
    "/projects",
    "/projects/{project_slug}",
    "/experiences",
    "/education",
    "/certifications",
    "/blog/posts",
    "/blog/posts/{post_slug}",
    "/blog/categories",
    "/blog/tags",
    "/settings",
)


@dataclass(frozen=True)
class Result:
    path: str
    latencies_ms: list[float]
    errors: Counter[str]
    seconds: float

    def row(self) -> str:
        ordered = sorted(self.latencies_ms)
        p95 = ordered[max(0, round(len(ordered) * 0.95) - 1)]
        reasons = ", ".join(f"{reason} x{count}" for reason, count in self.errors.items())
        return (
            f"{self.path:<40} {statistics.median(ordered):>8.1f} {p95:>8.1f} "
            f"{ordered[-1]:>8.1f} {len(ordered) / self.seconds:>8.0f} "
            f"{self.errors.total():>7} {reasons}"
        ).rstrip()


async def _first_slug(client: httpx.AsyncClient, path: str) -> str | None:
    response = await client.get(path, params={"size": 1})
    items = response.json().get("items", []) if response.status_code == 200 else []
    return str(items[0]["slug"]) if items else None


async def _hammer(client: httpx.AsyncClient, path: str, requests: int, concurrency: int) -> Result:
    latencies: list[float] = []
    errors: Counter[str] = Counter()
    gate = asyncio.Semaphore(concurrency)

    async def one() -> None:
        async with gate:
            started = time.perf_counter()
            try:
                response = await client.get(path)
                if response.status_code != 200:
                    errors[f"HTTP {response.status_code}"] += 1
            except httpx.HTTPError as exc:
                errors[type(exc).__name__] += 1
            latencies.append((time.perf_counter() - started) * 1000)

    started = time.perf_counter()
    await asyncio.gather(*(one() for _ in range(requests)))
    return Result(path, latencies, errors, time.perf_counter() - started)


async def run(base_url: str, requests: int, concurrency: int) -> None:
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(base_url=base_url, limits=limits, timeout=30) as client:
        slugs = {
            "project_slug": await _first_slug(client, "/projects"),
            "post_slug": await _first_slug(client, "/blog/posts"),
        }
        print(f"{requests} requests per endpoint, {concurrency} at a time, against {base_url}\n")
        print(
            f"{'endpoint':<40} {'p50 ms':>8} {'p95 ms':>8} {'max ms':>8} {'req/s':>8} {'errors':>7}"
        )
        for template in PUBLIC_ENDPOINTS:
            if any(f"{{{name}}}" in template and slug is None for name, slug in slugs.items()):
                print(f"{template:<40} skipped (nothing published)")
                continue
            path = template.format(**slugs)
            probe = await client.get(path)
            if probe.status_code != 200:
                print(f"{path:<40} skipped ({probe.status_code})")
                continue
            print((await _hammer(client, path, requests, concurrency)).row())


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Load-test the public read endpoints.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--requests", type=int, default=500, help="per endpoint")
    parser.add_argument("--concurrency", type=int, default=100)
    args = parser.parse_args(argv)
    asyncio.run(run(args.base_url, args.requests, args.concurrency))


if __name__ == "__main__":
    main()
