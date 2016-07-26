from kivy.vector import Vector
from kivy.graphics import Ellipse
from math import sin, cos

"""Module used to contain all of the character components in the game
"""
class HeroInputComponent:

    def __init__(self):
        # Same one as the one in left stick, used for reference by physics.
        # This is not encapsulated and decoupled, use caution.
        # Decimal distance of moving stick from border
        self.touch_distance = 0

    def update(self, entity, game):
        left_stick = game.left_stick
        angle = left_stick.angle
        self.touch_distance = left_stick.touch_distance
        # TODO: variable speed
        # The 'ratios' of the x and y velocities in a circle with r of 1.
        x = cos(angle)
        y = sin(angle)
        # Merely tells physics the direction, not the full velocity, which is processed more.
        entity.components['Physics'].direction = [x, y]

class HeroPhysicsComponent:

    def __init__(self):
        self.direction = [0, 0]
        # Pixels/s is the intended value,
        self.speed_multiplier = 200

    def update(self, entity, game):
        if entity.components['Input'].touch_distance <= .2:
            # Ensures the hero does not 'slide'
            entity.velocity = 0, 0
            return None
        # Multiply 'direction' with speed and divide by 60 for updates per second.
        entity.velocity = [i * self.speed_multiplier / 60
                             for i in self.direction]

    # Called in action component to allow 'Postprocessing'.
    # Changed to return to allow for it to be used 
    def move(self, entity, game):
        bounds = game.map_size
        next_pos = Vector(*entity.pos) + Vector(*entity.velocity)
        outx, outy = entity.pos
        # Compares x and y borders individually to allow sliding along the border.
        if (0 < next_pos.x) and (next_pos.x + entity.width < bounds[0]):
            outx = next_pos.x

        if (0 < next_pos.y) and (next_pos.y + entity.height < bounds[1]):
            outy = next_pos.y

        return outx, outy
    # TODO: Add displacement/knockback

# Job is to contain the graphical elements of the entity,
# and handle drawing with the camera.
class HeroGraphicsComponent:

    def __init__(self, entity):
        self.graphics = Ellipse(size=entity.size)
    
    # Mostly handled by .kv lang, jk
    def update(self, entity, game):
        offset = game.camera.offset
        draw_pos = Vector(*entity.pos) + Vector(*offset)
        self.graphics.pos = draw_pos

        entity.canvas.clear()
        entity.canvas.add(self.graphics)

class HeroActionComponent:

    def __init__(self):
        # Functions/Objects which contain active effects, their duration,
        self.effects = []

    def update(self, entity, game):
        for effect in self.effects:
            # Have faith in the effects not lingering...
            effect(entity)
        entity.pos = entity.components['Physics'].move(entity, game)