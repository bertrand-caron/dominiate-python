from logging import DEBUG
from random import shuffle
from collections import defaultdict

from game import *
from players import *
from basic_ai import *
from combobot import *
from cards import BASE_ACTIONS

def compare_bots(bots, n: int = 2):
    scores = defaultdict(int)
    for i in range(n):
        shuffle(bots)
        game = Game.setup(bots, BASE_ACTIONS)
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
    game = Game.setup([player1, player2], BASE_ACTIONS)
    results = game.run()
    return results

if __name__ == '__main__':
    print(compare_bots([WitchBot(), SmithyBot()], n=5))
    print(compare_bots([MoatBot(), SmithyBot()], n=5))
    print(compare_bots([MoatBot(), WitchBot()], n=5))
    #test_game()
    #compare_bots([BigMoney(), SmithyBot(), HillClimbBot(2, 3, 40)])
    #compare_bots([smithyComboBot, chapelComboBot, HillClimbBot(2, 3, 40)])
