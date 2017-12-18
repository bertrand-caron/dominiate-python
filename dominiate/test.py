from logging import DEBUG
from random import shuffle
from collections import defaultdict

from game import *
from players import *
from basic_ai import *
from combobot import *
from cards import variable_cards

def compare_bots(bots):
    scores = defaultdict(int)
    for i in range(50):
        shuffle(bots)
        game = Game.setup(bots, variable_cards)
        results = game.run()
        maxscore = 0
        for (bot, score) in results:
            if score > maxscore:
                maxscore = score
        for (bot, score) in results:
            if score == maxscore:
                scores[bot] += 1
                break
    return scores

def test_game():
    player1 = BigMoney()
    player2 = BigMoney()
    #player2.setLogLevel(DEBUG)
    game = Game.setup([player1, player2], variable_cards)
    results = game.run()
    return results

if __name__ == '__main__':
    test_game()
    compare_bots([smithyComboBot, chapelComboBot, HillClimbBot(2, 3, 40)])
