import pygame
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from random import random
import math

from body import Body
from vector import Vector
from world import World

FPS = 120
SIM_MULTIPLIER = 1
SPEED = 1
TIME_STEP = 1 / FPS / SIM_MULTIPLIER * SPEED

PIXEL_HEIGHT = 900
PIXEL_WIDTH = 1600
PIXELS_PER_METER = 100
WIDTH = PIXEL_WIDTH / PIXELS_PER_METER
HEIGHT = PIXEL_HEIGHT / PIXELS_PER_METER
MAX_PARTICLES = 4000
SPAWN_DELAY = 20

def meters_to_pixels(meters):
    return meters * PIXELS_PER_METER

def pixels_to_meters(pixels):
    return pixels / PIXELS_PER_METER

def exprandom(m):
    x = random()
    return -m * math.log(x)


def draw_circle(x, y, radius):
    glBegin(GL_TRIANGLE_FAN)
    glColor3f(0.5, 0.7, 1.0)
    glVertex2f(x, y)
    for i in range(17):
        angle = 2.0 * 3.14159 * i / 16
        dx = radius * math.cos(angle)
        dy = radius * math.sin(angle)
        glVertex2f(x + dx, y + dy)
    glEnd()

def fade_screen(alpha=0.1):
    glColor4f(0.0, 0.0, 0.0, alpha)  # low alpha = longer trails
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(PIXEL_WIDTH, 0)
    glVertex2f(PIXEL_WIDTH, PIXEL_HEIGHT)
    glVertex2f(0, PIXEL_HEIGHT)
    glEnd()



if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((PIXEL_WIDTH, PIXEL_HEIGHT), DOUBLEBUF | OPENGL)
    gluOrtho2D(0, PIXEL_WIDTH, PIXEL_HEIGHT, 0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.0, 0.0, 0.0, 1.0)

    world = World()
    mousePos = Vector(0, 0)
    lastMousePos = False;


    clock = pygame.time.Clock()
    lastTick = pygame.time.get_ticks()


    while True:
        clock.tick(FPS)
    
        world.update(TIME_STEP)

        fade_screen() 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        x, y = pygame.mouse.get_pos()
        mousePos.x, mousePos.y = pixels_to_meters(x), pixels_to_meters(y)
            
        if pygame.time.get_ticks() - lastTick > SPAWN_DELAY:
            radius = 0.025 + exprandom(0.05)
            body = Body(radius, mass=5 * radius, position=mousePos)
            body.velocity = Vector(random() * 10 -5, random() * 10 - 5)
            world.add_entity(body)
            lastTick = pygame.time.get_ticks()

        for particle in world.entities:
            if (lastMousePos):
                if (mousePos.distance_to(particle.position) < 1):
                    particle.apply_force(Vector(mousePos.x - lastMousePos.x, mousePos.y - lastMousePos.y)*100)
            particle.apply_force(particle.velocity * - 2)
            draw_circle(meters_to_pixels(particle.position.x), meters_to_pixels(particle.position.y), meters_to_pixels(particle.radius))

        lastMousePos = Vector(mousePos.x, mousePos.y)
        pygame.display.flip()
