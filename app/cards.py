""""Back-end representations of a Card, Deck, Player and Game."""

import itertools
import random

from abc import ABCMeta, abstractmethod
from deuces import Card as DCard


class Card(object):
    """Each instance is a representation of a single card."""

    SUITS = {"diamonds": 1, "clubs": 2, "hearts": 3, "spades": 4}
    FACES = dict({str(n): n for n in range(2, 11)},
                 **{"J": 11, "Q": 12, "K": 13, "A": 14})

    @staticmethod
    def from_dict(properties):
        # type: (dict) -> Card
        """Alternative constructor for the Card class.

        Args:
            properties: A dictionary of the parameters Card.__init__() takes

        Returns:
            A new instance of the Card class
        """
        return Card(properties['suit'], properties['face'],
                    properties['selected'])

    def __init__(self, suit, face, selected=False):
        # type: (str, str, bool)
        """A card is being initialized.

        Args:
            suit: The suit of the card
            face: The face of the card
            selected: Has the card been selected in this hand
        """
        self.suit = suit
        self.face = face
        self.selected = selected

    def __cmp__(self, other):
        # type: (Card) -> int
        """Compare self to another object.

        Args:
            other: The object to be compared with self

        Returns:
            A negative integer if self < other, zero if self == other,
            a positive integer if self > other
        """
        if not isinstance(other, Card):
            return 0
        if self == other:
            return 0
        if self < other:
            return -1
        return 1

    def __lt__(self, other):
        # type: (Card) -> bool
        """Check if self is less than another object.

        Args:
            other: The object to be compared with self

        Returns:
            True if self < other, False otherwise
        """
        if self.SUITS[self.suit] < self.SUITS[other.suit]:
            return True
        if self.SUITS[self.suit] > self.SUITS[other.suit]:
            return False
        if self.FACES[self.face] < self.FACES[other.face]:
            return True
        return False

    def __eq__(self, other):
        # type: (Card) -> bool
        """Check if self is equal to another object.

        Args:
            other: The object to be compared with self

        Returns:
            True if self is equal to other, False otherwise
        """
        return self.FACES[self.face] == self.FACES[other.face] \
            and self.SUITS[self.suit] == self.SUITS[other.suit]

    def __repr__(self):
        # type: () -> str
        """Return a representation of self.

        Returns:
            Representation of this Card
        """
        return "cards.Card('{}', '{}', selected={})".format(self.face,
                                                            self.suit,
                                                            self.selected)

    @property
    def d_card(self):
        # type: () -> DCard
        """Create the DCard representation of this card.

        Returns:
            The DCard representation of this card
        """
        if self.face == "10":
            face = "T"
        else:
            face = self.face[0]
        return DCard.new(face + self.suit[0])


class Deck(object):
    """Represent a deck of cards."""

    def __init__(self):
        """Create cards with all possible face suit combinations."""
        self.cards = list(Card(s, f) for
                          s, f in itertools.product(Card.SUITS, Card.FACES))
        random.shuffle(self.cards)

    def __repr__(self):
        # type: () -> str
        """Return a text representation of this Deck.

        Returns:
            Text representation of this Deck
        """
        out = "Deck:\n"
        for c in self.cards:
            out += str(c) + "\n"
        return out

    def draw(self, num=0):
        # type: (int) -> list
        """Draw cards from deck.

        Args:
            num: The number of cards to draw

        Returns:
            A list of drawn cards
        """
        if num < 1:
            return []
        else:
            tmp = self.cards[-num:]
            del self.cards[-num:]
            return tmp


class Player(object):
    """Represent one of the players in the game."""

    def __init__(self, pid, game, hand=None, score=0):
        # type: (int, Game, [Card], int)
        """Initialize a Player.

        Args:
            pid: Players id
            game: Reference to the current Game
            hand: The players current hand
            score: The players current score
        """
        if hand is None:
            hand = []
        self.hand = hand
        self.id = pid
        self.game = game
        self.score = score

    def __repr__(self):
        # type: () -> str
        """Return a text representation of this Player.

        Returns:
            Text representation of this Player
        """
        return "Player({}, {}, score={})".format(self.id,
                                                 self.hand,
                                                 self.score)

    def draw(self, num=1):
        # type: (int)
        """Draw cards from the deck into this Player's hand.

        Args:
            num: The number of cards to draw
        """
        self.hand += self.game.deck.draw(num)
        self.hand.sort()


class Game(object):
    """Abstract class representing any card game."""

    __metaclass__ = ABCMeta

    def __init__(self, cards_app):
        # type: (CardsApp)
        """Initialize a Game.

        Args:
            cards_app: The main class of this application
        """
        self.ca = cards_app
        self.players = {}
        self.deck = Deck()

    def __repr__(self):
        # type: () -> str
        """Return a text representation of this Game.

        Returns:
            Text representation of this Game
        """
        return "Game. Players: {}. Deck: {}".format(self.players, self.deck)

    @abstractmethod
    def received(self, msg):
        # type: (dict)
        """Called whenever the back-end receives a new message.

        Args:
            msg: The content of the received message
        """
        pass

    @abstractmethod
    def run(self):
        """Called when the game is started."""
        pass
