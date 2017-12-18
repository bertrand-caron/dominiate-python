from game import *
from players import *
from basic_ai import *
from combobot import *
from cards import variable_cards

def human_game():
    player1 = smithyComboBot
    player2 = chapelComboBot
    player3 = HillClimbBot(2, 3, 40)
    player4 = HumanPlayer('You')
    game = Game.setup([player1, player2, player3, player4], variable_cards[-10:])
    return game.run()

if __name__ == '__main__':
    human_game()
