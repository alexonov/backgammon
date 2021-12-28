from game.components import Board
from game.gui import TerminalGUI


def main():
    board = Board()
    board.reset()
    # board._dummy_setup(2)

    gui = TerminalGUI()
    gui.show_board(board)


if __name__ == '__main__':
    main()