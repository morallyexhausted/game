import unittest

from main import Board, Game, GameConfig


class BoardTests(unittest.TestCase):
    def test_equal_tiles_merge_and_add_score(self):
        board = Board()
        board._cells[0] = [2, 2, 4, 0]

        changed, score = board.move("a")

        self.assertTrue(changed)
        self.assertEqual(score, 4)
        self.assertEqual(board._cells[0], [4, 4, 0, 0])

    def test_tiles_move_in_each_direction(self):
        board = Board()
        board._cells = [
            [0, 0, 0, 2],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]

        board.move("a")
        self.assertEqual(board._cells[0], [2, 0, 0, 0])
        board.move("d")
        self.assertEqual(board._cells[0], [0, 0, 0, 2])
        board.move("s")
        self.assertEqual(board._cells[3][3], 2)
        board.move("w")
        self.assertEqual(board._cells[0][3], 2)

    def test_game_over_when_board_is_full_without_pairs(self):
        board = Board()
        board._cells = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2],
        ]

        self.assertFalse(board.can_move())


class GameTests(unittest.TestCase):
    def test_undo_restores_board_and_score(self):
        game = Game(GameConfig(4, 2048))
        game.board._cells = [
            [2, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        before = [row[:] for row in game.board._cells]

        game.play_command("a")
        self.assertEqual(game.board._cells[0][:2], [4, 0])
        self.assertEqual(game.play_command("u"), "Последний ход отменён.")
        self.assertEqual(game.board._cells, before)
        self.assertEqual(game.score, 0)

    def test_invalid_command_does_not_change_score(self):
        game = Game(GameConfig(4, 2048))
        old_score = game.score

        message = game.play_command("x")

        self.assertIn("Неизвестная команда", message)
        self.assertEqual(game.score, old_score)


if __name__ == "__main__":
    unittest.main()
