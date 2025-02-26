import string
from abc import abstractmethod
from enum import IntEnum
from typing import List, Dict
import random

class CardValue(IntEnum):
    C_9 = 1
    C_10 = 2
    C_J = 3
    C_Q = 4
    C_K = 5
    C_A = 6

class Card:
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        self.value = Card.assign_value(rank)

    def __gt__(self, other: 'Card'):
        """Is greater than: self >= other"""
        return self.value > other.value

    def __ge__(self, other: 'Card'):
        """Is greater or equal: self >= other"""
        return self.value >= other.value

    def __lt__(self, other: 'Card'):
        """Is less than: self <= other"""
        return self.value < other.value

    def __le__(self, other: 'Card'):
        """Is less or equal: self <= other"""
        return self.value <= other.value

    def is_starter(self) -> bool:
        return self.suit == 'H' and self.rank == '9'

    def has_same_value(self, other: 'Card') -> bool:
        return self.value == other.value

    @staticmethod
    def assign_value(rank: str) -> int:
        """
        Assign card value according to rank hierarchy.
        :param rank: Card rank.
        :return: Card value.
        """
        values = {'9': 1, '10': 2, 'J': 3, 'Q': 4, 'K': 5, 'A': 6}
        return values[rank]

    @staticmethod
    def create_from_form(card: str) -> 'Card' | List['Card']:
        move = card.split(',')
        if len(move) == 1:
            return Card(card[0], card[1:])
        return [Card(card[0], card[1:]) for card in move]

class CardList(list):
    def get_by_value(self, value: int):
        return CardList(card for card in self if card.value == value)

    def count_by_value(self, value: int) -> int:
        return len(self.get_by_value(value))

    def remove_many(self, cards: List[Card]):
        self[:] = [card for card in self if card not in cards]

class PlayerCards(CardList):
    def get_starter(self) -> Card | None:
        return next((card for card in self if card.is_starter()), None)

    def get_lowest_valid_card(self, middle_cards: 'MiddleCards') -> Card | None:
        if not middle_cards:
            return self.get_starter()

        valid_cards = [card for card in self if card >= middle_cards.last()]
        return min(valid_cards, default=None, key=lambda card: card.value)

    def get_combo_by_value(self, value: int) -> List[Card] | None:
        combo = self.get_by_value(value)
        if len(combo) < 3: return None

        if value != 1:
            return combo if len(combo) == 4 else None

        if len(combo) == 3 and not any(card.is_starter() for card in combo):
            return combo
        if len(combo) == 4:
            combo.sort(key=lambda card: not card.is_starter())
            return combo

        return None

class MiddleCards(CardList):
    def last(self):
        return self[-1] if self else None

    def get_current_rank(self) -> str | None:
        return self[-1].rank if self else None

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
        self.cards: PlayerCards = PlayerCards()
        self.lost_rounds = 0
        self.is_playable = False

    @staticmethod
    def generate_name(length: int = 8 ) -> str:
        alphanumeric = string.ascii_letters + string.digits
        return ''.join(random.choices(alphanumeric, k=length))

    def has_starter(self) -> bool:
        return any(card.is_starter() for card in self.cards)

    def get_card(self, card: Card) -> Card | None:
        for x in self.cards:
            if x.rank == card.rank and x.suit == card.suit: return x

        return None

    def take_middle(self, middle_cards: List[Card], count: int = 3):
        if len(middle_cards) <= count:
            count = len(middle_cards) - 1

        if not count: return

        self.cards.extend(middle_cards[-count:])
        for _ in range(count):
            middle_cards.pop()

    @abstractmethod
    def make_move(self, middle_cards: List[Card], **kwargs):
        pass


class HumanPlayer(Player):
    def __init__(self, name: str = None):
        super().__init__(name)
        self.is_playable = True

    def make_move(self, middle_cards: List[Card], card: Card | List[Card] = None, skip = False):
        if skip:
            self.take_middle(middle_cards)
            return

        print(card)
        if isinstance(card, Card):
            card = [self.get_card(card)]
        else:
            card = [self.get_card(c) for c in card]
            if len(card) == 4 and card[0].rank == '9':
                card.sort(key = lambda c: not c.is_starter())

        if not card:
            raise ValueError("Gracz nie posiada tej karty.")

        middle_cards.extend(card)
        for c in card:
            self.cards.remove(c)

class AiPlayer(Player):
    def __init__(self, name: str = None):
        super().__init__(name)
        self.is_playable = False

    def make_move(self, middle_cards: MiddleCards, **kwargs):
        move = BasicStrategy().get_move(middle_cards, self.cards)
        if move is None:
            self.take_middle(middle_cards)
            return

        middle_cards.extend(move)
        self.cards.remove_many(move)

class StrategyFactory:
    @staticmethod
    def get_strategy(name: str) -> 'Strategy':
        pass

class Strategy:
    @staticmethod
    @abstractmethod
    def get_move(middle_cards: MiddleCards, player_cards: PlayerCards) -> List[Card] | Card | None:
        raise NotImplementedError

class BasicStrategy(Strategy):
    @staticmethod
    def get_move(middle_cards: MiddleCards, player_cards: PlayerCards) -> List[Card] | Card | None:
        lowest_card = player_cards.get_lowest_valid_card(middle_cards)
        if not lowest_card: return None

        combo = player_cards.get_combo_by_value(lowest_card.value)
        if not combo: return lowest_card

        return combo

class AggressiveStrategy(Strategy):
    @staticmethod
    def get_move(middle_cards: MiddleCards, player_cards: PlayerCards) -> List[Card] | Card | None:
        high_values = [cv for cv in CardValue if cv > CardValue.C_J and cv >= middle_cards.last().value]
        if not high_values: return None

        value = random.choice(high_values)
        attack = player_cards.get_by_value(value)
        if attack: return attack[0]

class SkipStrategy(Strategy):
    @staticmethod
    def get_move(middle_cards: MiddleCards, player_cards: PlayerCards) -> List[Card] | Card | None:
        return None

class Round:
    def __init__(self, players: Dict[str, Player]):
        self.middle_cards: MiddleCards = MiddleCards()
        self.players = players
        self.move_queue: List[Player] = []
        self.player_order: List[Player] = []
        self.loser = None

    def deal_cards(self):
        deck = Deck()
        card_count = int(len(deck) / len(self.players))
        for player in self.players.values():
            player.cards = PlayerCards(deck.deal(card_count))

    def create_queue(self):
        starter_player = None
        players = list(self.players.values())
        for player in players:
            if player.has_starter():
                starter_player = player
                break

        if starter_player is None:
            raise ValueError("Nie znaleziono gracza z kartą startową.")

        starter_pos = players.index(starter_player)
        self.move_queue = players[starter_pos:] + players[:starter_pos]

    def update_queue(self):
        current_player = self.move_queue.pop(0)
        if current_player.cards:
            self.move_queue.append(current_player)

    def set_player_order(self):
        self.player_order = self.move_queue.copy()

    def get_current_player(self):
        return self.move_queue[0]

    def is_valid_move(self, card: Card | List[Card] = None, skip = False) -> bool:
        if not card:
            if skip:
               return bool(self.middle_cards)
            raise ValueError("Brak ruchu do zweryfikowania.")

        if isinstance(card, Card):
            if not self.middle_cards:
                if not card.is_starter(): return False
                return True
            return card >= self.middle_cards[-1]
        else:
            if len(card) < 3: return False
            if len(card) == 3:
                if not self.middle_cards: return False
                if not self.middle_cards[-1].is_starter(): return False
                for c in card:
                    if c.rank != '9': return False
                return True
            if len(card) == 4:
                rank = card[0].rank
                print(rank)
                for c in card:
                    if c.rank != rank: return False
                if not self.middle_cards:
                    if rank != '9': return False
                    return True
                if self.middle_cards[-1] > card[0]: return False
                return True
            return False


    def is_over(self) -> bool:
        return len(self.move_queue) <= 1

    def declare_loser_if_over(self):
        if not self.is_over(): return
        self.get_current_player().lost_rounds += 1
        self.loser = self.get_current_player()

    def play(self, **kwargs):
        self.get_current_player().make_move(self.middle_cards, **kwargs)

        self.update_queue()
        self.declare_loser_if_over()

class LocalRound(Round):
    def __init__(self, players: Dict[str, Player]):
        super().__init__(players)
        self.deal_cards()
        self.create_queue()
        self.set_player_order()

class MultiplayerRound(Round):
    def __init__(self, players: Dict[str, Player]):
        super().__init__(players)
        self.is_started = False

    def start(self):
        if self.is_started: return
        self.deal_cards()
        self.create_queue()
        self.set_player_order()
        self.is_started = True

class Game:
    def __init__(self, players: Dict[str, Player]):
        self.players = players
        self.current_round = None

    def is_over(self) -> bool:
        for player in self.players.values():
            if player.lost_rounds == 3: return True
        return False

    def declare_loser_if_over(self):
        if self.is_over(): pass

    @abstractmethod
    def start_new_round(self):
        pass

    def play(self, **kwargs):
        if self.is_over(): return
        self.current_round.play(**kwargs)

        self.declare_loser_if_over()
        if self.is_over(): return
        if self.current_round.is_over():
            self.start_new_round()

class LocalGame(Game):
    def __init__(self, players: Dict[str, Player]):
        super().__init__(players)
        self.start_new_round()

    def start_new_round(self):
        self.current_round = LocalRound(self.players)

class MultiplayerGame(Game):
    def __init__(self, players: Dict[str, Player], player_count: int, game_host: Player):
        super().__init__(players)
        self.join_code = Player.generate_name()
        self.player_count = player_count
        self.is_started = False
        self.game_host = game_host
        self.inactive_players = set()

    def is_full_room(self):
        return not self.inactive_players and len(self.players) == self.player_count

    def join(self, player_id: str, player: Player):
        if self.is_full_room(): return
        self.players.update({player_id: player})

    def leave(self, player_id: str):
        self.inactive_players.add(player_id)

    def start_new_round(self):
        if not self.is_full_room(): return
        self.current_round = MultiplayerRound(self.players)
        self.current_round.start()

    def start(self):
        if not self.is_full_room(): return
        self.start_new_round()
        self.is_started = True