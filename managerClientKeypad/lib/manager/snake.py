#!/usr/bin/env python3

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: https://h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Affero General Public License, version 3.

# NOTE: This file intentionally only imports stdlib modules and urwid (no relative imports)
# so it can be started directly from the console: python3 lib/manager/snake.py

import collections
import logging
import os
import random
import urwid
from typing import Callable, Deque, List, Optional, Tuple


class SnakeGame:
    """
    Pure game logic of the snake game (does not depend on urwid).
    Coordinates are (x, y) with (0, 0) in the upper left corner.
    """

    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    def __init__(self, width: int = 20, height: int = 10):
        if width < 5 or height < 3:
            raise ValueError("Board has to be at least 5x3.")

        self._width = width
        self._height = height

        self._body = collections.deque()  # type: Deque[Tuple[int, int]]
        self._direction = SnakeGame.RIGHT
        self._pending_direction = SnakeGame.RIGHT
        self._blob = None  # type: Optional[Tuple[int, int]]
        self._is_over = False

        self.reset()

    def _spawn_blob(self) -> bool:
        """
        Places a new blob on a random free cell.
        :return: True if a blob was placed, False if the board is full.
        """
        occupied = set(self._body)
        free_cells = [(x, y)
                      for y in range(self._height)
                      for x in range(self._width)
                      if (x, y) not in occupied]
        if not free_cells:
            self._blob = None
            return False

        self._blob = random.choice(free_cells)
        return True

    @property
    def height(self) -> int:
        return self._height

    @property
    def width(self) -> int:
        return self._width

    def change_direction(self, direction: Tuple[int, int]):
        """
        Sets the direction the snake moves with the next step. A direction directly opposite to the
        direction the snake moved last is ignored (the snake can not reverse into itself).
        :param direction: one of SnakeGame.UP, SnakeGame.DOWN, SnakeGame.LEFT, SnakeGame.RIGHT
        """
        if direction not in (SnakeGame.UP, SnakeGame.DOWN, SnakeGame.LEFT, SnakeGame.RIGHT):
            return

        if (direction[0] + self._direction[0], direction[1] + self._direction[1]) == (0, 0):
            return

        self._pending_direction = direction

    def get_blob(self) -> Optional[Tuple[int, int]]:
        return self._blob

    def get_body(self) -> List[Tuple[int, int]]:
        """
        :return: copy of the snake body, head first
        """
        return list(self._body)

    def is_over(self) -> bool:
        return self._is_over

    def reset(self):
        """
        Starts a new round with a snake of length 3 in the middle of the board moving right.
        """
        center_x = self._width // 2
        center_y = self._height // 2
        self._body = collections.deque([(center_x, center_y),
                                        (center_x - 1, center_y),
                                        (center_x - 2, center_y)])
        self._direction = SnakeGame.RIGHT
        self._pending_direction = SnakeGame.RIGHT
        self._is_over = False
        self._spawn_blob()

    def step(self):
        """
        Moves the snake one cell into the current direction.
        """
        if self._is_over:
            return

        self._direction = self._pending_direction
        head_x, head_y = self._body[0]
        new_head = (head_x + self._direction[0], head_y + self._direction[1])

        # Wall hit.
        if not (0 <= new_head[0] < self._width and 0 <= new_head[1] < self._height):
            self._is_over = True
            return

        grows = (new_head == self._blob)

        # Self hit (the tail cell is free in this step if the snake does not grow since the tail moves away).
        body_to_check = list(self._body) if grows else list(self._body)[:-1]
        if new_head in body_to_check:
            self._is_over = True
            return

        self._body.appendleft(new_head)
        if grows:
            if not self._spawn_blob():
                # Board is full, nothing left to eat.
                self._is_over = True
        else:
            self._body.pop()


class SnakeUrwid:
    """
    urwid view of the snake game. Steered via numpad (8 = up, 2 = down, 4 = left, 6 = right).
    """

    _KEY_DIRECTIONS = {
        "8": SnakeGame.UP,
        "2": SnakeGame.DOWN,
        "4": SnakeGame.LEFT,
        "6": SnakeGame.RIGHT,
        # Fallback for a numpad with NumLock off.
        "up": SnakeGame.UP,
        "down": SnakeGame.DOWN,
        "left": SnakeGame.LEFT,
        "right": SnakeGame.RIGHT,
    }

    def __init__(self,
                 game_over_callback: Optional[Callable[[], None]] = None,
                 width: int = 20,
                 height: int = 10,
                 tick_interval: float = 0.25,
                 game_over_delay: float = 3.0):

        # file name of this file (used for logging)
        self._log_tag = os.path.basename(__file__)

        self._game = SnakeGame(width, height)
        self._game_over_callback = game_over_callback
        self._tick_interval = tick_interval
        self._game_over_delay = game_over_delay

        self._main_loop = None  # type: Optional[urwid.MainLoop]
        self._alarm_handle = None

        self._board = urwid.Text("", align="center")
        self._status = urwid.Text("", align="center")
        hint = urwid.Text("8=up 2=down 4=left 6=right", align="center")

        snake_pile = urwid.Pile([self._board, self._status, hint])
        self._snake_box = urwid.LineBox(snake_pile, title="Snake")

        self._render()

    def _finish(self, loop: urwid.MainLoop, user_data=None):
        self._alarm_handle = None
        if self._game_over_callback is not None:
            self._game_over_callback()

    def _render(self):
        body = self._game.get_body()
        head = body[0]
        body_cells = set(body[1:])
        blob = self._game.get_blob()

        border = "+" + "--" * self._game.width + "+\n"
        markup = [border]
        for y in range(self._game.height):
            markup.append("|")
            for x in range(self._game.width):
                cell = (x, y)
                if cell == head:
                    markup.append(("greenColor", "@@"))
                elif cell in body_cells:
                    markup.append(("greenColor", "##"))
                elif cell == blob:
                    markup.append(("redColor", "()"))
                else:
                    markup.append("  ")
            markup.append("|\n")
        markup.append(border.rstrip("\n"))
        self._board.set_text(markup)

        if self._game.is_over():
            self._status.set_text("Game Over")
        else:
            self._status.set_text("")

    def _tick(self, loop: urwid.MainLoop, user_data=None):
        self._alarm_handle = None
        self._game.step()
        self._render()

        if self._game.is_over():
            logging.debug("[%s]: Snake game over." % self._log_tag)
            self._alarm_handle = loop.set_alarm_in(self._game_over_delay, self._finish)
        else:
            self._alarm_handle = loop.set_alarm_in(self._tick_interval, self._tick)

    def get(self) -> urwid.LineBox:
        """
        This function returns the final urwid widget that is used by the renderer.
        :return:
        """
        return self._snake_box

    def keypress(self, key: str) -> bool:
        """
        Handles a key press.
        :param key: urwid key name
        :return: True if the key was handled
        """
        direction = SnakeUrwid._KEY_DIRECTIONS.get(key)
        if direction is None:
            return False

        self._game.change_direction(direction)
        return True

    def start(self, main_loop: urwid.MainLoop):
        """
        Starts a new round.
        :param main_loop: urwid main loop used to schedule the game ticks
        """
        self.stop()
        self._main_loop = main_loop
        self._game.reset()
        self._render()
        self._alarm_handle = main_loop.set_alarm_in(self._tick_interval, self._tick)

    def stop(self):
        """
        Stops the current round (removes the pending tick without calling the game over callback).
        """
        if self._main_loop is not None and self._alarm_handle is not None:
            self._main_loop.remove_alarm(self._alarm_handle)
        self._alarm_handle = None


def _main():
    def game_over():
        raise urwid.ExitMainLoop()

    snake = SnakeUrwid(game_over_callback=game_over)

    def handle_input(key):
        if key in ("q", "Q", "esc"):
            raise urwid.ExitMainLoop()
        snake.keypress(key)
        return True

    palette = [
        ('redColor', 'black', 'dark red'),
        ('greenColor', 'black', 'dark green'),
    ]

    main_loop = urwid.MainLoop(urwid.Filler(snake.get(), "top"),
                               palette=palette,
                               unhandled_input=handle_input)
    snake.start(main_loop)
    main_loop.run()


if __name__ == "__main__":
    _main()
