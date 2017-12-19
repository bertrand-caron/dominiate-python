from logging import DEBUG
from random import shuffle
from collections import defaultdict
from argparse import ArgumentParser, Namespace
from cProfile import runctx as profile_run
from pstats import Stats
from os import devnull
from contextlib import redirect_stdout

from game import *
from players import *
from basic_ai import *
from combobot import *
from cards import BASE_ACTIONS

def compare_bots(bots, n: int = 2):
    scores = {bot: 0 for bot in bots}
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

def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument('--profile', action='store_true')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    if args.profile:
        profile_file = '.profile'
        with open(devnull, 'w') as null:
            with redirect_stdout(null):
                profile_run(
                    'compare_bots([WitchBot(), MoatBot()], n=10)',
                    {},
                    dict(compare_bots=compare_bots, WitchBot=WitchBot, MoatBot=MoatBot),
                    filename=profile_file,
                )
        stats = Stats(profile_file).sort_stats('cumtime')
        stats.print_stats()

    #test_game()
    print(compare_bots([WitchBot(), MilitiaBot()], n=2))
    print(compare_bots([WitchBot(), SmithyBot()], n=2))
    print(compare_bots([MoatBot(), SmithyBot()], n=2))
    print(compare_bots([MoatBot(), WitchBot()], n=2))
    #compare_bots([BigMoney(), SmithyBot(), HillClimbBot(2, 3, 40)])
    #compare_bots([smithyComboBot, chapelComboBot, HillClimbBot(2, 3, 40)])
