from .board import Board


def test_board_setup():
    board = Board()
    assert len(board.slots) == 24
    assert len(board.checkers) == 0
    assert len(board.white_checkers) == 0
    assert len(board.black_checkers) == 0

    board.reset()
    assert len(board.checkers) == 30
    assert len(board.white_checkers) == 15
    assert len(board.black_checkers) == 15
