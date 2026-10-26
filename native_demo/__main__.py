"""Run with python3 -m native_demo --port 8765. Personal account only."""
import argparse
from .server import make_server


def main():
    parser = argparse.ArgumentParser(description='ATLAS personal localhost demo; never publish or tunnel this OAuth-backed service.')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--host', default='127.0.0.1', choices=['127.0.0.1'])
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('port must be between 0 and 65535')
    server = make_server(host=args.host, port=args.port)
    print('ATLAS personal demo: http://127.0.0.1:' + str(server.server_address[1]), flush=True)
    print('Local owner only. No history stored. Do not expose through a public tunnel.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
