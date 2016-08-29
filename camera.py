from kivy.uix.widget import Widget
from kivy.vector import Vector

"""Module used to contain all of the functions for the game camera.
"""

class Camera(Widget): # Widget to use the pos and size properties automatically

    def __init__(self, camerafunc, anchor=(0, 0), level=None, **kwargs):
        super(Camera, self).__init__(**kwargs)
        self.anchor = anchor # The 0, 0 point of the camera, used when calculating offset, changed when camera is not at 0, 0 absolute memery.
        self.camerafunc = camerafunc
        self.offset = (0, 0)

    def update(self, game):
        # A hack (..) as in __init__ right_stick's size hasn't been __init__
        self.size = game.user_interface.right_stick.size
        self.camerafunc(self, game.player)
        # Math to transform all drawn objects to within the window.
        self.offset = self.anchor[0] - self.x, self.anchor[1] - self.y

# Player is always at center of camera, the most basic and possibly only camera
def center_cam(camera, target):
    diff = Vector(*target.center) - camera.center
    camera.center = Vector(*camera.center) + diff / 2 # Adds slight lag/smoothing

if __name__ == '__main__':
    print('Here comes dat boi.')