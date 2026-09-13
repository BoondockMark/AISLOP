"""Black-box acceptance test for an installed AISLOP wheel.

Run this file with the Python interpreter of a clean environment containing the
built wheel.  It deliberately changes to a temporary directory before importing
the package, so neither the checkout nor its ``src`` directory can satisfy an
import.
"""

from __future__ import annotations

# ruff: noqa: ASYNC220, ASYNC240
import asyncio
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

SERVER_BOOTSTRAP = """
from rf_mcp.fake_receiver import FakeStreamingReceiverBackend
from rf_mcp.receiver_backend import register_backend
register_backend(FakeStreamingReceiverBackend(name='airspyhf'))
from rf_mcp.server import main
main()
"""
TOKEN = "wheel-e2e-token-0123456789abcdef"


def clean_environment(data_dir: Path, **values: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.update(RF_MCP_DATA_DIR=str(data_dir), PYTHONUNBUFFERED="1", **values)
    return environment


def response(url: str, token: str | None = None) -> tuple[int, bytes, str]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        with urlopen(Request(url, headers=headers), timeout=10) as result:
            return result.status, result.read(), result.headers.get_content_type()
    except HTTPError as error:
        return error.code, error.read(), error.headers.get_content_type()


async def verify_stdio(python: str, work_dir: Path, data_dir: Path) -> None:
    parameters = StdioServerParameters(
        command=python,
        args=["-c", SERVER_BOOTSTRAP],
        cwd=work_dir,
        env=clean_environment(data_dir, RF_MCP_TRANSPORT="stdio"),
    )
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            initialized = await session.initialize()
            assert initialized.serverInfo.name == "Multi-SDR RF Lab"
            tools = {tool.name for tool in (await session.list_tools()).tools}
            assert {"list_devices", "inspect_spectrum", "analyze_signal"} <= tools
            device = (await session.call_tool("list_devices", {})).structuredContent
            assert device is not None and device["model"] == "deterministic-test-tone"
            assert device["hardware"] is False

            called = await session.call_tool(
                "inspect_spectrum",
                {
                    "center_frequency_hz": 100_000_000,
                    "duration_seconds": 0.25,
                    "fft_size": 1024,
                    "threshold_above_noise_db": 6,
                    "include_plot": False,
                },
            )
            assert called.isError is False
            result = called.structuredContent
            assert result is not None
            assert result["receiver_backend"] == "airspyhf"
            assert result["sample_rate_hz"] == 768_000
            assert result["captured_samples"] >= 192_000
            assert result["captured_samples"] % 76_800 == 0
            assert result["center_frequency_hz"] == 100_000_000
            assert result["measurement_scale"] == "relative_db"
            assert result["job_id"].startswith("inspect-")

            jobs = (await session.call_tool("list_rf_jobs", {"limit": 10})).structuredContent
            artifacts = (
                await session.call_tool(
                    "list_rf_artifacts", {"job_id": result["job_id"], "limit": 10}
                )
            ).structuredContent
            assert jobs is not None and artifacts is not None
            job = next(item for item in jobs["jobs"] if item["job_id"] == result["job_id"])
            assert job["job_type"] == "spectrum_inspection" and job["state"] == "completed"
            assert {item["kind"] for item in artifacts["artifacts"]} == {
                "spectrum_plot",
                "result_json",
            }
            assert all(Path(item["path"]).is_file() for item in artifacts["artifacts"])
            persisted = json.loads(Path(job["result_json_path"]).read_text(encoding="utf-8"))
            assert persisted["job_id"] == result["job_id"]
            assert len(persisted["artifacts"]) == 2
    assert (data_dir / "SDR-MCP.sqlite3").is_file()


async def verify_http(python: str, work_dir: Path, data_dir: Path) -> None:
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    environment = clean_environment(
        data_dir,
        RF_MCP_TRANSPORT="streamable-http",
        RF_MCP_HOST="127.0.0.1",
        RF_MCP_PORT=str(port),
        RF_MCP_API_TOKEN=TOKEN,
    )
    process = subprocess.Popen(
        [python, "-c", SERVER_BOOTSTRAP],
        cwd=work_dir,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 20
        while True:
            if process.poll() is not None:
                raise AssertionError(f"HTTP server exited early: {process.stderr.read()}")
            try:
                if response(base + "/health")[0] == 200:
                    break
            except OSError:
                pass
            if time.monotonic() >= deadline:
                raise AssertionError("HTTP server did not become ready")
            await asyncio.sleep(0.1)

        status, body, content_type = response(base + "/health")
        health = json.loads(body)
        assert status == 200 and content_type == "application/json"
        assert health["status"] == "ok" and health["authentication_required"] is True
        assert response(base + "/dashboard")[0] == 401  # token login page
        assert response(base + "/api/dashboard")[0] == 401
        assert response(base + "/assets/rf-dashboard.css")[0] == 401
        assert response(base + "/assets/rf-dashboard.js")[0] == 401
        assert response(base + "/mcp")[0] == 401

        dashboard = response(base + "/dashboard", TOKEN)
        css = response(base + "/assets/rf-dashboard.css", TOKEN)
        javascript = response(base + "/assets/rf-dashboard.js", TOKEN)
        dashboard_api = response(base + "/api/dashboard", TOKEN)
        assert dashboard[0] == 200 and b"MiniRackDisplay" in dashboard[1]
        assert css[0] == 200 and css[2] == "text/css" and b".dashboard" in css[1]
        assert javascript[0] == 200 and "javascript" in javascript[2]
        assert b"refreshDashboard" in javascript[1]
        assert dashboard_api[0] == 200
        snapshot = json.loads(dashboard_api[1])
        assert "jobs" in snapshot and "artifacts" in snapshot

        async with streamablehttp_client(
            base + "/mcp", headers={"Authorization": f"Bearer {TOKEN}"}
        ) as (reader, writer, _session_id):
            async with ClientSession(reader, writer) as session:
                initialized = await session.initialize()
                assert initialized.serverInfo.name == "Multi-SDR RF Lab"
                assert "inspect_spectrum" in {
                    tool.name for tool in (await session.list_tools()).tools
                }
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


async def main() -> None:
    checkout = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="aislop-wheel-e2e-") as temporary:
        root = Path(temporary)
        os.chdir(root)
        import rf_mcp

        installed_package = Path(rf_mcp.__file__).resolve()
        assert checkout not in installed_package.parents, (
            f"rf_mcp was imported from checkout instead of installed wheel: {installed_package}"
        )
        await verify_stdio(sys.executable, root, root / "stdio-data")
        await verify_http(sys.executable, root, root / "http-data")


if __name__ == "__main__":
    asyncio.run(main())
