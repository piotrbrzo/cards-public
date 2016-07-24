"""The main menu and communication between components."""

from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.garden.qrcode import QRCodeWidget
from kivy.utils import platform
from kivy.logger import Logger
from kivy.core.window import Window
from poker import Poker
from websockets import WebSockets
from utils import thread, popup
import jsonpickle
from kivy.app import App
from game import Game
import webbrowser
from kivy.core.clipboard import Clipboard

# On Android
if platform == 'android':
    from jnius import autoclass
    from android import activity
    from bluetooth import Bluetooth
    from jnius.jnius import JavaException

    # Import Java classes
    PythonActivity = autoclass('org.renpy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
    AndroidActivityInfo = autoclass('android.content.pm.ActivityInfo')
    AndroidPythonActivity = autoclass('org.renpy.android.PythonActivity')

__version__ = "0.1"

Builder.load_file('gui.kv')


class MainMenu(Screen):
    """The main menu widget."""

    pass


class Server(Screen):
    """The Server sub-menu."""

    url = StringProperty('')
    num_connected = NumericProperty(0)
    bt_text = StringProperty('Start Bluetooth Server')

    @mainthread
    def set_url(self, url):
        # type: (str)
        """Set the host and port displayed.

        Args:
            url: The url to be displayed
        """
        self.url = url

    @staticmethod
    def clipboard(text):
        # type: (str)
        """Copy to device clipboard.

        Args:
            text: Text to be copied
        """
        Clipboard.copy(text)

    def server_on(self):
        """Disable the button for turning on a Bluetooth server."""
        self.bt_text = "Waiting for Bluetooth connections"
        self.ids.bt_server.disabled = True

    def server_off(self):
        """Enable the button for turning on a Bluetooth server."""
        self.bt_text = 'Start Bluetooth Server'
        self.ids.bt_server.disabled = False


class WSClient(Screen):
    """Sub-menu for connecting to Web Socket servers."""

    pass


class BTClient(Screen):
    """Sub-menu for choosing a Bluetooth device to connect to."""

    @mainthread
    def add_devices(self, names):
        # type: (list)
        """Update the list of available devices.

        Args:
            names: Names of paired Bluetooth devices.
        """
        self.ids.devices.clear_widgets()
        for name in names:
            self.ids.devices.add_widget(BTDeviceButton(text=name.getName()))


class BTDeviceButton(Button):
    """Each of the device buttons in the BTClient sub-menu."""

    pass


class About(Screen):
    """Sub-menu displaying credits."""

    @staticmethod
    def open_link(link):
        # type: (str)
        """Open link in web browser.

        Args:
            link: URL to open
        """
        webbrowser.open(link)


class CardsApp(App):
    """The main Application."""

    # Constants used for calls to the Android API.
    READ_QR = 0x123
    BT_SET = 0x124
    BT_SRV = 0x125

    def __init__(self, headless=False, **kwargs):
        # type: (bool, dict)
        """Initiate CardsApp class. Create all the Screens and variables.

        Args:
            headless: If True no client is run on the server instance
            **kwargs: Passed on to App super class
        """
        super(CardsApp, self).__init__(**kwargs)

        self.headless = headless

        self.sm = ScreenManager()
        self.sm.add_widget(MainMenu(name='main_menu'))
        self.sm.add_widget(WSClient(name='ws_client'))
        self.sm.add_widget(Server(name='server'))
        self.sm.add_widget(About(name='about'))
        self.sm.add_widget(BTClient(name='bt_client'))

        self.sm.add_widget(Game(self, name='game'))

        self.path = []

        self.bt = None
        self.is_server = False
        self.ws = WebSockets(self)
        self.backend = None

        self.client_id = 0
        self.connections = {}  # server always id=0

    def build(self):
        # type: () -> ScreenManager
        """Return the GUI.

        Returns:
            Application ScreenManager
        """
        Window.bind(on_keyboard=self.my_key_handler)

        return self.sm

    def add_conn(self, fun, conn=None):
        # type: (function, object)
        """Assign player IDs and store connections with them.

        Args:
            fun: Function to be called to connect to this client
            conn: Connection to client
        """
        Logger.info("Connected to " + str(conn))
        for clientId in xrange(1000):
            if clientId not in self.connections:
                self.connections[clientId] = {
                    'function': fun,
                    'connection': conn
                }

                self.sm.get_screen('server').num_connected \
                    = len(self.connections) - 2 if not self.headless \
                    else len(self.connections) - 1

                if self.is_server:
                    self.send({'_new_id_': clientId}, clientId)
                break

    def remove_conn(self, conn):
        # type: (object)
        """End game when a client disconnects.

        Args:
            conn: A connection to a client
        """
        Logger.info("Disconnected from " + str(conn))
        for i, data in self.connections.iteritems():
            if data['connection'] == conn:
                if i == 0:
                    popup("Disconnected from server", callback=self.go_home)
                else:
                    popup("Disconnected from player " + str(i),
                          callback=self.go_home)

                del self.connections[i]

                break

    def my_key_handler(self, window, key_code, *args):
        # type: (object, int, tuple)
        """Intercept ESC and BACK key events and binds them to go_back().

        Args:
            window: Active window
            key_code: Pressed key code
            *args: Additional arguments

        Returns:
            True if key was intercepted
        """
        if key_code in [27, 1001]:
            self.go_back()
            return True
        return False

    def server(self):
        """Setup routing for game server."""
        self.is_server = True
        self.add_conn(self.receive)  # Add server to routing table
        if not self.headless:
            # Add local client to routing table
            self.add_conn(self.receive, True)

    def ws_server(self, port=8000):
        # type: (int)
        """Run Web Socket server.

        Args:
            port: Port to run server on
        """
        self.server()
        thread(self.ws.server, [port])

    def ws_client(self, address):
        # type: (str)
        """Connect to a Web Socket server.

        Args:
            address: Server address to connect to
        """
        self.is_server = False
        thread(self.ws.client, [address])
        self.start()

    def bt_server(self):
        """Start Bluetooth server."""
        self.bt = Bluetooth(self)
        self.bt_settings(True, True)
        self.sm.get_screen('server').server_on()

    def bt_client(self):
        """Choose Bluetooth device to connect to."""
        self.bt = Bluetooth(self)
        self.bt_settings(True)
        self.is_server = False
        self.go('bt_client')
        self.sm.get_screen('bt_client').add_devices(self.bt.paired_devices)

    def bt_connect(self, name):
        # type: (str)
        """Connect to a specific device via Bluetooth.

        Args:
            name: Name of device to connect to
        """
        thread(self.bt.client, [name])
        self.start()

    @mainthread
    def start(self):
        """Start game."""
        self.screen_horizontal()
        self.go('game')

        if self.is_server:
            self.backend = Poker(self)
            self.backend.run()

            if self.headless:
                popup("Running in headless mode",
                      "Server",
                      callback=self.go_home)

    def send(self, msg, destination_id=0):
        # type: (dict, int)
        """Send message to the server or a specific client.

        Args:
            msg: Message to be sent
            destination_id: Id of destination - defaults to game server
        """
        msg = jsonpickle.dumps(msg, unpicklable=False)
        Logger.debug('Sending message to %s: %s', destination_id, msg)
        conn = self.connections[destination_id]
        thread(conn['function'], [msg, conn['connection']])

    def send_all(self, msg):
        # type: (dict)
        """Send message to all clients.

        Args:
            msg: Message to be sent
        """
        for c in self.connections:
            if c != 0:
                thread(self.send, [msg, c])

    def update_ip(self, port):
        # type: (int)
        """Update url displayed on server.

        Args:
            port: Port on which server is running
        """
        self.sm.get_screen('server').set_url(self.ws.ip + ":" + str(port))
        self.go('server')

    def scan_qr(self):
        """Scan QR code if on Android. Uses external application."""
        if self.android:
            activity.bind(on_activity_result=self.on_activity_result)

            intent = Intent()
            intent.setAction("com.google.zxing.client.android.SCAN")

            try:
                PythonActivity.mActivity.startActivityForResult(intent,
                                                                self.READ_QR)
            except JavaException as e:
                Logger.error('com.google.zxing.client.android not installed:'
                             ' %s', e)
                popup('Barcode Scanner not installed: '
                      'com.google.zxing.client.android')

    @mainthread
    def bt_settings(self, activate=False, server=False):
        # type: (bool, bool)
        """Turn on Bluetooth or open Bluetooth settings.

        Args:
            activate: If True enable Bluetooth
            server: If True this device is a server
        """
        activity.bind(on_activity_result=self.on_activity_result)

        if activate:
            intent = Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE)
        else:
            intent = Intent("android.settings.BLUETOOTH_SETTINGS")

        if activate and server:
            PythonActivity.mActivity.startActivityForResult(intent,
                                                            self.BT_SRV)
        else:
            PythonActivity.mActivity.startActivityForResult(intent,
                                                            self.BT_SET)

    @mainthread
    def on_activity_result(self, request_code, result_code, data):
        # type: (int, int, tuple)
        """Called when Android Intents return a result.

        Args:
            request_code: Identifies the request
            result_code: Result code (-1 is success)
            data: Additional data
        """
        Logger.debug("requestCode " + str(request_code) + " resultCode " +
                     str(result_code))
        if request_code == self.READ_QR and result_code == -1:
            Logger.info("QRCode reader returned")
            qrcode = data.getStringExtra("SCAN_RESULT")
            Logger.debug("QRCode: " + qrcode)
            self.ws_client(qrcode)
        elif request_code == self.BT_SET or request_code == self.BT_SRV:
            Logger.info("Bluetooth Settings returned")
            self.sm.get_screen('bt_client').ids.devices.clear_widgets()
            self.bt.reload_paired_devices()
            self.sm.get_screen('bt_client').add_devices(self.bt.paired_devices)

        if request_code == self.BT_SRV:
            thread(self.bt.server, [])

    def receive(self, msg, to_client=False):
        # type: (str, bool)
        """Run whenever a message is received.

        Args:
            msg: Received message
            to_client: If True send message to client not server
        """
        Logger.debug("Received: " + str(msg))
        try:
            msg = jsonpickle.loads(msg)
        except ValueError:
            Logger.error("Not valid JSON: " + msg)

        if '_new_id_' in msg:
            self.client_id = msg['_new_id_']
        else:
            if not self.is_server or to_client:
                thread(self.sm.get_screen('game').received, [msg])
            else:
                thread(self.backend.received, [msg])

    @staticmethod
    @mainthread
    def screen_horizontal(horizontal=True):
        # type: (bool)
        """Change screen orientation on Android.

        Args:
            horizontal: If true change to horizontal
        """
        if platform == 'android':
            activity = AndroidPythonActivity.mActivity
            if horizontal:
                activity.setRequestedOrientation(
                    AndroidActivityInfo.SCREEN_ORIENTATION_LANDSCAPE)
            else:
                activity.setRequestedOrientation(
                    AndroidActivityInfo.SCREEN_ORIENTATION_PORTRAIT)

    def go(self, screen):
        # type: (str)
        """Go to specific screen. Remember the path.

        Args:
            screen: Name of destination Screen
        """
        self.path.append(self.sm.current)
        self.sm.current = screen

    def go_back(self, home=False):
        # type: (bool)
        """Go to previous screen. Reset everything when in main menu.

        Args:
            home: If True go to main menu
        """
        if len(self.path) == 0 and not home:
            self.stop()
        else:
            self.screen_horizontal(False)
            self.sm.current = self.path.pop()

            if len(self.path) == 0 or home:
                Logger.debug("Resetting app")
                if home:
                    self.path = []
                    self.sm.current = 'main_menu'

                self.sm.remove_widget(self.sm.get_screen('game'))
                self.sm.add_widget(Game(self, name='game'))

                self.bt = None
                self.is_server = False
                self.ws = WebSockets(self)
                self.backend = None

                self.client_id = 0
                self.connections = {}  # server always id=0

    def go_home(self, *args):
        # type: (tuple)
        """Go to main menu.

        Args:
            *args: Other arguments
        """
        self.go_back(True)

    def on_pause(self):
        # type: () -> bool
        """Prevent the app from stopping when paused.

        Returns:
            True
        """
        return True

    def on_resume(self):
        # type: () -> bool
        """Run when the app is resumed.

        Returns:
            True
        """
        return True

    @property
    def android(self):
        # type: () -> bool
        """Check if current OS is Android.

        Returns:
            Is application running on Android
        """
        return platform == 'android'

if __name__ == '__main__':
    CardsApp().run()
