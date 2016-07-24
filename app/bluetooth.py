"""Works only on Android. Takes care of communication via Bluetooth."""

from jnius import autoclass, detach
from jnius.jnius import JavaException
from kivy import Logger
from utils import thread, popup

# Import Java classes
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
UUID = autoclass('java.util.UUID')


class Bluetooth(object):
    """Establish connections via Bluetooth. Send and receive data."""

    # Constant UUID which allows instances of this application to establish
    # connections with each other.
    uuid = UUID.fromString("8cb47de6-d67d-40a1-97f4-cf373769829f")

    paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()  # noqa

    def __init__(self, cards_app):
        # type: (CardsApp)
        """Initiate Bluetooth class.

        Args:
            cards_app: The main Game object
        """
        self.ca = cards_app

    def client(self, name):
        # type: (str)
        """Connect to a different device as a client.

        Args:
            name: Server device name
        """
        Logger.info("Bluetooth: Connecting to server: " + str(name))
        try:
            for device in self.paired_devices:
                if device.getName() == name:
                    socket = device.createRfcommSocketToServiceRecord(Bluetooth.uuid)  # noqa
                    recv_stream = socket.getInputStream()
                    socket.connect()
                    self.ca.add_conn(self.send, socket.getOutputStream())
                    thread(self.listen, [recv_stream])
                    break
        except JavaException as e:
            Logger.error("Bluetooth: Connecting to server failed: %s", e)
            popup('Connecting to {} via Bluetooth failed'.format(name),
                  callback=self.ca.go_back)
        finally:
            detach()

    def server(self):
        """Start Bluetooth server - wait for incoming connections."""
        Logger.info("Bluetooth: Waiting for clients")
        try:
            server_socket = BluetoothAdapter.getDefaultAdapter().listenUsingRfcommWithServiceRecord('Cards', Bluetooth.uuid)  # noqa
            socket = server_socket.accept()
            server_socket.close()
            recv_stream = socket.getInputStream()
            self.ca.add_conn(self.send, socket.getOutputStream())
            thread(self.listen, [recv_stream])
        except JavaException as e:
            Logger.error("Bluetooth: Waiting for clients failed: %s", e)
            popup("Bluetooth: Waiting for clients failed")
            self.ca.sm.get_screen('server').server_off()
        finally:
            detach()

    @staticmethod
    def send(msg, conn):
        # type: (str, OutputStream)
        """Send message to a device connected via Bluetooth.

        Args:
            msg: The message to send
            conn: The connection to send the message over
        """
        Logger.info("Bluetooth: Sending: " + str(msg))
        try:
            conn.write(bytearray(msg))
            conn.flush()
        except JavaException as e:
            Logger.error("Bluetooth: Sending \"%s\" failed: %s", msg, e)
        finally:
            detach()

    def listen(self, received):
        # type: (InputStream)
        """Listen for any received messages.

        Args:
            received: The connection to listen on
        """
        try:
            while True:
                buff = bytearray([0] * 1024)
                received.read(buff)
                msg = buff.partition(b'\0')[0].decode('utf-8')
                Logger.info("Bluetooth: Received: " + str(msg))
                self.ca.receive(msg)
        except JavaException as e:
            Logger.error("Bluetooth: Listening for connections failed: %s", e)
        finally:
            detach()

    def reload_paired_devices(self):
        """Reload the list of paired devices."""
        self.paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()  # noqa
