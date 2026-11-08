"""Основная логика игры 2048."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Protocol


DEFAULT_SIZE = 4
DEFAULT_TARGET = 2048
LARGE_SIZE = 5
LARGE_TARGET = 4096
START_TILES = 2
COMMANDS = {"w", "a", "s", "d"}


class RandomSource(Protocol):
    """Минимальный интерфейс генератора случайных чисел."""

    def choice(self, values: list[tuple[int, int]]) -> tuple[int, int]: ...

    def random(self) -> float: ...


class Board:
    """Хранит поле и выполняет операции с плитками."""

    def __init__(self, size: int = DEFAULT_SIZE, rng: RandomSource | None = None) -> None:
        self.size = size
        self._cells = [[0] * size for _ in range(size)]
        self._rng = rng or random

    @property
    def empty_cells(self) -> list[tuple[int, int]]:
        return [
            (row, column)
            for row in range(self.size)
            for column in range(self.size)
            if self._cells[row][column] == 0
        ]

    def value_at(self, row: int, column: int) -> int:
        """Возвращает значение плитки для отображения в интерфейсе."""
        return self._cells[row][column]

    def copy(self) -> Board:
        """Создаёт копию поля для отмены хода."""
        copied_board = Board(self.size, self._rng)
        copied_board._cells = [row[:] for row in self._cells]
        return copied_board

    def add_random_tile(self) -> None:
        """Добавляет 2 (или иногда 4) в случайную свободную клетку."""
        if not self.empty_cells:
            return
        row, column = self._rng.choice(self.empty_cells)
        self._cells[row][column] = 4 if self._rng.random() < 0.1 else 2

    def remove_tile(self, row: int, column: int) -> bool:
        """Удаляет плитку молотком и сообщает, был ли ход успешным."""
        if not (0 <= row < self.size and 0 <= column < self.size):
            return False
        if self._cells[row][column] == 0:
            return False
        self._cells[row][column] = 0
        return True

    def move(self, direction: str) -> tuple[bool, int]:
        """Сдвигает плитки и возвращает (изменение, полученные очки)."""
        if direction not in COMMANDS:
            return False, 0

        old_cells = [row[:] for row in self._cells]
        gained_score = 0

        for line_number in range(self.size):
            coordinates = self._line_coordinates(line_number, direction)
            old_line = [self._cells[row][column] for row, column in coordinates]
            new_line, line_score = self._merge_line(old_line)
            gained_score += line_score
            for (row, column), value in zip(coordinates, new_line):
                self._cells[row][column] = value

        changed = self._cells != old_cells
        return changed, gained_score if changed else 0

    def has_won(self, target: int = DEFAULT_TARGET) -> bool:
        return any(value >= target for row in self._cells for value in row)

    def can_move(self) -> bool:
        if self.empty_cells:
            return True

        for row in range(self.size):
            for column in range(self.size):
                value = self._cells[row][column]
                if column + 1 < self.size and value == self._cells[row][column + 1]:
                    return True
                if row + 1 < self.size and value == self._cells[row + 1][column]:
                    return True
        return False

    def render(self) -> str:
        """Возвращает текстовое представление поля для отладки и консоли."""
        width = max(4, max((len(str(value)) for row in self._cells for value in row), default=1))
        border = "+" + "+".join("-" * (width + 2) for _ in range(self.size)) + "+"
        rows = [border]
        for row in self._cells:
            values = [f"{value:>{width}}" if value else " " * width for value in row]
            rows.append("| " + " | ".join(values) + " |")
            rows.append(border)
        return "\n".join(rows)

    def _line_coordinates(self, line_number: int, direction: str) -> list[tuple[int, int]]:
        if direction == "a":
            return [(line_number, column) for column in range(self.size)]
        if direction == "d":
            return [(line_number, column) for column in range(self.size - 1, -1, -1)]
        if direction == "w":
            return [(row, line_number) for row in range(self.size)]
        return [(row, line_number) for row in range(self.size - 1, -1, -1)]

    @staticmethod
    def _merge_line(line: list[int]) -> tuple[list[int], int]:
        """Сжимает одну строку и объединяет соседние одинаковые плитки."""
        non_zero = [value for value in line if value]
        merged: list[int] = []
        score = 0
        index = 0

        while index < len(non_zero):
            if index + 1 < len(non_zero) and non_zero[index] == non_zero[index + 1]:
                value = non_zero[index] * 2
                merged.append(value)
                score += value
                index += 2
            else:
                merged.append(non_zero[index])
                index += 1

        return merged + [0] * (len(line) - len(merged)), score


@dataclass(frozen=True)
class GameConfig:
    size: int
    target: int


@dataclass
class GameSnapshot:
    board: Board
    score: int
    hammer_available: bool
    won_message_shown: bool


class Game:
    """Правила игры, очки, отмена хода и молоток."""

    def __init__(self, config: GameConfig, rng: RandomSource | None = None) -> None:
        self.config = config
        self._rng = rng or random
        self.best_score = 0
        self.history: list[GameSnapshot] = []
        self.board = Board(config.size, self._rng)
        self.score = 0
        self.hammer_available = True
        self.won_message_shown = False
        self.new_game()

    def new_game(self) -> None:
        """Начинает раунд, сохраняя рекорд текущего запуска."""
        self.board = Board(self.config.size, self._rng)
        self.score = 0
        self.history.clear()
        self.hammer_available = True
        self.won_message_shown = False
        for _ in range(START_TILES):
            self.board.add_random_tile()

    def move(self, direction: str) -> str:
        """Обрабатывает ход клавишами W/A/S/D."""
        if direction not in COMMANDS:
            return "Неизвестное направление. Используйте W, A, S или D."

        snapshot = self._snapshot()
        changed, gained_score = self.board.move(direction)
        if not changed:
            return "В эту сторону сдвинуть плитки нельзя."

        self.history.append(snapshot)
        self.score += gained_score
        self.best_score = max(self.best_score, self.score)
        self.board.add_random_tile()
        return self._state_message()

    def use_hammer(self, row: int, column: int) -> str:
        """Удаляет одну выбранную плитку, если молоток ещё доступен."""
        if not self.hammer_available:
            return "Молоток уже использован в этой игре."
        if not (0 <= row < self.config.size and 0 <= column < self.config.size):
            return "Выберите клетку на игровом поле."
        if self.board.value_at(row, column) == 0:
            return "Выберите занятую клетку."

        snapshot = self._snapshot()
        self.board.remove_tile(row, column)
        self.history.append(snapshot)
        self.hammer_available = False
        return self._state_message()

    def undo(self) -> str:
        """Отменяет последний обычный ход или использование молотка."""
        if not self.history:
            return "Отменять пока нечего."

        snapshot = self.history.pop()
        self.board = snapshot.board
        self.score = snapshot.score
        self.hammer_available = snapshot.hammer_available
        self.won_message_shown = snapshot.won_message_shown
        return "Последний ход отменён."

    @property
    def is_game_over(self) -> bool:
        return not self.board.can_move()

    def play_command(self, command: str) -> str:
        """Оставляет простой текстовый интерфейс для проверки логики."""
        if command == "u":
            return self.undo()
        if command == "n":
            self.new_game()
            return "Начата новая игра."
        return self.move(command)

    def _snapshot(self) -> GameSnapshot:
        return GameSnapshot(
            board=self.board.copy(),
            score=self.score,
            hammer_available=self.hammer_available,
            won_message_shown=self.won_message_shown,
        )

    def _state_message(self) -> str:
        if self.board.has_won(self.config.target) and not self.won_message_shown:
            self.won_message_shown = True
            return f"Поздравляем! Вы собрали {self.config.target}. Можно продолжить игру."
        if self.is_game_over:
            return "Ходы закончились. Используйте молоток или начните новую игру."
        return "Ход принят."


def main() -> None:
    """Запускает оконный интерфейс."""
    from gui import GameApp

    GameApp().run()


if __name__ == "__main__":
    main()
