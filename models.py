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

    def add_one_or_more(self, cards: Card | List[Card]):
        if isinstance(cards, Card):
            self.append(cards)
        else:
            self.extend(cards)

    def remove_one_or_more(self, cards: Card | List[Card]):
        if isinstance(cards, Card):
            self.remove(cards)
        else:
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

    def contains_invalid_cards(self, middle_cards: 'MiddleCards') -> bool:
        return any(card < middle_cards.last() for card in self) if middle_cards else False

    def contains_urgent_cards(self, middle_cards: 'MiddleCards') -> bool:
        return any(middle_cards.is_last_card_from_rank(card, self) for card in self)

    def get_valid_cards(self, middle_cards: 'MiddleCards') -> 'PlayerCards':
        return PlayerCards([card for card in self if card >= middle_cards.last()])

    def get_invalid_cards(self, middle_cards: 'MiddleCards') -> 'PlayerCards':
        return PlayerCards([card for card in self if card < middle_cards.last()])

class MiddleCards(CardList):
    def last(self):
        return self[-1] if self else None

    def get_worst_skip_value(self) -> int | None:
        if len(self) <= 1: return None
        if len(self) < 4: return self[1].value
        return min(self[-3:], default=None, key=lambda card: card.value).value

    def is_last_card_from_rank(self, card: Card, player_cards: PlayerCards) -> bool:
        temp = player_cards.count_by_value(card.value)
        return temp + self.count_by_value(card.value) == 4

    def get_high_value(self) -> int:
        return min(self[-1].value + 3, CardValue.C_A)

    def last_move_is_combo(self) -> bool:
        return any(card.value != self[-1].value for card in self[-4:]) if len(self) >= 4 else False

    def has_good_skip_value(self) -> bool:
        return self.get_worst_skip_value() >= self[-1].value - 1 if len(self) > 1 else True

    def is_developed(self) -> bool:
        return any(card.value > CardValue.C_10 for card in self)

    def get_skip_cards(self) -> CardList | None:
        if len(self) <= 1: return None
        if len(self) == 2: return CardList([self[-1]])
        if len(self) == 3: return CardList(self[-2:])
        return CardList(self[-3:])

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
        self.skipped_moves_in_row = 0

    def make_move(self, middle_cards: MiddleCards, **kwargs):
        move = BasicStrategy().get_move(middle_cards, self.cards)
        if move is None:
            self.skipped_moves_in_row += 1
            self.take_middle(middle_cards)
            return

        self.skipped_moves_in_row = 0
        middle_cards.add_one_or_more(move)
        self.cards.remove_one_or_more(move)

    def has_good_high_cards_ratio(self, middle_cards: MiddleCards) -> bool:
        high_cards = [card for card in self.cards if card.value > CardValue.C_Q]
        return len(high_cards) >= len(middle_cards) / 3

    def skipped_last_moves(self, move_count: int = 2) -> bool:
        return self.skipped_moves_in_row >= move_count

    def gets_combo_if_skipped(self, middle_cards: MiddleCards):
        skip_cards = middle_cards.get_skip_cards()
        if not skip_cards: return False

        for skip_card in skip_cards:
            cards_by_value = self.cards.get_by_value(skip_card.value)
            if not cards_by_value: continue

            combo_length = len(cards_by_value) + len(skip_cards.get_by_value(skip_card.value))
            if combo_length < 3: continue
            if combo_length == 3: return skip_card.value == CardValue.C_9
            return True

    def gets_just_aces_if_skipped(self, middle_cards):
        skip_cards = middle_cards.get_skip_cards()
        return not any(card.value != CardValue.C_A for card in skip_cards) if skip_cards else False

class StrategyFactory:
    @staticmethod
    def get_strategy(name: str) -> 'Strategy':
        pass

    @staticmethod
    def vote_for_strategy(bot: AiPlayer, middle_cards: MiddleCards):
        votes = {AggressiveStrategy: 0, BasicStrategy: 0, SkipStrategy: 0}

        conditions = [
            (AggressiveStrategy, bot.cards.contains_urgent_cards(middle_cards), 4),

            (BasicStrategy, not bot.cards.contains_invalid_cards(middle_cards), 4),
            (BasicStrategy, not middle_cards.is_developed(), 2),

            ((AggressiveStrategy, BasicStrategy), bot.skipped_last_moves(), 2),
            ((AggressiveStrategy, BasicStrategy), middle_cards.last_move_is_combo(), 2),
            ((AggressiveStrategy, BasicStrategy), not middle_cards.has_good_skip_value(), 2),
            ((AggressiveStrategy, BasicStrategy), bot.has_good_high_cards_ratio(middle_cards), 1),

            (SkipStrategy, bot.gets_just_aces_if_skipped(middle_cards), 3),
            (SkipStrategy, bot.gets_combo_if_skipped(middle_cards), 2),
            (SkipStrategy, not bot.skipped_last_moves(), 2),
            (SkipStrategy, not middle_cards.last_move_is_combo(), 1),
            (SkipStrategy, not bot.has_good_high_cards_ratio(middle_cards), 1),
            (SkipStrategy, middle_cards.has_good_skip_value(), 1),
        ]

        for strategy, condition, weight in conditions:
            if condition:
                if isinstance(strategy, tuple):
                    for strat in strategy:
                        votes[strat] += weight
                else:
                    votes[strategy] += weight
        return votes

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