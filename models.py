import string
from abc import abstractmethod
from typing import List, Dict
import random

class Card:
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        self.value = Card.assign_value(rank)
        self.img_src = self.suit + self.rank + '.png'

    def __ge__(self, other: 'Card'):
        """Is greater or equal: self >= other"""
        return self.value >= other.value

    def __le__(self, other: 'Card'):
        """Is less or equal: self <= other"""
        return self.value <= other.value

    def is_starter(self) -> bool:
        return self.suit == 'H' and self.rank == '9'

    @staticmethod
    def assign_value(rank: str) -> int:
        """
        Assign card value according to rank hierarchy.
        :param rank: Card rank.
        :return: Card value.
        """
        values = {'9': 1, '10': 2, 'J': 3, 'Q': 4, 'K': 5, 'A': 6}
        return values[rank]

class Deck:
    def __init__(self):
        self.cards = Deck.create()
        self.shuffle()

    def __bool__(self):
        """Check if deck contains cards."""
        return bool(self.cards)

    def __len__(self):
        return len(self.cards)

    @staticmethod
    def create() -> List['Card']:
        """
        Create a deck of 24 cards. The deck contains cards ranked from 9 to Ace in all suits.
        :return: Deck of cards.
        """
        suits = ['C', 'D', 'H', 'S']
        ranks = ['9', '10', 'J', 'Q', 'K', 'A']
        return [Card(suit, rank) for suit in suits for rank in ranks]

    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)

    def deal(self, card_count: int) -> List['Card']:
        """
        Deal given number of cards. If there are less than card_count cards, deal the remaining cards.
        :param card_count: Number of cards to deal.
        :return: Cards.
        """
        card_count = min(card_count, len(self.cards))
        cards = self.cards[:card_count]
        self.cards = self.cards[card_count:]
        return cards

class Player:
    def __init__(self, name: str = None):
        self.name = Player.generate_name() if name is None else name
        self.cards: List[Card] = []
        self.lost_rounds = 0

    @staticmethod
    def generate_name(length: int = 8 ) -> str:
        alphanumeric = string.ascii_letters + string.digits
        return ''.join(random.choices(alphanumeric, k=length))

    def has_starter(self) -> bool:
        return any(card.is_starter() for card in self.cards)

    #@abstractmethod
    def make_move(self, card: Card, middle_cards: List[Card]):
        if card >= middle_cards[-1]:
            middle_cards.append(card)

class AiPlayer(Player):
    def make_move(self, card: Card, middle_cards: List[Card]):
        pass


class Round:
    def __init__(self, players: List[Player]):
        self.middle_cards: List[Card] = []
        self.players = players
        self.move_queue: List[Player] = []

        self.deal_cards()
        self.create_queue()

    def deal_cards(self):
        deck = Deck()
        card_count = int(len(deck) / len(self.players))
        for player in self.players:
            player.cards = deck.deal(card_count)

    def create_queue(self):
        starter_index = None
        for i, player in enumerate(self.players):
            if player.has_starter():
                starter_index = i
                break

        if starter_index is None:
            raise ValueError("Nie znaleziono gracza z kartą startową.")

        self.move_queue = self.players[starter_index:] + self.players[:starter_index]

    def update_queue(self):
        current_player = self.move_queue[0]
        self.move_queue.pop(0)
        if current_player.cards:
            self.move_queue.append(current_player)

    def is_over(self) -> bool:
        return len(self.move_queue) == 1

    def declare_loser_if_over(self):
        if self.is_over(): self.move_queue[0].lost_rounds += 1


    def play(self):
        #self.deal_cards()
        #self.create_queue()

        '''
        player.make_move()
        validate_move()
        self.update_queue()
        self.declare_loser_if_over()
            
        '''

