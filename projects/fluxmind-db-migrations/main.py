from __future__ import annotations

import os
import sys

from alembic.config import CommandLine, Config


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    alembic_cfg_path = os.path.join(
        os.path.dirname(__file__),
        "alembic.ini",
    )

    if not os.path.exists(alembic_cfg_path):
        raise SystemExit(f"Alembic config not found: {alembic_cfg_path}")

    cli = CommandLine(prog="fluxmind-db-migrations")
    options = cli.parser.parse_args(argv)

    if not hasattr(options, "cmd"):
        cli.parser.print_help()
        return 1

    config = Config(alembic_cfg_path)
    return cli.run_cmd(config, options)


if __name__ == "__main__":
    raise SystemExit(main())
