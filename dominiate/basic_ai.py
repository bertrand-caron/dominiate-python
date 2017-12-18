import logging
import sys

from game import TrashDecision, DiscardDecision, STARTING_HAND
from players import AIPlayer, BigMoney
from cards import Copper, Estate, Silver, Duchy, Province, Gold, Smithy

class SmithyBot(BigMoney):
    def __init__(self, cutoff1=3, cutoff2=6, cards_per_smithy=8):
        self.cards_per_smithy = len(STARTING_HAND) + Smithy.cards
        self.name = 'SmithyBot(%d, %d, %d)' % (cutoff1, cutoff2, cards_per_smithy)
        BigMoney.__init__(self, cutoff1, cutoff2)

    def num_smithies(self, state) -> int:
        return list(state.all_cards()).count(Smithy)

    def buy_priority_order(self, decision):
        state = decision.state()
        provinces_left = decision.game.card_counts[Province]
        if provinces_left <= self.cutoff1:
            order = [None, Estate, Silver, Duchy, Province]
        elif provinces_left <= self.cutoff2:
            order = [None, Silver, Smithy, Duchy, Gold, Province]
        else:
            order = [None, Silver, Smithy, Gold, Province]
        if ((self.num_smithies(state) + 1) * self.cards_per_smithy > state.deck_size()) and (Smithy in order):
            order.remove(Smithy)
        return order

    def make_act_decision(self, decision):
        return Smithy

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

