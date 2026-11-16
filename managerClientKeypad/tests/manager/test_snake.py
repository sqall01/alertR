import collections
from unittest import TestCase

from lib.manager.snake import SnakeGame


class TestSnakeGame(TestCase):

    def _create_game(self) -> SnakeGame:
        game = SnakeGame(10, 6)
        # Put the blob far away so it does not interfere.
        game._blob = (0, 0)
        return game

    def test_move(self):
        """
        Tests that the snake moves one cell per step.
        """
        game = self._create_game()
        head_x, head_y = game.get_body()[0]
        game.step()
        self.assertEqual((head_x + 1, head_y), game.get_body()[0])
        self.assertEqual(3, len(game.get_body()))
        self.assertFalse(game.is_over())

    def test_reversal_ignored(self):
        """
        Tests that reversing into the opposite direction is ignored, also with a buffered turn.
        """
        game = self._create_game()
        head_x, head_y = game.get_body()[0]
        game.change_direction(SnakeGame.LEFT)
        game.step()
        self.assertEqual((head_x + 1, head_y), game.get_body()[0])

        # Pressing up and then left before the next step must not reverse the snake
        # (left is ignored, the snake moves up).
        game.change_direction(SnakeGame.UP)
        game.change_direction(SnakeGame.LEFT)
        game.step()
        self.assertFalse(game.is_over())
        self.assertEqual((head_x + 1, head_y - 1), game.get_body()[0])

    def test_wall_hit(self):
        """
        Tests that hitting a wall ends the game.
        """
        game = self._create_game()
        for _ in range(game.width):
            game.step()
        self.assertTrue(game.is_over())

    def test_self_hit(self):
        """
        Tests that hitting itself ends the game.
        """
        game = self._create_game()
        game._body = collections.deque([(4, 3), (3, 3), (2, 3), (2, 2), (3, 2), (4, 2), (5, 2)])
        game.change_direction(SnakeGame.UP)
        game.step()
        self.assertTrue(game.is_over())

    def test_tail_follow(self):
        """
        Tests that moving into the cell the tail just left does not end the game.
        """
        game = self._create_game()
        game._body = collections.deque([(4, 3), (3, 3), (3, 2), (4, 2)])
        game.change_direction(SnakeGame.UP)
        game.step()
        self.assertFalse(game.is_over())

    def test_eat_blob(self):
        """
        Tests that eating a blob grows the snake and spawns a new blob.
        """
        game = self._create_game()
        head_x, head_y = game.get_body()[0]
        game._blob = (head_x + 1, head_y)
        game.step()
        self.assertEqual(4, len(game.get_body()))
        self.assertEqual((head_x + 1, head_y), game.get_body()[0])
        self.assertIsNotNone(game.get_blob())
        self.assertNotIn(game.get_blob(), game.get_body())
