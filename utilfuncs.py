from kivy.vector import Vector
from math import hypot

"""Module used to contain utility functions used for processing in the game.
"""

# deltay/deltax distance calculations
def difference(pos1, pos2):
    return (pos2[0] - pos1[0], pos2[1] - pos1[1])

# For graphics components, returns the sprite facing direction.
def get_direction(angle):
    if -22.5 < angle <= 22.5:
        return 'right'
    elif 22.5 < angle <= 67.5:
        return 'downright'
    elif 67.5 < angle <= 112.5:
        return 'down'
    elif 112.5 < angle <= 157.5:
        return 'downleft'
    elif 157.5 < angle <= 180 or -180 <= angle < -157.5:
        return 'left'
    elif -157.5 <= angle < -112.5:
        return 'upleft'
    elif -112.5 <= angle < -67.5:
        return 'up'
    elif -67.5 <= angle < -22.5:
        return 'upright'
    else:
        # idk why this exists.
        raise ValueError('The angle {} is out of bounds.'.format(angle))

# For circular collision detection
def circle_collide(a, b):
    return hypot(*difference(a.center, b.center)) <= a.width + b.width

# Gets x, y direction towards target.
def get_dir_to(entity, other):
        delta = difference(entity.center, other.center)
        angle = atan2(delta[1], delta[0])
        x = cos(angle)
        y = sin(angle)
        return [x, y]

if __name__ == '__main__':
	print('To shreds, you say?')