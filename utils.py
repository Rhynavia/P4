from OpenGL.GL import *
from pygame.math import Vector2
from math import cos, sin, pi
import pygame
import numpy as np

def snap_to_note(freq, base=440.0):
    # Convert to MIDI-like index
    if freq <= 0:
        return 0.0
    note_index = round(12 * np.log2(freq / base))
    return base * (2 ** (note_index / 12))


def draw_catmull_rom(points: list[Vector2], segments: int = 20, loop: bool = False) -> None:
    if len(points) < 4:
        return  # Need at least 4 points for Catmull-Rom

    glBegin(GL_POLYGON)

    n = len(points)
    for i in range(n):
        p0 = points[i % n]
        p1 = points[(i + 1) % n]
        p2 = points[(i + 2) % n]
        p3 = points[(i + 3) % n]

        for j in range(segments + 1):
            t = j / segments
            t2 = t * t
            t3 = t2 * t

            # Catmull-Rom spline formula
            point = 0.5 * (
                (2 * p1) +
                (-p0 + p2) * t +
                (2*p0 - 5*p1 + 4*p2 - p3) * t2 +
                (-p0 + 3*p1 - 3*p2 + p3) * t3
            )

            glVertex2d(point.x, point.y)

    glEnd()


def drawCircle(center: Vector2, radius: float, points: int = 20):
    glBegin(GL_POLYGON)
    for i in range(points):
        glVertex2d(center.x + cos(pi * 2 * i / points)*radius, center.y + sin(pi * 2 * i / points)* radius)
    glEnd()

def rgb255(r: int, g: int, b: int, a: int = 255) -> tuple[float, float, float, float]:
    return r / 255.0, g / 255.0, b / 255.0, a / 255.0

def load_texture(path: str) -> int:
    image = pygame.image.load(path)
    image = pygame.transform.flip(image, False, True)  # Flip for OpenGL
    image_data = pygame.image.tostring(image, "RGBA", 1)
    width, height = image.get_size()

    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height,
                 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
    
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    return texture_id

def draw_image(texture_id, x, y, width, height):
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glColor4f(1, 1, 1, 1)

    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(x, y)
    glTexCoord2f(1, 0); glVertex2f(x + width, y)
    glTexCoord2f(1, 1); glVertex2f(x + width, y + height)
    glTexCoord2f(0, 1); glVertex2f(x, y + height)
    glEnd()

    glDisable(GL_TEXTURE_2D)


# def fade_screen(alpha=0.1):
#     glColor4f(0.0, 0.0, 0.0, alpha)  # low alpha = longer trails
#     glBegin(GL_QUADS)
#     glVertex2f(0, 0)
#     glVertex2f(WIDTH, 0)
#     glVertex2f(WIDTH, HEIGHT)
#     glVertex2f(0, HEIGHT)
#     glEnd()