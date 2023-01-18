import random
import ghost
import arcade
import time
import player
import settings as s
import swordslash as ss
from arcade.experimental import Shadertoy
from pathlib import Path
from pyglet.math import Vec2


class MyGame(arcade.Window):

    def __init__(self, width, height, title):
        super().__init__(width, height, title, resizable=True)

        # Init the shaders
        self.box_shadertoy = None
        self.channel0 = None
        self.channel1 = None
        self.load_shader()

        # Init the sprites
        self.player_sprite = None
        self.monster_sprite = None
        self.wall_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.monster_list = arcade.SpriteList()
        self.swordslash_list = arcade.SpriteList()

        # Other stuff
        arcade.set_background_color((108, 121, 147))
        self.key_press_buffer = set()
        self.ghosts_to_spawn = 2.0
        self.ghosts_to_spawn_multiplier = 1.25
        self.no_ghost_timer = 0.0
        self.initialized = 10

        # Make the camera
        self.camera = arcade.Camera(s.SCREEN_WIDTH, s.SCREEN_HEIGHT)

        # Load the level map
        map_location = "assets/level/level_map.json"
        layer_options = {"Tile Layer 1": {"use_spatial_hash": True, "spatial_hash_cell_size": 128}}
        self.level_map = arcade.tilemap.load_tilemap(map_location, s.SPRITE_SCALING, layer_options=layer_options)
        self.map_center_x = self.level_map.width * self.level_map.tile_width * s.SPRITE_SCALING / 2
        self.map_center_y = self.level_map.height * self.level_map.tile_height * s.SPRITE_SCALING / 2
        self.wall_tile_map = arcade.load_tilemap(map_location, s.SPRITE_SCALING, layer_options)
        self.wall_tile_map = arcade.Scene.from_tilemap(self.wall_tile_map)
        scene_wall_sprite_list = self.wall_tile_map.get_sprite_list("Tile Layer 1")
        self.wall_list.extend(scene_wall_sprite_list)

        # Create the sprites
        self.player_sprite = player.Seraphima(self.map_center_x, self.map_center_y, s.PLAYER_SCALING)
        self.player_list.append(self.player_sprite)
        self.generate_walls(self.level_map.width, self.level_map.height)
        self.monster_sprite = ghost.GhostMonster(self.map_center_x, self.map_center_y + 60, s.MONSTER_SCALING)
        self.monster_sprite.texture = arcade.load_texture("assets/enemies/ghost/g_south-0.png")
        self.monster_list.append(self.monster_sprite)

        # Physics engine, so we don't run into walls
        self.player_and_wall_collider = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
        self.player_and_monster_collider = arcade.PhysicsEngineSimple(self.player_sprite, self.monster_list)
        self.monster_and_wall_collider = arcade.PhysicsEngineSimple(self.monster_sprite, self.wall_list)

    def on_draw(self):

        # Use the camera
        self.camera.use()

        # Draw the monsters on top of the shadow
        self.channel1.use()
        self.channel1.clear()
        self.monster_list.draw()

        # Draw the walls
        self.channel0.use()
        self.channel0.clear()
        self.wall_list.draw()
        self.use()
        self.clear()

        # Calculate the light position
        position = (self.player_sprite.position[0] - self.camera.position[0],
             self.player_sprite.position[1] - self.camera.position[1])

        # Run the shader and render to the window
        self.box_shadertoy.program['lightPosition'] = position
        self.box_shadertoy.program['lightSize'] = s.SPOTLIGHT_SIZE
        self.box_shadertoy.render()

        # Draw the player
        self.player_list.draw()
        self.swordslash_list.draw()

    def on_update(self, delta_time: float = 1 / 240):

        # Update the physics
        self.player_and_wall_collider.update()
        self.player_and_monster_collider.update()
        self.monster_and_wall_collider.update()
        self.monster_list.update()
        self.scroll_to_player()
        self.process_key_presses()
        for projectile in self.swordslash_list:
            projectile.update_animation(delta_time)
            projectile.update()
            if arcade.check_for_collision_with_list(projectile, self.wall_list):
                projectile.is_hitting_wall = True

        # Make a projectile if the player is slashing and there currently isn't another one
        if self.player_sprite.is_slashing and self.player_sprite.c_key_timer == 0 and not self.swordslash_list:
            slash_projectile = ss.SwordSlash(self.player_sprite)
            self.swordslash_list.append(slash_projectile)

        # Update the player
        self.player_sprite.update_animation(delta_time)
        if self.player_sprite.c_key_timer > 0:
            self.player_sprite.change_x *= s.SLASH_CHARGE_SPEED_MODIFIER
            self.player_sprite.change_y *= s.SLASH_CHARGE_SPEED_MODIFIER

        # Handle the player's slash
        player_collisions = arcade.check_for_collision_with_list(self.player_sprite, self.monster_list)
        for projectile in self.swordslash_list:
            projectile_collisions = arcade.check_for_collision_with_list(projectile, self.monster_list)
            for monster in projectile_collisions:
                monster.is_being_hurt = True
        for monster in player_collisions:
            if self.player_sprite.is_slashing:
                monster.is_being_hurt = True

        # Handle spawning in more monsters if there aren't any on the screen, and it's been a few seconds
        self.spawn_monsters_on_empty_list()

        # Make sure the new monsters cant walk through walls, this causes monsters to bounce off the walls
        for monster in self.monster_list:
            if arcade.check_for_collision_with_list(monster, self.wall_list):
                monster.change_x *= -1
                monster.change_y *= -1

    def load_shader(self):
        shader_file_path = Path("shaders/box_shadows.glsl")
        window_size = self.get_size()
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
        map_width = int(map_width * self.level_map.tile_width * s.SPRITE_SCALING)
        map_height = int(map_height * self.level_map.tile_height * s.SPRITE_SCALING)
        for _ in range(150):
            x = random.randint(100, map_width - 100)
            y = random.randint(100, map_height - 100)
            wall = arcade.Sprite("assets/level/wall.png", s.SPRITE_SCALING)
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
                x = random.randint(100, map_width - 100)
                y = random.randint(100, map_height - 100)
                wall.center_x = x
                wall.center_y = y
            if random.random() < 0.5:
                wall.angle = 90

    def spawn_monsters_on_empty_list(self):

        # Handle spawning in more monsters if there aren't any on the screen, and it's been a few seconds
        if not self.monster_list:
            if self.no_ghost_timer != 0:
                self.no_ghost_timer = time.time()
            elif time.time() - self.no_ghost_timer > 5:
                self.spawn_monsters()
                # Reset the timer and increase the number of ghosts to spawn
                self.ghosts_to_spawn += 0.5
            self.ghosts_to_spawn *= self.ghosts_to_spawn_multiplier
            self.no_ghost_timer = 0.0

    def spawn_monsters(self):
        for i in range(int(self.ghosts_to_spawn)):
            random_x = random.uniform(self.player_sprite.center_x - 50, self.player_sprite.center_x + 50)
            random_y = random.uniform(self.player_sprite.center_y - 50, self.player_sprite.center_y + 50)
            if random_x < 0 or random_x > self.level_map.width or random_y < 0 or \
                    random_y > self.level_map.height:
                random_x = random.uniform(0, self.width)
                random_y = random.uniform(0, self.height)
            monster = ghost.GhostMonster(random_x, random_y, s.MONSTER_SCALING)
            monster.texture = arcade.load_texture("assets/enemies/ghost/g_south-0.png")

            # Check if the new monster collides with any existing monsters, wall sprites or player
            collision = False
            for wall in self.wall_list:
                if wall.collides_with_point((random_x, random_y)):
                    collision = True
                    break
            for mon in self.monster_list:
                if mon.collides_with_point((random_x, random_y)):
                    collision = True
            if self.player_sprite.collides_with_point((random_x, random_y)):
                collision = True
            if not collision:
                self.monster_list.append(monster)
            else:

                # If there is a collision, try again
                self.spawn_monsters()

    def on_key_press(self, key, modifiers):
        self.key_press_buffer.add(key)

    def process_key_presses(self):
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0

        # Handle slashing, hold the c key for SLASH_CHARGE_TIME to activate
        if arcade.key.C in self.key_press_buffer:
            if self.player_sprite.c_key_timer == 0:
                self.player_sprite.c_key_timer = time.time()
            elif time.time() - self.player_sprite.c_key_timer >= s.SLASH_CHARGE_TIME:
                self.player_sprite.is_slashing = True
                self.player_sprite.c_key_timer = 0

        # Handle running, hold the shift key
        if arcade.key.LEFT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer \
                and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.RUN_SPEED_MODIFIER
            self.player_sprite.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "northwest"
            self.player_sprite.is_running = True
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer \
                and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.RUN_SPEED_MODIFIER
            self.player_sprite.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "southwest"
            self.player_sprite.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer \
                and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.RUN_SPEED_MODIFIER
            self.player_sprite.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "northeast"
            self.player_sprite.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer \
                and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.RUN_SPEED_MODIFIER
            self.player_sprite.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "southeast"
            self.player_sprite.is_running = True
        elif arcade.key.UP in self.key_press_buffer and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_y = s.PLAYER_MOVEMENT_SPEED * s.RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "north"
            self.player_sprite.is_running = True
        elif arcade.key.DOWN in self.key_press_buffer and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_y = -s.PLAYER_MOVEMENT_SPEED * s.RUN_SPEED_MODIFIER
            self.player_sprite.current_direction = "south"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.is_running = True
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = -s.PLAYER_MOVEMENT_SPEED * s.RUN_SPEED_MODIFIER
            self.player_sprite.current_direction = "west"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = s.PLAYER_MOVEMENT_SPEED * s.RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "east"
            self.player_sprite.is_running = True

        # Handle basic movement use the arrow keys
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer:
            self.player_sprite.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7
            self.player_sprite.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.current_direction = "northwest"
            self.player_sprite.is_walking = True
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer:
            self.player_sprite.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7
            self.player_sprite.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.current_direction = "southwest"
            self.player_sprite.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer:
            self.player_sprite.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7
            self.player_sprite.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.current_direction = "northeast"
            self.player_sprite.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer:
            self.player_sprite.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7
            self.player_sprite.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.current_direction = "southeast"
            self.player_sprite.is_walking = True
        elif arcade.key.UP in self.key_press_buffer:
            self.player_sprite.change_y = s.PLAYER_MOVEMENT_SPEED
            self.player_sprite.current_direction = "north"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.is_walking = True
        elif arcade.key.DOWN in self.key_press_buffer:
            self.player_sprite.change_y = -s.PLAYER_MOVEMENT_SPEED
            self.player_sprite.current_direction = "south"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.is_walking = True
        elif arcade.key.LEFT in self.key_press_buffer:
            self.player_sprite.change_x = -s.PLAYER_MOVEMENT_SPEED
            self.player_sprite.current_direction = "west"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer:
            self.player_sprite.change_x = s.PLAYER_MOVEMENT_SPEED
            self.player_sprite.current_direction = "east"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.is_walking = True

        # Modify the movement speed again to make a charge effect when c is pressed
        if arcade.key.C in self.key_press_buffer:
            self.player_sprite.change_x *= s.SLASH_CHARGE_SPEED_MODIFIER
            self.player_sprite.change_y *= s.SLASH_CHARGE_SPEED_MODIFIER

    def on_key_release(self, key, modifiers):
        self.key_press_buffer.discard(key)
        if not self.key_press_buffer:
            if self.player_sprite.is_walking:
                self.player_sprite.is_walking = False
            if self.player_sprite.is_running:
                self.player_sprite.is_running = False
                self.player_sprite.just_stopped_running = True
        elif arcade.key.C not in self.key_press_buffer:
            self.player_sprite.c_key_timer = 0

    def scroll_to_player(self, speed=s.CAMERA_SPEED):
        position = Vec2(self.player_sprite.center_x - self.width / 2,
                        self.player_sprite.center_y - self.height / 2)
        self.camera.move_to(position, speed)


if __name__ == "__main__":
    window = MyGame(s.SCREEN_WIDTH, s.SCREEN_HEIGHT, s.SCREEN_TITLE)
    # window.set_location(1025, 35)
    arcade.run()
