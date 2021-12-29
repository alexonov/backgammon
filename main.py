from game.components import Board, Move, Colors, SingleMove
from game.gui import TerminalGUI
from pathlib import Path


def test_position():
    # file = 'bearingoff_position.pos'
    file = 'test_position.pos'

    with open(Path('data') / file, 'r') as f:
        data = f.readlines()
    board = Board()
    board.setup_position(data)
    gui = TerminalGUI()
    gui.show_board(board)


def main():
    board = Board()
    board.reset()

    gui = TerminalGUI()
    gui.show_board(board)

    move_1 = SingleMove(Colors.WHITE, 1, 6)
    move_2 = SingleMove(Colors.WHITE, 6, 9)
    board.do_single_move(move_1)
    gui.show_board(board)
    board.do_single_move(move_2)
    gui.show_board(board)
    print(board.moves)


if __name__ == '__main__':
    # main()
    test_position()