import logging
import sys
from typing import List

from game import TrashDecision, DiscardDecision, DEFAULT_HAND_SIZE
from players import AIPlayer, BigMoney
from cards import Card, Copper, Estate, Silver, Duchy, Province, Gold, Smithy, Witch, Moat, Militia, Chapel, NO_CARD

class Terminal_Draw_Big_Money(BigMoney):
    def __init__(self, terminal_draws: List[Card] = [], cutoff1: int = 3, cutoff2: int = 6) -> None:
        super().__init__(cutoff1, cutoff2)
        self.terminal_draws = terminal_draws
        if False:
            assert all(card.cards > 0 for card in self.terminal_draws), [
                card
                for card in self.terminal_draws
                if card.cards <= 0
            ]
        self.name = '{0}Bot(cutoff1={1}, cutoff2={2})'.format(
            ''.join([card.name.title() for card in self.terminal_draws]),
            cutoff1,
            cutoff2,
        )

    def buy_priority_order(self, game, decision) -> Card:
        state = decision.state()
        provinces_left = decision.game.card_counts[Province]
        if provinces_left <= self.cutoff1:
            choices = [Estate, Silver, Duchy, Province]
        elif provinces_left <= self.cutoff2:
            choices = [Silver, Duchy, Gold, Province]
        else:
            choices = [Silver, Gold, Province]

        if state.action_density() < 1.0:
            buy_more_actions = True
            choices += self.terminal_draws
        else:
            buy_more_actions = False

        sorted_choices = sorted(
            filter(
                lambda card: card.cost <= state.hand_value() and game.card_counts[card] > 0,
                choices,
            ),
            key=lambda card: (
                card not in self.terminal_draws if buy_more_actions else False,
                -card.cost,
            ),
        )

        try:
            return sorted_choices[0]
        except IndexError:
            return NO_CARD

    def make_act_decision(self, decision):
        try:
            return [card for card in decision.state().all_cards() if card in self.terminal_draws][0]
        except IndexError:
            return NO_CARD

SmithyBot = lambda cutoff1= 3, cutoff2=6: Terminal_Draw_Big_Money(
    terminal_draws=[Smithy],
    cutoff1=cutoff1,
    cutoff2=cutoff2,
)

WitchBot = lambda cutoff1=3, cutoff2=6: Terminal_Draw_Big_Money(
    terminal_draws=[Witch],
    cutoff1=cutoff1,
    cutoff2=cutoff2,
)

MoatBot = lambda cutoff1=3, cutoff2=6: Terminal_Draw_Big_Money(
    terminal_draws=[Moat],
    cutoff1=cutoff1,
    cutoff2=cutoff2,
)

MilitiaBot = lambda cutoff1=3, cutoff2=6: Terminal_Draw_Big_Money(
    terminal_draws=[Militia],
    cutoff1=cutoff1,
    cutoff2=cutoff2,
)

ChapelBot = lambda cutoff1=3, cutoff2=6: Terminal_Draw_Big_Money(
    terminal_draws=[Chapel],
    cutoff1=cutoff1,
    cutoff2=cutoff2,
)

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
        if card is NO_CARD:
            add = ()
        else:
            add = (card,)
        for (coins, buys) in state.simulate_hands(self.simulation_steps, add):
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
