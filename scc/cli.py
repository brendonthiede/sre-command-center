import argparse
import sys


def main() -> None:
    p = argparse.ArgumentParser(prog="scc", description="SRE command center")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("serve", help="run the dashboard and background syncs")
    s = sub.add_parser("sync", help="sync one source now")
    s.add_argument("source")
    sub.add_parser("backup", help="back up the sqlite db to the NAS")
    args = p.parse_args()

    if args.cmd == "serve":
        from scc.web import serve
        serve()
    elif args.cmd == "sync":
        from scc.sync import sync_source
        n = sync_source(args.source)
        print(f"{args.source}: {n} items")
    elif args.cmd == "backup":
        from scc.backup import backup
        print(backup())


if __name__ == "__main__":
    sys.exit(main())
