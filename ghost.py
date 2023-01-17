import arcade
import random
import math


class GhostMonster(arcade.Sprite):
    def __init__(self, center_x, center_y, scale):
        super().__init__()
        self.north_idle_frames = []
        self.south_idle_frames = []
        self.hurt_frames = []
        self.death_frames = []
        self.is_being_hurt = False
        self.current_frame = 0
        self.hurt_frame = 0
        self.death_frame = 0
        self.update_interval = 1 / 10
        self.health = 7
        self.scale = scale
        self.center_x, self.center_y = center_x, center_y
        self.directions = ["north", "south"]
        self.current_direction = self.directions[1]
        self.time = 0
        self.bob_frequency = 5
        self.bob_amplitude = 0.3
        self.load_frames()

    def update_animation(self, delta_time: float = 1 / 30):
        self.current_frame += self.update_interval * delta_time

        # If the sprite has no health, play that animation then kill it
        if self.health <= 0 and self.death_frame < len(self.death_frames):
            self.texture = self.death_frames[self.death_frame]
            self.death_frame += 1
        elif self.health <= 0:
            self.death_frame = 0
            self.kill()

        # If the monster is being hurt, play the hurt animation
        elif self.is_being_hurt and self.hurt_frame < len(self.hurt_frames) - 1:
            self.hurt_frame += 1
            self.texture = self.hurt_frames[self.hurt_frame]
        elif self.is_being_hurt:
            self.health -= 1
            self.is_being_hurt = False
            self.hurt_frame = 0

        # If the monster is not being hurt, play the idle animation
        elif self.current_frame < len(self.north_idle_frames):
            if self.current_direction == self.directions[0]:
                self.texture = self.north_idle_frames[int(self.current_frame)]
            else:
                self.texture = self.south_idle_frames[int(self.current_frame)]
        else:
            self.current_frame = 0

    def update(self):

        # Update the ghost's position
        if not self.is_being_hurt or self.health > 0:
            self.update_animation(1)
            self.center_x += self.change_x
            self.center_y += self.change_y

            # Make the ghost bob
            self.time += 1 / 60
            self.center_y += math.sin(self.time * self.bob_frequency) * self.bob_amplitude

            # Make the ghost move
            if random.randint(0, 100) == 0:
                self.change_x = random.randint(-1, 1)
                self.change_y = random.randint(-1, 1)

        else:
            self.update_animation(1 / 2)

        # Update the ghost's direction
        if self.change_y > 0:
            self.current_direction = self.directions[0]
        else:
            self.current_direction = self.directions[1]

    def load_frames(self):
        for i in range(0, 1):
            self.north_idle_frames.append(arcade.load_texture(f"assets/enemies/ghost/g_north-{i}.png"))
        for i in range(0, 1):
            self.south_idle_frames.append(arcade.load_texture(f"assets/enemies/ghost/g_south-{i}.png"))
        for i in range(0, 7):
            self.hurt_frames.append(arcade.load_texture(f"assets/enemies/ghost/g_scream-{i}.png"))
        for i in range(0, 10):
            self.death_frames.append(arcade.load_texture(f"assets/enemies/ghost/g_death-{i}.png"))
