import arcade
import random


class GreenMonster(arcade.Sprite):
    def __init__(self, center_x, center_y, scale):
        super().__init__()
        self.idle_frames = []
        self.hurt_frames = []
        self.death_frames = []
        self.is_being_hurt = False
        self.current_frame = 0
        self.hurt_frame = 0
        self.death_frame = 0
        self.update_interval = 1 / 10
        self.health = 5
        self.scale = scale
        self.center_x, self.center_y = center_x, center_y
        self.load_frames()

    def load_frames(self):
        for i in range(0, 9):
            self.idle_frames.append(arcade.load_texture(f"assets/enemies/tile00{i}.png"))
        for i in range(0, 5):
            self.idle_frames.append(arcade.load_texture(f"assets/enemies/tile01{i}.png"))
        for i in range(6, 8):
            self.hurt_frames.append(arcade.load_texture(f"assets/enemies/tile01{i}.png"))
        for i in range(4, 9):
            self.death_frames.append(arcade.load_texture(f"assets/enemies/tile02{i}.png"))
        self.death_frames.append(arcade.load_texture("assets/enemies/tile030.png"))

    def update_animation(self, delta_time):
        self.current_frame += self.update_interval * delta_time

        # If the enemy has 0 health, play the death animation, then remove the enemy from the list
        if self.health <= 0 and self.death_frame < len(self.death_frames):
            self.texture = self.death_frames[self.death_frame]
            self.death_frame += 1
        elif self.health <= 0:
            self.death_frame = 0
            self.kill()

        # If the monster is being hurt, play the hurt animation
        elif self.is_being_hurt and self.hurt_frame < len(self.hurt_frames):
            self.hurt_frame += 1
            self.texture = self.hurt_frames[self.hurt_frame]
        elif self.is_being_hurt:
            self.health -= 1
            self.is_being_hurt = False
            self.hurt_frame = 0

        # If the monster is not being hurt, play the idle animation
        elif self.current_frame < len(self.idle_frames):
            self.texture = self.idle_frames[int(self.current_frame)]
        else:
            self.current_frame = 0

    def update(self):
        if not self.is_being_hurt or self.health > 0:
            self.update_animation(1)
            self.center_x += self.change_x
            self.center_y += self.change_y

            if random.randint(0, 100) == 0:
                self.change_x = random.randint(-2, 2)
                self.change_y = random.randint(-2, 2)

        else:
            self.update_animation(1 / 40)
