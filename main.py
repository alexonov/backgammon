from game.components import Board, Move, Colors, SingleMove
from game.gui import TerminalGUI


def main():
    board = Board()
    board.reset()
    # board._dummy_setup(2)

    gui = TerminalGUI()
    gui.show_board(board)

    move = Move(Colors.WHITE, SingleMove(1, 6), SingleMove(6, 11))
    board.do_move(move)
    gui.show_board(board)
    board.do_move(move)
    gui.show_board(board)
    print(board.moves)


if __name__ == '__main__':
    main()