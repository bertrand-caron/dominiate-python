from typing import Any

from game import Curse, Estate, Duchy, Province, Copper, Silver, Gold, NO_CARD
from game import Card, TrashDecision, VoluntaryTrashDecision, DiscardDecision, GainDecision, Game

# simple actions
Village = Card('Village', 3, actions=2, cards=1)
Woodcutter = Card('Woodcutter', 3, coins=2, buys=1)
Smithy = Card('Smithy', 4, cards=3)
Festival = Card('Festival', 5, coins=2, actions=2, buys=1)
Market = Card('Market', 5, coins=1, cards=1, actions=1, buys=1)
Laboratory = Card('Laboratory', 5, cards=2, actions=1)

def chapel_action(game: Game) -> Game:
    newgame = game.current_player().make_decision(
        game,
        TrashDecision(game, minimum=0, maximum=4)
    )
    return newgame

def cellar_action(game: Game) -> Game:
    newgame = game.current_player().make_decision(
        game,
        DiscardDecision(game)
    )
    card_diff = game.state().hand_size() - newgame.state().hand_size()
    return newgame.replace_current_state(newgame.state().draw(card_diff))

def warehouse_action(game: Game) -> Game:
    newgame = game.current_player().make_decision(
        game,
        DiscardDecision(game, minimum=3, maximum=3)
    )
    return newgame

def council_room_action(game: Game) -> Game:
    return game.change_other_states(delta_cards=1)

def militia_attack(game: Game) -> Game:
    return game.attack_with_decision(
        lambda game: DiscardDecision(game, minimum=2, maximum=2)
    )

def witch_attack(game: Game) -> Game:
    return game.attack_with_decision(
        lambda game: GainDecision(game, card=Curse)
    )

def throne_room_action(game: Game) -> Game:
    return game

def bridge_action(game: Game) -> Game:
    return game

Chapel = Card('Chapel', 2, effect=chapel_action)
Cellar = Card('Cellar', 2, actions=1, effect=cellar_action)
Warehouse = Card('Warehouse', 3, cards=3, actions=1, effect=warehouse_action)
Council_Room = Card('Council Room', 5, cards=4, buys=1, effect=council_room_action)
Militia = Card('Militia', 4, coins=2, effect=militia_attack)
Moat = Card('Moat', 2, cards=2, isDefense=True)
Throne_Room = Card('Throne Room', 4, actions=1, effect=throne_room_action)
Bridge = Card('Bridge', 4, coins=1, buys=1, effect=bridge_action)
Witch = Card('Witch', 5, cards=2, effect=witch_attack)

BASE_ACTIONS = [
    Village, Cellar, Smithy, Festival, Market, Laboratory,
    Chapel, Warehouse, Council_Room, Militia, Moat,
    Witch,
]
