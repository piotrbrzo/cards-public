"""Back-end game implementation -- Five-card Draw Poker."""

from cards import Game, Card, Player, Deck
from deuces import Evaluator


class Poker(Game):
    """Represents a Game of Five-card Draw Poker."""

    def __repr__(self):
        # type: () -> str
        """Return a representation of self.

        Returns:
            Representation of this Card
        """
        return "Poker Game. Players: {}. {}".format(self.players, self.deck)

    def run(self):
        """Called when the game is started."""
        for k in self.ca.connections:
            if k != 0:
                self.players[k] = PokerPlayer(False, k, self)

        for pid in self.players:
            self.ca.send({'hand': self.players[pid].hand,
                          'init': [(k, v.score)
                                   for k, v in self.players.items()]
                          }, pid)

    def received(self, msg):
        # type: (dict)
        """Called whenever the back-end receives a new message.

        Args:
            msg: The content of the received message. The msg['action'] string
            determines how this request should be processed:
                - 'swap' - a player is requesting to swap some of his cards.
                    His hand is passed along in msg['hand'].
                - 'deal' - a player is requesting a new hand to be dealt.
        """
        if msg['action'] == 'swap':
            p = self.players[msg['senderId']]
            hand = map(Card.from_dict, msg['hand'])
            p.swap(filter(lambda obj: obj.selected, hand))

            if len(filter(lambda (key, obj): not obj.swapped,
                          self.players.items())) == 0:

                self.ca.send_all({'won': self.calculate_score(),
                                  'hs': [(k, v.score, v.hand)
                                         for k, v in self.players.items()]})
            else:
                self.ca.send({'hand': p.hand, 'swapped': True}, p.id)

        if msg['action'] == 'deal':
            self.deck = Deck()
            for k, v in self.players.items():
                v.hand = []
                v.swapped = False
                v.draw(5)
                self.ca.send({'hand': v.hand}, k)

    def calculate_score(self):
        # type: () -> list
        """Evaluate and compares the hands of all players.

        Returns:
            Ids of players who won this hand
        """
        scores = {}
        for k, v in self.players.items():
            scores[k] = Evaluator().evaluate([card.d_card for card in v.hand],
                                             [])

        m = min(scores.values())
        l = [k for k, v in scores.items() if v == m]

        for i in l:
            self.players[i].win()

        return l


class PokerPlayer(Player):
    """Represent a poker player in the game."""

    def __init__(self, swapped=False, *args, **kwargs):
        # type: (bool, tuple, dict)
        """Initiate a poker player.

        Args:
            swapped: Has the player swapped his cards this round already
            *args: Passed on to Player
            **kwargs: Passed on to Player
        """
        super(PokerPlayer, self).__init__(*args, **kwargs)
        self.swapped = swapped
        self.score = 0
        self.draw(5)

    def swap(self, cards):
        # type: (list)
        """Draw new cards to substitute all the ones the player wants to swap.

        Args:
            cards: Subset of cards in the Players hand to be swapped
        """
        if not self.swapped:
            for card in cards:
                self.hand.remove(card)
            self.draw(5 - len(self.hand))
            self.swapped = True

    def win(self):
        """Increment this players score by 1."""
        self.score += 1
