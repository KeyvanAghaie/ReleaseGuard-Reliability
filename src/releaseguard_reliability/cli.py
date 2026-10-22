import argparse
import json

from .scenarios import run_scenario


def main(argv=None):
    parser = argparse.ArgumentParser(prog="releaseguard-reliability")
    parser.add_argument("--scenario", choices=["success", "timeout", "server-error", "rate-limit"], default="success")
    args = parser.parse_args(argv)
    print(json.dumps(run_scenario(args.scenario), indent=2))
    return 0
if __name__ == "__main__": raise SystemExit(main())

