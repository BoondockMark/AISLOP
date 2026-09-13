"""Multi-SDR RF Lab MCP server."""

# The distribution has one release version. Re-exporting it keeps RF API and
# dashboard metadata aligned with the wheel and the workspace observer CLI.
from aislop import __version__

__all__ = ["__version__"]
