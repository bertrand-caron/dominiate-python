import logging
import sys
from typing import List

from game import TrashDecision, DiscardDecision, DEFAULT_HAND_SIZE
from players import AIPlayer, BigMoney
from cards import Card, Copper, Estate, Silver, Duchy, Province, Gold, Smithy, Witch

class SmithyBot(BigMoney):
    def __init__(self, cutoff1: int = 3, cutoff2: int = 6):
        self.cards_per_smithy = DEFAULT_HAND_SIZE + Smithy.cards
        self.name = 'SmithyBot(%d, %d)' % (cutoff1, cutoff2)
        BigMoney.__init__(self, cutoff1, cutoff2)

    def num_smithies(self, state) -> int:
        return list(state.all_cards()).count(Smithy)

    def buy_priority_order(self, decision) -> List[Card]:
        state = decision.state()
        provinces_left = decision.game.card_counts[Province]
        if provinces_left <= self.cutoff1:
            order = [Estate, Silver, Duchy, Province]
        elif provinces_left <= self.cutoff2:
            order = [Silver, Smithy, Duchy, Gold, Province]
        else:
            order = [Silver, Smithy, Gold, Province]
        if ((self.num_smithies(state) + 1) * self.cards_per_smithy > state.deck_size()) and (Smithy in order):
            order.remove(Smithy)

        try:
            return sorted(
                filter(
                    lambda card: card.cost <= state.hand_value(),
                    order,
                ),
                key=lambda card: -card.cost,
            )[0]
        except IndexError:
            return None

    def make_act_decision(self, decision):
        return Smithy

class WitchBot(BigMoney):
    def __init__(self, cutoff1: int = 3, cutoff2: int = 6):
        self.terminal_draws = [Witch]
        self.name = 'WitchBot(%d, %d)' % (cutoff1, cutoff2)
        BigMoney.__init__(self, cutoff1, cutoff2)

    def num_terminal_draws(self, state) -> int:
        all_cards = state.all_cards()
        return sum(all_cards.count(cards) for card in self.terminal_draws)

    def buy_priority_order(self, decision) -> List[Card]:
        state = decision.state()
        provinces_left = decision.game.card_counts[Province]
        if provinces_left <= self.cutoff1:
            choices = [Estate, Silver, Duchy, Province]
        elif provinces_left <= self.cutoff2:
            choices = [Silver] + self.terminal_draws + [Duchy, Gold, Province]
        else:
            choices = [Silver] + self.terminal_draws + [Gold, Province]

        potential_draw = sum(state.all_cards().count(card) * (DEFAULT_HAND_SIZE + card.cards) for card in self.terminal_draws)
        if potential_draw > state.deck_size():
            [choices.remove(card) for card in self.terminal_draws if card in choices]

        try:
            return sorted(
                filter(
                    lambda card: card.cost <= state.hand_value(),
                    choices,
                ),
                key=lambda card: -card.cost,
            )[0]
        except IndexError:
            return None

    def make_act_decision(self, decision):
        try:
            return [card for card in decision.state().all_cards() if card in self.terminal_draws][0]
        except IndexError:
            return None

class HillClimbBot(BigMoney):
    def __init__(self, cutoff1=2, cutoff2=3, simulation_steps=100):
        self.simulation_steps = simulation_steps
        if not hasattr(self, 'name'):
            self.name = 'HillClimbBot(%d, %d, %d)' % (cutoff1, cutoff2,
            simulation_steps)
        BigMoney.__init__(self, cutoff1, cutoff2)

    def buy_priority(self, decision, card):
        state = decision.state()
        total = 0
        if card is None: add = ()
        else: add = (card,)
        for coins, buys in state.simulate_hands(self.simulation_steps, add):
            total += buying_value(coins, buys)

        # Gold is better than it seems
        if card == Gold:
            total += self.simulation_steps / 2
        self.log.debug("%s: %s" % (card, total))
        return total

    def make_buy_decision(self, decision):
        choices = decision.choices()
        provinces_left = decision.game.card_counts[Province]

        if Province in choices:
            return Province
        if Duchy in choices and provinces_left <= self.cutoff2:
            return Duchy
        if Estate in choices and provinces_left <= self.cutoff1:
            return Estate
        return BigMoney.make_buy_decision(self, decision)

def buying_value(coins: int, buys: int) -> int:
    if coins > buys * Province.cost:
        coins = buys * Province.cost
    if (coins - (buys-1) * Province.cost) in (1, Province.cost - 1):  # there exists a useless coin
        coins -= 1
    return coins
