"""Оконный интерфейс игры 2048 на pygame."""

from __future__ import annotations

import pygame

from main import (
    DEFAULT_SIZE,
    DEFAULT_TARGET,
    LARGE_SIZE,
    LARGE_TARGET,
    Board,
    Game,
    GameConfig,
)


WINDOW_SIZE = (940, 760)
BACKGROUND = (250, 248, 239)
BOARD_BACKGROUND = (187, 173, 160)
DARK_TEXT = (119, 110, 101)
LIGHT_TEXT = (249, 246, 242)
BUTTON_COLOR = (143, 122, 102)
BUTTON_HOVER = (121, 101, 83)
DISABLED_COLOR = (190, 179, 168)
TILE_COLORS = {
    0: (205, 193, 180),
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
    4096: (60, 58, 50),
}


class GameApp:
    """Меню и игровое окно 2048."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("2048 — оконная игра")
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.fonts = {
            "title": pygame.font.SysFont("dejavusans", 54, bold=True),
            "subtitle": pygame.font.SysFont("dejavusans", 22),
            "button": pygame.font.SysFont("dejavusans", 20, bold=True),
            "small": pygame.font.SysFont("dejavusans", 16),
            "tile": pygame.font.SysFont("dejavusans", 34, bold=True),
        }
        self.running = True
        self.screen_mode = "menu"
        self.game: Game | None = None
        self.paused = False
        self.hammer_mode = False
        self.status_text = "Выберите размер поля."
        self.menu_buttons: dict[str, pygame.Rect] = {}
        self.game_buttons: dict[str, pygame.Rect] = {}
        self.tile_rects: dict[tuple[int, int], pygame.Rect] = {}

    def run(self) -> None:
        while self.running:
            self._handle_events()
            if self.screen_mode == "menu":
                self._draw_menu()
            else:
                self._draw_game()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _handle_key(self, key: int) -> None:
        if self.screen_mode == "menu":
            if key == pygame.K_ESCAPE:
                self.running = False
            return

        directions = {
            pygame.K_LEFT: "a",
            pygame.K_RIGHT: "d",
            pygame.K_UP: "w",
            pygame.K_DOWN: "s",
            pygame.K_a: "a",
            pygame.K_d: "d",
            pygame.K_w: "w",
            pygame.K_s: "s",
        }
        if key in directions:
            self._move(directions[key])
        elif key in (pygame.K_p, pygame.K_SPACE):
            self._toggle_pause()
        elif key == pygame.K_h:
            self._activate_hammer()
        elif key == pygame.K_u:
            self._undo()
        elif key == pygame.K_n:
            self._new_game()
        elif key == pygame.K_ESCAPE:
            self._back_to_menu()

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.screen_mode == "menu":
            for name, rect in self.menu_buttons.items():
                if rect.collidepoint(position):
                    self._menu_action(name)
                    return
            return

        for name, rect in self.game_buttons.items():
            if rect.collidepoint(position):
                self._game_action(name)
                return

        if self.hammer_mode and not self.paused:
            for cell, rect in self.tile_rects.items():
                if rect.collidepoint(position):
                    self._use_hammer(*cell)
                    return

    def _menu_action(self, name: str) -> None:
        if name == "small":
            self._start_game(GameConfig(DEFAULT_SIZE, DEFAULT_TARGET))
        elif name == "large":
            self._start_game(GameConfig(LARGE_SIZE, LARGE_TARGET))
        elif name == "exit":
            self.running = False

    def _game_action(self, name: str) -> None:
        if name == "pause":
            self._toggle_pause()
        elif name == "hammer":
            self._activate_hammer()
        elif name == "undo":
            self._undo()
        elif name == "new":
            self._new_game()
        elif name == "menu":
            self._back_to_menu()

    def _start_game(self, config: GameConfig) -> None:
        self.game = Game(config)
        self.screen_mode = "game"
        self.paused = False
        self.hammer_mode = False
        self.status_text = "Игра началась. Сделайте ход."

    def _move(self, direction: str) -> None:
        if self.game is None or self.paused:
            return
        if self.hammer_mode:
            self.status_text = "Сначала выберите плитку для молотка или отключите его."
            return
        self.status_text = self.game.move(direction)

    def _toggle_pause(self) -> None:
        if self.game is None:
            return
        self.paused = not self.paused
        self.hammer_mode = False
        self.status_text = "Игра продолжена." if not self.paused else "Пауза."

    def _activate_hammer(self) -> None:
        if self.game is None or self.paused:
            return
        if not self.game.hammer_available:
            self.status_text = "Молоток уже использован в этой игре."
            return
        self.hammer_mode = not self.hammer_mode
        self.status_text = "Молоток активирован: выберите плитку." if self.hammer_mode else "Молоток отключён."

    def _use_hammer(self, row: int, column: int) -> None:
        if self.game is None:
            return
        self.status_text = self.game.use_hammer(row, column)
        if not self.game.hammer_available:
            self.hammer_mode = False

    def _undo(self) -> None:
        if self.game is None or self.paused:
            return
        self.hammer_mode = False
        self.status_text = self.game.undo()

    def _new_game(self) -> None:
        if self.game is None:
            return
        self.game.new_game()
        self.paused = False
        self.hammer_mode = False
        self.status_text = "Начата новая игра."

    def _back_to_menu(self) -> None:
        self.screen_mode = "menu"
        self.game = None
        self.paused = False
        self.hammer_mode = False
        self.status_text = "Выберите размер поля."

    def _draw_menu(self) -> None:
        self.screen.fill(BACKGROUND)
        self.menu_buttons = {}
        self._draw_text("2048", self.fonts["title"], DARK_TEXT, (WINDOW_SIZE[0] // 2, 100), center=True)
        self._draw_text(
            "Игра с очками, паузой, отменой хода и молотком",
            self.fonts["subtitle"],
            DARK_TEXT,
            (WINDOW_SIZE[0] // 2, 160),
            center=True,
        )

        self.menu_buttons["small"] = pygame.Rect(300, 245, 340, 62)
        self.menu_buttons["large"] = pygame.Rect(300, 330, 340, 62)
        self.menu_buttons["exit"] = pygame.Rect(370, 535, 200, 52)
        self._draw_button(self.menu_buttons["small"], "Поле 4 × 4   |   Цель 2048")
        self._draw_button(self.menu_buttons["large"], "Поле 5 × 5   |   Цель 4096")
        self._draw_button(self.menu_buttons["exit"], "Выход")

        lines = [
            "Управление в игре:",
            "стрелки или W/A/S/D — движение плиток",
            "P / пробел — пауза, U — отмена, H — молоток",
            "Молоток удаляет одну занятую плитку за игру.",
        ]
        for index, line in enumerate(lines):
            self._draw_text(line, self.fonts["small"], DARK_TEXT, (WINDOW_SIZE[0] // 2, 430 + index * 24), center=True)

    def _draw_game(self) -> None:
        assert self.game is not None
        self.screen.fill(BACKGROUND)
        self.game_buttons = {}
        self.tile_rects = {}
        self._draw_text("2048", self.fonts["title"], DARK_TEXT, (50, 35))
        self._draw_text(
            f"Цель: {self.game.config.target}",
            self.fonts["small"],
            DARK_TEXT,
            (52, 105),
        )
        self._draw_score_box("Очки", self.game.score, pygame.Rect(545, 30, 145, 66))
        self._draw_score_box("Рекорд", self.game.best_score, pygame.Rect(705, 30, 175, 66))

        self._draw_board()
        self._draw_sidebar()
        self._draw_text(self.status_text, self.fonts["small"], DARK_TEXT, (50, 700))
        self._draw_text(
            "Стрелки/WASD — ход   |   P — пауза   |   U — отмена   |   H — молоток",
            self.fonts["small"],
            DARK_TEXT,
            (50, 730),
        )

        if self.paused:
            overlay = pygame.Surface((530, 530), pygame.SRCALPHA)
            overlay.fill((50, 45, 40, 180))
            self.screen.blit(overlay, (45, 145))
            self._draw_text("ПАУЗА", self.fonts["title"], LIGHT_TEXT, (310, 410), center=True)

    def _draw_board(self) -> None:
        assert self.game is not None
        size = self.game.config.size
        board_rect = pygame.Rect(45, 145, 530, 530)
        pygame.draw.rect(self.screen, BOARD_BACKGROUND, board_rect, border_radius=10)
        gap = 10
        tile_size = (530 - gap * (size + 1)) // size
        for row in range(size):
            for column in range(size):
                x = board_rect.x + gap + column * (tile_size + gap)
                y = board_rect.y + gap + row * (tile_size + gap)
                rect = pygame.Rect(x, y, tile_size, tile_size)
                self.tile_rects[(row, column)] = rect
                value = self.game.board.value_at(row, column)
                pygame.draw.rect(self.screen, TILE_COLORS.get(value, (60, 58, 50)), rect, border_radius=7)
                if value:
                    font_size = 34 if value < 1000 else 28
                    font = pygame.font.SysFont("dejavusans", font_size, bold=True)
                    color = DARK_TEXT if value in (2, 4) else LIGHT_TEXT
                    self._draw_text(str(value), font, color, rect.center, center=True)

    def _draw_sidebar(self) -> None:
        assert self.game is not None
        self.game_buttons["pause"] = pygame.Rect(625, 180, 255, 52)
        self.game_buttons["hammer"] = pygame.Rect(625, 245, 255, 52)
        self.game_buttons["undo"] = pygame.Rect(625, 310, 255, 52)
        self.game_buttons["new"] = pygame.Rect(625, 375, 255, 52)
        self.game_buttons["menu"] = pygame.Rect(625, 440, 255, 52)

        self._draw_button(self.game_buttons["pause"], "Продолжить" if self.paused else "Пауза")
        hammer_text = "Молоток: выберите плитку" if self.hammer_mode else f"Молоток ({1 if self.game.hammer_available else 0})"
        hammer_color = BUTTON_HOVER if self.hammer_mode else BUTTON_COLOR
        self._draw_button(
            self.game_buttons["hammer"],
            hammer_text,
            enabled=self.game.hammer_available and not self.paused,
            color=hammer_color,
        )
        self._draw_button(self.game_buttons["undo"], "Отменить ход", enabled=bool(self.game.history) and not self.paused)
        self._draw_button(self.game_buttons["new"], "Новая игра")
        self._draw_button(self.game_buttons["menu"], "В меню")

        hint = "Кликните по занятой плитке" if self.hammer_mode else "Нажмите H или кнопку «Молоток»"
        self._draw_text(hint, self.fonts["small"], DARK_TEXT, (625, 530))

    def _draw_button(
        self,
        rect: pygame.Rect,
        text: str,
        enabled: bool = True,
        color: tuple[int, int, int] = BUTTON_COLOR,
    ) -> None:
        mouse_over = rect.collidepoint(pygame.mouse.get_pos())
        fill = color if enabled and not mouse_over else BUTTON_HOVER if enabled else DISABLED_COLOR
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        text_color = LIGHT_TEXT if enabled else (220, 214, 207)
        self._draw_text(text, self.fonts["button"], text_color, rect.center, center=True)

    def _draw_score_box(self, label: str, value: int, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, BOARD_BACKGROUND, rect, border_radius=7)
        self._draw_text(label.upper(), self.fonts["small"], LIGHT_TEXT, (rect.centerx, rect.y + 17), center=True)
        self._draw_text(str(value), self.fonts["button"], LIGHT_TEXT, (rect.centerx, rect.y + 45), center=True)

    def _draw_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        position: tuple[int, int],
        center: bool = False,
    ) -> None:
        surface = font.render(text, True, color)
        rectangle = surface.get_rect()
        if center:
            rectangle.center = position
        else:
            rectangle.topleft = position
        self.screen.blit(surface, rectangle)
