from game import *
from players import *
from cards import variable_cards
from collections import defaultdict
import random

def compare_bots(bots):
    scores = defaultdict(int)
    for i in xrange(50):
        random.shuffle(bots)
        game = Game.setup(bots, variable_cards)
        results = game.run()
        maxscore = 0
        for bot, score in results:
            if score > maxscore: maxscore = score
        for bot, score in results:
            if score == maxscore:
                scores[bot] += 1
                break
    return scores

def test_game():
    player1 = SmithyBot(2, 4, 7)
    player2 = Contrafactus(2, 3, 40)
    player3 = DerivBot(100)
    game = Game.setup([player1, player2], variable_cards)
    results = game.run()
    return results

if __name__ == '__main__':
    #print compare_bots([SmithyBot(2, 4, 7), Contrafactus(2, 3, 40)])
    print test_game()

