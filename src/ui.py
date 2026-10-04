"""
UI helpers: buttons, panels, text with shadow.
Buttons support keyboard + mouse with hover highlight.
"""
import pygame
from .levels import WHITE, BLACK, YELLOW, CYAN


class Button:
    def __init__(self, rect, text, action, font, color=WHITE,
                 hover_color=YELLOW, bg=(30, 30, 40), hover_bg=(60, 60, 90)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.bg = bg
        self.hover_bg = hover_bg
        self.hovered = False
        self.selected = False

    def draw(self, surface):
        bg = self.hover_bg if (self.hovered or self.selected) else self.bg
        fg = self.hover_color if (self.hovered or self.selected) else self.color

        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        pygame.draw.rect(surface, fg, self.rect, width=2, border_radius=8)

        label = self.font.render(self.text, True, fg)
        surface.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return self.action
        return None


def draw_text(surface, text, font, color, center=None,
              topleft=None, shadow=True):
    if shadow:
        s = font.render(text, True, BLACK)
        if center:
            surface.blit(s, s.get_rect(center=(center[0] + 2, center[1] + 2)))
        elif topleft:
            surface.blit(s, (topleft[0] + 2, topleft[1] + 2))
    t = font.render(text, True, color)
    if center:
        surface.blit(t, t.get_rect(center=center))
    elif topleft:
        surface.blit(t, topleft)
    return t.get_rect(center=center) if center else t.get_rect(topleft=topleft)


def overlay(surface, alpha=160, color=(0, 0, 0)):
    s = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    s.fill((*color, alpha))
    surface.blit(s, (0, 0))