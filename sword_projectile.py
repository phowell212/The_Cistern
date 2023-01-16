import arcade
import settings
import time


class SwordProjectile(arcade.Sprite):
    def __init__(self, player):
        super().__init__()

        # Set the starting position and direction of the projectile based on the player's position and facing direction
        self.center_x = player.center_x
        self.center_y = player.center_y
        self.direction = player.current_direction
        self.hit_box = arcade.create_rectangle_filled(self.center_x, self.center_y, 10, 10, arcade.color.RED)

        # Set the movement speed
        self.speed = 10
        self.timer = time.time()

    def update(self):
        # Move the projectile in the direction it is facing
        if self.direction == "north":
            self.center_y += self.speed
        elif self.direction == "south":
            self.center_y -= self.speed
        elif self.direction == "east":
            self.center_x += self.speed
        elif self.direction == "west":
            self.center_x -= self.speed
        elif self.direction == "northwest":
            self.center_y += self.speed
            self.center_x -= self.speed
        elif self.direction == "northeast":
            self.center_y += self.speed
            self.center_x += self.speed
        elif self.direction == "southwest":
            self.center_y -= self.speed
            self.center_x -= self.speed
        elif self.direction == "southeast":
            self.center_y -= self.speed
            self.center_x += self.speed

        # Check if the projectile has gone offscreen, and if so, mark it for removal
        if self.center_x < 0 or self.center_x > settings.SCREEN_WIDTH or self.center_y < 0 or \
                self.center_y > settings.SCREEN_HEIGHT:
            self.remove_from_sprite_lists()

        # If it has been 0.5 seconds since the projectile was created, mark it for removal
        if time.time() - self.timer > 0.5:
            self.kill()
