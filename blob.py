from pygame.math import Vector2
from math import cos, sin, pi
from OpenGL.GL import *
from utils import draw_catmull_rom, drawCircle, rgb255, snap_to_note
from collections import deque
import time
from audioManager import Wave
from shaders import draw_circle_shader
from consts import *


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
                temp = (midPoint - cur.pos)
                if temp.magnitude() > 0:
                    acc = temp.normalize() * (cur.pos.distance_to(next.pos)-self.cordLen) / 2
                    cur.acc += acc 
                    next.acc -= acc
        
        areaError = (self.area - self.getArea()) / (self.radius * pi * 2)
        for i in range(len(self.points)):
            prev = self.points[(i - 1) % len(self.points)]
            cur = self.points[i]
            next = self.points[(i + 1) % len(self.points)]
            secant = (next.pos - prev.pos)
            if secant.magnitude():
                secant = secant.normalize()
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
        glUseProgram(0)
        glColor4f(*self.color, 1)  # Bright red, fully opaque for visibility
        draw_catmull_rom([point.pos for point in self.points], segments=20, loop=True)

class BlobPoint:
    def __init__(self, pos: Vector2):
        self.radius = 0
        self.pos: Vector2 = pos
        self.ppos: Vector2 = pos.copy()
        self.acc: Vector2 = Vector2(0, 0)
        self.imune = False

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
    def __init__(self, radius: float, pos:  Vector2, color: tuple[float, float, float], imune: bool = False):
        self.radius = radius
        self.pos = pos
        self.ppos = pos
        self.acc = Vector2(0, 0)

class BlobPoint:
    def __init__(self, pos: Vector2):
        self.radius = 0
        self.pos: Vector2 = pos
        self.ppos: Vector2 = pos.copy()
        self.acc: Vector2 = Vector2(0, 0)
        self.imune = False
        self.wave = Wave(0, 0)

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
    def __init__(self, radius: float, pos:  Vector2, color: tuple[float, float, float], imune: bool = False):
        self.radius = radius
        self.pos = pos
        self.ppos = pos
        self.acc = Vector2(0, 0)
        self.trail = deque()
        self.time = time.time()
        self.color = color
        self.imune = imune
        self.wave = Wave(0, radius * AREA_SCALE)


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
        raw_freq = vel.magnitude() * 70
        self.wave.frequency = snap_to_note(raw_freq)
        self.pos += vel
        self.ppos = temp
        self.pos += self.acc * dt
        self.acc = Vector2(0, 0)

        if (self.pos - self.ppos).length_squared() > 1**2:
            self.trail.append({
                "pos": self.ppos.copy(),
                "time": current_time
            })

        self.trail = deque([
            p for p in self.trail if current_time - p["time"] < MAX_TRAIL_AGE
        ])

    def draw(self, shader, elapsedTime) -> None:
        if self.imune:
            glUseProgram(0)
            glColor4f(*self.color, 0.1)
            drawCircle(self.pos, self.radius)
        else:
            current_time = time.time()
            for particle in self.trail:
                age = current_time - particle["time"]
                t = 1 - (age / MAX_TRAIL_AGE)
                if t <= 0:
                    continue
                draw_circle_shader(shader, particle["pos"].x, HEIGHT - particle["pos"].y, self.radius*t, time.time() - self.time, self.color, (self.color[0] * 1., self.color[1] * 1., self.color[2] * 1.), (self.color[0]*0.75, self.color[1]*0.75, self.color[2]*0.75), t* (1-elapsedTime))
            draw_circle_shader(shader, self.pos.x, HEIGHT - self.pos.y, self.radius, time.time() - self.time, self.color, (self.color[0] * 1., self.color[1] * 1., self.color[2] * 1.), (self.color[0]*0.75, self.color[1]*0.75, self.color[2]*.75), 1-elapsedTime)

