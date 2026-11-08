"""
Модуль навигации и поиска пути для игры.
Реализует сетку навигации (NavGrid) и алгоритм поиска кратчайшего пути A* (AStarPathfinder).
Используется врагами для обхода стен и препятствий при преследовании игрока.
"""

from settings import NAV_CELL_SIZE, NAV_OBSTACLE_PADDING, NAV_SEARCH_RADIUS

# Бесконечность для алгоритма A*
INF = 10**9


from typing import List, Tuple, Optional, Set, Dict

class NavGrid:
    """
    Класс сетки навигации, представляющий карту в виде сетки проходимых/непроходимых ячеек.
    """

    def __init__(self, world_width: int, world_height: int) -> None:
        """
        Инициализирует сетку навигации на основе размеров игрового мира.

        :param world_width: Ширина игрового мира в пикселях.
        :param world_height: Высота игрового мира в пикселях.
        """
        self.cell_size = NAV_CELL_SIZE
        self.cols = world_width // NAV_CELL_SIZE + 1
        self.rows = world_height // NAV_CELL_SIZE + 1
        # Двумерный массив флагов блокировки ячеек (True — стена или препятствие)
        self.blocked = [[False] * self.cols for _ in range(self.rows)]

    def world_to_cell(self, x: float, y: float) -> Tuple[int, int]:
        """
        Преобразует мировые координаты (пиксели) в индексы ячейки сетки (колонку и строку).

        :param x, y: Мировые координаты.
        :return: Кортеж (col, row) индексов ячейки.
        """
        cx = int(x // self.cell_size)
        cy = int(y // self.cell_size)
        cx = max(0, min(cx, self.cols - 1))
        cy = max(0, min(cy, self.rows - 1))
        return cx, cy

    def cell_to_world(self, cell: Tuple[int, int]) -> Tuple[float, float]:
        """
        Преобразует индексы ячейки сетки в мировые координаты её центра (в пикселях).

        :param cell: Кортеж (col, row) индексов ячейки.
        :return: Кортеж (x, y) мировых координат центра ячейки.
        """
        cx, cy = cell
        half = self.cell_size / 2
        return cx * self.cell_size + half, cy * self.cell_size + half

    def is_walkable(self, cell: Tuple[int, int]) -> bool:
        """
        Проверяет, является ли ячейка проходимой для врагов.

        :param cell: Кортеж (col, row) индексов ячейки.
        :return: True, если ячейка проходима и находится в границах сетки.
        """
        cx, cy = cell
        if cx < 0 or cy < 0 or cx >= self.cols or cy >= self.rows:
            return False
        return not self.blocked[cy][cx]

    def neighbors(self, cell: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Возвращает список проходимых соседних ячеек (по 4 направлениям).

        :param cell: Кортеж (col, row) текущей ячейки.
        :return: Список кортежей соседних проходимых ячеек.
        """
        cx, cy = cell
        deltas = ((1, 0), (-1, 0), (0, 1), (0, -1))
        return [
            (cx + dx, cy + dy)
            for dx, dy in deltas
            if self.is_walkable((cx + dx, cy + dy))
        ]

    def closest_walkable(self, cell: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Находит ближайшую проходимую ячейку в некотором радиусе, если целевая ячейка заблокирована.
        Предотвращает зависание поиска пути, если игрок или зомби оказались внутри стены.

        :param cell: Исходная ячейка (col, row).
        :return: Ближайшая проходимая ячейка или None, если таковая не найдена.
        """
        if self.is_walkable(cell):
            return cell
        cx, cy = cell
        # Поиск по спирали в пределах заданного радиуса
        for r in range(1, NAV_SEARCH_RADIUS):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    cand = (cx + dx, cy + dy)
                    if self.is_walkable(cand):
                        return cand
        return None

    def rebuild_from_map(self, game_map: "GameMap") -> None:
        """
        Перестраивает сетку проходимости на основе стен игровой карты.
        Добавляет безопасный отступ (padding) вокруг стен, чтобы круглые тела врагов не застревали в углах.

        :param game_map: Объект игровой карты.
        """
        self.blocked = [[False] * self.cols for _ in range(self.rows)]
        padding = NAV_OBSTACLE_PADDING * 2
        for wall in game_map.walls:
            # Раздуваем прямоугольник стены на величину отступа
            padded = wall.inflate(padding, padding)
            x1, y1 = self.world_to_cell(padded.left, padded.top)
            x2, y2 = self.world_to_cell(padded.right, padded.bottom)
            # Помечаем все ячейки под раздутой стеной как непроходимые
            for cy in range(y1, y2 + 1):
                for cx in range(x1, x2 + 1):
                    self.blocked[cy][cx] = True


class AStarPathfinder:
    """
    Класс поиска кратчайшего пути на графе по алгоритму A* (A-star).
    """

    @staticmethod
    def _heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
        """
        Манхэттенское расстояние в качестве эвристической(оценочной) функции для A*.
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def find_path(
        self, navgrid: NavGrid, start: Tuple[int, int], goal: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """
        Находит кратчайший путь от стартовой ячейки до целевой.

        :param navgrid: Объект сетки навигации NavGrid.
        :param start: Стартовая ячейка (col, row).
        :param goal: Целевая ячейка (col, row).
        :return: Список ячеек (координат сетки) от старта до финиша или пустой список, если путь не найден.
        """
        # Корректируем точки старта и финиша на ближайшие проходимые ячейки
        start = navgrid.closest_walkable(start)
        goal = navgrid.closest_walkable(goal)
        if start is None or goal is None:
            return []

        open_set = {start}  # Множество ячеек для исследования
        came_from = {}  # Словарь для восстановления пути (родительские ячейки)

        # Стоимость пути от старта до текущей ячейки
        g_score = {start: 0}
        # Полная оценочная стоимость пути через ячейку (g_score + эвристика)
        f_score = {start: self._heuristic(start, goal)}

        while open_set:
            # Выбираем ячейку с наименьшим значением f_score
            current = min(open_set, key=lambda c: f_score.get(c, INF))
            open_set.remove(current)

            # Если цель достигнута, строим и возвращаем путь
            if current == goal:
                return self._build_path(came_from, current)

            # Исследуем соседей текущей ячейки
            for neighbor in navgrid.neighbors(current):
                new_g = g_score[current] + 1
                if new_g >= g_score.get(neighbor, INF):
                    continue  # Этот путь не лучше предыдущих

                came_from[neighbor] = current
                g_score[neighbor] = new_g
                f_score[neighbor] = new_g + self._heuristic(neighbor, goal)
                open_set.add(neighbor)

        return []  # Путь не найден

    @staticmethod
    def _build_path(
        came_from: Dict[Tuple[int, int], Tuple[int, int]], current: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """
        Восстанавливает путь, проходя в обратном направлении от цели к старту.

        :param came_from: Словарь родительских связей ячеек.
        :param current: Конечная ячейка.
        :return: Список ячеек в правильном порядке (от старта к цели).
        """
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path
