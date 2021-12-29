from .components import Board


def is_single_move_legal(self, move: SingleMove):
    """
    checks if move can be legally made
    1. not obstructed
    2. moves in the right direction
    3. not blocking opponent's bear-off completely (unless there's checker at home)
    4. bearing off only allowed if all are ot home
    """
    assert MIN_POSITION < move.position_from, f'position_from is out of range, must be at least {MIN_POSITION}'
    assert MIN_POSITION < move.position_to, f'position_to is out of range, must be at least {MIN_POSITION}'
    pass


def is_move_legal(self, move: Move):
    """
    1. only one take from the head
    2. if bering off overshooting allowed only if there is no other not-bearing-off move
    """