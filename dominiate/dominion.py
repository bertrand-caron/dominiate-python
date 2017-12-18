from random import sample as draw_N

from game import *
from players import *
from basic_ai import *
from combobot import *
from cards import BASE_ACTIONS

def human_game():
    player1 = smithyComboBot
    player2 = chapelComboBot
    player3 = HillClimbBot(2, 3, 40)
    player4 = HumanPlayer('You')
    game = Game.setup(
        [player1, player2, player3, player4],
        draw_N(BASE_ACTIONS, 10),
    )
    return game.run()

if __name__ == '__main__':
    human_game()
