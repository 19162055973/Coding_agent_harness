from __future__ import annotations

import argparse
import getpass
import sys

from forgeloop.credentials.store import CredentialStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="forgeloop", description="ForgeLoop coding agent harness")
    sub = parser.add_subparsers(dest="cmd", required=True)

    creds = sub.add_parser("creds", help="manage API credentials")
    creds_sub = creds.add_subparsers(dest="creds_cmd", required=True)
    creds_sub.add_parser("status", help="show credential status (no plaintext)")
    creds_sub.add_parser("set", help="set API key (hidden input)")
    creds_sub.add_parser("clear", help="clear stored API key")

    serve = sub.add_parser("serve", help="run WebUI")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8000)

    demo = sub.add_parser("demo", help="run mechanism demos with MockLLM")

    args = parser.parse_args(argv)

    if args.cmd == "creds":
        store = CredentialStore()
        if args.creds_cmd == "status":
            st = store.status()
            print(f"configured={st.configured} backend={st.backend} hint={st.hint_mask or '-'}")
            return 0
        if args.creds_cmd == "set":
            key = getpass.getpass("API key (input hidden): ")
            backend = store.set_key(key.strip())
            print(f"stored via {backend}")
            return 0
        if args.creds_cmd == "clear":
            store.clear()
            print("cleared")
            return 0

    if args.cmd == "serve":
        import uvicorn

        uvicorn.run("forgeloop.api.app:app", host=args.host, port=args.port, reload=False)
        return 0

    if args.cmd == "demo":
        from forgeloop.demo.mechanisms import main as demo_main

        return demo_main()

    return 1


if __name__ == "__main__":
    sys.exit(main())
