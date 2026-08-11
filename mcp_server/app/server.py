import os

from app import tools  # noqa: F401  (import registers all @mcp.tool handlers)
from app.mcp_instance import mcp


def main() -> None:
    port = int(os.environ.get("PORT", 8080))
    # Streamable HTTP so this can run as an independent Cloud Run service
    # reachable over the network, not an in-process/stdio fake. Cloud Run's
    # IAM layer (see infra/) handles auth; the app itself trusts its ingress.
    mcp.run(transport="http", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
