"""Takes care of communication over Web Sockets."""

from kivy import Logger
from kivy.support import install_twisted_reactor
from utils import thread, popup

# install_twisted_rector must be called before importing and using the reactor
install_twisted_reactor()

from twisted.internet import reactor  # noqa
from twisted.internet import protocol  # noqa
from twisted.internet.error import CannotListenError  # noqa
from twisted.internet.protocol import connectionDone  # noqa
from txws import WebSocketFactory  # noqa
from websocket import (create_connection, WebSocket, socket,
                       WebSocketConnectionClosedException)  # noqa


class WSProtocol(protocol.Protocol):
    """Protocol for connections over Web Sockets."""

    def __init__(self):
        """Initiate WSProtocol class."""
        pass

    def connectionMade(self):
        """Run when a connection is made."""
        self.factory.ws.add(self)

    def dataReceived(self, data):
        # type: (str)
        """Run when data is received.

        Args:
            data: Data received
        """
        self.factory.ws.ca.receive(data)

    def connectionLost(self, reason=connectionDone):
        # type: (Failure)
        """Run when connection is lost.

        Args:
            reason: Reason for the connection being lost
        """
        self.factory.ws.ca.remove_conn(self)


class WSFactory(protocol.Factory):
    """Web Socket server Factory."""

    protocol = WSProtocol

    def __init__(self, ws):
        # type: (WebSockets)
        """Initiate WSFactory class.

        Args:
            ws: WebSockets module creating this Factory
        """
        self.ws = ws


class WebSockets(object):
    """Establish connections via Web Sockets. Send and receive data."""

    def __init__(self, cards_app):
        # type: (CardsApp)
        """Initiate WebSockets class.

        Args:
            cards_app: The main Game object
        """
        self.ca = cards_app

    def server(self, port=8000):
        # type: (int)
        """Start a Web Socket server.

        Args:
            port: Port on which to start the server
        """
        ws_factory = WSFactory(self)
        while port < 65536:
            try:
                reactor.listenTCP(port, WebSocketFactory(ws_factory))
            except CannotListenError:
                port += 1
                continue
            break

        Logger.info("server started on port " + str(port))
        self.ca.update_ip(port)

    def client(self, host="localhost:8000"):
        # type: (str)
        """Connect as a client to a Web Socket server.

        Args:
            host: Host and optional colon and port to connect to
        """
        host_address = 'ws://' + host
        Logger.info("Client started - connecting to %s", host_address)

        try:
            ws = create_connection(host_address)
        except (socket.gaierror, socket.error):
            popup("Cannot connect to host.", callback=self.ca.go_home)
            return

        self.ca.add_conn(self.send, ws)
        try:
            while True:
                self.ca.receive(ws.recv())
        except WebSocketConnectionClosedException:
            pass
        finally:
            Logger.info("client stopped")
            self.ca.remove_conn(ws)
            ws.close()

    def add(self, conn):
        # type: (object)
        """Save a connection in the main directory.

        Args:
            conn: Connection to be saved
        """
        thread(self.ca.add_conn, [self.send, conn])

    @staticmethod
    def send(msg, conn):
        # type: (str, object)
        """Send a message over Web Sockets.

        Args:
            msg: Message to send
            conn: Connection to destination
        """
        if isinstance(conn, WebSocket):
            thread(conn.send, [msg])
        else:
            thread(conn.transport.write, [msg])

    @property
    def ip(self):
        # type: () -> str
        """Get host.

        Returns:
            IPv4 address of this machine
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            s.connect(('<broadcast>', 0))
            return s.getsockname()[0]
        except socket.error:
            return 'localhost'
