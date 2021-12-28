"""
classes to represent the board of the game

board positions go from 1 to 24 to conform to standard backgammon notation
"""
from typing import NamedTuple

MIN_POSITION = 0
MAX_POSITION = 23


def white_to_black(position: int) -> int:
    assert MIN_POSITION <= position <= MAX_POSITION
    return list(range(MIN_POSITION, MAX_POSITION + 1))[-position]


class Colors:
    WHITE = 'white'
    BLACK = 'black'

    @classmethod
    def opponent(cls, color: str):
        if color == cls.BLACK:
            return cls.WHITE
        elif color == cls.WHITE:
            return cls.BLACK
        else:
            raise ValueError


class SingleMove(NamedTuple):
    position_from: int
    position_to: int


class Move(NamedTuple):
    color: str
    first_move: SingleMove
    second_move: SingleMove


class PlacementNotPossibleError(Exception):
    pass


class Checker:
    def __init__(self, color: str, position: int):
        assert MIN_POSITION <= position <= MAX_POSITION, 'Position is out of range'
        self.color = color
        self.point = position


class Slot:
    def __init__(self, white_position: int):
        assert MIN_POSITION <= white_position <= MAX_POSITION, 'Position is out of range'
        self.checkers: list[Checker] = []
        self.position = {
            Colors.WHITE: white_position,
            Colors.BLACK: white_to_black(white_position)
        }

    @property
    def is_empty(self):
        return len(self.checkers) == 0

    @property
    def color(self):
        if self.is_empty:
            return None
        else:
            return self.checkers[-1].color

    def can_place_checker(self, checker: Checker):
        """
        checker can only be placed on an empty slot
        or a slop taken by the same color checker
        """
        return self.color is None or self.color == checker.color

    def place_checker(self, checker: Checker):
        if self.can_place_checker(checker):
            self.checkers.append(checker)
        else:
            raise PlacementNotPossibleError(
                f'Cannot place checker of color {checker.color} into the slot {self.position[checker.color]}')


class Board:
    def __init__(self):
        self._slots = [Slot(i) for i in range(MIN_POSITION, MAX_POSITION + 1)]
        self.slots = {
            Colors.WHITE: [s for s in self._slots],
            Colors.BLACK: [s for s in self._slots[::-1]]
        }
        self.moves = []
        self.checkers = {
            Colors.WHITE: [],
            Colors.BLACK: [],
        }

    def reset(self):
        """
        resets the board for a new game
        """
        self.checkers = {
            Colors.WHITE: [Checker(Colors.WHITE, MAX_POSITION) for _ in range(15)],
            Colors.BLACK: [Checker(Colors.BLACK, MAX_POSITION) for _ in range(15)],
        }

        self.moves = []

    def is_single_move_obstructed(self, color: str, single_move: SingleMove):
        """
        checks if move is not obstructed by enemy's checkers
        """
        slots = self.slots[color]
        try:
            # check if there's a checker
            assert not slots[
                single_move.position_from].is_empty, f'No checker to move in {single_move.position_from}'

            # if not bearing off, check that there's no opponent's checker
            if single_move.position_to <= MAX_POSITION:
                checker_to_move = slots[single_move.position_to].checkers[-1]
                assert slots[single_move.position_to].can_place_checker(
                    checker_to_move), f'Cannot place checker from {single_move.position_from} to {single_move.position_to}'
        except AssertionError:
            return False
        else:
            return True

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

    def do_move(self, move: Move):
        pass
