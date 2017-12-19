import logging
from typing import Dict, Optional, List

from game import Game, BuyDecision, ActDecision, TrashDecision, DiscardDecision, MultiDecision, GainDecision, INF, NO_CARD
from cards import Card, Copper, Silver, Gold, Curse, Estate, Duchy, Province

class Player(object):
    def __init__(self, *args) -> None:
        raise NotImplementedError("Player is an abstract class")

    def make_decision(self, decision, state) -> None:
        assert state.player is self # pragma: no cover
        raise NotImplementedError

    def make_multi_decision(self, decision, state) -> None:
        raise NotImplementedError

    def make_gain_decision(self, card: Card) -> Card:
        return card

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return "<Player: %s>" % self.name

    def before_turn(self, game) -> None:
        pass

    def after_turn(self, game) -> None:
        pass

class HumanPlayer(Player):
    def __init__(self, name):
        self.name = name

    def make_decision(self, decision):
        if decision.game.simulated:
            # Don't ask the player to tell the AI what they'll do!
            return self.substitute_ai().make_decision(decision)
        state = decision.game.state()
        print(state.hand)
        print("Deck: %d cards" % state.deck_size())
        print("VP: %d" % state.score())
        print(decision)
        if isinstance(decision, MultiDecision):
            chosen = self.make_multi_decision(decision)
        else:
            chosen = self.make_single_decision(decision)
        return decision.choose(chosen)

    def make_single_decision(self, decision):
        for index, choice in enumerate(decision.choices()):
            print("\t[%d] %s" % (index, choice))
        choice = input('Your choice: ')
        try:
            return decision.choices()[int(choice)]
        except (ValueError, IndexError):
            # Try again
            print("That's not a choice.")
            return self.make_single_decision(decision)

    def make_multi_decision(self, decision):
        for index, choice in enumerate(decision.choices()):
            print("\t[%d] %s" % (index, choice))
        if decision.min != 0:
            print("Choose at least %d options." % decision.min)
        if decision.max != INF:
            print("Choose at most %d options." % decision.max)
        choices = input('Your choices (separated by commas): ')
        try:
            chosen = [decision.choices()[int(choice.strip())]
                      for choice in choices.split(',')]
            return chosen
        except (ValueError, IndexError):
            # Try again
            print("That's not a valid list of choices.")
            return self.make_multi_decision(decision)
        if len(chosen) < decision.min:
            print("You didn't choose enough things.")
            return self.make_multi_decision(decision)
        if len(chosen) > decision.max:
            print("You chose too many things.")
            return self.make_multi_decision(decision)
        for ch in chosen:
            if chosen.count(ch) > 1:
                print("You can't choose the same thing twice.")
                return self.make_multi_decision(decision)

    def substitute_ai(self, game):
        return BigMoney(game)

class AIPlayer(Player):
    def __init__(self):
        self.log = logging.getLogger(self.name)
        self.setLogLevel(logging.INFO)

    def setLogLevel(self, level):
        self.log.setLevel(level)

    def make_decision(self, game, decision):
        self.log.debug("Decision: %s" % decision)
        if isinstance(decision, BuyDecision):
            choice = self.make_buy_decision(game, decision)
        elif isinstance(decision, ActDecision):
            choice = self.make_act_decision(decision)
        elif isinstance(decision, DiscardDecision):
            choice = self.make_discard_decision(decision)
        elif isinstance(decision, TrashDecision):
            choice = self.make_trash_decision(decision)
        elif isinstance(decision, GainDecision):
            choice = self.make_gain_decision(decision.card)
        else:
            raise NotImplementedError
        return decision.choose(choice)

class BigMoney(AIPlayer):
    """
    This AI strategy provides reasonable defaults for many AIs. On its own,
    it aims to buy money, and then buy victory (the "Big Money" strategy).
    """
    def __init__(self, terminal_draws: List[Card] = [], cutoff1=3, cutoff2=6) -> None:
        self.cutoff1 = cutoff1  # when to buy duchy instead of gold
        self.cutoff2 = cutoff2  # when to buy duchy instead of silver
        #FIXME: names are implemented all wrong
        if not hasattr(self, 'name'):
            self.name = 'BigMoney(%d, %d)' % (self.cutoff1, self.cutoff2)
        AIPlayer.__init__(self)

    def buy_priority_order(self, game, decision):
        """
        Provide a buy_priority by ordering the cards from least to most
        important.
        """
        provinces_left = decision.game.card_counts[Province]
        if provinces_left <= self.cutoff1:
            return [None, Estate, Silver, Duchy, Province]
        elif provinces_left <= self.cutoff2:
            return [None, Silver, Duchy, Gold, Province]
        else:
            return [None, Silver, Gold, Province]

    def make_buy_decision(self, game, decision) -> Optional[Card]:
        """
        Choose a card to buy.
        """
        return self.buy_priority_order(game, decision)

    def act_priority(self, decision, card: Card) -> int:
        """
        Assign a numerical priority to each action. Higher priority actions
        will be chosen first.
        """
        if card is NO_CARD:
            return 0
        else:
            return (100 * card.actions + 10 * (card.coins + card.cards) + card.buys) + 1

    def make_act_decision(self, decision) -> Card:
        """
        Choose an Action to play.

        By default, this chooses the action with the highest positive
        act_priority.
        """
        choices = decision.choices()
        choices.sort(key=lambda card: self.act_priority(decision, card))
        return choices[-1]

    def make_trash_decision_incremental(self, decision, choices, allow_none=True) -> Optional[Card]:
        "Choose a single card to trash."
        deck = decision.state().all_cards()
        money = sum([card.treasure + card.coins for card in deck])
        if Curse in choices:
            return Curse
        elif Copper in choices and money > 3:
            return Copper
        elif decision.game.round < 10 and Estate in choices:
            # TODO: judge how many turns are left in the game and whether
            # an Estate is worth it
            return Estate
        elif allow_none:
            return NO_CARD
        else:
            # oh shit, we don't know what to trash
            # get rid of whatever looks like it's worth the least
            choices.sort(key=lambda x: (x.vp, x.cost))
            return choices[0]

    def make_trash_decision(self, decision) -> List[Card]:
        """
        The default way to decide which cards to trash is to repeatedly
        choose one card to trash until NO_CARD is chosen.

        TrashDecision is a MultiDecision, so return a list.
        """
        latest = False
        chosen: List[Card] = []
        choices = decision.choices()
        while choices and latest is not NO_CARD and len(chosen) < decision.max:
            latest = self.make_trash_decision_incremental(
                decision, choices,
                allow_none = (len(chosen) >= decision.min)
            )
            if latest is not NO_CARD:
                choices.remove(latest)
                chosen.append(latest)
        return chosen

    def make_discard_decision_incremental(self, decision, choices: List[Card], allow_none: bool = True) -> Optional[Card]:
        actions_sorted = [card for card in choices if card.is_action()]
        actions_sorted.sort(key=lambda a: a.actions)
        plus_actions = sum([ca.actions for ca in actions_sorted])
        wasted_actions = len(actions_sorted) - plus_actions - decision.state().actions
        victory_cards = [
            card for card in choices
            if card.is_victory() and not card.is_action() and not card.is_treasure()
        ]
        if wasted_actions > 0:
            return actions_sorted[0]
        elif len(victory_cards):
            return victory_cards[0]
        elif Copper in choices:
            return Copper
        elif allow_none:
            return NO_CARD
        else:
            priority_order = sorted(choices,
              key=lambda ca: (ca.actions, ca.cards, ca.coins, ca.treasure))
            return priority_order[0]

    def make_discard_decision(self, decision) -> List[Card]:
        # TODO: make this good.
        # This probably involves finding all distinct sets of cards to discard,
        # of size decision.min to decision.max, and figuring out how well the
        # rest of your hand plays out (including things like the Cellar bonus).

        # Start with
        #   game = decision.game().simulated_copy() ...
        # to avoid cheating.

        latest = False
        chosen: List[Optional[Card]] = []
        choices = decision.choices()
        while choices and latest is not NO_CARD and len(chosen) < decision.max:
            latest = self.make_discard_decision_incremental(
                decision, choices,
                allow_none = (len(chosen) >= decision.min)
            )
            if latest is not NO_CARD:
                choices.remove(latest)
                chosen.append(latest)
        return chosen
