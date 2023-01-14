import random
from pyglet.math import Vec2
import player
from pathlib import Path
import arcade
from arcade.experimental import Shadertoy
import time

SCREEN_WIDTH = 700
SCREEN_HEIGHT = 1000
SCREEN_TITLE = "Ray-casting Demo"

SPRITE_SCALING = 0.25
PLAYER_SCALING = 0.4

# How fast the camera pans to the player. 1.0 is instant.
CAMERA_SPEED = 0.9

PLAYER_MOVEMENT_SPEED = 3
RUN_SPEED_MODIFIER = 2
SLASH_SPEED_MODIFIER = 0.2
SLASH_CHARGE_SPEED_MODIFIER = 0.8
SLASH_CHARGE_TIME = 0.5
BOMB_COUNT = 70
PLAYING_FIELD_WIDTH = SCREEN_WIDTH - 50
PLAYING_FIELD_HEIGHT = SCREEN_HEIGHT - 50


class MyGame(arcade.Window):

    def __init__(self, width, height, title):
        super().__init__(width, height, title, resizable=True)

        # Init the shaders
        self.box_shadershadertoy = None
        self.channel0 = None
        self.channel1 = None
        self.load_shader()

        # Make the sprites
        self.player_sprite = None
        self.wall_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()

        # Other stuff
        arcade.set_background_color((108, 121, 147))
        self.key_press_buffer = set()

        # Make the camera
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Create the sprites
        self.player_sprite = player.Player(256, 512, PLAYER_SCALING)
        self.player_list.append(self.player_sprite)
        self.generate_walls()

        # Physics engine, so we don't run into walls
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)

    def load_shader(self):
        shader_file_path = Path("shaders/box_shadows.glsl")

        # Size of the window
        window_size = self.get_size()

        # Create the shader toy
        self.box_shadershadertoy = Shadertoy.create_from_file(window_size, shader_file_path)

        # Create the channels 0 and 1 frame buffers.
        # Make the buffer the size of the window, with 4 channels (RGBA)
        self.channel0 = self.box_shadershadertoy.ctx.framebuffer(
            color_attachments=[self.box_shadershadertoy.ctx.texture(window_size, components=4)]
        )
        self.channel1 = self.box_shadershadertoy.ctx.framebuffer(
            color_attachments=[self.box_shadershadertoy.ctx.texture(window_size, components=4)])

        # Assign the frame buffers to the channels
        self.box_shadershadertoy.channel_0 = self.channel0.color_attachments[0]
        self.box_shadershadertoy.channel_1 = self.channel1.color_attachments[0]

    def generate_walls(self):

        # Set up several columns of walls
        for x in range(0, PLAYING_FIELD_WIDTH, 128):
            player_height = self.player_sprite.height

            # Add some extra space between the walls and player sprite
            extra_space = 20
            for y in range(0, PLAYING_FIELD_HEIGHT, int((player_height + extra_space) / 2)):

                # Randomly skip a box so the player can find a way through
                if random.randrange(3) > 0:
                    wall = arcade.Sprite(":resources:images/tiles/dirt.png", SPRITE_SCALING)
                    wall.center_x = x
                    wall.center_y = y
                    self.wall_list.append(wall)

    def on_key_press(self, key, modifiers):
        self.key_press_buffer.add(key)

    def process_key_presses(self):
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0

        # Handle slashing, hold the c key for SLASH_CHARGE_TIME to activate
        if arcade.key.C in self.key_press_buffer:
            if self.player_sprite.c_key_timer == 0:
                self.player_sprite.c_key_timer = time.time()
            elif time.time() - self.player_sprite.c_key_timer >= SLASH_CHARGE_TIME:
                self.player_sprite.is_slashing = True
                self.player_sprite.c_key_timer = 0

        # Handle running, hold the shift key
        if arcade.key.LEFT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer \
                and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED * 0.7 * RUN_SPEED_MODIFIER
            self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED * 0.7 * RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= SLASH_SPEED_MODIFIER
                self.player_sprite.change_y *= SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "northwest"
            self.player_sprite.is_running = True
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer \
                and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED * 0.7 * RUN_SPEED_MODIFIER
            self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED * 0.7 * RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= SLASH_SPEED_MODIFIER
                self.player_sprite.change_y *= SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "southwest"
            self.player_sprite.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer \
                and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED * 0.7 * RUN_SPEED_MODIFIER
            self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED * 0.7 * RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= SLASH_SPEED_MODIFIER
                self.player_sprite.change_y *= SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "northeast"
            self.player_sprite.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer \
                and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED * 0.7 * RUN_SPEED_MODIFIER
            self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED * 0.7 * RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= SLASH_SPEED_MODIFIER
                self.player_sprite.change_y *= SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "southeast"
            self.player_sprite.is_running = True
        elif arcade.key.UP in self.key_press_buffer and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED * RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_y *= SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "north"
            self.player_sprite.is_running = True
        elif arcade.key.DOWN in self.key_press_buffer and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED * RUN_SPEED_MODIFIER
            self.player_sprite.current_direction = "south"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_y *= SLASH_SPEED_MODIFIER
            self.player_sprite.is_running = True
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED * RUN_SPEED_MODIFIER
            self.player_sprite.current_direction = "west"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= SLASH_SPEED_MODIFIER
            self.player_sprite.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED * RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_y *= SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "east"
            self.player_sprite.is_running = True

        # Handle basic movement use the arrow keys
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED * 0.7
            self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED * 0.7
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= SLASH_SPEED_MODIFIER + (SLASH_SPEED_MODIFIER / 3)
                self.player_sprite.change_y *= SLASH_SPEED_MODIFIER + (SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.current_direction = "northwest"
            self.player_sprite.is_walking = True
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED * 0.7
            self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED * 0.7
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= SLASH_SPEED_MODIFIER + (SLASH_SPEED_MODIFIER / 3)
                self.player_sprite.change_y *= SLASH_SPEED_MODIFIER + (SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.current_direction = "southwest"
            self.player_sprite.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED * 0.7
            self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED * 0.7
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= SLASH_SPEED_MODIFIER + (SLASH_SPEED_MODIFIER / 3)
                self.player_sprite.change_y *= SLASH_SPEED_MODIFIER + (SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.current_direction = "northeast"
            self.player_sprite.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED * 0.7
            self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED * 0.7
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= SLASH_SPEED_MODIFIER + (SLASH_SPEED_MODIFIER / 3)
                self.player_sprite.change_y *= SLASH_SPEED_MODIFIER + (SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.current_direction = "southeast"
            self.player_sprite.is_walking = True
        elif arcade.key.UP in self.key_press_buffer:
            self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED
            self.player_sprite.current_direction = "north"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_y *= SLASH_SPEED_MODIFIER + (SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.is_walking = True
        elif arcade.key.DOWN in self.key_press_buffer:
            self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED
            self.player_sprite.current_direction = "south"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_y *= SLASH_SPEED_MODIFIER + (SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.is_walking = True
        elif arcade.key.LEFT in self.key_press_buffer:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
            self.player_sprite.current_direction = "west"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= SLASH_SPEED_MODIFIER + (SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
            self.player_sprite.current_direction = "east"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= SLASH_SPEED_MODIFIER + (SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.is_walking = True

    def on_key_release(self, key, modifiers):
        self.key_press_buffer.discard(key)
        if not self.key_press_buffer:
            if self.player_sprite.is_walking:
                self.player_sprite.is_walking = False
            if self.player_sprite.is_running:
                self.player_sprite.is_running = False
                self.player_sprite.just_stopped_running = True
        elif not arcade.key.C in self.key_press_buffer:
            self.player_sprite.c_key_timer = 0

    def scroll_to_player(self, speed=CAMERA_SPEED):
        position = Vec2(self.player_sprite.center_x - self.width / 2,
                        self.player_sprite.center_y - self.height / 2)
        self.camera.move_to(position, speed)

    def on_draw(self):
        # Use the camera
        self.camera.use()

        # Select the channel 0 frame buffer to draw on
        self.channel0.use()
        self.channel0.clear()

        # Draw the walls in shadow
        self.wall_list.draw()

        # Select the channel 1 frame buffer to draw on
        self.channel1.use()
        self.channel1.clear()

        # Select this window to draw on
        self.use()
        # Clear to background color
        self.clear()

        # Calculate the light position
        p = (self.player_sprite.position[0] - self.camera.position[0],
             self.player_sprite.position[1] - self.camera.position[1])

        # Run the shader and render to the window
        self.box_shadershadertoy.program['lightPosition'] = p
        self.box_shadershadertoy.program['lightSize'] = 200
        self.box_shadershadertoy.render()

        # Draw the player
        self.player_list.draw()

    def on_update(self, delta_time):
        self.physics_engine.update()
        self.process_key_presses()
        self.player_sprite.update_animation(delta_time)
        self.scroll_to_player()

        if self.player_sprite.c_key_timer > 0:
            self.player_sprite.change_x *= SLASH_CHARGE_SPEED_MODIFIER
            self.player_sprite.change_y *= SLASH_CHARGE_SPEED_MODIFIER


if __name__ == "__main__":
    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.set_location(1025, 35)
    arcade.run()
