import random
import logging
from typing import List, Optional, Union, Callable, Union, Sequence, Any, Dict
from sys import maxsize
from itertools import groupby

mainLog = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN, format='%(levelname)s: %(message)s')

INF = maxsize

EFFECT = Callable[['Game'], 'Game']

class Card(object):
    """
    Represents a class of card.

    To save computation, only one of each card should be constructed. Decks can
    contain many references to the same Card object.
    """
    def __init__(
        self,
        name: str,
        cost: int,
        treasure: int = 0,
        vp: int = 0,
        coins: int = 0,
        cards: int = 0,
        actions: int = 0,
        buys: int = 0,
        potionCost: int = 0,
        effect: Union[EFFECT, Sequence[EFFECT]] = (),
        isAttack: bool = False,
        isDefense: bool = False,
        reaction=(),
        duration=(),
    ) -> None:
        self.name = name
        self.cost = cost
        self.potionCost = potionCost
        if isinstance(treasure, int):
            self.treasure = treasure
        else:
            self.treasure = property(treasure)
        if isinstance(vp, int):
            self.vp = vp
        else:
            self.vp = property(vp)
        self.coins = coins
        self.cards = cards
        self.actions = actions
        self.buys = buys
        self._isAttack = isAttack
        self._isDefense = isDefense
        if not isinstance(effect, (tuple, list)):
            self.effect = (effect,)
        else:
            self.effect = effect
        self.reaction = reaction
        self.duration = duration

    def is_victory(self) -> bool:
        return self.vp > 0

    def is_pure_victory(self) -> bool:
        return self.is_victory() and not self.is_action() and self.is_treasure()

    def is_curse(self) -> bool:
        return self.vp < 0

    def is_treasure(self):
        return self.treasure > 0

    def is_action(self) -> bool:
        return any(
            [
                self.coins,
                self.cards,
                self.actions,
                self.buys,
                self.effect,
            ]
        )

    def is_attack(self) -> bool:
        return self._isAttack

    def is_defense(self) -> bool:
        return self._isDefense

    def perform_action(self, game):
        assert self.is_action()
        if self.cards:
            game = game.current_draw_cards(self.cards)
        if (self.coins or self.actions or self.buys):
            game = game.change_current_state(
              delta_coins=self.coins,
              delta_actions=self.actions,
              delta_buys=self.buys
            )
        for action in self.effect:
            game = action(game)
        return game

    def __str__(self) -> str:
        return self.name

    def __lt__(self, other) -> bool:
        raise Exception('Cards can only be compared with an explicit context (e.g. trashing, buying)')

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return self.name

# define the cards that are in every game
Curse    = Card('Curse', 0, vp=-1)
Estate   = Card('Estate', 2, vp=1)
Duchy    = Card('Duchy', 5, vp=3)
Province = Card('Province', 8, vp=6)

Copper = Card('Copper', 0, treasure=1)
Silver = Card('Silver', 3, treasure=2)
Gold   = Card('Gold', 6, treasure=3)

NO_CARD = None

DEFAULT_HAND_SIZE = 5
STARTING_HAND = (Copper,)*7 + (Estate,)*3

class PlayerState(object):
    """
    A PlayerState represents all the game state that is particular to a player,
    including the number of actions, buys, and +coins they have.
    """
    def __init__(self, player, hand, drawpile, discard, tableau, actions: int = 0, buys: int = 0, coins: int = 0) -> None:
        self.player = player
        self.actions = actions;   assert isinstance(self.actions, int)
        self.buys = buys;         assert isinstance(self.buys, int)
        self.coins = coins;       assert isinstance(self.coins, int)
        self.hand = hand;         assert isinstance(self.hand, tuple)
        self.drawpile = drawpile; assert isinstance(self.drawpile, tuple)
        self.discard = discard;   assert isinstance(self.discard, tuple)
        self.tableau = tableau;   assert isinstance(self.tableau, tuple)
        # TODO: duration cards

    @staticmethod
    def initial_state(player):
        # put it all in the discard pile so it auto-shuffles, then draw
        return PlayerState(
            player,
            hand=(),
            drawpile=(),
            discard=STARTING_HAND,
            tableau=(),
        ).next_turn()

    def change(self, delta_actions: int = 0, delta_buys: int = 0, delta_cards: int = 0, delta_coins: int = 0):
        """
        Change the number of actions, buys, cards, or coins available on this
        turn.
        """
        state= PlayerState(self.player, self.hand, self.drawpile, self.discard,
                           self.tableau, self.actions+delta_actions,
                           self.buys+delta_buys, self.coins+delta_coins)
        assert delta_cards >= 0
        if delta_cards > 0:
            return state.draw(delta_cards)
        else:
            return state

    def deck_size(self) -> int:
        return len(self.all_cards())

    def __len__(self) -> int:
        return self.deck_size()

    def all_cards(self) -> List[Card]:
        return self.hand + self.tableau + self.drawpile + self.discard

    def card_counts(self) -> Dict[Card, int]:
        on_name = lambda x: x.name

        return {
            key: len(list(group))
            for (key, group) in groupby(
                sorted(
                    self.all_cards(),
                    key=on_name,
                ),
                key=on_name,
            )
        }

    def hand_value(self) -> int:
        """How many coins can the player spend?"""
        return self.coins + sum(card.treasure for card in self.hand)

    def hand_size(self) -> int:
        return len(self.hand)

    def is_defended(self) -> bool:
        return any(card.is_defense() for card in self.hand)

    def get_reactions(self):
        """
        TODO: implement complex reactions like Secret Chamber
        """
        return []

    def draw(self, n=1):
        """
        Returns a new PlayerState in which n cards have been drawn (shuffling
        if necessary).
        """
        if len(self.drawpile) >= n:
            return PlayerState(
              self.player, self.hand+self.drawpile[:n], self.drawpile[n:],
              self.discard, self.tableau, self.actions, self.buys, self.coins
            )
        elif self.discard:
            got = self.drawpile
            newdraw = list(self.discard)
            random.shuffle(newdraw)

            state2 = PlayerState(
              self.player, self.hand+got, tuple(newdraw), (), self.tableau,
              self.actions, self.buys, self.coins
            )
            return state2.draw(n-len(got))
        else:
            return PlayerState(
              self.player, self.hand+self.drawpile, (), (), self.tableau,
              self.actions, self.buys, self.coins
            )

    def next_turn(self):
        """
        First, discard everything. Then, get 5 (DEFAULT_HAND_SIZE) cards, 1 action, and 1 buy.
        """
        return PlayerState(
          self.player, (), self.drawpile, self.discard+self.hand+self.tableau,
          (), actions=1, buys=1, coins=0
        ).draw(DEFAULT_HAND_SIZE)

    def gain(self, card):
        "Gain a single card."
        return PlayerState(
            self.player,
            self.hand,
            self.drawpile,
            self.discard + (card,),
            self.tableau,
            self.actions,
            self.buys,
            self.coins
        )

    def gain_cards(self, cards):
        "Gain multiple cards."
        self.player.log.info('Player {0} gains {1}'.format(self.player, ','.join(map(str, cards))))
        return PlayerState(
            self.player,
            self.hand,
            self.drawpile,
            self.discard + cards,
            self.tableau,
            self.actions,
            self.buys,
            self.coins,
        )

    def play_card(self, card):
        """
        Play a card from the hand into the tableau.

        Decreasing the number of actions available is handled in
        play_action(card).
        """

        index = list(self.hand).index(card)
        newhand = self.hand[:index] + self.hand[index+1:]
        result = PlayerState(
            self.player, newhand, self.drawpile, self.discard,
            self.tableau+(card,), self.actions, self.buys, self.coins
        )
        assert len(self) == len(result)
        return result

    def play_action(self, card):
        """
        Play an action card, putting it in the tableau and decreasing the
        number of actions remaining.

        This does not actually put the Action into effect; the Action card
        does that when it is chosen in an ActDecision.
        """
        return self.play_card(card).change(delta_actions=-1)

    def discard_card(self, card):
        """
        Discard a single card from the hand.
        """
        index = list(self.hand).index(card)
        newhand = self.hand[:index] + self.hand[index+1:]
        return PlayerState(
          self.player, newhand, self.drawpile, self.discard+(card,),
          self.tableau, self.actions, self.buys, self.coins
        )

    def trash_card(self, card, game):
        """
        Remove a card from the game.
        """
        index = list(self.hand).index(card)
        newhand = self.hand[:index] + self.hand[index + 1:]
        return PlayerState(
          self.player, newhand, self.drawpile, self.discard,
          self.tableau, self.actions, self.buys, self.coins
        )

    def actionable(self):
        """Are there actions left to take with this hand?"""
        return (
            self.actions > 0
            and any(card.is_action() for card in self.hand)
        )

    def buyable(self):
        """Can this hand still buy a card?"""
        return self.buys > 0

    def next_decision(self):
        """
        Return the next decision that must be made. This will be either
        an ActDecision or a BuyDecision; other kinds of decisions only happen
        as a result of ActDecisions.
        """
        if self.actionable():
            return ActDecision
        elif self.buyable():
            return BuyDecision
        else:
            return None

    def score(self) -> int:
        """How many points is this deck worth?"""
        return sum(card.vp for card in self.all_cards())

    def simulate(self):
        return self.simulation_state()

    def simulate_from_here(self):
        newdraw = list(self.drawpile)
        random.shuffle(newdraw)
        return PlayerState(self.player, self.hand, tuple(newdraw),
                           self.discard, self.tableau, self.actions,
                           self.buys, self.coins)

    def simulation_state(self, cards=()):
        """
        Get a state with a freshly-shuffled deck, a new turn, and certain cards
        on top of the deck. Generally useful for simulating the effect of
        gaining a new card.
        """
        state = PlayerState(self.player, (), cards, self.all_cards(), (),
                            1, 1, 0)
        return state.draw(DEFAULT_HAND_SIZE)

    def simulate_hands(self, n=100, cards=()):
        """
        Simulate n hands with certain cards in them, yielding the number of
        coins and buys they end with.
        """
        for i in range(n):
            # make sure there are cards to gain, even though we haven't
            # kept track of the real game state
            game = Game(
                [self.simulation_state(cards)],
                {Province: 12, Duchy: 12, Estate: 12, Copper: 12, Silver: 12, Gold: 12},
                simulated=True,
                trash=[],
                total_card_count=None,
            )
            coins, buys = game.simulate_turn()
            yield coins, buys

    def money_density(self, account_for_draws: bool = True) -> float:
        all_cards = self.all_cards()
        return (
            sum(card.coins + card.treasure for card in all_cards)
            /
            sum(1 - (card.cards if account_for_draws else 0) for card in all_cards) # Draw cards makes money density higher
        )

    def mean_hand_size(self) -> float:
        '''
        Return expected number of cards per hand (assuming that all actions can be played)
        '''
        all_actions = [card for card in self.all_cards() if card.is_action()]
        return DEFAULT_HAND_SIZE + sum(card.cards for card in all_actions) / (len(self.all_cards()) / DEFAULT_HAND_SIZE)

    def action_density(self) -> float:
        '''
        Return expected number of action cards per hand.
        '''
        all_actions = [card for card in self.all_cards() if card.is_action()]
        return len(all_actions) * DEFAULT_HAND_SIZE / len(self.all_cards())

    def action_engine_lifetime(self) -> float:
        '''
        Returns the expected lifetime of an (action) engine.
        A running engine is an engine drawing (at least) as many cards as it consumes.
        '''
        mean_draw_per_action = [card for card in self.all_cards() if card.is_action()]

    def mean_money_per_turn(self) -> float:
        return self.mean_hand_size() * self.money_density(account_for_draws=False)

# How many duchies/provinces are there for n players?
VICTORY_CARDS = {
    1: 5,  # useful for simulation
    2: 8,
    3: 12,
    4: 12,
    5: 15,
    6: 18
}

class Game(object):
    def __init__(self, playerstates, card_counts, turn=0, simulated=False, trash: List[Card] = [], total_card_count: Optional[int] = None):
        self.playerstates = playerstates
        self.card_counts = card_counts
        self.turn = turn
        self.player_turn = turn % len(playerstates)
        self.round = turn // len(playerstates)
        self.simulated = simulated
        logid = 'Game'
        if self.simulated:
            logid = 'Simulation'
        self.log = logging.getLogger(logid)
        if self.simulated:
            self.log.setLevel(logging.WARN)
        else:
            self.log.setLevel(logging.INFO)
        self.trash = trash
        self.total_card_count = sum(self.card_counts.values()) if total_card_count is None else total_card_count

    def copy(self) -> 'Game':
        "Make an exact copy of this game state."
        return Game(
            self.playerstates[:],
            self.card_counts,
            turn=self.turn,
            simulated=self.simulated,
            trash=self.trash,
            total_card_count=self.total_card_count,
        )

    @staticmethod
    def setup(players, var_cards: List[Card] = (), simulated: bool = False):
        "Set up the game."
        counts = {
            Estate: VICTORY_CARDS[len(players)],
            Duchy: VICTORY_CARDS[len(players)],
            Province: VICTORY_CARDS[len(players)],
            Copper: 60 - 7 * len(players),
            Silver: 40,
            Gold: 30,
            Curse: 10 * (len(players) - 1), #TODO: Find exact formula
        }
        for card in var_cards:
            counts[card] = 10 #TODO: This formula needs to be adjusted for treasure cards

        playerstates = [PlayerState.initial_state(p) for p in players]
        random.shuffle(playerstates)
        return Game(
            playerstates,
            counts,
            turn=0,
            simulated=simulated,
            trash=[],
            total_card_count=None,
        )

    def state(self):
        """
        Get the game's state for the current player. Most methods that
        do anything interesting need to do this.
        """
        return self.playerstates[self.player_turn]

    def current_play_card(self, card: Card):
        """
        Play a card in the current state without decrementing the action count.
        Could be useful for Throne Rooms and such.
        """
        return self.replace_current_state(self.state().play_card(card))

    def current_play_action(self, card: Card):
        """
        Remember, this is the one that decrements the action count.
        """
        return self.replace_current_state(self.state().play_action(card))

    def current_draw_cards(self, n: int):
        """
        The current player draws n cards.
        """
        return self.replace_current_state(self.state().draw(n))

    def current_player(self):
        return self.state().player

    def num_players(self) -> int:
        return len(self.playerstates)

    def card_choices(self) -> List[Card]:
        """
        List all the cards that can currently be bought.
        """
        return sorted(
            [
                card
                for (card, count) in self.card_counts.items()
                if count > 0
            ],
            key=lambda card: (card.cost, card.name),
        )

    def remove_card(self, card: Card) -> 'Game':
        """
        Remove a single card from the table.
        """
        new_counts = self.card_counts.copy()
        new_counts[card] -= 1
        assert new_counts[card] >= 0, (card, new_counts[card])
        return Game(
            self.playerstates[:],
            new_counts,
            turn=self.player_turn,
            simulated=self.simulated,
            trash=self.trash + [card],
            total_card_count=self.total_card_count,
        )

    def replace_states(self, newstates):
        """
        Do something with the current player's state and make a new overall
        game state from it.
        """
        newgame = self.copy()
        newgame.playerstates = newstates
        return newgame

    def replace_current_state(self, newstate):
        """
        Do something with the current player's state and make a new overall
        game state from it.
        """
        newgame = self.copy()
        newgame.playerstates[self.player_turn] = newstate
        return newgame

    def change_current_state(self, **changes):
        """
        Make a numerical change to the current player's state, such as adding
        a buy or using up an action. The changes are expressed as deltas from
        the current state.
        """
        return self.replace_current_state(self.state().change(**changes))

    def change_other_states(self, **changes):
        """
        Make a numerical change to the states of all non-current players, the
        same way as change_current_state.
        """
        newgame = self.copy()
        for i in range(self.num_players()):
            if i == self.player_turn: continue
            newgame.playerstates[i] = newgame.playerstates[i].change(**changes)
        return newgame

    def transform_other_states(self, func, attack=False):
        """
        Apply a function to all other states, with no decisions to be made.

        This does not work for attacks, because other players might have a
        counter that requires them to make a decision. Implement attacks using
        the attack_with_decision method instead.
        """
        newgame = self.copy()
        for i in range(self.num_players()):
            if i == self.player_turn: continue
            newgame.playerstates[i] = func(newgame.playerstates[i])
        return newgame

    def next_mini_turn(self):
        """
        Temporarily increase the turn counter, without doing any of the usual
        end-of-turn mechanics.

        This is useful when players need to make decisions in the middle of
        another player's turn, creating what we call here a "mini-turn".
        """
        return Game(
            self.playerstates[:],
            self.card_counts,
            turn=self.turn + 1,
            simulated=self.simulated,
            trash=self.trash,
            total_card_count=self.total_card_count,
        )

    def everyone_else_makes_a_decision(self, decision_template, attack=False):
        newgame = self.next_mini_turn()
        while newgame.player_turn != self.player_turn:
            if attack:
                if newgame.state().is_defended():
                    self.log.info('Player {0} is defended'.format(newgame.state().player))
                    newgame = newgame.next_mini_turn()
                    continue
                reactions = newgame.state().get_reactions()
                for reaction in reactions:
                    newgame = reaction(newgame)
            decision = decision_template(newgame)
            turn = newgame.player_turn
            game2 = newgame.current_player().make_decision(self, decision)
            assert game2.player_turn == turn
            newgame = game2.next_mini_turn()
        return newgame

    def attack_with_decision(self, decision):
        return self.everyone_else_makes_a_decision(decision, attack=True)

    def run_decisions(self):
        """
        Run through all the decisions the current player has to make, and
        return the resulting state.
        """
        state = self.state()
        decisiontype = state.next_decision()
        if decisiontype is None:
            return self
        else:
            decision = decisiontype(self)
            newgame = self.current_player().make_decision(self, decision)
            return newgame.run_decisions()

    def simulated_copy(self):
        """
        Get a copy of this game, but with the `simulated` flag set to True
        and no information that the current player should not have. This
        prevents accidentally cheating when looking at the implications of
        various actions.
        """
        return Game(
            [
                state.simulated_from_here() if state is self.state() else state.simulate()
                for state in self.playerstates
            ],
            self.card_counts,
            turn=self.turn,
            simulated=True,
            trash=self.trash,
            total_card_count=self.total_card_count,
        )

    def simulate_turn(self):
        """
        Run through all the decisions the current player has to make, and
        return the number of coins and buys they end up with. Useful for
        the BigMoney strategy.
        """
        if not self.simulated: self = self.simulated_copy()
        state = self.state()
        decisiontype = state.next_decision()
        if decisiontype is None:
            assert False, "BuyDecision never happened this turn"
        if decisiontype is BuyDecision:
            return (state.hand_value(), state.buys)
        decision = decisiontype(self)
        newgame = self.current_player().make_decision(decision)
        return newgame.simulate_turn()

    def simulate_partial_turn(self):
        """
        Run through all the decisions the current player has to make, and
        return the state where the player buys stuff.
        """
        if not self.simulated: self = self.simulated_copy()
        state = self.state()
        decisiontype = state.next_decision()
        if decisiontype is None:
            assert False, "BuyDecision never happened this turn"
        if decisiontype is BuyDecision:
            return state
        decision = decisiontype(self)
        newgame = self.current_player().make_decision(decision)
        return newgame.simulate_partial_turn()

    def take_turn(self):
        """
        Play an entire turn, including drawing cards at the end. Return
        the game state where it is the next player's turn.
        """
        self.log.info("")
        self.log.info("Round %d / player %d: %s (vp=%d, money_density=%.1f, action_density=%.1f, mean_money=%.1f)" % (
            self.round + 1,
            self.player_turn + 1,
            self.current_player().name,
            self.state().score(),
            self.state().money_density(),
            self.state().action_density(),
            self.state().mean_money_per_turn(),
        ))

        if False:
            self.log.info("%d provinces left" % self.card_counts[Province])

        # Run AI hooks that need to happen before the turn.
        self.current_player().before_turn(self)
        endturn = self.run_decisions()

        next_turn = (self.turn + 1)

        newgame = Game(
            endturn.playerstates[:],
            endturn.card_counts,
            turn=next_turn,
            simulated=self.simulated,
            trash=[],
            total_card_count=None,
        )
        # mutate the new game object since nobody cares yet
        newgame.playerstates[self.player_turn] = newgame.playerstates[self.player_turn].next_turn()

        # Run AI hooks that need to happen after the turn.
        self.current_player().after_turn(newgame)
        #self.assert_no_cards_missing()
        return newgame

    def over(self) -> bool:
        "Returns True if the game is over."
        if self.card_counts[Province] == 0:
            return True
        else:
            zeros = 0
            for count in list(self.card_counts.values()):
                if count == 0: zeros += 1

            if self.num_players() > 4:
                return (zeros >= 4)
            else:
                return (zeros >= 3)

    def assert_no_cards_missing(self) -> None:
        '''
        Make sure no cards 'disappeared'.
        '''

        assert (
            len(self.trash)
            +
            sum(len(state.all_cards()) for state in self.playerstates)
            +
            sum(self.card_counts.values())
            -
            len(STARTING_HAND) * len(self.playerstates)
        ) == self.total_card_count, (
            self.total_card_count,
            len(self.trash) + sum(len(state.all_cards()) for state in self.playerstates) + sum(self.card_counts.values()) - len(STARTING_HAND) * len(self.playerstates),
            self.trash,
            [state.all_cards() for state in self.playerstates],
        )

    def run(self, max_rounds: int = 300) -> Dict[Any, int]:
        """
        Play a game of Dominion. Return a dictionary mapping players to scores.
        """
        game = self
        while not game.over():
            game = game.take_turn()
            assert game.round < max_rounds, 'Game has entered infinite loop?'
        scores = [(state.player, state.score()) for state in game.playerstates]
        self.log.info(
            "End of game (finished_piles: {0})".format(
                [card for (card, count) in game.card_counts.items() if count == 0],
            )
        )

        self.assert_no_cards_missing()

        self.log.info(
            'Finish decks: {0}'.format(
                {
                    state.player: state.card_counts()
                    for state in game.playerstates
                }
            ),
        )
        self.log.info("Scores: %s" % scores)
        return scores

    def __repr__(self) -> str:
        return 'Game%s[%s]' % (str(self.playerstates), str(self.turn))

class Decision(object):
    def __init__(self, game: Game) -> None:
        self.game = game

    def state(self) -> PlayerState:
        return self.game.state()

    def player(self) -> Any:
        return self.game.current_player()

class GainDecision(Decision):
    def __init__(self, game, card: Optional[Card] = None) -> None:
        super().__init__(game)
        self.card = card

    def choose(self, card):
        if self.game.card_counts[card] > 0:
            self.game.card_counts[card] -= 1
            return self.game.replace_current_state(
                self.game.state().gain_cards((self.card,)),
            )
        else:
            return self.game

class MultiDecision(Decision):
    def __init__(self, game, minimum: int = 0, maximum: int = INF) -> None:
        self.min = minimum
        self.max = maximum
        super().__init__(game)

class ActDecision(Decision):
    def choices(self) -> List[Optional[Card]]:
        return [NO_CARD] + [card for card in self.state().hand if card.is_action()]

    def choose(self, card):
        self.game.log.info("%s plays %s" % (self.player().name, card))
        if card is NO_CARD:
            newgame = self.game.change_current_state(
              delta_actions=-self.state().actions
            )
            return newgame
        else:
            newgame = card.perform_action(self.game.current_play_action(card))
            return newgame

    def __str__(self) -> str:
        return "ActDecision (%d actions, %d buys, +%d coins)" %\
          (self.state().actions, self.state().buys, self.state().coins)

class BuyDecision(Decision):
    def coins(self) -> int:
        return self.state().hand_value()

    def buys(self) -> int:
        return self.state().buys

    def choices(self) -> List[Optional[Card]]:
        assert self.coins() >= 0
        value = self.coins()
        return [NO_CARD] + [card for card in self.game.card_choices() if card.cost <= value] 

    def choose(self, card):
        assert card is NO_CARD or isinstance(card, Card), card
        if card is not NO_CARD:
            assert card.cost <= self.coins(), 'This card is too expensive (cost={0}, coins={1})'.format(card.cost, self.coins())
            assert self.game.card_counts[card] > 0, 'This card ({0}) has run out...'.format(card)
        self.game.log.info(
            "{player} buys {cards} (coins={coins}, buys={buys}, hand={hand})".format(
                player=self.player().name,
                cards=card,
                coins=self.coins(),
                buys=self.buys(),
                hand=self.state().hand,
            ),
        )
        state = self.state()
        if card is NO_CARD:
            newgame = self.game.change_current_state(
              delta_buys=-state.buys
            )
            return newgame
        else:
            newgame = self.game.remove_card(card).replace_current_state(
              state.gain(card).change(delta_buys=-1, delta_coins=-card.cost)
            )
            return newgame

    def __str__(self) -> str:
        return "BuyDecision (%d buys, %d coins)" % (self.buys(), self.coins())

class TrashDecision(MultiDecision):
    def choices(self) -> List[Card]:
        return sorted(
            self.state().hand,
            key=lambda card: (not card.is_curse(), card.cost), # Trash curses, then cheapest cards
        )

    def choose(self, choices):
        self.game.log.info("%s trashes %s" % (self.player().name, choices))
        state = self.state()
        for card in choices:
            state = state.trash_card(card)
        return self.game.replace_current_state(state)

    def __str__(self) -> str:
        return "TrashDecision(%s, %s, %s)" % (self.state().hand, self.min, self.max)

class VoluntaryTrashDecision(TrashDecision):
    '''
    Voluntary trash decision (for instance, after playing a Chapel)
    '''
    pass

class ForcedTrashDecision(TrashDecision):
    '''
    Forced trash decision (for instance, after playing an Upgrade).
    '''
    pass

class DiscardDecision(MultiDecision):
    def choices(self) -> List[Card]:
        return sorted(
            self.state().hand,
            key=lambda card: (not card.is_curse(), not card.is_pure_victory(), card.cost), # Discard curses, then (pure) victory cards, then cheapest cards
        )

    def choose(self, choices: List[Card]):
        self.game.log.info("%s discards %s" % (self.player().name, choices))
        state = self.state()
        for card in choices:
            state = state.discard_card(card)
        return self.game.replace_current_state(state)

    def __str__(self) -> str:
        return "DiscardDecision" + str(self.state().hand)
