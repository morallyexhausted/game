"""Консольная игра 2048 без сторонних библиотек."""

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
    """Хранит поле и выполняет все операции с плитками."""

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

    def copy(self) -> Board:
        """Создаёт копию поля для функции отмены хода."""
        copied_board = Board(self.size, self._rng)
        copied_board._cells = [row[:] for row in self._cells]
        return copied_board

    def add_random_tile(self) -> None:
        """Добавляет 2 (или иногда 4) в случайную свободную клетку."""
        if not self.empty_cells:
            return
        row, column = self._rng.choice(self.empty_cells)
        self._cells[row][column] = 4 if self._rng.random() < 0.1 else 2

    def move(self, direction: str) -> tuple[bool, int]:
        """Сдвигает плитки, возвращая (было ли изменение, сколько очков получено)."""
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
        if not changed:
            return False, 0
        return True, gained_score

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
        """Возвращает красивое текстовое представление поля."""
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


class Game:
    """Игровой цикл, очки, отмена хода и повторная игра."""

    def __init__(self, config: GameConfig, rng: RandomSource | None = None) -> None:
        self.config = config
        self._rng = rng or random
        self.board = Board(config.size, self._rng)
        self.score = 0
        self.best_score = 0
        self.history: list[tuple[Board, int]] = []
        self.won_message_shown = False
        self._start_board()

    def _start_board(self) -> None:
        self.board = Board(self.config.size, self._rng)
        self.score = 0
        self.history.clear()
        self.won_message_shown = False
        for _ in range(START_TILES):
            self.board.add_random_tile()

    def play_command(self, command: str) -> str:
        """Обрабатывает одну команду и возвращает сообщение для пользователя."""
        if command == "u":
            if not self.history:
                return "Отменять пока нечего."
            self.board, self.score = self.history.pop()
            return "Последний ход отменён."

        if command == "n":
            self._start_board()
            return "Начата новая игра."

        if command not in COMMANDS:
            return "Неизвестная команда. Используйте W, A, S, D, U, N или Q."

        previous_board = self.board.copy()
        previous_score = self.score
        changed, gained_score = self.board.move(command)
        if not changed:
            return "В эту сторону сдвинуть плитки нельзя."

        self.history.append((previous_board, previous_score))
        self.score += gained_score
        self.best_score = max(self.best_score, self.score)
        self.board.add_random_tile()
        return self._state_message()

    def _state_message(self) -> str:
        if self.board.has_won(self.config.target) and not self.won_message_shown:
            self.won_message_shown = True
            return f"Поздравляем! Вы собрали {self.config.target}. Можно продолжить игру."
        if not self.board.can_move():
            return "Ходы закончились. Нажмите N для новой игры или Q для выхода."
        return "Ход принят."

    def run(self) -> None:
        print("\n=== 2048 ===")
        print(f"Соберите плитку {self.config.target}.")

        while True:
            print("\n" + self.board.render())
            print(f"Очки: {self.score} | Рекорд: {self.best_score}")
            print("W/A/S/D — ход, U — отмена, N — новая игра, Q — выход")
            command = input("Команда: ").strip().lower()
            if command == "q":
                print("Спасибо за игру!")
                return
            print(self.play_command(command))


def choose_config() -> GameConfig:
    print("Выберите размер поля:")
    print("1 — 4x4, цель 2048")
    print("2 — 5x5, цель 4096")
    while True:
        choice = input("Ваш выбор: ").strip()
        if choice == "1":
            return GameConfig(DEFAULT_SIZE, DEFAULT_TARGET)
        if choice == "2":
            return GameConfig(LARGE_SIZE, LARGE_TARGET)
        print("Введите 1 или 2.")


def main() -> None:
    try:
        Game(choose_config()).run()
    except (KeyboardInterrupt, EOFError):
        print("\nИгра завершена.")


if __name__ == "__main__":
    main()
