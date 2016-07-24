"""Front-end representation of a Poker Game."""

from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image

Builder.load_file('game.kv')


class Card(ButtonBehavior, Image):
    """A graphical representation of a playing card."""

    def __init__(self, properties, **kwargs):
        # type: (dict, dict)
        """Initiate an instance of the Card class.

        Args:
            properties: Information about the card:
                - 'suit' - the suit of the card.
                - 'face' - the face of the card.
                - 'selected' - weather the card was selected by the user
            **kwargs: Passed to super
        """
        self.suit = properties['suit']
        self.face = properties['face']
        self.selected = False
        super(Card, self).__init__(**kwargs)
        self.selected = properties['selected']
        self.source = "data/{}/{}.png".format(self.suit, self.face)

    def __repr__(self):
        # type: () -> str
        """Return a text representation of this Card.

        Returns:
            Text representation of this Card
        """
        return "game.Card('{}', '{}', selected={})".format(self.face,
                                                           self.suit,
                                                           self.selected)

    def __getstate__(self):
        # type: () -> dict
        """Represent this Card as a picklable object.

        Returns:
            Picklable representation of this card
        """
        return {
            'suit': self.suit,
            'face': self.face,
            'selected': self.selected
        }

    def on_release(self):
        """Select or de-select Card depending on current state."""
        self.selected = not self.selected
        if self.selected:
            self.y -= 40
        else:
            self.y += 40


class Game(Screen):
    """A front-end representation of a Poker game."""

    bottom = StringProperty('Waiting for server to start game')

    def __init__(self, cards_app, **kwargs):
        # type: (CardsApp, dict)
        """Initiate Game class.

        Args:
            cards_app: The main class of this application
            **kwargs: kwargs passed on to super class Screen
        """
        super(Screen, self).__init__(**kwargs)
        self.ca = cards_app
        self.show_score = False
        self.hands = {}

    @mainthread
    def update_hand(self, cards, pid):
        # type: (list, int)
        """Replace the hand of a user with the one provided.

        Args:
            cards: New hand
            pid: Player whose hand should be updated
        """
        hand = self.hands[pid][1]
        hand.clear_widgets()
        for card in cards:
            card = Card(card)
            card.selected = False
            hand.add_widget(card)

    @mainthread
    def update_opponents(self, hs=None, won=None):
        # type: (list, list)
        """
        Display opponents cards.

        Args:
            hs: Hands of all players - if None displays backs of cards
            won: Who won the last hand
        """
        if hs is None:
            for k, v in self.hands.items():
                if k != self.ca.client_id:
                    v[1].clear_widgets()
                    for i in range(5):
                        card = Card({'suit': 'backs',
                                     'face': 'red',
                                     'selected': False})
                        v[1].add_widget(card)
        else:
            for pid, score, cards in hs:
                win = ""
                if pid in won:
                    win = " WON"

                self.hands[pid][0].text = "Player " + str(pid) + ": " \
                                          + str(score) + win
                self.update_hand(cards, pid)

    @mainthread
    def set_show_score(self, show_score):
        # type: (bool)
        """Modify the button text and hide opponents cards if appropriate.

        Args:
            show_score: True if scores are being displayed
        """
        if show_score:
            self.bottom = "New hand"
        else:
            self.bottom = "Trade"
            self.update_opponents()

        self.show_score = show_score

    def bottom_button(self):
        """Determine and perform the action of the button based on state."""
        if self.show_score:
            self.send({'action': 'deal'})
        else:
            self.send({'action': 'swap',
                       'hand': self.hands[self.ca.client_id][1].children})

    @mainthread
    def received(self, msg):
        # type: (dict)
        """Run whenever a message is received.

        Args:
            msg: Message from game server. May have the following components:
                - 'init' - Starts a new game.
                - 'hand' - Update to this players hand.
                - 'hs' - Hands and scores of all players from the last hand.
                - 'won' - List of winners of the last hand.
                - 'swapped' - The card swap was successful.
        """
        if 'init' in msg:
            self.ids.b_button.disabled = False
            for pid, score in msg['init']:
                player = BoxLayout(orientation='vertical', padding=(10, 0))

                if pid == self.ca.client_id:
                    self.ids.hand.add_widget(player)
                else:
                    self.ids.opponents.add_widget(player)

                score = Label(text="Player " + str(pid) + ": " + str(score),
                              size_hint_y=.2)
                player.add_widget(score)

                hand = BoxLayout()
                player.add_widget(hand)

                self.hands[pid] = (score, hand)

                for i in range(5):
                    card = Card({'suit': 'backs',
                                 'face': 'red',
                                 'selected': False})
                    hand.add_widget(card)

        if 'hand' in msg:
            self.set_show_score(False)
            self.update_hand(msg['hand'], self.ca.client_id)

        if 'hs' in msg:
            self.set_show_score(True)
            self.update_opponents(msg['hs'], msg['won'])
            self.ids.b_button.disabled = False

        if 'swapped' in msg:
            self.ids.b_button.text = "Wait for others"
            self.ids.b_button.disabled = msg['swapped']

    def send(self, msg):
        # type: (object) -> object
        """Send message to game server.

        Args:
            msg: Message to be sent
        """
        msg['senderId'] = self.ca.client_id
        self.ca.send(msg)
