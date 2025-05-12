import sys
import random
import cv2
import mediapipe as mp
import pygame
import math
import numpy as np

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800 * 2, 600 * 2))
pygame.display.set_caption("Wrist & Elbow Tracker")
clock = pygame.time.Clock()

width, height = screen.get_size()
lineColor = (255, 0, 0)  # Red color for lines

# Surface for persistent drawing (with alpha)
draw_surface = pygame.Surface((width, height), pygame.SRCALPHA)

# Surface for particles
particle_surface = pygame.Surface((width, height), pygame.SRCALPHA)

# head surface
head_surface = pygame.Surface((width, height), pygame.SRCALPHA)

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Load a brush texture with transparency
brush = pygame.image.load("brush.png").convert_alpha()
brush_size = brush.get_width()  # assuming it's square

# Start webcam
cap = cv2.VideoCapture(0)

def map_coords(x, y):
    return int(x * width), int(y * height)

def tint_brush(brush, color, width):
    # Scale the brush to the desired width
    scale_factor = width / brush.get_width()
    scaled_size = int(brush.get_width() * scale_factor)
    scaled_brush = pygame.transform.smoothscale(brush, (scaled_size, scaled_size))

    # Tint the brush
    tinted_brush = scaled_brush.copy()
    tint_surface = pygame.Surface(tinted_brush.get_size(), pygame.SRCALPHA)
    tint_surface.fill(color)
    tinted_brush.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    return tinted_brush

def draw_brush_line(surf, start, end, brush, color, width):
    tinted_brush = tint_brush(brush, lineColor, width)
    brush_size = tinted_brush.get_width()

    dx = end[0] - start[0]
    dy = end[1] - start[1]
    distance = int(math.sqrt(dx ** 2 + dy ** 2)/5);

    for i in range(distance):
        x = int(start[0] + dx * i / distance)
        y = int(start[1] + dy * i / distance)
        surf.blit(tinted_brush, (x - brush_size // 2, y - brush_size // 2))

last_points = {
    mp_pose.PoseLandmark.LEFT_WRIST: None,
    mp_pose.PoseLandmark.LEFT_ELBOW: None,
    mp_pose.PoseLandmark.LEFT_SHOULDER: None,
    mp_pose.PoseLandmark.LEFT_HIP: None,
    mp_pose.PoseLandmark.LEFT_KNEE: None,
    mp_pose.PoseLandmark.LEFT_ANKLE: None,
    mp_pose.PoseLandmark.RIGHT_WRIST: None,
    mp_pose.PoseLandmark.RIGHT_ELBOW: None,
    mp_pose.PoseLandmark.RIGHT_SHOULDER: None,
    mp_pose.PoseLandmark.RIGHT_HIP: None,
    mp_pose.PoseLandmark.RIGHT_KNEE: None,
    mp_pose.PoseLandmark.RIGHT_ANKLE: None,
}

def draw_line(landmarks, lm_name):
    lm = landmarks[lm_name]
    if lm.visibility < 0.75:
        return

    x, y = map_coords(lm.x, lm.y)
    if last_points[lm_name]:
        last_x, last_y = last_points[lm_name]
        draw_brush_line(draw_surface, (last_x, last_y), (x, y), brush, lineColor, 20)

    last_points[lm_name] = (x, y)

def draw_arm_lines(landmarks, side):
    if side == "right":
        draw_line(landmarks, mp_pose.PoseLandmark.RIGHT_WRIST)
        draw_line(landmarks, mp_pose.PoseLandmark.RIGHT_ELBOW)
        draw_line(landmarks, mp_pose.PoseLandmark.RIGHT_SHOULDER)
        draw_line(landmarks, mp_pose.PoseLandmark.RIGHT_HIP)
        draw_line(landmarks, mp_pose.PoseLandmark.RIGHT_KNEE)
        draw_line(landmarks, mp_pose.PoseLandmark.RIGHT_ANKLE)
    elif side == "left":
        draw_line(landmarks, mp_pose.PoseLandmark.LEFT_WRIST)
        draw_line(landmarks, mp_pose.PoseLandmark.LEFT_ELBOW)
        draw_line(landmarks, mp_pose.PoseLandmark.LEFT_SHOULDER)
        draw_line(landmarks, mp_pose.PoseLandmark.LEFT_HIP)
        draw_line(landmarks, mp_pose.PoseLandmark.LEFT_KNEE)
        draw_line(landmarks, mp_pose.PoseLandmark.LEFT_ANKLE)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            cap.release()
            pygame.quit()
            sys.exit()

    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb_frame)


    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark

        # Calculate the middle of the body
        middle_x = int((landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x + landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x) / 2 * frame.shape[1])
        middle_y = int((landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y + landmarks[mp_pose.PoseLandmark.LEFT_HIP].y) / 2 * frame.shape[0])

        # Get the color of the pixel at the middle of the body
        pixel_color = frame[middle_y, middle_x]  # BGR format
        lineColor = (pixel_color[2], pixel_color[1], pixel_color[0])  # Convert to RGB format

        draw_arm_lines(landmarks, "right")
        draw_arm_lines(landmarks, "left")

        pygame.draw.circle(head_surface, (255, 0, 0), map_coords(landmarks[mp_pose.PoseLandmark.NOSE].x, landmarks[mp_pose.PoseLandmark.NOSE].y), 50)
        for i in range(2):
            max_x = map_coords(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y)[0]
            min_x = map_coords(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y)[0]
            max_y = map_coords(landmarks[mp_pose.PoseLandmark.LEFT_HIP].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP].y)[1]
            min_y = map_coords(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y)[1]
            if min_x > max_x:
                min_x, max_x = max_x, min_x
            if min_y > max_y:
                min_y, max_y = max_y, min_y
            x = np.random.normal(0.5, 0.2, 1)[0] * (max_x - min_x) + min_x
            y = np.random.normal(0.5, 0.2, 1)[0] * (max_y - min_y) + min_y

            size = random.randint(1, 10)
            pygame.draw.circle(particle_surface, (255, 255, 255), (x, y), size)

    # Slightly fade the draw_surface by drawing a transparent black rectangle
    draw_surface.fill((0, 0, 0, 1), special_flags=pygame.BLEND_RGBA_SUB)

    # fade the particle surface
    particle_surface.fill((0, 0, 0, 5), special_flags=pygame.BLEND_RGBA_SUB)

    head_surface.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_SUB)

    screen.fill((0, 0, 0))  # Optional: fill background black
    screen.blit(draw_surface, (0, 0))
    screen.blit(particle_surface, (0, 0))
    screen.blit(head_surface, (0, 0))
    pygame.display.flip()
    clock.tick(30)
