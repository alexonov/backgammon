from game.bot import HeuristicsBot
from game.bot import RandomBot  # noqa
from game.bot import TDBot
from game.components import Colors
from game.match import play_match
from game.match import save_moves


def main():
    moves, score = play_match(
        white=HeuristicsBot(Colors.WHITE),
        black=TDBot(Colors.BLACK),
        show_gui=True,
    )
    save_moves(moves)


if __name__ == '__main__':
    main()
