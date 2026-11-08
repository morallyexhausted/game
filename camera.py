"""
Камера плавно следует за игроком, удерживая его в центре экрана,
и ограничивает свой обзор границами игровой карты.
"""

from settings import HEIGHT, WIDTH
from utils import clamp


class Camera:
    """
    Класс камеры, определяющий смещение отрисовки игрового мира относительно экрана.
    """

    def __init__(self):
        """
        Инициализирует камеру в начале координат (0.0, 0.0).
        """
        self.x = 0.0
        self.y = 0.0

    def update(self, target: "Player", game_map: "GameMap") -> None:
        """
        Обновляет положение камеры, центрируя её на игроке
        и не позволяя ей выходить за пределы игровой карты.

        :param target: Объект, за которым следует камера (должен иметь свойства x и y).
        :param game_map: Объект игровой карты (должен иметь свойства width и height).
        """
        # Вычисляем идеальное положение камеры для центрирования игрока
        self.x = target.x - WIDTH // 2
        self.y = target.y - HEIGHT // 2

        # Ограничиваем координаты камеры размерами карты
        self.x = clamp(self.x, 0, max(0, game_map.width - WIDTH))
        self.y = clamp(self.y, 0, max(0, game_map.height - HEIGHT))
