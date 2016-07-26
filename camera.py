from kivy.uix.widget import Widget
from kivy.vector import Vector

"""Module used to contain all of the functions for the game camera.
"""

class Camera(Widget): # Widget to use the pos and size properties automatically

    def __init__(self, window_size, camerafunc, level=None, **kwargs):
        super(Camera, self).__init__(**kwargs)
        self.size = window_size
        self.camerafunc = camerafunc
        self.offset = (0, 0)

    def update(self, game):
        self.camerafunc(self, game.player)
        # Math to transform all drawn objects to within the window.
        self.offset = 0 - self.x, 0 - self.y

# Player is always at center of camera, the most basic and possible only camera
def center_cam(camera, target):
	camera.center = target.center
	return None

if __name__ == '__main__':
	print('do jack shit')