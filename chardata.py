from kivy.vector import Vector
from kivy.graphics import Ellipse, Color, Rectangle, PushMatrix, PopMatrix, Rotate
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.image import Image as CoreImage # For loading graphics properly
from math import sin, cos, atan2, hypot, degrees
from utilfuncs import circle_collide, difference
from abilitydata import DamageInfo, Cooldown, Invincibility, SuperSpeed, SpeedUp
from entity import Entity
from functools import partial
from constants import UPDATE_RATE
import random

"""Module used to contain all of the character components in the game
"""

class InputComponent:
    pass

class PhysicsComponent:

    def __init__(self): # Pls call super()... every time it's subclassed
        # direction is a value received from the input component indicating direction of movement.
        self.direction = Vector(0, 0)
        self.total_velocity = [0, 0] # imperative movement + displacement.
        self.can_collide_wall = True
        self.can_fly = False
        """
        # The controlled movement velocity.
        self.c_velocity = [0, 0]
        """

    def update(self, entity, game):
        self.move(entity, game)

    # Called in action component to allow 'Postprocessing'. RESOLVED with get_value()
    # next_pos is a universal moving interface that checks for map boundaries when moving an entity.
    # This could be moved to entity container, and call individual entity behaviour when e.g. hitting the walls.
    def temp_move(self, entity, next_pos, map_size):
        bounds = map_size
        outx, outy = entity.pos
        # Compares x and y borders individually to allow sliding along the border.
        if 0 > next_pos.x:
            outx = 0
        elif next_pos.x + entity.width > bounds[0]:
            outx = bounds[0] - entity.width
        else:
            outx = next_pos.x

        if 0 > next_pos.y:
            outy = 0
        elif next_pos.y + entity.height > bounds[1]:
            outy = bounds[1] - entity.height
        else:
            outy = next_pos.y

        entity.pos = outx, outy

    """ Moved to entity container.
    # For the physics interactions with colliding entity.
    def collide_entity(self, entity, other, entity_container): # Returns next position.
        return self.separate(entity, other)
    """

    """Returns next_pos where objects don't intersect, recommend to call this first
    in collision resolving.
    """
    """ Moved to entity container
    def separate(self, entity, other):
        v = self.total_velocity # Total, adding displacement and imperative movement.
        
        Theory, find the amount to add to the currrent entity position so that
        it is exactly colliding with the other using circle_collide,
        which is hypot(*difference(a.center, b.center)) == a.width + b.width.
        In an eqn where x is the coefficient (time) for the total velocity so that it
        fulfills the exact collision. NOT WORKING

        New, calculate overlapping distance by subtracting distance of two entities from the sum of
        the radii. Then move back by the current direction * depth.
        
        diff = difference(entity.pos, other.pos)
        depth = (entity.width + other.width) / 2 - hypot(*diff) # Overlapping distance
        min_pv = Vector(*diff).normalize() * depth # Min penetrating vector using current velocity vector (not actually minimum)
        next_pos = Vector(*entity.pos) + (v - min_pv)
        return next_pos
    """

    # Wall colliding behaviour, default from entity container is to do nothing.
    def collide_wall(self, entity, entity_container):
        pass

    def move(self, entity, game):
        get_value = entity.components['Action'].get_value
        multiplier = get_value(entity, 'velocity_multiplier')
        # Multiply 'direction' with speed and divide by UPDATE_RATE for updates per second.
        if self.direction:
            controlled_movement = Vector(self.direction) * (multiplier / UPDATE_RATE)
        else:
            controlled_movement = Vector(0, 0)
        displacement = entity.velocity
        self.total_velocity = Vector(*controlled_movement) + displacement
        next_pos = Vector(*entity.pos) + self.total_velocity

        # Reducing displacment vector based on friction.
        entity.velocity *= (1 - entity.friction/UPDATE_RATE) if displacement.length() > 0.01 else 0 # Prevent infinitely close to 0.
        #entity.velocity *= 1 / ((2 / UPDATE_RATE) * displacement.length() + 1) # Diminishing returns, moved to player.

        entity.pos = next_pos

        # Checks for collision with all types, keeps recalculating physics until there are no more collisions,
        # makes entity move up to the border of an entity it collides with, while the collision funcs define behaviour afterwards.

        """ Moved to collision engine (entity container)
        # This block is currently bugged beyond belief.

        e_container = game.e_container
        
        for e in e_container.children:
            
            if circle_collide(entity, e):
                # Resolves the physics portion of the collision.
                next_pos = self.collide_entity(entity, e, e_container)
                
                # Collide for both entities MUST be called, otherwise your own collision will only be called when you move.
                entity.components['Action'].collide(entity, e, e_container)
                e.components['Action'].collide(e, entity, e_container)
        """

    # if cant_collide: return False else: return True is the way this should be used, called with an all().
    def can_collide(self, entity, other, entity_container):
        return True # Can be physically resolved, called in entity container.
        
# Convert center pos to actual pos for canvas instructions.
def center_to_pos(size, pos):
    return Vector(*pos) - Vector(*size) / 2

class GraphicsComponent:

    image = '' # Main image path, must be implemented in children.

    def __init__(self):
        self.graphics = None

    # Not handled by kv lang bc it's not explicit enough for update loop.
    def update(self, entity, game):
        entity.canvas.clear()
        if not game.camera.collide_widget(entity):
            return None
        self.graphics = self.update_graphics(entity)

        # Apply camera offset
        offset = game.camera.offset
        draw_pos = Vector(*entity.pos) + Vector(*offset)

        # Not using instruction group because iterating over it is not working.
        # Iterates because container of graphical elements is iterable.

        entity.canvas.add(PushMatrix()) # Allows rotations!
        for i in self.graphics:
            # The position of the instruction of a coordinate space of (0, 0)-(width, height) which is then offsetted by camera.
            # Works because draw_pos accounted for the original position of the entity.
            try:
                i.pos = Vector(center_to_pos(i.size, i.pos)) + draw_pos
            except AttributeError: # For matrices, color, etc.
                if type(i) == Rotate:
                    i.origin = Vector(*entity.size) / 2 + draw_pos # Rotation needs to be adjusted by camera offset as well.
            entity.canvas.add(i)
        entity.canvas.add(PopMatrix())

    # the graphics can be altered without copying the entire update function.
    # Contains the graphical information of the entity
    # Color() at the beginning of each set of instructions is needed, rotation is needed as well.
    def update_graphics(self, entity):
        # The default
        g = [Color()]
        g.append(Ellipse(size=entity.size, pos=(entity.width/2,entity.height/2)))
        return g

    def fit_image(self, entity, image_obj): # Scaling image to entity size while keeping aspect ratio. Goes larger than entity, not smaller.
        v = Vector(*image_obj.size).normalize()
        ratio = entity.width / min(v)
        image_size = v * ratio
        return image_size

    def rotate_angle(self, vector): # Used to get correct angle for Rotate instruction, input is [x, y] direction.
        return degrees(atan2(vector[1], vector[0])) - 90

class ActionComponent:

    def __init__(self):
        # Functions/Objects which contain active effects, their duration,
        self.effects = []

    def update(self, entity, game):
        if entity.hp <= 0:
            # Destroy is provisional here, exp and other systems have not been added.
            self.destroy(entity, game)
        for effect in self.effects:
            effect.time_step()
            if effect.duration <= 0:
                self.effects.remove(effect)

    def destroy(self, entity, game):
        game.player.receive_exp(entity.exp) # Giving player exp.
        game.e_container.remove_widget(entity)
    """The universal value getter used in all components, although the __dict__
    might (probably not) need to be changed, since it doesn't apply to any
    attributes in the widget class.

    The function applies all of the active effects as 'Post processing' onto the
    character attribute, so the attribute itself is not modified, while the used
    value is. The multipliers are applied before the additives.

    It is yet to be decided if multipliers have diminishing returns, or if another
    system is used all together, at that point, simply change this.
    """
    def get_value(self, entity, attribute_id):
        try:
            val = entity.__dict__[attribute_id]
        except AttributeError:
            # Should really be with logging...
            print('Attribute {} is not in {}'.format(attribute_id, entity))
            return val

        for effect in self.effects:
            val = effect.m_apply_modifier(attribute_id, val)
        for effect in self.effects:
            val = effect.a_apply_modifier(attribute_id, val)
        for effect in self.effects:
            val = effect.spec_apply_modifier(attribute_id, val)
        return val

    # Defines behaviour of entity when colliding with another entity.
    def collide(self, entity, other, entity_container):
        pass

    """Pass DamageInfo object (abilitydata.py) as argument,
    defines behaviour when receiving damage, whether armour or whatever
    effects are applied, before lowering the hp.
    """
    def on_receive_damage(self, entity, damage_info):
        #print('damaged, %s' % self.get_value(entity, 'can_be_damaged'))
        if self.get_value(entity, 'can_be_damaged'):
            entity.hp -= damage_info.amount
        elif damage_info.type == 'absolute': # can't evade abs dmg bois.
            entity.hp -= damage_info.amount 
        #attacker = damage_info.attacker

    """ Changed system to globallly accessible player exp, and adding to that.
        if entity.hp <= 0 and True: # attacker.name in EntityContainer.players -> Not implemented bc entity container needs to be moduled and imported. I think is Singleton.
            # Destruction not handled here to allow for better overriding (?), decorators may be applicable here.
            attacker.receive_exp(entity.exp) # If action component contained exp.

    def on_receive_exp(self, entity, amount):
        pass
    """

"""The character input component only handles the movement stick, and not the
actual ability buttons, because they are as simple as binding an ability with
argument being the player.
"""

class HeroInputComponent(InputComponent):

    def __init__(self):
        # Same one as the one in left stick, used for reference by physics.
        # This is not encapsulated and decoupled, use caution.
        # Decimal distance of moving stick from border

        self.leftdown = False # Booleans for entity state.
        self.rightdown = False
        self.right_angle = 0 # Allow access for right stick angle without game, USE rightdown with this!!

    def update(self, entity, game):
        ui = game.user_interface
        left_stick = ui.left_ui.left_stick
        if left_stick.touch_distance != None and left_stick.touch_distance >= 0.7:
            self.leftdown = True
            self.activate_left(entity, left_stick)
        else:
            #entity.components['Physics'].direction = [0, 0]
            self.leftdown = False
        self.rightdown = bool(ui.right_stick.angle)
        self.right_angle = ui.right_stick.angle

    def activate_left(self, entity, left_stick):
        angle = left_stick.angle
        x = cos(angle)
        y = sin(angle)
        # Tells physics the direction, not the full velocity, which is processed more.
        entity.components['Physics'].direction = [x, y]


class HeroPhysicsComponent(PhysicsComponent):

    def __init__(self, **kw):
        super(HeroPhysicsComponent, self).__init__(**kw)
        self.controlled_velocity = 0 # For acceleration, acceleration is defined as SPEED_MULTIPLIER / UPDATE_RATE / 30
        """States, for working around deceleration.
        stopped
        moving
        slowing
        """
        self.state = 'stopped'

    def update(self, entity, game):
        """acomp = entity.components['Action']

        if acomp.state in ('moving', 'attacking') and self.direction: # If left_stick is activated.
        """
        self.move(entity, game)

    def move(self, entity, game):
        get_value = entity.components['Action'].get_value
        multiplier = get_value(entity, 'velocity_multiplier')
        LEFTDOWN = entity.components['Input'].leftdown

        # Acceleration/Deceleration when moving.
        ACCEL = 1/8 # Takes 8 frames to get up to speed.
        #DECEL = 1/UPDATE_RATE Default, adds displacement equal to current controlled velocity / frames.
        DECEL = 1 / (1.5 * UPDATE_RATE)

        if self.state == 'stopped':

            if LEFTDOWN:
                self.state = 'moving'


        if self.state == 'moving':

            if not LEFTDOWN:
                self.state = 'slowing'

            if self.controlled_velocity <= multiplier:
                self.controlled_velocity += multiplier * ACCEL

            elif self.controlled_velocity > multiplier:
                self.controlled_velocity = multiplier

        if self.state == 'slowing':

            if self.controlled_velocity: # For giving deceleration slide.
                entity.velocity = Vector(*entity.velocity) + (Vector(*self.direction) * self.controlled_velocity * DECEL)
                self.controlled_velocity = 0
            else:
                self.state = 'stopped'

        if False:#Vector(*entity.velocity).length() > 5: # Speed cap.
            entity.velocity = Vector(*entity.velocity).normalize() * 5
            displacement = entity.velocity
        else:
            displacement = entity.velocity
        if not LEFTDOWN: # Workaround for direction still being available.
            self.direction = [0, 0]

        # / UPDATE_RATE since controlled_velocity is not divided beforehand.
        self.total_velocity = Vector(*self.direction) * (self.controlled_velocity / UPDATE_RATE) + displacement
        next_pos = Vector(*entity.pos) + self.total_velocity

        # Reducing displacment vector based on friction.
        displacement *= 1 - (entity.friction / UPDATE_RATE) if displacement.length() > 0.01 else 0 # Prevent infinitely close to 0.
        entity.velocity *= 1 / ((1 / UPDATE_RATE) * displacement.length() + 1) # Diminishing returns for high knockback

        entity.pos = next_pos


# Job is to contain the graphical elements of the entity,
# and handle drawing with the camera.
class HeroGraphicsComponent(GraphicsComponent):

    image = CoreImage('assets/entities/player.png')

    def __init__(self):
        super(HeroGraphicsComponent, self).__init__()
        r = random.random
        #self.color = [1, 1, 1, 1]
        self.last_direction = [0, 0]
        self.cooldown_fx = False # not used yet.

    def update_graphics(self, entity):      
        g = []

        # This code is about al dente.
        phys = entity.components['Physics']
        act = entity.components['Action']
        right_angle = entity.components['Input'].right_angle
        rightdown = entity.components['Input'].rightdown

        if act.state == 'attacking' and rightdown: # Face same direction if attacking.
            direction = cos(right_angle), sin(right_angle)
            self.last_direction = direction
        elif phys.direction == [0, 0]: # To keep direction facing when player is stopped.
            direction = self.last_direction
        else:
            direction = phys.direction
            self.last_direction = direction # Save last direction if moving in case entity stops

        angle = self.rotate_angle(direction)

        img = self.image
        image_size = Vector(*self.fit_image(entity, img)) * 1 # Make player sprite 1.5x bigger than hitbox

        attk_speed = entity.components['Action'].basic_attack_cd # Monstrous, literally cooking to al dente.
        max_as = attk_speed.default
        cur_as = attk_speed.current

        # Prevent division by zero.
        if max_as == 0: max_as = 0.01
        if cur_as == 0: cur_as = 0.01

        r, gr, b, a = 0, 0, 0, 1 # color channels for useful editing, gr to avoid namespace conflict.

        #print('max: {}, cur: {}'.format(max_as, cur_as))

        #r = 1.2 - (cur_as / max_as) # Shades of red depending on attack cd.

        u = 2 - (cur_as / max_as) # Black to color.
        r, gr, b = u, u, u

        color = [r, gr, b, a]

        #color = [i if i <= 1 else 0 for i in [i + random.uniform(0, 0.05) for i in self.color]]
        #color[-1] = 1

        for i in [
            Color(rgba=color),
            Rotate(angle=angle),
            Rectangle(size=image_size, pos=Vector(*entity.size)/2, texture=img.texture)
        ]:
            g.append(i)
        return g

# The base class for player characters action components.
class HeroActionComponent(ActionComponent):

    states = ['idle', 'moving', 'attacking']
    
    def __init__(self):
        super(HeroActionComponent, self).__init__()
        self.abilities = [None, None]
        # Using cooldown object to reduce number of variables
        self.basic_attack_cd = Cooldown(0) # The duration is attack cooldown duration.
        self.attack_time = Cooldown(0.5) # The duration of attack animation, goes before basic_attack_cd starts.
        #self.attack_time.activate() # Prime the cooldown

        self.exp = 0
        self.level = 0 # used for checking for level ups.
        self.lvl_boundaries = (0, 500, 7, 20) # Level increments.
        self.state = 'idle'

        self.knockback = 2


    def assign_util_ability(self, ability):
        for idx, slot in enumerate(self.abilities):
            if slot is None:
                self.abilities[idx] = ability
                return None

    def update(self, entity, game):
        super(HeroActionComponent, self).update(entity, game)
        self.basic_attack_cd.default = entity.attack_speed
        for ability in self.abilities:
            try:
                ability.time_step()
            except AttributeError:
                continue

        if self.state != 'attacking': # Timestep if attack_animation is finished.
            self.basic_attack_cd.time_step()

        attk_ok = self.basic_attack_cd.current <= 0 # Store whether attack is available, as it is used often.

        icomp = entity.components['Input']

        if self.state == 'idle':
            if icomp.rightdown and attk_ok:
                self.state = 'attacking'
            elif icomp.leftdown:
                self.state = 'moving'

        elif self.state == 'attacking': # cd cycle of attack -> attk_time -> attk_cd -> attack

            if attk_ok and icomp.rightdown:
                self.activate_right(entity, game)
                self.attack_time.activate() # Prime attack animation cd for next time.
                self.basic_attack_cd.activate() # Falsify the condition of this if loop, only time_steps if attk animation is finished.

            if self.attack_time.current > 0: # If attack animation is not finished.
                self.attack_time.time_step()
                effect = SpeedUp(None, 1/UPDATE_RATE, 0.8) # Slow movement while attacking, one frame effects.
                self.effects.append(effect)
                #print(self.attack_time.current)
            else:
            #elif icomp.rightdown:
                #self.activate_right(entity, game)
                #self.attack_time.activate() # Prime attack animation cd for next time.

                if icomp.leftdown:
                    self.state = 'moving'
                else:
                    self.state = 'idle'

            """if self.basic_attack_cd.current > 0: # If attack animation is not finished.
                effect = SpeedUp(None, 1/UPDATE_RATE, 0.8) # Slow movement while attacking.
                self.effects.append(effect)
            elif icomp.rightdown:
                self.activate_right(entity, game)
            elif icomp.leftdown:
                self.state = 'moving'
            else:
                self.state = 'idle'"""

        elif self.state == 'moving':
            if icomp.rightdown and attk_ok:
                self.state = 'attacking'
            elif icomp.leftdown:
                pass
            else:
                self.state = 'idle'
            

        if self.exp >= self.lvl_boundaries[self.level+1]:
            self.level += 1
            Clock.schedule_once(game.level_up, -1)


    # Needs to know game for both ui and e_container
    # Used for handling cooldowns and conditions for basic attack.
    def activate_right(self, entity, game):
        angle = game.user_interface.right_stick.angle # Angle of touch.
        # Angle is None if touch is not pressed.
        if angle:# and self.basic_attack_cd.current <= 0:

            def create_proj(*args):
                a = create_hero_projectile(entity.center) # target_pos is for curving towards a location.
                direction = Vector(cos(angle), sin(angle)).rotate(random.uniform(-5, 5))
                #a.velocity_multiplier = random.uniform(400, 700) # TODO: Replace with some kwarg instead of direct access.
                a.components['Physics'].direction = direction
                a.center = Vector(*a.center) + direction * entity.width / 2 # For spawning missile at edge of entity.
                game.e_container.add_entity(a)

            def create_triple_proj(rot, *args):
                a = create_hero_projectile(entity.center) # target_pos is for curving towards a location.
                direction = Vector(cos(angle), sin(angle)).rotate(rot)
                a.components['Physics'].direction = direction
                a.center = Vector(*a.center) + direction * entity.width / 2 # For spawning missile at edge of entity.
                #a.velocity_multiplier = 700 # Experimental.
                game.e_container.add_entity(a)

            #for idx, _ in enumerate(range(1)): # Chain missile test.
                #Clock.schedule_once(create_proj, idx/10)
                #create_proj()

            #for rot in range(-180, 180, 30):#[-15, 0, 15]: # Chain missile test.
            for rot in (-15, 0, 15):
                create_triple_proj(rot)

            # Moved to be decoupled from activate_right.
            #self.basic_attack_cd.activate()
            #self.attack_time.activate() # Prime attack animation cd for next time.

            entity.velocity += -Vector(cos(angle), sin(angle)) * 2 # Recoil to give weight, multiplier is magnitude.
        else:
            pass
            #self.basic_attack_cd.time_step()

    def collide(self, entity, other, entity_container):
        if other.name in entity_container.enemies:
            diff = Vector(*other.center) - entity.center
            other.velocity += diff.normalize() * self.knockback
        """ Deprecated because of becoming invincible before receiving damage, functionality moved to on_receive_damage.
        if other.name in entity_container.enemies:
            if Invincibility in (type(i) for i in self.effects):
                return None
            def append(itm, dt): self.effects.append(itm)
            effect = partial(append, Invincibility(self, 1.5))
            Clock.schedule_once(effect, -1)
        """

    def on_receive_damage(self, entity, damage_info):
        #print('damaged, %s' % self.get_value(entity, 'can_be_damaged'))
        if self.get_value(entity, 'can_be_damaged'):
            entity.hp -= damage_info.amount
            self.effects.append(Invincibility(self, 0.5))
        elif damage_info.type == 'absolute': # can't evade abs dmg bois.
            entity.hp -= damage_info.amount 

    def on_receive_exp(self, entity, amount): # Unique to player action component.
        print('Player has received {} exp'.format(amount))
        self.exp += amount

    def destroy(self, entity, game):
        #Clock.schedule_once(game.game_over, -1)
        game.game_over(entity)


"""Below this point are enemy components.
"""

"""Provisionally, the AI will work through trees of decision making with methods,
starting with what action to do, which will put the AI into a predetermined state. (Enum, Dict, whateever)
Whenever update is called, the method for the AI's state is called, giving instruction.
"""
class BaseAIComponent(InputComponent):
    
    def __init__(self):

        # Dict for now, can switch to Enum, database.

        # states can include routines, which are a list of state functions that cannot be easily broken out of.
        self.states = {
            'IDLE': lambda *args: None,
            'CHASE': self.chase_state
            }

        self.state = 'IDLE'
        # Seconds * update speed.
        self.cooldown = 2 * UPDATE_RATE

    def update(self, entity, game):
        if self.cooldown <= 0:
            self.state = self.get_state(entity, game)
        self.cooldown -= 1

        self.states[self.state](entity, game)

    """The ai states work in a hierarchy of 2 levels (as of now).
    First is get_state, which makes a broad decision based on the game situation
    as for what the ai should do. Then the determined state function is called
    every update loop, making its own decisions for the ai's tangible behaviour.

    Routines can be part of an AI 'state', where a list of state functions that
    can be unique to the routine are called in order, such as 'move in an arc
    relative to the player, then shoot the player'.
    """

    # The highest level function for determining which state to use.
    def get_state(self, entity, game):
        player = game.player
        return 'CHASE'

    # Mindless chasing, TODO: cooldown of state switching.
    def chase_state(self, entity, game):
        # The number of cycles in between each change, to create a sense of lag.
        # Research closures to figure out method specific variables.
        frequency = 15

        player = game.player

        delta = difference(entity.pos, player.pos)
        angle = atan2(delta[1], delta[0])
        x = cos(angle)
        y = sin(angle)

        entity.components['Physics'].direction = [x, y]

class RiotPoliceInputComponent(BaseAIComponent):
    pass

class RiotPolicePhysicsComponent(PhysicsComponent):
    
    def update(self, entity, game):
        super(RiotPolicePhysicsComponent, self).update(entity, game)
        # TODO: Add stuff here.

class RiotPoliceGraphicsComponent(GraphicsComponent):

    image = CoreImage('assets/entities/riotpolice.png')

    def update_graphics(self, entity):
        g = []

        img = self.image
        angle = self.rotate_angle(entity.components['Physics'].direction)
        image_size = self.fit_image(entity, img) * 1.5
        
        for i in [
            Color(),
            Rotate(angle=angle),
            Rectangle(pos=Vector(*entity.size)/2, size=image_size, texture=img.texture)
        ]:
            g.append(i)

        """ Provisional graphics
        g.append(Ellipse(size=entity.size, pos=(entity.width/2, entity.height/2)))
        g.append(Ellipse(size=(10,10), pos=(0, entity.height/2)))
        g.append(Ellipse(size=(10,10), pos=(entity.width/2, entity.height)))
        g.append(Ellipse(size=(10,10), pos=(entity.width, entity.height/2)))
        g.append(Ellipse(size=(10,10), pos=(entity.width/2, 0)))"""
        return g

class RiotPoliceActionComponent(ActionComponent):

    def __init__(self):
        super(RiotPoliceActionComponent, self).__init__()
        # Proposition: make the contact_damage 'derive' from a base damage, so all damage from an entity is changed when dmg is changed.
        # self.contact_damage = 1
        # Moved to main entity

    def collide(self, entity, other, entity_container):
        knockback = (Vector(*other.pos) - Vector(*entity.pos)).normalize()
        if other.name in entity_container.players: # entity_id is yet to be implemented.
            dmg_inf = DamageInfo(
                entity,
                self.get_value(entity, 'contact_damage'), # damage is gotten through get_value interface.
                'contact' # dmg_type
                )
            #print(other.name)
            other.receive_damage(dmg_inf)
            # Knockback code on contact.
            # TODO: Add variable for knockback magnitude.
            other.velocity +=  knockback * 4
        elif other.name in entity_container.enemies:
            other.velocity += knockback * 4

    def destroy(self, entity, game):
        game.player.receive_exp(entity.exp)
        game.decal_engine.add_decal(entity.center, 'splash')
        game.e_container.remove_widget(entity)

class SinerInputComponent(InputComponent):
    # No need for Ω AI Ω, since this entity doesn't respond to player.
    def __init__(self, origin, y_direction):
        self.origin = origin # Starting location.
        # Properties of a sin wave.
        self.magnitude = 0 # Distance of peaks from origin y.
        self.x_speed = 3#1.8 # Horizontal speed/Overall cycle speed.
        self.frequency = 0.015#0.03 # Vertical speed, best below ~0.1, lower is slower.
        self.time = 0 # Elapsed time.

        self.position = self.origin # Position the entity SHOULD be at.

        self.x_direction = 1 # Left or right, -1 or 1.

        self.y_direction = y_direction # +sin(x) or -sin(x)

    def update(self, entity, game):
        self.position = self.get_ideal_path(entity, game)

        self.time += self.x_direction

    def get_ideal_path(self, entity, game):
        # Function for determining where the entity SHOULD be.
        game_map = game.game_map
        self.magnitude = game_map.height / 2 - 10

        t = self.time
        x, y = self.origin
        y += self.magnitude * self.y_direction * sin(self.frequency * t)
        x += t * self.x_speed

        # Bounce off left and right walls.
        if entity.right >= game_map.right:
            self.x_direction = -1

        elif entity.x <= game_map.x:
            self.x_direction = 1

        return [x, y]


    def reverse(self):
        pass

class SinerPhysicsComponent(PhysicsComponent):

    def __init__(self):
        super(SinerPhysicsComponent, self).__init__()
        self.can_collide_wall = False # Cannot collide with walls.
        self.can_fly = True
    
    def collide_wall(self, entity, entity_container):
        pass

    def can_collide(self, entity, other, entity_container):
        # Cannot collide with anything, gives knockback instead.
        if other.name in entity_container.players:
            return True
        else:
            return False

    def move(self, entity, game):
        entity.pos = entity.components['Input'].position

class SinerGraphicsComponent(GraphicsComponent):
    
    image = CoreImage('assets/entities/siner.png')

    def __init__(self):
        super(SinerGraphicsComponent, self).__init__()
        self.angle = Vector(1, 0) # Static direction not affected by movement.

    def update_graphics(self, entity):
        g = []

        img = self.image
        angle = self.rotate_angle(self.angle)

        self.angle = self.angle.rotate(-3) # Rotates at set rate.

        image_size = self.fit_image(entity, img) * 1.5
        
        for i in [
            Color(),
            Rotate(angle=angle),
            Rectangle(pos=Vector(*entity.size)/2, size=image_size, texture=img.texture)
        ]:
            g.append(i)

        return g

class SinerActionComponent(ActionComponent):

    def __init__(self):
        super(SinerActionComponent, self).__init__()
        self.knockback = 64 # KNOCKOASKOBACK, 64 is freight train level.
    
    def collide(self, entity, other, entity_container):
        if other.name in entity_container.players:
            dmg_inf = DamageInfo(
                entity,
                self.get_value(entity, 'contact_damage'), # damage is gotten through get_value interface.
                'contact' # dmg_type
                )
            other.receive_damage(dmg_inf)
            # Gives knockback to players.
            other.velocity += (Vector(*other.center) - entity.center).normalize() * self.knockback

class LancerInputComponent(BaseAIComponent):
    
    def __init__(self):

        self.states = {
        'COOLDOWN': None,
        'CHARGING': None
        }
        self.state = 'COOLDOWN'
        self.cooldown = Cooldown(3)
        # Start on cd.
        self.cooldown.activate()
        self.rotation_speed = 60 # / UPDATERATE

        self.direction = Vector(1, 0)

    def update(self, entity, game):

        #print(self.direction)

        player = game.player
        #physics = entity.components['Physics']

        if self.state == 'COOLDOWN':

            if self.cooldown.current <= 0:
                self.state = 'CHARGING'
                self.cooldown.activate()

            else:
                d = Vector(*player.center) - entity.center
                #angle = atan2(d[1], d[0])
                a_v = self.rotation_speed / UPDATE_RATE # angular velocity.

                # The difference between current and ideal directions.
                rot_direction = self.direction.angle(d)
                
                if rot_direction == 0:
                    # At ideal angle.
                    pass
                elif rot_direction > 0:
                    # Closest rotation is negative.
                    self.direction = self.direction.rotate(-a_v)
                else:
                    # Closest rotation is positive.
                    self.direction = self.direction.rotate(a_v)

                self.cooldown.time_step()

        elif self.state == 'CHARGING':
            pass#self.state = 'COOLDOWN'

class LancerPhysicsComponent(PhysicsComponent):
    
    def __init__(self, velocity_multiplier):
        # v_m is 0 by default, instead value is passed to here from creation func.
        super(LancerPhysicsComponent, self).__init__()
        # Charge speed is based off of velocity multiplier for easy changes.
        self.charging_speed = velocity_multiplier * 2
        self.charge_duration = Cooldown(0.5)
        self.charge_duration.activate()
        """ Not in use due to static charge velocity.
        def velocity_func(t):
            pass
        self.velocity_func = """

    def update(self, entity, game):
        super(LancerPhysicsComponent, self).update(entity, game)
        self.direction = entity.components['Input'].direction
        state = entity.components['Input'].state
        
        if state == 'CHARGING':
            if self.charge_duration.current > 0:
                self.charge_duration.time_step()
                # Acceleration
                entity.velocity_multiplier = self.charging_speed
            
            else:
                self.stop_charge(entity)

    def stop_charge(self, entity): # icomp is input component.
        self.charge_duration.activate()
        entity.velocity_multiplier = 0

        # To give slide.
        entity.velocity += self.direction * self.charging_speed / UPDATE_RATE
        entity.components['Input'].state = 'COOLDOWN'

    def collide_wall(self, entity, entity_container):
        if entity.components['Input'].state == 'CHARGING':
            entity.components['Action'].missiles(entity, entity_container)
            self.stop_charge(entity)


    def charge(self):
        pass # self.velocity

class LancerGraphicsComponent(GraphicsComponent):
    
    image = CoreImage('assets/entities/lancer.png')

    def update_graphics(self, entity):

        img = self.image
        angle = self.rotate_angle(entity.components['Physics'].direction)
        image_size = self.fit_image(entity, img)

        g = []

        for i in [
            Color(),
            Rotate(angle=angle),
            Rectangle(pos=Vector(*entity.size)/2, size=image_size, texture=img.texture)
        ]:
            g.append(i)

        return g

class LancerActionComponent(ActionComponent):

    def __init__(self):
        super(LancerActionComponent, self).__init__()
        self.knockback = 10

    def collide(self, entity, other, entity_container):
        if other.name in entity_container.players:
            # Deal dmg to players.
            dmg_inf = DamageInfo(
                entity,
                self.get_value(entity, 'contact_damage'), # damage is gotten through get_value interface.
                'contact' # dmg_type
                )
            other.receive_damage(dmg_inf)
            other.velocity += (Vector(*other.center) - entity.center).normalize() * self.knockback / 5

        if entity.components['Input'].state == 'CHARGING':
            # Stop charging upon hitting player, reason is so they do not appear to defy physics.
            entity.components['Physics'].stop_charge(entity)

            # Knocks back anyone
            other.velocity += (Vector(*other.center) - entity.center).normalize() * self.knockback
            self.missiles(entity, entity_container)

    def missiles(self, entity, entity_container):
        # Experimental missiles.
        for i in [-45, 45]:
            a = create_hero_projectile(entity.center, knockback=3)

            a.components['Action'].damage = 0

            direction = entity.components['Physics'].direction
            direction = direction.rotate(i)
            a.components['Physics'].direction = direction
            entity_container.add_entity(a)

"""Below here are all of the 'sub entities' created by entities (projectiles, etc.)
Each one will have a comment as to what entity(s) it belongs to.
"""

class HeroProjectilePhysicsComponent(PhysicsComponent):

    #def collide_entity(self, entity, other, entity_container): # Overridden bc projectile is destroyed on contact with enemy.
        #return Vector(*entity.pos) + self.total_velocity

    def __init__(self, target_pos=None, **kw):
        super(HeroProjectilePhysicsComponent, self).__init__(**kw)
        self.target_pos = target_pos # Aimed position, NOT IN USE.
        self.can_fly = True

    def update(self, entity, game):
        super(HeroProjectilePhysicsComponent, self).update(entity, game)
        #self.direction = Vector(*self.direction).rotate(random.choice([2, -2, 0])) # 'shakes' the missile. Testing.

    def can_collide(self, entity, other, entity_container):
        return False # Shouldn't resolve with anything.

    def collide_wall(self, entity, entity_container):
        entity.components['Action'].collide_wall(entity, entity_container) # Calls into exploding upon hitting wall.

class HeroProjectileGraphicsComponent(GraphicsComponent):

    #images = CoreImage('assets/entities/player_missile.png') # Shared instance of the image texture.

    def __init__(self, **kwargs):
        super(HeroProjectileGraphicsComponent, self).__init__(**kwargs)
        self.explosion_config = None # To save the randomly generated explosion color.
        self.image = CoreImage('assets/entities/cookie{}.png'.format(random.randint(1, 2)))

    def update_graphics(self, entity):
        r = random.random
        state = entity.components['Action'].state
        angle = entity.components['Physics'].direction
        angle = self.rotate_angle(angle)
        g = []
        if state == 'initial':
            img = self.image
            image_size = self.fit_image(entity, img) * 5
            ins = [
            Color(), 
            Rotate(angle=angle, axis=(0, 0, 1)), # origin is omitted, set in update_graphics.
            Rectangle(size=image_size, pos=(entity.width/2, entity.height/2), texture=img.texture),
            ]
            for i in ins:
                g.append(i)
        else:
            colors = self.generate_explosion()
            g.append(colors[0])
            g.append(Ellipse(size=Vector(*entity.size)*1.5, pos=(entity.width/2, entity.height/2)))
            #g.append(colors[1])
            #g.append(Ellipse(size=entity.size, pos=(entity.width/2, entity.height/2)))
            
        return g

    def generate_explosion(self):
        r = random.random
        if self.explosion_config == None:
            self.explosion_config = []
            self.explosion_config.append(Color(rgba=(1,r(),r(),1)))
            self.explosion_config.append(Color(rgba=(r(),r(),r(),0.2)))
            return self.explosion_config
        else:
            return self.explosion_config


# Belongs to the 'Hero' or 'test_hero' entity, as a projectile to fire.
class HeroProjectileActionComponentPROTOTYPE(ActionComponent):

    def __init__(self, dmg=1):
        super(HeroProjectileActionComponent, self).__init__()
        self.damage = dmg

    # No need for active effects on a projectile.
    def update(self, *args):
        pass

    def collide(self, entity, other, entity_container):
        if other.name in entity_container.enemies:
            d = DamageInfo(entity, self.damage, 'projectile')
            other.receive_damage(d)
            # The access to total velocity is unelegant.
            # Knockback code, knocks enemy back in average(pos_difference, projectile direction) direction.
            difference = (Vector(*other.pos) - Vector(*entity.pos)).normalize()
            entity_velocity = Vector(*entity.components['Physics'].total_velocity).normalize()
            knockback = (difference + entity_velocity) / 2
            other.velocity += knockback * 20 # The magnitude of the knockback.
            entity_container.remove_widget(entity) # Remove projectile after hitting something.

    # Can't be destroyed, destructible projectiles have 1 hp.
    def on_receive_damage(self, *args):
        pass

class HeroProjectileActionComponent(ActionComponent):

    def __init__(self, knockback, dmg=1):
        super(HeroProjectileActionComponent, self).__init__()
        self.damage = dmg
        self.states = ['initial', 'exploding', 'exploded']
        self.state = 'initial'
        self.explode_time = 0
        self.knockback = knockback

    # No need for active effects on a projectile.
    def update(self, entity, game):
        if self.state == 'initial':
            entity.velocity_multiplier += (10 * 40) / UPDATE_RATE # Acceleration, 1st term is 'meter', where 10 pixels is a meter. 2nd is how many m/s acceleration.
        
        elif self.state == 'exploded':
            entity.velocity_multiplier = 200 # Causes a 'blast' visual effect on the target.
        
        if self.explode_time > 0:
            self.state = 'exploded'
            Clock.schedule_once(lambda dt: game.e_container.remove_widget(entity), 0.2)

        if self.state == 'exploding':
            self.explode_time += 1

    def collide(self, entity, other, entity_container):
        if self.state == 'initial': 

            def death_memes(*args):
                self.explode(entity)
                self.state = 'exploding'

            if other.name in entity_container.enemies:
                death_memes()

            elif other.name in entity_container.terrain:
                death_memes()

            elif other.name == entity.name and other.components['Action'].state == 'exploding':
            # Temporary check for missiles exploding eachother, needs to be changed for different missile types.
                Clock.schedule_once(death_memes, 0.1)

            else:
                return None

        elif self.state == 'exploding': 

            if other.name in entity_container.enemies or other.name in entity_container.players:

                difference = Vector(*other.center) - Vector(*entity.center)
                #entity_velocity = Vector(*entity.components['Physics'].total_velocity).normalize()
                #knockback = (difference + entity_velocity) / 2
                # Above comments are pre explosion knockback code.
                percent = (difference.length() - (other.width / 2)) / entity.width # Edge distance from center of explosion
                percent = percent if percent > 0 else 0 # Prevents 'negative distance' if other covers the center point of explosion.
                #percent = percent if percent > 0
                # Results in 1/3 knockback at max explosion range.
                magnitude =  (-(2.5*self.knockback/3) * percent) + self.knockback # The magnitude of the knockback. First term is function which reduces knockback based on distance.
                other.velocity += difference.normalize() * magnitude


            if other.name not in entity_container.players:
                d = DamageInfo(entity, self.damage, 'projectile')
                other.receive_damage(d)


        elif self.state == 'exploded':
            pass

    def explode(self, entity):
        c = [entity.center_x, entity.center_y][:]
        entity.size = (45, 45)
        entity.center = c
        entity.velocity_multiplier = 0
        entity.components['Physics'].can_collide_wall = False # So dirty access, better change, stops explosions from being resolved.

    def collide_wall(self, entity, entity_container): # Called from physics component.
        def death_memes(dt):
            self.explode(entity)
            self.state = 'exploding'
        Clock.schedule_once(death_memes, -1) # To stop explosion overlap from chain explosions, which can cause double explosions.

    # Can't be destroyed, destructible projectiles have 1 hp.
    def on_receive_damage(self, *args):
        pass

"""Below here are map object classes (pillars, walls, etc.)
"""

class PillarPhysicsComponent(PhysicsComponent):

    def __init__(self, center):
        super(PillarPhysicsComponent, self).__init__()
        self.eternal_rest = center # position.
        self.can_fly = True
    
    def move(self, entity, game): # Redundant since move() is called from update()
        pass

    def update(self, entity, game):
        entity.center = self.eternal_rest # Pillars do not move from collision.

class PillarGraphicsComponent(GraphicsComponent):
    
    image = CoreImage('assets/entities/pillar.png')

    def update_graphics(self, entity):
        # Bad accessing.
        acomp = entity.components['Action']
        ratio = sum(entity.size) / sum(acomp.original) # ratio between current pillar size and original size.

        g = [Color(0,ratio-1,1,mode='hsv')]
        img = self.image
        image_size = Vector(*self.fit_image(entity, img)) * 2

        g.append(Rectangle(size=image_size, pos=Vector(*entity.size)/2, texture=img.texture))

        return g

class PillarActionComponent(ActionComponent):
    
    # Can receive damage, but won't get destroyed?
    #def on_receive_damage(self, entity, damage_info):
        #pass

    def __init__(self, grow_to=1.5, knockback=10):
        super(PillarActionComponent, self).__init__()
        self.original = 0
        self.grow_to = grow_to # Size to grow to when hit, multiplier.
        self.deflate_speed = 200 # Side pixels/sec
        self.knockback = knockback
        self.inflated_cd = Cooldown(1) # Duration of inflation before deflation.

    def update(self, entity, game):
        if not self.original: # Should be moved to init if it takes entity.
            self.original = entity.size[:] # Important to make copy.

        #print(self.inflated_cd.current)
        if self.inflated_cd.current:
            self.inflated_cd.time_step()
        elif entity.size > self.original:
            entity.size = Vector(entity.size) - [self.deflate_speed / UPDATE_RATE] * 2
        else:
            entity.size = self.original

    def on_receive_damage(self, entity, damage_info): # Grows in size then deflates when hit by projectile.
        if damage_info.type == 'projectile':
            if self.original: # If original is not assigned yet -.- fix so init takes entity pls.
                entity.size = Vector(self.original) * self.grow_to
                self.inflated_cd.activate()

    def collide(self, entity, other, entity_container):
        if self.inflated_cd.current >= self.inflated_cd.default - 0.1: # 0.1 secs of high knockback.
            other.velocity += (Vector(*other.center) - entity.center).normalize() * self.knockback


"""Below here are powerups.
"""

class PowerupPhysicsBase(PhysicsComponent):
    
    def can_collide(*args):
        return False

    def move(*args):
        return None

class PowerupGraphicsBase(GraphicsComponent):
    
    image = ''

    def __init__(self):
        super(PowerupGraphicsBase, self).__init__()
        self.time = 0 # For actions upon spawning.
        self.color = [0.8, 0.8, 1, 1]

    def update(self, entity, game):
        super(PowerupGraphicsBase, self).update(entity, game)
        self.time += 1

    def init_anim(self, entity): # Call in update_graphics.
        t = self.time / UPDATE_RATE # Time elapsed in seconds
        size = (entity.width, entity.height * t) # Grow in height.
        if self.time % 3 == 0:
            self.color[-1] = 1 if self.color[-1] == 0 else 0
        return [Color(rgba=self.color), 
                Rectangle(pos=Vector(size)/2, size=size)]

    def update_graphics(self, entity):
        if self.time / UPDATE_RATE < 1:
            return self.init_anim(entity)
        else:
            return [Color(),
                    Rectangle(size=entity.size, pos=(entity.width/2,entity.height/2), source='./assets/misc/harambe.jpg')]

class PowerupActionBase(ActionComponent):

    def __init__(self):
        super(PowerupActionBase, self).__init__()
        self.dead = False # Flag to disable powerups if already collected.

    def destroy(self, entity, game):
        game.e_container.remove_widget(entity)

    def effect(self):
        # self may need to be replaced with type(self)
        return SpeedUp(self, 12, 3) # First arg is origin_id, which is hacky.

    
    def collide(self, entity, other, entity_container):
        if self.dead:
            return None

        if other.name in entity_container.players:
            ac = other.components['Action'].effects
            for effect in ac: # Take care: temp variable effect can override namespaces.
                if effect.origin_id == self: # Prevent effect stacking.
                    break
            else:
                ac.append(self.effect()) # Give effect to player, then destroy self.

            self.dead = True
            
            def death(self):
                entity_container.remove_widget(entity)
            anim = Animation(size=(1, 1), pos=entity.center, duration=0.5)
            anim.start(entity)
            Clock.schedule_once(death, 2)
            
"""Below here are entity creation functions, includes:
components, entity, various attributes.
"""

# Window.center is to be changed to starting position on the game map
def create_hero(center, size=(48, 48)):
    # TODO: Add error checking if the name is not in any valid names.
    e = Entity(center=center, size=size)
    chardata = {'name': 'test_hero', 'max_hp': 5, 'hp': 5,
        'velocity_multiplier': 175, 'attack_speed': 0.3
        }
    for key, val in chardata.items():
        e.__dict__[key] = val
    e.components['Input'] = HeroInputComponent()
    e.components['Physics'] = HeroPhysicsComponent()
    e.components['Graphics'] = HeroGraphicsComponent()
    e.components['Action'] = HeroActionComponent()
    e.components['Action'].assign_util_ability(SuperSpeed())
    # The add_widget step is not in the function, so it's decoupled.
    return e

def create_hero_projectile(center, size=(16, 16), velocity_multiplier=100, target_pos=None, knockback=16): # target_pos is for missile curving.
    e = Entity(size=size)
    e.center = center
    chardata = {'name': 'test_projectile', 'max_hp': 1, 'hp': 1,
        'velocity_multiplier': velocity_multiplier, 'can_be_damaged': False
        }
    for key, val in chardata.items():
        e.__dict__[key] = val
    e.components['Input'] = None
    e.components['Physics'] = HeroProjectilePhysicsComponent(target_pos)
    e.components['Graphics'] = HeroProjectileGraphicsComponent()
    e.components['Action'] = HeroProjectileActionComponent(knockback)
    return e

def create_riot_police(center, size=(24, 24)):
    e = Entity(center=center, size=size)
    chardata = {'name': 'Riot Police', 'max_hp': 2, 'hp': 2, 'velocity_multiplier': 75,
        'contact_damage': 1, 'exp': 1
                }
    for key, val in chardata.items():
        e.__dict__[key] = val
    e.components['Input'] = RiotPoliceInputComponent()
    e.components['Physics'] = RiotPolicePhysicsComponent()
    e.components['Graphics'] = RiotPoliceGraphicsComponent()
    e.components['Action'] = RiotPoliceActionComponent()
    return e

def create_siner(center, y_direction=1, size=(24, 24)):
    e = Entity(center=center, size=size)
    chardata = {'name': 'Siner', 'max_hp': 4, 'hp': 4, 'velocity_multiplier': 0,
        'contact_damage': 1, 'exp': 1
                }
    for key, val in chardata.items():
        e.__dict__[key] = val
    e.components['Input'] = SinerInputComponent(origin=center, y_direction=y_direction)
    e.components['Physics'] = SinerPhysicsComponent()
    e.components['Graphics'] = SinerGraphicsComponent()
    e.components['Action'] = SinerActionComponent()
    return e

def create_lancer(center, velocity_multiplier=175, size=(24, 24)):
    e = Entity(center=center, size=size)
    chardata = {'name': 'Lancer', 'max_hp': 3, 'hp': 3, 'velocity_multiplier': 0,
        'contact_damage': 1, 'exp': 1, 'friction': 5
                }
    for key, val in chardata.items():
        e.__dict__[key] = val
    e.components['Input'] = LancerInputComponent()
    e.components['Physics'] = LancerPhysicsComponent(velocity_multiplier)
    e.components['Graphics'] = LancerGraphicsComponent()
    e.components['Action'] = LancerActionComponent()
    return e

def create_pillar(center, size=(64, 64)):
    e = Entity(center=center, size=size)
    chardata = {'name': 'Pillar', 'max_hp': 1, 'hp': 1, 'velocity_multiplier': 0,
        'contact_damage': 0, 'exp': 0, 'friction': 0, 'can_be_damaged': False
                }
    for key, val in chardata.items():
        e.__dict__[key] = val
    e.components['Input'] = None
    e.components['Physics'] = PillarPhysicsComponent(center)
    e.components['Graphics'] = PillarGraphicsComponent()
    e.components['Action'] = PillarActionComponent()
    return e

def create_powerup(center, size=(48, 48)):
    e = Entity(center=center, size=size)
    chardata = {'name': 'TestPowerup', 'max_hp': 1, 'hp': 1, 'velocity_multiplier': 0,
        'contact_damage': 0, 'exp': 0, 'friction': 0, 'can_be_damaged': False
                }
    for key, val in chardata.items():
        e.__dict__[key] = val
    e.components['Input'] = None
    e.components['Physics'] = PowerupPhysicsBase()
    e.components['Graphics'] = PowerupGraphicsBase()
    e.components['Action'] = PowerupActionBase()
    return e

