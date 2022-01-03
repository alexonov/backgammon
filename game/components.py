"""
classes to represent the board of the game

board positions go from 1 to 24 to conform to standard backgammon notation
"""
import re
from copy import deepcopy
from random import randrange
from typing import NamedTuple

import numpy as np

MIN_POSITION = 1
MAX_POSITION = 24


def norm_index(position):
    """
    convert board point position (from MIN to MAX) to
    absolute normalized position from 0 to 23
    """
    return list(range(MIN_POSITION, MAX_POSITION + 1)).index(position)


def convert_coordinates(position: int) -> int:
    assert MIN_POSITION <= position
    mid_point = MAX_POSITION - 12
    lookup = list(range(mid_point + 1, MAX_POSITION + 1)) + list(
        range(MIN_POSITION, mid_point + 1)
    )
    lookup_ind = norm_index(position)
    return lookup[lookup_ind]


def sorted_inds(l: list, key_func):
    return sorted(range(len(l)), key=lambda k: key_func(l[k]))


class Colors:
    WHITE = 'W'
    BLACK = 'B'

    @classmethod
    def opponent(cls, color: str):
        if color == cls.BLACK:
            return cls.WHITE
        elif color == cls.WHITE:
            return cls.BLACK
        else:
            raise ValueError


class Dice:
    def __init__(self, max_point=6):
        self.max_point = max_point

    def throw(self):
        return randrange(1, self.max_point + 1), randrange(1, self.max_point + 1)


class SingleMove(NamedTuple):
    color: str
    position_from: int
    position_to: int

    def __repr__(self):
        return f'{self.color}:{self.position_from}->{self.position_to}'

    @classmethod
    def generate_from_str(cls, str_move):
        regex = re.compile('^([WB]):(\d*)->(\d*)$')
        m = regex.match(str_move)
        color, position_from, position_to = m.groups()
        return cls(color, int(position_from), int(position_to))

    @property
    def length(self) -> int:
        return self.position_to - self.position_from

    def __eq__(self, other):
        other: SingleMove
        try:
            assert self.color == other.color
            assert self.position_from == other.position_from
            assert self.position_to == other.position_to
        except AssertionError:
            return False
        else:
            return True


class Move(NamedTuple):
    color: str
    first_move: SingleMove
    second_move: SingleMove

    def __repr__(self):
        return f'{self.color}: {self.first_move.position_from}->{self.first_move.position_to}, {self.second_move.position_from}->{self.second_move.position_to}'


class MoveNotPossibleError(Exception):
    pass


class Checker(NamedTuple):
    color: str

    def __repr__(self):
        return f'{self.color} checker'


class Slot:
    def __init__(self, white_position, black_position):
        self.checkers: list[Checker] = []
        self.real_position = white_position
        self.position = {Colors.WHITE: white_position, Colors.BLACK: black_position}

    @classmethod
    def generate_from_position(cls, real_position: int):
        white_position = real_position
        black_position = convert_coordinates(real_position)
        return cls(white_position, black_position)

    @property
    def num_checkers(self):
        return len(self.checkers)

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
        or a slot taken by the same color checker
        """
        return self.is_empty or self.color == checker.color

    def place_checker(self, checker: Checker):
        if self.can_place_checker(checker):
            self.checkers.append(checker)
        else:
            raise MoveNotPossibleError(
                f'Cannot place checker of color {checker.color} into the slot {self.position[checker.color]}'
            )

    def __repr__(self):
        repr = f'Slot {self.real_position}: '
        if self.is_empty:
            return repr + 'empty'
        else:
            return repr + f'{len(self.checkers)} {self.color} checkers'


class Board:
    HOME_POINTS = list(range(MAX_POSITION - 6, MAX_POSITION + 1))
    YARD_POINTS = list(range(MIN_POSITION, MIN_POSITION + 6))
    BOARD_POINTS = list(range(MIN_POSITION, MAX_POSITION + 1))

    BITS_PER_COLOR_SLOT = 2
    ENCODED_SHAPE = (BITS_PER_COLOR_SLOT * 24 * 2 + 2 + 2,)

    def __init__(self):
        self.slots = [Slot.generate_from_position(i) for i in self.BOARD_POINTS]
        self.slot_lookup_dict = {
            Colors.WHITE: [
                i
                for i in sorted_inds(
                    self.slots, key_func=lambda x: x.position[Colors.WHITE]
                )
            ],
            Colors.BLACK: [
                i
                for i in sorted_inds(
                    self.slots, key_func=lambda x: x.position[Colors.BLACK]
                )
            ],
        }
        self.moves = []
        self.off_tray = {
            Colors.WHITE: Slot(MAX_POSITION + 1, MIN_POSITION - 1),
            Colors.BLACK: Slot(MIN_POSITION - 1, MAX_POSITION + 1),
        }

    def deepcopy_with_sharing(self, memo=None):
        """
        Deepcopy an object, except for a given list of attributes, which should
        be shared between the original object and its copy.

        self is some object
        shared_attribute_names: A list of strings identifying the attributes that
            should be shared between the original and its copy.
        memo is the dictionary passed into __deepcopy__.  Ignore this argument if
            not calling from within __deepcopy__.
        """
        shared_attribute_names = ['slot_lookup_dict']

        assert isinstance(shared_attribute_names, (list, tuple))
        shared_attributes = {k: getattr(self, k) for k in shared_attribute_names}

        if hasattr(self, '__deepcopy__'):
            # Do hack to prevent infinite recursion in call to deepcopy
            deepcopy_method = self.__deepcopy__
            self.__deepcopy__ = None

        for attr in shared_attribute_names:
            del self.__dict__[attr]

        clone = deepcopy(self)

        for attr, val in shared_attributes.iteritems():
            setattr(self, attr, val)
            setattr(clone, attr, val)

        if hasattr(self, '__deepcopy__'):
            # Undo hack
            self.__deepcopy__ = deepcopy_method
            del clone.__deepcopy__

        return clone

    def get_slot(self, color: str, position: int):
        try:
            norm_position = norm_index(position)
            ind = self.slot_lookup_dict[color][norm_position]
            return self.slots[ind]
        except (IndexError, ValueError) as e:
            if position > MAX_POSITION:  # color tray
                return self.off_tray[color]
            elif position == MIN_POSITION - 1:  # opposite color tray
                return self.off_tray[Colors.opponent(color)]
            else:
                raise e

    def clear(self):
        for s in self.slots:
            s.checkers = []
        self.moves = []
        for _, s in self.off_tray.items():
            s.checkers = []

    def reset(self):
        """
        resets the board for a new game
        """
        starting_position = ['1[W15]', '13[B15]']
        self.setup_position(starting_position)

    def setup_position(self, positions):
        """
        takes a list representing a position on the board.
        each element is <slot number>[<W or B>:<number of checkers]
        slots can be omitted if empty
        example:
        1[W15] - means on slot 1 there are 15 White checkers
        """
        self.clear()
        mask = re.compile('(\d+)\[([WB])(\d+)]')
        for p in positions:
            m = mask.match(p)
            slot_num, color, checkers_num = m.groups()
            slot = self.get_slot(Colors.WHITE, int(slot_num))
            for _ in range(int(checkers_num)):
                slot.place_checker(Checker(color))

            # norm_ind = norm_index(int(slot_num))
            # for _ in range(int(checkers_num)):
            #     self.slots[norm_ind].place_checker(Checker(color))

    def is_single_move_possible(self, single_move: SingleMove):
        """
        checks if move is physically possible
        only single color can occupy a slot
        """

        slot_from = self.get_slot(single_move.color, single_move.position_from)
        slot_to = self.get_slot(single_move.color, single_move.position_to)
        try:
            # check if it's not "blank" move
            assert (
                single_move.position_from != single_move.position_to
            ), 'Starting and end positions are the same'

            # check if there's a checker
            assert (
                not slot_from.is_empty
            ), f'No checker to move in {single_move.position_from}'

            # check there's a checker of correct color
            assert (
                slot_from.color == single_move.color
            ), f'No checker of color {single_move.color} as position {single_move.position_from}'

            # if not bearing off, check that there's no opponent's checker
            if slot_to is not None:
                checker_to_move = slot_from.checkers[-1]
                assert slot_to.can_place_checker(
                    checker_to_move
                ), f'Cannot place checker from {single_move.position_from} to {single_move.position_to}'
        except AssertionError:
            return False
        else:
            return True

    def do_single_move(self, single_move):
        if self.is_single_move_possible(single_move):
            checker = self.get_slot(
                single_move.color, single_move.position_from
            ).checkers.pop()
            self.get_slot(single_move.color, single_move.position_to).place_checker(
                checker
            )
            self.moves.append(single_move)
        else:
            raise MoveNotPossibleError(
                f'Cannot make move {single_move}, board position: {self.export_position()}'
            )

    def undo_single_move(self, single_move):
        pos_from = single_move.position_to
        pos_to = single_move.position_from
        self.do_single_move(SingleMove(single_move.color, pos_from, pos_to))

    def num_checkers(self, color: str) -> int:
        num = 0
        for s in self.slots:
            if s.color == color:
                num += s.num_checkers
        return num

    def num_checkers_after_position(self, color, position) -> int:
        num = 0
        for p in range(position + 1, MAX_POSITION + 1):
            slot = self.get_slot(color, p)
            if slot.color == color:
                num += slot.num_checkers
        return num

    def num_checkers_before_position(self, color, position) -> int:
        num = 0
        for p in range(MIN_POSITION, position):
            slot = self.get_slot(color, p)
            if slot.color == color:
                num += slot.num_checkers
        return num

    def has_any_checkers_home(self, color: str) -> bool:
        """
        checks if color has ANY checkers home
        """
        for p in self.HOME_POINTS:
            slot = self.get_slot(color, p)
            if not slot.is_empty and slot.color == color:
                return True
        else:
            return False

    def has_all_checkers_home(self, color: str) -> bool:
        """
        checks if color has ALL checkers home
        """
        num_checkers_home = 0
        for p in self.HOME_POINTS:
            slot = self.get_slot(color, p)
            if not slot.is_empty and slot.color == color:
                num_checkers_home += slot.num_checkers

        return num_checkers_home == self.num_checkers(color)

    def find_blocks(self, color):
        """
        finds blocks of checkers of <color>
        """
        blocks = []
        block = []
        for p in self.BOARD_POINTS:
            slot = self.get_slot(color, p)

            # if there's a checker of needed color - save
            if slot.color == color:
                block.append(p)
            # otherwise end current block and if long enough - save. reset
            else:
                blocks.append(block)
                block = []
        return blocks

    def find_blocks_min_length(self, color, min_length):
        """
        finds blocks of checkers of <color> with a least <at_lest_checkers> number of checkers
        """
        blocks = self.find_blocks(color)
        return [b for b in blocks if len(b) >= min_length]

    def find_possible_moves(self, color: str, die_roll: int) -> list[SingleMove]:
        """
        finds all possible (not necessarily legal) moves for a given color and die roll
        """
        moves = []
        for p in self.BOARD_POINTS:
            slot = self.get_slot(color, p)
            position_from = slot.position[color]
            position_to = position_from + die_roll
            possible_move = SingleMove(color, position_from, position_to)
            if self.is_single_move_possible(possible_move):
                moves.append(possible_move)

        return moves

    @property
    def slots_and_tray(self):
        return [*self.slots, self.off_tray[Colors.WHITE], self.off_tray[Colors.BLACK]]

    def export_position(self):
        position = []
        _points_with_checkers = []
        for s in self.slots_and_tray:
            if s.is_empty:
                continue
            point = s.position[Colors.WHITE]
            color = s.color
            num_checkers = s.num_checkers
            position.append(f'{point}[{color}{num_checkers}]')
            _points_with_checkers.append(point)

        # sorting using points
        return [x for _, x in sorted(zip(_points_with_checkers, position))]

    def pip_count(self, color: str) -> int:
        count = 0
        for p in self.BOARD_POINTS:
            slot = self.get_slot(color, p)
            if slot.color == color:
                count += (MAX_POSITION + 1 - p) * slot.num_checkers
        return count

    def encode(self, color_turn):
        """
        encodes the board for learning
        each slot is represented by 1 inputs for each color (total 4 per slot)
         - if no checkers -> 0
         - if 1 checker -> 1
         - if > 1 checkers = n / 15
        additionally two slots for number of white and black checkers in the tray
        n / 15
        also 2 bits to signify whose move it is
        """
        encoded = np.zeros(self.ENCODED_SHAPE)
        BITS_PER_COLOR_SLOT = self.BITS_PER_COLOR_SLOT

        for p in self.BOARD_POINTS:
            ind = p - 1
            slot = self.get_slot(Colors.WHITE, p)
            if slot.color == Colors.WHITE:
                encoded[ind * BITS_PER_COLOR_SLOT] = 1
                if slot.num_checkers > 1:
                    encoded[ind * BITS_PER_COLOR_SLOT + 1] = slot.num_checkers / 15
            elif slot.color == Colors.BLACK:
                encoded[24 * BITS_PER_COLOR_SLOT + ind * BITS_PER_COLOR_SLOT] = 1
                if slot.num_checkers > 1:
                    encoded[
                        24 * BITS_PER_COLOR_SLOT + ind * BITS_PER_COLOR_SLOT + 1
                    ] = (slot.num_checkers / 15)

        # add checkers on the tray
        encoded[BITS_PER_COLOR_SLOT * 24 * 2] = (
            self.off_tray[Colors.WHITE].num_checkers / 15
        )
        encoded[BITS_PER_COLOR_SLOT * 24 * 2 + 1] = (
            self.off_tray[Colors.BLACK].num_checkers / 15
        )

        # whose move it is
        if color_turn == Colors.WHITE:
            encoded[BITS_PER_COLOR_SLOT * 24 * 2 + 2] = 1
        else:
            encoded[BITS_PER_COLOR_SLOT * 24 * 2 + 2 + 1] = 1

        return encoded

    @property
    def is_over(self):
        return (
            self.num_checkers(Colors.WHITE) == 0 or self.num_checkers(Colors.BLACK) == 0
        )

    @classmethod
    def generate_from_hash(cls, hash: str):
        position = [h.strip('\'') for h in hash[1:-1].split(',')]
        board = cls()
        board.setup_position(position)
        return board

    @classmethod
    def generate_from_position(cls, position):
        board = cls()
        board.setup_position(position)
        return board

    def copy_board(self):
        return self.generate_from_position(self.export_position())
