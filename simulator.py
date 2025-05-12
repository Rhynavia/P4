import pygame
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from random import random
import math
import time
import cv2
import mediapipe as mp
from collections import deque

from pygame.math import Vector2
from blob import Blob, Body
from collections import defaultdict

FPS = 60
HEIGHT = 900
WIDTH = 1600
MAX_PARTICLES = 4000
SPAWN_DELAY = 1000
MAX_PARTICLE_AGE = 10

CELL_SIZE = 50  # Should be >= max particle diameter

def hash_pos(pos: Vector2):
    return int(pos.x // CELL_SIZE), int(pos.y // CELL_SIZE)

def exprandom(m):
    x = random()
    return -m * math.log(x)

def check_and_resolve_collision(a: Body, b: Body):
    delta = b.pos - a.pos
    dist_sq = delta.length_squared()
    radius_sum = a.radius + b.radius

    if dist_sq == 0 or dist_sq >= radius_sum * radius_sum:
        return  # no collision

    dist = dist_sq**0.5
    overlap = radius_sum - dist
    correction = delta.normalize() * (overlap / 2)

    a.pos -= correction
    b.pos += correction



def handle_collisions(bodies: list[Body]):
    grid = defaultdict(list)

    # Fill grid
    for body in bodies:
        key = hash_pos(body.pos)
        grid[key].append(body)

    # Check local neighborhoods
    for key, cell in grid.items():
        neighbors = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                neighbors.extend(grid.get((key[0] + dx, key[1] + dy), []))

        for i, a in enumerate(cell):
            for b in neighbors:
                if a is not b:
                    check_and_resolve_collision(a, b)

def map_to_pixels(coords: Vector2):
    return Vector2(coords.x * WIDTH, coords.y * HEIGHT)

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    gluOrtho2D(0, WIDTH, HEIGHT, 0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.0, 0.0, 0.0, 1.0)

    colors = [
        (255, 36, 2), (255, 0, 114), (255, 133, 0), (255, 225, 20), (148, 255, 0), (9, 7, 255), (244, 0, 255), (255, 255, 255)
    ]
    colorCounter = 0

    # Initialize MediaPipe Pose
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    # Start webcam
    cap = cv2.VideoCapture(0)

    clock = pygame.time.Clock()
    lastTick = pygame.time.get_ticks()
    lastWrist = False
    particles = deque()
    blobs = deque()

    while True:
        dt = clock.tick(FPS) / 1000
        currentTime = time.time()

        glClear(GL_COLOR_BUFFER_BIT)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            if not lastWrist:
                lastWristSpeed = 1
                lastWrist = map_to_pixels(Vector2(landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y))
            wrist = map_to_pixels(Vector2(landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y))
            wristSpeed = wrist - lastWrist
            wristSpeedDir = wristSpeed
            wristSpeed = wristSpeed.magnitude()

            if pygame.time.get_ticks() - lastTick > SPAWN_DELAY / (wristSpeed + 1):
                radius = 300 / (wristSpeed + 1)
                if (radius > 80):
                    blobs.append(Blob(wrist, 16, radius, colors[colorCounter]))
                elif(radius > 1):
                    body = Body(radius, wrist, colors[colorCounter])
                    body.acc = Vector2(wristSpeedDir * 10)
                    particles.append(body)
                lastTick = pygame.time.get_ticks()
                colorCounter = (colorCounter + 1) % len(colors)
            lastWrist = wrist


        particles = deque([
            p for p in particles if currentTime - p.time < MAX_PARTICLE_AGE
        ])

        remove = 0
        for blob in blobs:
            if (currentTime - blob.time > MAX_PARTICLE_AGE):
                remove += 1
                for point in blob.points:
                    body = Body(random()*30, point.pos, blob.color)
                    body.acc = Vector2(random() * 2 - 1, random() * 2 - 1) * 200
                    particles.append(body)
            else:
                blob.update(dt)
                blob.draw()
                for point in blob.points:
                    point.constrain_to_bounds(WIDTH, HEIGHT)
        for i in range(remove):
            blobs.popleft()

        points = []
        for blob in blobs:
            for point in blob.points:
                points.append(point)

        handle_collisions(list(particles) + points)

        for particle in particles:
            elapsedTime = currentTime - particle.time
            particle.update(dt)
            particle.constrain_to_bounds(WIDTH, HEIGHT)
            particle.draw(elapsedTime / MAX_PARTICLE_AGE)
    
        pygame.display.flip()
