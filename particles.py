from kivy.graphics import Color, Rectangle, Ellipse
from kivy.vector import Vector
from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.widget import Widget
from random import uniform, random
from math import atan2, degrees

class ParticleEmitter1(Widget):

    def __init__(self, lifetime, spawnrate, direction, speed, p_size, color, **kwargs): # accepts either a tuple for random range, or single number.
        super(ParticleEmitter1, self).__init__(**kwargs)
        self.particles = []

        self.source_image = None
        self.lifetime = lifetime
        self.spawnrate = spawnrate
        self.p_direction = direction
        self.p_speed = speed
        self.p_size = p_size
        self.p_color = color

    """Particle list format:
    [t since created, color, size, position, direction, speed]
    Color in rgba
    """
    def tick(self, dt):
        
        self.p_direction = tuple(i+2 for i in self.p_direction)

        for idx, p in enumerate(self.particles):
            if p[0] >= self.lifetime:
                del self.particles[idx]
            p[3] = Vector(*p[3]) + Vector(1, 0).rotate(p[4]) * p[5]
            p[4] += 0 # direction
            p[2] += 1 # size
            p[5] += 0 # speed
            p[0] += 1

        #self.p_speed %= 10

        #self.p_speed += 1


        self.spawn()
        self.draw()
        

    def draw(self):
        self.canvas.clear()
        with self.canvas:
            for p in self.particles:
                Color(rgba=p[1])
                Rectangle(size=(p[2], p[2]), pos=p[3], source=self.source_image)


    def spawn(self):
        for _ in range(self.spawnrate):
            rng = self.rng_value_init
            t = 0
            color = (random(), 1, random(), 0.4) # random colors!
            size = rng(self.p_size)
            pos = (self.x + random() * 20, self.y + random() * 20)
            direction = rng(self.p_direction)
            velocity = rng(self.p_speed)

            new = [t, color, size, pos, direction, velocity]
            self.particles.append(new)

    def rng_value_init(self, value):
        if type(value) in (int, float):
            return value

        elif False:
            raise ValueError('random range: {} in particle system is not valid'.format(value))

        return uniform(*value)

class ParticleEmitter2(Widget):

    def __init__(self, lifetime, spawnrate, direction, speed, p_size, color, **kwargs): # accepts either a tuple for random range, or single number.
        super(ParticleEmitter2, self).__init__(**kwargs)
        self.particles = []
        self.particles2 = []
        self.lifetime2 = 60

        self.source_image = None
        self.lifetime = lifetime
        self.spawnrate = spawnrate
        self.p_direction = direction
        self.p_speed = speed
        self.p_size = p_size
        self.p_color = color
        self.ellapsed = 0 # ellapsed time of emitter

    """Particle list format:
    [t since created, color, size, position, direction, speed]
    Color in rgba
    """
    def tick(self, dt):
        #self.p_direction = tuple(i+2 for i in self.p_direction)
        normal = Vector(1, 0)
        gravity = Vector(*self.pos) - Vector(0, 50) # location of gravity center
        g = 100
        """if self.ellapsed < 70:
            g -= 5
        elif self.ellapsed < 130:
            g += 12.5
        else:
            self.ellapsed = self.ellapsed % 60 + 10"""

        for idx, p in enumerate(self.particles):
            if p[0] >= self.lifetime:
                del self.particles[idx]
            # gravity
            g_magnitude = g / (Vector(*gravity).distance(p[3]) ** 2)
            g_vector = (Vector(*gravity) - Vector(*p[3])) * g_magnitude
            # position
            speed_vec = normal.rotate(p[4]) * p[5]
            total_vec = speed_vec + g_vector
            p[4] = degrees(atan2(total_vec[1], total_vec[0]))
            p[3] = Vector(*p[3]) + total_vec
            # speed
            p[5] += 0
            # direction
            p[4] += 5
            # size
            p[2] += 0
            # time
            p[0] += 1

        for idx, p in enumerate(self.particles2):
        	if p[0] >= self.lifetime2:
        		del self.particles2[idx]
       		p[0] += 1

        if self.ellapsed < 10:
        	self.spawn()
        self.spawn2()
        self.draw()
        self.ellapsed += 1
        

    def draw(self):
        self.canvas.clear()
        with self.canvas:
        	for p in self.particles2:
        		Color(rgba=p[1])
        		Ellipse(size=(p[2], p[2]), pos=p[3])

        with self.canvas:
            for p in self.particles:
                Color(rgba=p[1])
                Ellipse(size=(p[2], p[2]), pos=p[3], source=self.source_image)


    def spawn(self):
        for _ in range(self.spawnrate):
            rng = self.rng_value_init
            t = 0
            color = (random(), random(), random(), 1) # random colors!
            size = rng(self.p_size)
            pos = self.pos
            direction = size * 1.2
            velocity = rng(self.p_speed)

            new = [t, color, size, pos, direction, velocity]
            self.particles.append(new)

    def spawn2(self):
        for i in self.particles:
        	self.particles2.append([0, (1, 0, 0, 1), 3, i[3], 0, 0])

    def rng_value_init(self, value):
        if type(value) in (int, float):
            return value

        elif False:
            raise ValueError('random range: {} in particle system is not valid'.format(value))

        return uniform(*value)

if __name__ == '__main__':
    class ParticleApp(App):

        def build(self):
            Window.size = (1024, 768)
            main = Widget(center=Window.center)
            p = ParticleEmitter1(20, 30, (0, 315), 20, 4, (1, 1, 1, 1), pos=main.center)
            #(720, 1, (6, 25), 10, (3, 20), (1, 1, 1, 1), pos=main.center)
            Clock.schedule_interval(p.tick, 1/30)
            main.add_widget(p)
            return main

    ParticleApp().run()