"""
Модуль для управления игровыми ресурсами (активами).
Обеспечивает загрузку изображений и звуковых файлов из директории assets.
"""

from pathlib import Path

import pygame

# Абсолютный путь к директории с ресурсами игры
ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def load_image(filename: str, alpha: bool = True) -> pygame.Surface:
    """
    Загружает изображение из папки и оптимизирует его для Pygame.

    :param filename: Имя файла изображения (например, 'player.png').
    :param alpha: Если True, сохраняет прозрачность (convert_alpha),
                  иначе оптимизирует без прозрачности (convert).
    :return: Объект pygame.Surface с загруженным изображением.
    """
    image = pygame.image.load(ASSETS_DIR / filename)
    if alpha:
        return image.convert_alpha()
    return image.convert()


def load_sound(filename: str, volume: float) -> pygame.mixer.Sound:
    """
    Загружает звуковой файл из папки и устанавливает его громкость.

    :param filename: Имя звукового файла (например, 'shoot.mp3').
    :param volume: Уровень громкости звука от 0.0 до 1.0.
    :return: Объект pygame.mixer.Sound.
    """
    sound = pygame.mixer.Sound(ASSETS_DIR / filename)
    sound.set_volume(volume)
    return sound
