from vector import Vector

class Body:
    def __init__(self, radius: float, position:  Vector):
        self.radius = radius
        self.position = position
        self.velocity = Vector(0, 0)
        self.force = Vector(0, 0)
    
    def update(self, dt: float):
        self.position += self.velocity * dt

        if self.mass > 0:
            acceleration = self.force
            self.velocity += acceleration * dt
            self.force = Vector(0, 0)
    
    def apply_force(self, force: Vector):
        self.force += force
