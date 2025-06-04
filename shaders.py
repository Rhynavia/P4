
import pygame
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
import time
import numpy as np

WIDTH, HEIGHT = 800, 600

VERT_SHADER = """
#version 120

attribute vec2 position;

void main() {
    gl_Position = vec4(position, 0.0, 1.0);
}

"""

def load_shader():
    with open("circle.frag") as f:
        frag_shader = f.read()
    return compileProgram(
        compileShader(VERT_SHADER, GL_VERTEX_SHADER),
        compileShader(frag_shader, GL_FRAGMENT_SHADER)
    )

def setup_vertex_data(shader):
    # Your quad vertices (two triangles)
    vertices = np.array([
        -1.0, -1.0,
         1.0, -1.0,
         1.0,  1.0,
        -1.0, -1.0,
         1.0,  1.0,
        -1.0,  1.0
    ], dtype=np.float32)

    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    pos_loc = glGetAttribLocation(shader, "position")
    glEnableVertexAttribArray(pos_loc)
    glVertexAttribPointer(pos_loc, 2, GL_FLOAT, GL_FALSE, 0, None)

def draw_circle_shader(shader, x, y, r, t, c1, c2, c3, alpha=1.0):
    glUseProgram(shader)
    glUniform2f(glGetUniformLocation(shader, "resolution"), WIDTH, HEIGHT)
    glUniform3f(glGetUniformLocation(shader, "color1"), *c1)  # red-ish
    glUniform3f(glGetUniformLocation(shader, "color2"), *c2)  # teal-ish
    glUniform3f(glGetUniformLocation(shader, "color3"), *c3)  # white
    glUniform1f(glGetUniformLocation(shader, "alpha"), alpha)  # white
    glUniform2f(glGetUniformLocation(shader, "center"), x, y)
    glUniform1f(glGetUniformLocation(shader, "radius"), r)
    glUniform1f(glGetUniformLocation(shader, "time"), t)
    glDrawArrays(GL_TRIANGLES, 0, 6)

def main():
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
    shader = load_shader()
    setup_vertex_data(shader) 
    clock = pygame.time.Clock()
    start = time.time()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        t = time.time() - start
        glClear(GL_COLOR_BUFFER_BIT)

        draw_circle_shader(shader, 400+t*100, 300, 80, t, (255/255,0/255,178/255), (255/255, 0, 114/255), (163/255,0,64/255))
        draw_circle_shader(shader, 600, 200, 50, t + 2, (0.0, 1.0, 0.0), (1.0, 0.0, 1.0), (1.0, 1.0, 1.0))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
