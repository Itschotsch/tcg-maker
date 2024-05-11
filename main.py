import os
import sys

def start_web(ip: str | None = None, port: int | None = None) -> None:
    from app.web.tcg_maker_web import TCGMakerWeb
    from app.tcg_maker_io import TCGMakerIO
    # Initialize the TCG Maker IO
    TCGMakerIO.init(os.getcwd())
    # Create a new TCG Maker object
    ui = TCGMakerWeb()
    # Run the TCG Maker program
    ui.start_web(ip, port)

if __name__ == "__main__":
    ip: str | None = None
    port: int | None = None

    if "--help" in sys.argv:
        print("Usage: python main.py [options]")
        print("Options:")
        print("  --help - Display this help message")
        print("  --ip <ip> - Set the IP address to run the web server on")
        print("  --port <port> - Set the port to run the web server on")
        sys.exit(0)
    
    # --ip <ip> - Set the IP address to run the web server on
    if "--ip" in sys.argv and sys.argv.index("--ip") + 1 < len(sys.argv):
        ip = sys.argv[sys.argv.index("--ip") + 1]

    # --port <port> - Set the port to run the web server on
    if "--port" in sys.argv and sys.argv.index("--port") + 1 < len(sys.argv):
        port_str = sys.argv[sys.argv.index("--port") + 1]
        if port_str.isdigit():
            port = int(port_str)
        else:
            print("Invalid port number")
            sys.exit(1)

    start_web(ip, port)
    sys.exit(0)