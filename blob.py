from pygame.math import Vector2, Vector3
from math import cos, sin, pi
from OpenGL.GL import *
from utils import draw_catmull_rom, drawCircle, rgb255
from collections import deque
import time

FRICTION = 0.02
AREA_SCALE = 0.01
MAX_TRAIL_AGE = 0.5

class Blob:
    def __init__(self, origin: Vector2, numPoints: int, radius: float, color: tuple[float, float, float]):
        self.origin = origin
        self.radius = radius
        self.color = color
        self.time = time.time()
        self.points: list[BlobPoint] = []
        self.cordLen = (radius * pi * 2)/numPoints
        self.area = radius ** 2 * pi
        for i in range(numPoints):
            self.points.append(BlobPoint(Vector2(origin.x + cos(2*pi * i / numPoints)*radius, origin.y + sin(2*pi * i/ numPoints) * radius)))
    
    def update(self, dt: float) -> None:
        
        for i in range(len(self.points)):
            cur = self.points[i]
            next = self.points[(i + 1) % len(self.points)]
            if(cur.pos.distance_to(next.pos) > self.cordLen):
                midPoint = (cur.pos + next.pos) / 2
                acc = (midPoint - cur.pos).normalize() * (cur.pos.distance_to(next.pos)-self.cordLen) / 2
                cur.acc += acc 
                next.acc -= acc
        
        areaError = (self.area - self.getArea()) / (self.radius * pi * 2)
        for i in range(len(self.points)):
            prev = self.points[(i - 1) % len(self.points)]
            cur = self.points[i]
            next = self.points[(i + 1) % len(self.points)]
            secant = (next.pos - prev.pos).normalize()
            normal = Vector2(secant.y, -secant.x) * areaError
            cur.acc += normal

        for point in self.points:
            point.update(dt)


    def getArea(self):
        area = 0
        for i in range(len(self.points)):
            cur = self.points[i].pos
            next = self.points[(i+1) % len(self.points)].pos
            area += ((cur.x - next.x) * (cur.y + next.y) / 2);
        return area
    
    def draw(self) -> None:
        glColor4f(*rgb255(self.color[0], self.color[1], self.color[2]))
        draw_catmull_rom([*map(lambda point: point.pos, self.points)])


class BlobPoint:
    def __init__(self, pos: Vector2):
        self.radius = 0
        self.pos: Vector2 = pos
        self.ppos: Vector2 = pos.copy()
        self.acc: Vector2 = Vector2(0, 0)

    def constrain_to_bounds(self, width: int, height: int, bounce: float = 1):
        vel = self.pos - self.ppos

        # Left
        if self.pos.x - self.radius < 0:
            self.pos.x = self.radius
            self.ppos.x = self.pos.x + vel.x * bounce

        # Right
        if self.pos.x + self.radius > width:
            self.pos.x = width - self.radius
            self.ppos.x = self.pos.x + vel.x * bounce

        # Top
        if self.pos.y - self.radius < 0:
            self.pos.y = self.radius
            self.ppos.y = self.pos.y + vel.y * bounce

        # Bottom
        if self.pos.y + self.radius > height:
            self.pos.y = height - self.radius
            self.ppos.y = self.pos.y + vel.y * bounce
    
    def update(self, dt: float) -> None:
        temp = self.pos.copy()
        vel = (self.pos -  self.ppos) * (1-FRICTION)
        self.pos += vel
        self.ppos = temp;
        self.pos += self.acc * dt
        self.acc = Vector2(0, 0)


    def __str__(self):
        return str(self.pos.x) + " " + str(self.pos.y)


class Body:
    def __init__(self, radius: float, pos:  Vector2, color: tuple[float, float, float]):
        self.radius = radius
        self.pos = pos
        self.ppos = pos
        self.acc = Vector2(0, 0)
        self.trail = deque()
        self.time = time.time()
        self.color = color


    def constrain_to_bounds(self, width: int, height: int, bounce: float = 1):
        vel = self.pos - self.ppos

        # Left
        if self.pos.x - self.radius < 0:
            self.pos.x = self.radius
            self.ppos.x = self.pos.x + vel.x * bounce

        # Right
        if self.pos.x + self.radius > width:
            self.pos.x = width - self.radius
            self.ppos.x = self.pos.x + vel.x * bounce

        # Top
        if self.pos.y - self.radius < 0:
            self.pos.y = self.radius
            self.ppos.y = self.pos.y + vel.y * bounce

        # Bottom
        if self.pos.y + self.radius > height:
            self.pos.y = height - self.radius
            self.ppos.y = self.pos.y + vel.y * bounce
    
    def update(self, dt: float):
        current_time = time.time()

        temp = self.pos.copy()
        vel = (self.pos - self.ppos) * (1 - FRICTION)
        self.pos += vel
        self.ppos = temp
        self.pos += self.acc * dt
        self.acc = Vector2(0, 0)

        if (self.pos - self.ppos).length_squared() > 1**2:
            self.time = time.time()
            self.trail.append({
                "pos": self.ppos.copy(),
                "time": current_time
            })

        self.trail = deque([
            p for p in self.trail if current_time - p["time"] < MAX_TRAIL_AGE
        ])

    def draw(self, elapsedTime) -> None:
        glColor(*rgb255(self.color[0], self.color[1], self.color[2], elapsedTime))
        drawCircle(self.pos, self.radius)
        current_time = time.time()

        for particle in self.trail:
            age = current_time - particle["time"]
            t = 1 - (age / MAX_TRAIL_AGE)
            if t <= 0:
                continue
            glColor4f(*rgb255(self.color[0], self.color[1], self.color[2]))
            drawCircle(particle["pos"], self.radius * t)
