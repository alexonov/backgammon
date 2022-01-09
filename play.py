from game.bot import HeuristicsBot  # noqa
from game.bot import RandomBot  # noqa
from game.components import Colors
from game.hill_model import HillClimberBot  # noqa
from game.match import play_match
from game.match import save_moves
from game.td_model import TDBot


def main():
    moves, score = play_match(
        # white=TDBot(Colors.WHITE),
        black=TDBot(Colors.BLACK),
        show_gui=True,
    )
    save_moves(moves)


if __name__ == '__main__':
    main()
