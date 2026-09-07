from pathlib import Path

import pytest

from aislop.server import main, parser


def test_configuration_defaults(tmp_path: Path) -> None:
    args = parser().parse_args(["--allow-root", str(tmp_path)])
    assert args.allow_root == [tmp_path]
    assert (args.transport, args.host, args.port) == ("stdio", "127.0.0.1", 8000)
    assert (args.max_request_bytes, args.request_timeout) == (1_048_576, 35.0)
    assert args.rate_limit == 60


@pytest.mark.parametrize(
    "arguments, message",
    [
        ([], "--allow-root"),
        (["--allow-root", "relative"], "must be absolute"),
        (["--allow-root", "/does/not/exist"], "invalid --allow-root"),
        (["--allow-root", "/", "--max-request-bytes", "0"], "must be positive"),
        (["--allow-root", "/", "--request-timeout", "0"], "must be positive"),
        (["--allow-root", "/", "--rate-limit", "0"], "must be positive"),
        (["--allow-root", "/", "--transport", "http"], "HTTP requires"),
        (
            [
                "--allow-root",
                "/",
                "--transport",
                "http",
                "--host",
                "0.0.0.0",
                "--auth-token",
                "short",
            ],
            "at least 32 printable non-whitespace characters",
        ),
    ],
)
def test_invalid_configuration_exits(
    arguments: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as caught:
        main(arguments)
    assert caught.value.code == 2
    assert message in capsys.readouterr().err


def test_http_token_can_come_from_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AISLOP_AUTH_TOKEN", "x" * 32)
    invoked: dict[str, object] = {}
    monkeypatch.setattr("uvicorn.run", lambda app, **kwargs: invoked.update(kwargs))
    assert main(["--allow-root", str(tmp_path), "--transport", "http"]) == 0
    assert invoked == {"host": "127.0.0.1", "port": 8000, "log_config": None}


def test_short_loopback_token_is_rejected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit):
        main(["--allow-root", str(tmp_path), "--transport", "http", "--auth-token", "short"])
    assert "at least 32" in capsys.readouterr().err


def test_tls_is_deliberately_a_reverse_proxy_responsibility() -> None:
    options = {action.dest for action in parser()._actions}
    assert "ssl_keyfile" not in options
    assert "ssl_certfile" not in options
