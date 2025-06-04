import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from random import random, randint
import math
import time
import cv2
import mediapipe as mp
from collections import deque

from pygame.math import Vector2
from blob import Blob, Body
from collections import defaultdict
from utils import load_texture, draw_image
from audioManager import AudioManager
from shaders import load_shader, setup_vertex_data
from consts import *


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

    if delta.magnitude() > 0:
        correction = delta.normalize() * (overlap / 2)

        if not a.imune:
            a.pos -= correction
        if not b.imune:
            b.pos += correction
        a.wave.time_offset = 0

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

    screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL | FULLSCREEN)
    actual_size = pygame.display.get_window_size()
    WIDTH, HEIGHT = actual_size

    gluOrtho2D(0, WIDTH, HEIGHT, 0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.0, 0.0, 0.0, 1.0)
    shader = load_shader()
    setup_vertex_data(shader) 

    colorCounter = 0

    # Initialize MediaPipe Pose
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    imgs = [load_texture("assets/blue.png"), load_texture("assets/green.png"), load_texture("assets/pink.png"), load_texture("assets/white.png"), load_texture("assets/yellow.png"),]
    active_img = randint(0, len(imgs)-1)

    # Start webcam
    cap = cv2.VideoCapture(1)

    clock = pygame.time.Clock()
    lastTick = pygame.time.get_ticks()
    lastWrist = False
    particles = []
    blobs = deque()
    rightHand = Body(100, Vector2(0, 0), (1, 1, 1), True)
    audioManager = AudioManager(particles)
    audioManager.start()

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
        
        glUseProgram(0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
                
            body_width = abs(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x - landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x)*WIDTH
            body_heigth = abs(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y - landmarks[mp_pose.PoseLandmark.LEFT_HIP].y)*HEIGHT
            draw_image(imgs[active_img], landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x*WIDTH, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * HEIGHT, body_width, body_heigth)

            if not lastWrist or landmarks[mp_pose.PoseLandmark.LEFT_WRIST].visibility < 0.5:
                lastWristSpeed = 0
                lastWrist = map_to_pixels(Vector2(landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y))
            wrist = map_to_pixels(Vector2(landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y))
            wristSpeed = wrist - lastWrist
            wristSpeedDir = wristSpeed
            wristSpeed = wristSpeed.magnitude()

            rightHand.pos = map_to_pixels(Vector2(landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y))

            if wristSpeed > 0:
                if pygame.time.get_ticks() - lastTick > SPAWN_DELAY / (wristSpeed):
                    radius = MAX_PARTICLE_RADIUS / (wristSpeed)
                    if (radius > MAX_PARTICLE_RADIUS / 3):
                        blobs.append(Blob(wrist, 16, radius, colors[colorCounter]))
                    elif(radius > 1):
                        body = Body(radius, wrist, colors[colorCounter])
                        body.acc = Vector2(wristSpeedDir * 10)
                        particles.append(body)
                    lastTick = pygame.time.get_ticks()
                    colorCounter = (colorCounter + 1) % len(colors)
            lastWrist = wrist
        else:
            active_img = randint(0, len(imgs)-1)
            rightHand.pos = Vector2(-rightHand.radius, -rightHand.radius)


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

        handle_collisions(list(particles) + points + [rightHand])

        for particle in particles:
            elapsedTime = currentTime - particle.time
            if elapsedTime > MAX_PARTICLE_AGE:
                particles.remove(particle)
                continue
            particle.update(dt)
            particle.constrain_to_bounds(WIDTH, HEIGHT)
            particle.draw(shader, elapsedTime / MAX_PARTICLE_AGE)
        
        # rightHand.draw(shader, dt)
    
        pygame.display.flip()
