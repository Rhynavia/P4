import pygame


class World:
    def __init__(self):
        self.entities = []

    def add_entity(self, entity):
        self.entities.append(entity)

    def remove_entity(self, entity):
        self.entities.remove(entity)

    def get_entities(self):
        return self.entities

    def update(self, dt):
        for entity in self.entities:
            entity.update(dt)
