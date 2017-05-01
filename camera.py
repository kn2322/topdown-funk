from kivy.uix.widget import Widget
from kivy.vector import Vector

"""Module used to contain all of the functions for the game camera.
"""

class Camera(Widget): # Widget to use the pos and size properties automatically

    def __init__(self, camera_type, anchor=(0, 0), level=None, **kwargs):
        super(Camera, self).__init__(**kwargs)
        self.anchor = anchor # The 0, 0 point of the camera, used when calculating offset, changed when camera is not at 0, 0 absolute memery.

        camera_functions_dict = {
            'center': self.center_cam,
            'static': self.static_cam
                            }

        self.camera_func = camera_functions_dict.get(camera_type, None)
        if not self.camera_func: # Name validation.
            raise ValueError('No camera type {} found.'.format(camera_type))
        self.offset = (0, 0) # offset applied by other entities when accessing camera.

    def update(self, game):
        rs = game.user_interface.right_stick
        # A hack (..) as in __init__ right_stick's size hasn't been __init__
        self.size = Vector(*rs.size) * 1
        self.center = self.camera_func(game)

        #diff = Vector(*game.player.center) - self.center
        #center = Vector(self.center) + diff / 10
        """if rs.touchpos: # Enter the Gungeon style camera.
            center = Vector(self.center) + diff / 10
            touchoffset = Vector(rs.touchpos) - Vector(rs.center) # Where mouse is compared is rightstick center.
            #diff = Vector(touchpos) - self.center
            center = Vector(center) + Vector(touchoffset) / 25
        else: # If touch is not down.
            center = Vector(*self.center) + diff / 15 # Adds slight lag/smoothing
        """
        #self.center = center
        # Math to transform all drawn objects to within the window.
        self.offset = self.anchor[0] - self.x, self.anchor[1] - self.y

    # Player is always at center of camera, the most basic and possibly only camera
    def center_cam(self, game):
        target = game.player
        diff = Vector(*target.center) - self.center
        return Vector(*self.center) + diff / 10 # Adds slight lag/smoothing

    def static_cam(self, game):
        return game.game_map.center

if __name__ == '__main__':
    print('Here comes dat boi.')