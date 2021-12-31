from pathlib import Path

from game.components import Board
from game.gui import TerminalGUI
from game.match import play_match
from game.match import Players


def position():
    # file = 'bearingoff_position.pos'
    file = 'test_position.pos'
    # file = 'rule_six_block_position.pos'

    with open(Path('data') / file, 'r') as f:
        data = f.readlines()
    board = Board()
    board.setup_position(data)
    gui = TerminalGUI()
    gui.show_board(board)


def main():
    play_match(white=Players.AI, black=Players.AI)


if __name__ == '__main__':
    main()
    # position()
