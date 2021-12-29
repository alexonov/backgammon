from .components import Board, SingleMove, Colors


def is_single_move_legal(self, color, move: SingleMove, last_move: SingleMove):
    """
    checks if move can be legally made
    1. not blocking opponent's bear-off completely (unless there's checker at home)
    2. bearing off only allowed if all are ot home
    3. if bering off overshooting allowed only if there is no other not-bearing-off move
    4. only one take from the head
    """

    # 1. not blocking opponent's bear-off completely (unless there's checker at home)
    # if there's a checker home then skip this check
    if