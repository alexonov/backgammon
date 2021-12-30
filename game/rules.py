"""
Main rules:
    1. bearing off only if all home
    2. overshooting bearing off only if no other non-bear-off move

    3. only once from the head unless first move
    4. not blocking 6 in a row (unless there's a checker in front)
    5. play both dice when possible
    6. if only one die can be played - play biggest

"""
import copy

from game.components import Board
from game.components import Colors
from game.components import convert_coordinates
from game.components import MAX_POSITION
from game.components import MIN_POSITION
from game.components import SingleMove


def opponent(color: str) -> str:
    return Colors.WHITE if color == Colors.BLACK else Colors.BLACK


def rule_six_block(board: Board, move: list[SingleMove]) -> bool:
    """
    not blocking 6 in a row (unless there's a checker in front)
    """

    fake_board = copy.deepcopy(board)
    for m in move:
        fake_board.do_single_move(m)

    # check if there are 6-blocks after the move
    blocks = fake_board.find_blocks_min_length(move[-1].color, 6)
    if len(blocks) == 0:
        return True

    opponent_color = opponent(move[-1].color)

    # check each block if it can be legally allowed
    for b in blocks:
        # take last position
        last_position = b[-1]

        # convert it to opponent's coordinates
        last_position_opponent = convert_coordinates(last_position)
        num_checkers = fake_board.num_checkers_after_position(
            opponent_color, last_position_opponent
        )

        if num_checkers == 0:
            return False
    else:
        return True


def is_single_move_legal(board: Board, move: SingleMove):
    """
    checks if move can be legally made
    0. move is possible
    1. not blocking 6 in a row (unless there's a checker in front)
    2. bearing off only allowed if all are ot home
    """
    try:
        assert board.is_single_move_possible(move), 'Move is not possible'

        if move.position_to > MAX_POSITION:
            assert board.has_all_checkers_home(
                move.color
            ), 'Cannot bear off until all checkers are home'
    except AssertionError:
        return False
    else:
        return True


def find_single_legal_moves(board: Board, color: str, die_roll: int):
    """
    finds all legal moves for a die roll

    if bearing off, overshooting allowed only if there is no other not-bearing-off move
    """
    # 1. get all possible moves
    moves = board.find_possible_moves(color, die_roll)

    # 2. check basic rules
    moves = [m for m in moves if is_single_move_legal(board, m)]

    # check overshooting bear-off moves (position_to > 25)
    # these moves are only allowed when no non-bear-off moves are left
    # TODO: check this rule
    tray_position = MAX_POSITION + 1

    min_position_to = min(m.position_to for m in moves)

    # if there are non-bear-off moves - remove all overshooting
    if min_position_to < tray_position:
        moves = [m for m in moves if not m.position_to > tray_position]

    return moves


def find_complete_legal_moves(board: Board, color: str, dice_roll: tuple[int, int]):
    """
    finds all complete legal moves for dice roll

    4. play both dice when possible
    5. only once from the head per move
    6. if only one die can be played - play second from the head (?)
    7. if only one die can be played - play biggest
    """
    # check if double
    if dice_roll[0] == dice_roll[1]:
        dice_roll *= 2

    def _find_combos(the_board, dice):
        first_roll = dice[0]
        moves = find_single_legal_moves(the_board, color, first_roll)

        # reached last die
        if len(dice) == 1:
            return moves
        else:
            result = []
            for m in moves:
                fake_board = copy.deepcopy(the_board)
                fake_board.do_single_move(m)
                rest_of_moves = _find_combos(fake_board, dice[1:])
                for r in rest_of_moves:
                    if type(r) == list:
                        result.append([m, *r])
                    else:
                        result.append([m, r])
            return result

    complete_moves: list[list[SingleMove]] = _find_combos(board, dice_roll)

    # 1. first move allows for taking twice from the head
    def _num_from_head(moves: list[SingleMove]) -> int:
        num = 0
        for m in moves:
            if m.position_from == MIN_POSITION:
                num += 1
        return num

    # 1. only once from the head unless first move
    first_slot = board.get_slot(color, 1)

    if first_slot.num_checkers != 15:
        # if not first move - take from the head only once
        complete_moves = [m for m in complete_moves if _num_from_head(m) < 2]

    # 2. not blocking 6 in a row (unless there's a checker in front)
    complete_moves = [m for m in complete_moves if rule_six_block(board, m)]

    # 3. play both dice when possible
    # filter out moves with incomplete moves
    max_times_move = max(len(m) for m in complete_moves)
    complete_moves = [m for m in complete_moves if len(m) == max_times_move]

    # 4. if only one die can be played - play biggest
    if max_times_move == 1:
        biggest_die = max(dice_roll)
        complete_moves = [m for m in complete_moves if m[0].length == biggest_die]

    return complete_moves


def win_condition(board: Board, color: str):
    """
    checks if any color has won
    """
    if board.num_checkers(color) == 0:
        if board.has_all_checkers_home(opponent(color)):
            return 1
        else:
            # mars
            return 2
    else:
        return None
