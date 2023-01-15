import random
from pyglet.math import Vec2
import player
import green_monster
from pathlib import Path
import arcade
from arcade.experimental import Shadertoy
import time

# Screen Settings
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 1000
SCREEN_TITLE = "The Cistercian Cistern"
PLAYING_FIELD_WIDTH = SCREEN_WIDTH - 50
PLAYING_FIELD_HEIGHT = SCREEN_HEIGHT - 50

# Scaling Settings
SPRITE_SCALING = 0.25
PLAYER_SCALING = 0.4
MONSTER_SCALING = 1

# How fast the camera pans to the player. 1.0 is instant.
CAMERA_SPEED = 0.9

# Movement settings
PLAYER_MOVEMENT_SPEED = 2
RUN_SPEED_MODIFIER = 2
SLASH_SPEED_MODIFIER = 0.2
SLASH_CHARGE_SPEED_MODIFIER = 0.8

# Time settings
SLASH_CHARGE_TIME = 0.075


class MyGame(arcade.Window):

    def __init__(self, width, height, title):
        super().__init__(width, height, title, resizable=True)

        # Init the shaders
        self.box_shadertoy = None
        self.channel0 = None
        self.channel1 = None
        self.load_shader()

        # Make the sprites
        self.player_sprite = None
        self.monster_sprite = None
        self.wall_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.monster_list = arcade.SpriteList()

        # Other stuff
        arcade.set_background_color((108, 121, 147))
        self.key_press_buffer = set()

        # Make the camera
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Load the level map
        map_location = "assets/level/level_map.json"
        layer_options = {"Tile Layer 1": {"use_spatial_hash": True, "spatial_hash_cell_size": 128}}
        self.level_map = arcade.tilemap.load_tilemap(map_location, SPRITE_SCALING, layer_options=layer_options)
        map_center_x = self.level_map.width * self.level_map.tile_width * SPRITE_SCALING / 2
        map_center_y = self.level_map.height * self.level_map.tile_height * SPRITE_SCALING / 2
        self.wall_tile_map = arcade.load_tilemap(map_location, SPRITE_SCALING, layer_options)
        self.wall_tile_map = arcade.Scene.from_tilemap(self.wall_tile_map)
        scene_wall_sprite_list = self.wall_tile_map.get_sprite_list("Tile Layer 1")
        self.wall_list.extend(scene_wall_sprite_list)

        # Create the other sprites
        # Create the sprites
        self.player_sprite = player.Player(map_center_x, map_center_y, PLAYER_SCALING)
        self.player_list.append(self.player_sprite)
        self.generate_walls(self.level_map.width, self.level_map.height)
        self.monster_sprite = green_monster.GreenMonster(596, 512, MONSTER_SCALING)
        self.monster_list.append(self.monster_sprite)

        # Physics engine, so we don't run into walls
        self.player_and_wall_collider = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
        self.player_and_monster_collider = arcade.PhysicsEngineSimple(self.player_sprite, self.monster_list)
        self.monster_and_wall_collider = arcade.PhysicsEngineSimple(self.monster_sprite, self.wall_list)

    def load_shader(self):
        shader_file_path = Path("shaders/box_shadows.glsl")

        # Size of the window
        window_size = self.get_size()

        # Create the shader toy
        self.box_shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)

        # Create the channels 0 and 1 frame buffers.
        # Make the buffer the size of the window, with 4 channels (RGBA)
        self.channel0 = self.box_shadertoy.ctx.framebuffer(
            color_attachments=[self.box_shadertoy.ctx.texture(window_size, components=4)]
        )
        self.channel1 = self.box_shadertoy.ctx.framebuffer(
            color_attachments=[self.box_shadertoy.ctx.texture(window_size, components=4)])

        # Assign the frame buffers to the channels
        self.box_shadertoy.channel_0 = self.channel0.color_attachments[0]
        self.box_shadertoy.channel_1 = self.channel1.color_attachments[0]

    def generate_walls(self, map_width, map_height):
        map_width = map_width * self.level_map.tile_width * SPRITE_SCALING
        map_height = map_height * self.level_map.tile_height * SPRITE_SCALING
        for _ in range(150):
            # Generate random x, y coordinates for the wall
            x = random.randrange(100, map_width - 100)
            y = random.randrange(100, map_height - 100)

            wall = arcade.Sprite("assets/level/wall.png", SPRITE_SCALING)
            wall.center_x = x
            wall.center_y = y
            overlap = False
            for wall_check in self.wall_list:
                if wall.collides_with_sprite(wall_check):
                    overlap = True
                    break
            if not overlap:
                self.wall_list.append(wall)
            else:
                # Generate new coordinates for the wall
                x = random.randrange(100, map_width - 100)
                y = random.randrange(100, map_height - 100)
                wall.center_x = x
                wall.center_y = y

    def on_key_press(self, key, modifiers):
        self.key_press_buffer.add(key)

    def spawn_monster(self, x, y):
        self.monster_sprite = green_monster.GreenMonster(x, y, MONSTER_SCALING)

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

        # Modify the movement speed again to make a charge effect when c is pressed
        if arcade.key.C in self.key_press_buffer:
            self.player_sprite.change_x *= SLASH_CHARGE_SPEED_MODIFIER
            self.player_sprite.change_y *= SLASH_CHARGE_SPEED_MODIFIER

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

        # Draw the enemies
        self.monster_list.draw()

        # Calculate the light position
        p = (self.player_sprite.position[0] - self.camera.position[0],
             self.player_sprite.position[1] - self.camera.position[1])

        # Run the shader and render to the window
        self.box_shadertoy.program['lightPosition'] = p
        self.box_shadertoy.program['lightSize'] = 200
        self.box_shadertoy.render()

        # Draw the player
        self.player_list.draw()

    def on_update(self, delta_time):

        # Update the physics
        self.player_and_wall_collider.update()
        self.player_and_monster_collider.update()
        self.monster_and_wall_collider.update()
        self.process_key_presses()

        self.player_sprite.update_animation(delta_time)
        if self.player_sprite.c_key_timer > 0:
            self.player_sprite.change_x *= SLASH_CHARGE_SPEED_MODIFIER
            self.player_sprite.change_y *= SLASH_CHARGE_SPEED_MODIFIER

        self.monster_sprite.update()
        self.scroll_to_player()


if __name__ == "__main__":
    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.set_location(1025, 35)
    arcade.run()
