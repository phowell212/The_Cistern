import math
import random
import arcade
import time
import player
import flameslash
import swordslash
import darkfairy
import darkfairy_spell
import altar
import settings as s
import ghost as g
from arcade.experimental import Shadertoy
from arcade.experimental.crt_filter import CRTFilter
from pathlib import Path
from pyglet.math import Vec2


class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title, resizable=True)

        # Init the sprites
        self.player = None
        self.wall_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.ghost_list = arcade.SpriteList()
        self.swordslash_list = arcade.SpriteList()
        self.flameslash_list = arcade.SpriteList()
        self.heart_list = arcade.SpriteList()
        self.boss_list = arcade.SpriteList()
        self.dark_fairy_spell_list = arcade.SpriteList()
        self.secret_door_list = arcade.SpriteList()
        self.altar_list = arcade.SpriteList()
        self.heart_frames = []
        self.heart_frame = 0

        # Init counters, constants, arrays, flags, and sounds
        self.level = 1
        self.altar_points = 0
        self.key_press_buffer = set()
        self.ghosts_to_spawn = 4.0
        self.ghosts_to_spawn_multiplier = 1.4
        self.no_ghost_timer = 0.0
        self.transition_time = 0.0
        self.score = 0
        self.music_timer = time.time()
        self.general_timer = time.time()
        self.health = s.PLAYER_STARTING_HEALTH
        self.is_transitioning = False
        self.is_dead = False
        self.is_faded_out = False
        self.has_spawned_player_death_ghost = True
        self.title_screen = True
        self.restart = False
        self.debug_mode = True
        self.swoosh_sounds = []
        self.is_door_open = False
        self.door_open_sound = arcade.load_sound("sounds/door_open.wav")
        for i in range(0, 3):
            self.swoosh_sounds.append(arcade.load_sound(f"sounds/sword_swoosh-{i}.wav"))
        arcade.play_sound(arcade.load_sound("sounds/most.wav"), s.MUSIC_VOLUME)
        self.music_timer = time.time() + (5 * 60) + 57

        # Make the colors
        self.level_1_floor_color = (108, 121, 147)
        self.level_2_floor_color = (51, 25, 0)

        # Init the shaders
        self.box_shadertoy = None
        self.channel0 = None
        self.channel1 = None
        self.load_shader(self.level)

        # Init the pathfinding vars
        self.path = None
        self.barrier_list = None

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
        self.generate_walls(self.level_map.width, self.level_map.height)
        self.generate_secret_door()

        # Make the altar
        self.altar = altar.Altar(2837, -348)
        self.altar_list.append(self.altar)

        # Create playing field sprites
        self.player = player.Player(self.map_center_x, self.map_center_y, s.PLAYER_SCALING)
        self.player_list.append(self.player)
        self.spawn_ghosts_on_empty_list()
        self.load_heart_frames()
        for i in range(int(self.health / 10)):
            heart = arcade.Sprite("assets/heart/heart-0.png", s.HEART_SCALING)
            heart.center_x = (self.width - 200) + i * 40
            heart.center_y = 45
            self.heart_list.append(heart)
        self.heart_list.reverse()

        # Make the physics engine
        self.player_and_wall_collider = arcade.PhysicsEngineSimple(self.player, self.wall_list)
        self.player_and_secret_door_collider = arcade.PhysicsEngineSimple(self.player, self.secret_door_list)
        self.player_and_ghost_collider = None
        self.player_and_boss_collider = None
        self.boss_and_wall_collider = None
        self.ghost_and_wall_collider = None
        self.ghost_and_ghost_collider = None
        self.ghost_and_boss_collider = None
        self.camera = arcade.Camera2D()
        self.camera_gui = arcade.Camera2D()

        # Make the pathfinding vars
        self.playing_field_left_boundary = 0
        self.playing_field_right_boundary = self.level_map.width * self.level_map.tile_width * s.SPRITE_SCALING
        self.playing_field_top_boundary = self.level_map.height * self.level_map.tile_height * s.SPRITE_SCALING
        self.playing_field_bottom_boundary = 0
        self.grid_size = 128 * s.SPRITE_SCALING
        self.barrier_list = arcade.AStarBarrierList(self.player, self.wall_list, self.grid_size,
                                                    self.playing_field_left_boundary,
                                                    self.playing_field_right_boundary,
                                                    self.playing_field_bottom_boundary,
                                                    self.playing_field_top_boundary)

        # Make the CRT filter
        self.crt_filter = CRTFilter(width, height, resolution_down_scale=1.0,
                                    hard_scan=-3.0,
                                    hard_pix=-3.0,
                                    display_warp=Vec2(1 / 32, 1 / 64))

    def on_draw(self):
        self.camera.use()

        # Select the CRT filter (bottom layer) to draw on, then draw it, this gives the floor a cool effect
        self.crt_filter.use()
        self.crt_filter.clear()
        self.draw_channel_crt()

        # Select channel 1 (below-shadow layer) to draw on, then draw it
        self.channel1.use()
        self.channel1.clear()
        self.draw_channel1()

        # Select channel 0 (shadow layer) to draw on, then draw it
        self.channel0.use()
        self.channel0.clear()
        self.draw_channel0()

        # Select our window (top game layer) to draw on, then draw it
        self.use()
        self.clear()
        self.crt_filter.draw()
        self.draw_window()

        # Select the GUI camera (top layer) to draw on, then draw the GUI
        self.camera_gui.use()
        self.draw_gui()


    def on_update(self, delta_time: float = 1 / 60):
        self.update_physics()
        self.update_movement()
        self.update_projectiles()
        self.update_secret_door()
        self.update_music()

        self.update_player(delta_time)
        self.update_gui(delta_time)
        self.update_ghosts(delta_time)
        self.update_bosses(delta_time)
        self.update_altar(delta_time)

    def on_key_press(self, key: arcade.key, modifiers):
        if self.heart_list:
            self.key_press_buffer.add(key)
        if self.restart:
            if key == arcade.key.X:
                self.key_press_buffer.add(key)

    def on_key_release(self, key: arcade.key, modifiers):
        self.key_press_buffer.discard(key)
        if not self.key_press_buffer:
            if self.player.is_walking:
                self.player.is_walking = False
            if self.player.is_running:
                self.player.is_running = False
                self.player.just_stopped_running = True
        elif arcade.key.C not in self.key_press_buffer:
            self.player.c_key_timer = 0

    def draw_channel_crt(self):
        # Draw the floor
        # If the floor is not transitioning, draw the floor of the current level
        if not self.is_transitioning:
            if self.level == 1:
                arcade.draw_lrbt_rectangle_filled(-99999, -99999, 99999, 99999, self.level_1_floor_color)
            elif self.level == 2:
                arcade.draw_lrbt_rectangle_filled(-99999, -99999, 99999, 99999, self.level_2_floor_color)

        # If the floor is transitioning, use the shader to determine the color of the floor
        else:
            self.transition_time += 1

            # Calculate progress (0.0 to 1.0) of transition
            progress = min(self.transition_time / 300, 1.0)

            # Set the mix value for the shader
            self.box_shadertoy.program["iMix"] = progress

            # Interpolate between current and target colors
            red = int(self.lerp(self.level_1_floor_color[0], self.level_2_floor_color[0], progress))
            green = int(self.lerp(self.level_1_floor_color[1], self.level_2_floor_color[1], progress))
            blue = int(self.lerp(self.level_1_floor_color[2], self.level_2_floor_color[2], progress))

            # Draw the floor with the interpolated color
            arcade.draw_lrbt_rectangle_filled(-99999, -99999, 99999, 99999, (red, green, blue))

            # Check if transition is complete
            if progress >= 1.0:
                self.is_transitioning = False
                self.transition_time = 0

    def draw_channel0(self):
        self.wall_list.draw()
        self.secret_door_list.draw()

    def draw_channel1(self):
        self.altar_list.draw()
        self.ghost_list.draw()
        self.boss_list.draw()
        self.dark_fairy_spell_list.draw()

    def draw_window(self):
        screen_center = (self.width / 2, self.height / 2)
        self.box_shadertoy.program['lightPosition'] = screen_center
        self.box_shadertoy.program['lightSize'] = s.SPOTLIGHT_SIZE
        self.box_shadertoy.render()

        # Draw the projectiles first
        self.swordslash_list.draw()
        self.flameslash_list.draw()

        self.player_list.draw()

    def draw_gui(self):
        self.heart_list.draw()
        if s.ghosts_killed == 0:
            self.score = 0
        score_text = f"Score: {int(self.score / 6.5)}.0"

        ghost_text = f"Ghosts: {len(self.ghost_list)}.0"
        arcade.draw_text(ghost_text, x=40, y=70, color=(255, 255, 242), font_size=19, font_name="Garamond")
        arcade.draw_text(score_text, x=40, y=32, color=(255, 255, 242), font_size=19, font_name="Garamond")

        # Draw the title screen if the game hasn't started yet
        if self.title_screen:
            arcade.draw_text("Welcome to: The Cistern", x=s.SCREEN_WIDTH / 2, y=s.SCREEN_HEIGHT / 2 + 50,
                             color=(255, 255, 242), font_size=72, font_name="Garamond", anchor_x="center",
                             anchor_y="baseline", bold=True)
            arcade.draw_text("Press any key to start.", x=s.SCREEN_WIDTH / 2, y=s.SCREEN_HEIGHT / 2 - 100,
                             color=(255, 255, 242), font_size=36, font_name="Garamond", anchor_x="center",
                             anchor_y="baseline")

        # Draw the game over screen if the player has died
        if not self.heart_list:
            arcade.draw_text("GAME OVER", x=s.SCREEN_WIDTH / 2, y=s.SCREEN_HEIGHT / 2 + 50,
                             color=(255, 255, 242), font_size=72, font_name="Garamond", anchor_x="center",
                             anchor_y="baseline", bold=True)

            # Draw the game over effects:
            # If the player isn't already transparent make the player sprite slowly fade out
            if self.player.alpha != 0:
                self.player.alpha -= 0.03 * self.player.alpha
                self.player.alpha = max(0, self.player.alpha)
            elif not self.is_faded_out:
                self.is_faded_out = True
                self.has_spawned_player_death_ghost = False
                self.restart = True

            # If the player is fully transparent, spawn a ghost on their death location
            elif not self.has_spawned_player_death_ghost:
                ghost_sprite = g.GhostMonster(self.player.center_x, self.player.center_y,
                                              s.PLAYER_SCALING)
                ghost_sprite.texture = arcade.load_texture("assets/enemies/ghost/g_south-0.png")
                ghost_sprite.is_death_ghost = True
                self.player.remove_from_sprite_lists()
                self.ghost_list.append(ghost_sprite)
                self.has_spawned_player_death_ghost = True

        # Draw the restart text if the player's ghost has spawned
        if self.restart:
            arcade.draw_text("Press x to restart.", x=s.SCREEN_WIDTH / 2, y=s.SCREEN_HEIGHT / 2 - 100,
                             color=(255, 255, 242), font_size=36, font_name="Garamond", anchor_x="center",
                             anchor_y="baseline")

        # Draw the debug text if the debug mode is enabled and the debug key is pressed
        if self.debug_mode and arcade.key.D in self.key_press_buffer:
            num_ghosts_hunting = 0
            ghost_velocities = []
            for ghost in self.ghost_list:
                if ghost.is_hunting:
                    num_ghosts_hunting += 1
                ghost_velocities.append((ghost.change_x, ghost.change_y))
            text = f"Player position: ({int(self.player.position[0])}, {int(self.player.position[1])}), " \
                   f" ({int(self.player.top)}, {int(self.player.left)}, " \
                   f"{int(self.player.bottom)}, {int(self.player.right)})."
            ghost_hunting_text = f"Ghosts hunting you: {num_ghosts_hunting}."
            arcade.draw_text(ghost_hunting_text, x=40, y=964, color=(255, 255, 242), font_size=19,
                             font_name="Garamond")
            for i in range((len(ghost_velocities))):
                ghost_velocity_text = f"\n    Ghost {i} velocity: ({ghost_velocities[i][0]}, " \
                                      f" {ghost_velocities[i][1]})."
                ghost_position_text = f"Ghost {i} position: ({int(self.ghost_list[i].position[0])}, " \
                                      f" {int(self.ghost_list[i].position[1])})."
                arcade.draw_text(ghost_velocity_text, x=40, y=904 - (i * 30 * 2), color=(255, 255, 242),
                                 font_size=19, font_name="Garamond")
                arcade.draw_text(ghost_position_text, x=90, y=874 - (i * 30 * 2), color=(255, 255, 242),
                                 font_size=19, font_name="Garamond")
                if i == 4:
                    break
            arcade.draw_text(text, x=40, y=934, color=(255, 255, 242), font_size=19,
                             font_name="Garamond")

    def update_physics(self):
        if self.heart_list:
            self.player_and_ghost_collider = arcade.PhysicsEngineSimple(self.player, self.ghost_list)
            self.player_and_ghost_collider.update()
            self.player_and_wall_collider.update()
            if s.bosses_killed < 3:
                self.player_and_secret_door_collider.update()
        else:
            for ghost in self.ghost_list:
                ghost.can_hunt = False

        if self.boss_list:
            for boss in self.boss_list:
                self.boss_and_wall_collider = arcade.PhysicsEngineSimple(boss, self.wall_list)
                self.boss_and_wall_collider.update()
                self.player_and_boss_collider = arcade.PhysicsEngineSimple(self.player, self.boss_list)
                self.player_and_boss_collider.update()

        for ghost in self.ghost_list:
            if arcade.check_for_collision_with_list(ghost, self.wall_list):
                self.ghost_and_wall_collider = arcade.PhysicsEngineSimple(ghost, self.wall_list)
                self.ghost_and_wall_collider.update()
            if arcade.check_for_collision_with_list(ghost, self.ghost_list):
                self.ghost_and_ghost_collider = arcade.PhysicsEngineSimple(ghost, self.ghost_list)
                self.ghost_and_ghost_collider.update()
            if self.boss_list:
                self.ghost_and_boss_collider = arcade.PhysicsEngineSimple(ghost, self.boss_list)
                self.ghost_and_boss_collider.update()

    def update_movement(self):
        self.scroll_to_player()
        self.process_key_presses()
        for projectile in self.swordslash_list:
            if arcade.check_for_collision_with_list(projectile, self.wall_list):
                projectile.is_hitting_wall = True
            elif arcade.check_for_collision_with_list(projectile, self.secret_door_list):
                projectile.is_hitting_wall = True
        for projectile in self.flameslash_list:
            if arcade.check_for_collision_with_list(projectile, self.wall_list):
                projectile.is_hitting_wall = True
            elif arcade.check_for_collision_with_list(projectile, self.secret_door_list):
                projectile.is_hitting_wall = True

        # Decrease the player's speed when a boss is out because for whatever reason the player's speed is increased
        # when more bosses are spawned. I know you could use a loop to do this but why do that when if statements are
        # faster and easier to read?
        if len(self.boss_list) >= 1:
            self.player.change_x *= 0.75
            self.player.change_y *= 0.75
            if len(self.boss_list) >= 2:
                self.player.change_x *= 0.75
                self.player.change_y *= 0.75
                if len(self.boss_list) >= 3:
                    self.player.change_x *= 0.8
                    self.player.change_y *= 0.8
                    if len(self.boss_list) >= 4:
                        self.player.change_x *= 0.85
                        self.player.change_y *= 0.85
                        if len(self.boss_list) >= 5:
                            self.player.change_x *= 0.9
                            self.player.change_y *= 0.9

    def update_projectiles(self):

        # Update the swordslash projectiles
        self.swordslash_list.update()
        self.swordslash_list.update_animation()

        # Update the flameslash projectiles
        self.flameslash_list.update()
        self.flameslash_list.update_animation()

        # Make a new projectile if the attack key is pressed and the player is not already attacking
        if self.player.is_slashing and self.player.c_key_timer == 0 and not self.swordslash_list and \
                s.bosses_killed < 1:
            slash_projectile = swordslash.SwordSlash(self.player)
            self.swordslash_list.append(slash_projectile)
            arcade.play_sound(random.choice(self.swoosh_sounds), s.SWOOSH_VOLUME)
        elif self.player.is_slashing and self.player.c_key_timer == 0 and not self.flameslash_list and \
                s.bosses_killed >= 1:
            flameslash_projectile = flameslash.FlameSlash(self.player)
            self.flameslash_list.append(flameslash_projectile)
            arcade.play_sound(random.choice(self.swoosh_sounds), s.SWOOSH_VOLUME)

        # Handle swordslash dealing damage
        if self.swordslash_list:
            for projectile in self.swordslash_list:
                projectile_collisions = arcade.check_for_collision_with_list(projectile, self.ghost_list)
                for ghost in projectile_collisions:
                    self.handle_ghost_damage(ghost, projectile)
                boss_collisions = arcade.check_for_collision_with_list(projectile, self.boss_list)
                for boss in boss_collisions:
                    self.handle_boss_damage(boss, projectile)

        # Handle flameslash dealing damage
        if self.flameslash_list:
            for projectile in self.flameslash_list:
                projectile_collisions = arcade.check_for_collision_with_list(projectile, self.ghost_list)
                for ghost in projectile_collisions:
                    self.handle_ghost_damage(ghost, projectile)
                boss_collisions = arcade.check_for_collision_with_list(projectile, self.boss_list)
                for boss in boss_collisions:
                    self.handle_boss_damage(boss, projectile)

        # Update the dark fairy's spells and make them deal damage
        self.dark_fairy_spell_list.update()
        self.dark_fairy_spell_list.update_animation()
        for spell in self.dark_fairy_spell_list:
            self.move_spell(spell)
            spell_collisions = arcade.check_for_collision_with_list(spell, self.ghost_list)
            for ghost in spell_collisions:
                self.handle_ghost_damage(ghost, spell)
            if arcade.check_for_collision(spell, self.player):
                self.handle_player_damage()

    def update_player(self, delta_time):
        self.player.update_animation(delta_time)
        if self.player.c_key_timer > 0:
            self.player.change_x *= s.SLASH_CHARGE_SPEED_MODIFIER
            self.player.change_y *= s.SLASH_CHARGE_SPEED_MODIFIER

    def update_gui(self, delta_time):
        self.heart_frame += 18 * delta_time
        for heart in self.heart_list:
            if self.heart_frame < len(self.heart_frames):
                heart.texture = self.heart_frames[int(self.heart_frame)]
            else:
                self.heart_frame = 0

        # Set the first heart's size to represent the player's health
        for heart in self.heart_list:
            heart.scale = (self.health / len(self.heart_list)) / 100
            break

        # If a ghost dies increase the counter
        for ghost in self.ghost_list:
            if ghost.health <= 0 and self.restart == False:
                if s.ghosts_killed != 0:
                    self.score += ghost.scale * (self.level * self.level)
                else:
                    self.score += 6.5

        # If the boss dies increase the counter
        for boss in self.boss_list:
            if boss.health == 0 and boss.phase == 2:
                self.score += 11

    def update_ghosts(self, delta_time):
        self.ghost_list.update(delta_time)  # Pass delta_time to ghost_list update
        self.ghost_list.update_animation(delta_time)
        self.spawn_ghosts_on_empty_list()
        for ghost in self.ghost_list:
            if not ghost.is_being_hurt and self.title_screen is False:
                self.move_ghost(ghost)
            if ghost.left < 0 or ghost.top > 2559 or ghost.right > 2559 or ghost.bottom < 0:
                ghost.health = 0

            # Make the ghosts deal damage to the player
            if arcade.check_for_collision(ghost, self.player):
                self.handle_player_damage()

    def update_bosses(self, delta_time):
        self.boss_list.update(delta_time)  # Pass delta_time to boss_list update
        self.boss_list.update_animation()
        if self.boss_list:
            self.move_boss()

            # Let the boss cast spells
            for boss in self.boss_list:
                if (random.randint(0, 90) == 0 and arcade.get_distance_between_sprites(self.player, boss) < 700 and
                    boss.phase == 1 and not self.dark_fairy_spell_list) or (random.randint(0, 80) == 0 and
                                                                            arcade.get_distance_between_sprites(
                                                                                self.player,
                                                                                boss) < 400 and boss.phase == 2):
                    boss.is_casting = True
                    spell_x = self.player.center_x + random.randint(-300, 300)
                    spell_y = self.player.center_y + random.randint(-300, 300)
                    spell = darkfairy_spell.DarkFairySpell(spell_x, spell_y, s.BOSS_SCALING, boss)
                    distance = arcade.get_distance_between_sprites(spell, self.player)
                    if distance > spell.min_spawn_distance:
                        self.dark_fairy_spell_list.append(spell)
                    else:
                        while distance <= spell.min_spawn_distance:
                            spell_x = self.player.center_x + random.randint(-500, 500)
                            spell_y = self.player.center_y + random.randint(-500, 500)
                            spell.center_x, spell.center_y = spell_x, spell_y
                            distance = arcade.get_distance_between_sprites(spell, self.player)
                        self.dark_fairy_spell_list.append(spell)

        # Spawn the boss once you kill enough ghosts
        if s.ghosts_killed % 15 == 0 and s.ghosts_killed != 0:
            if s.ghosts_killed == 15:
                self.spawn_boss()
                s.ghosts_killed += 1
            else:
                if random.randint(0, 3) == 0:
                    self.spawn_boss()
                    s.ghosts_killed += 1
                if random.randint(0, 2) == 0:
                    s.bosses_to_spawn = 2

    def update_secret_door(self):
        if s.bosses_killed >= 3:
            self.secret_door_list.clear()
            if not self.is_door_open:
                self.is_door_open = True
                arcade.play_sound(self.door_open_sound, 0.5)

    def update_altar(self, delta_time):
        self.altar_list.update_animation(delta_time)
        if arcade.check_for_collision(self.player, self.altar):
            self.altar_points += 1
            self.score -= 1

            if self.player and self.level == 1 and self.score > 0:
                if arcade.check_for_collision_with_list(self.player, self.altar_list):
                    self.altar_points += 1
                    self.score -= 1

                # Load in the shader for level 2 if the player has enough altar points
                if self.altar_points >= 100 and self.level == 1:
                    self.altar_points = 0
                    self.level = 2
                    self.load_shader(self.level)
                    self.is_transitioning = True

    def update_music(self):
        if time.time() > self.music_timer:
            arcade.play_sound(arcade.load_sound("sounds/most.wav"), s.MUSIC_VOLUME)
            self.music_timer = time.time() + (5 * 60) + 57

    def load_shader(self, level: int):
        shader_file_path = Path(f"shaders/level_{level}_shader.glsl")
        window_size = self.get_size()
        self.box_shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)
        if self.level == 2:
            self.box_shadertoy.program['iMix'] = 0

        # Create the channels 0 and 1 frame buffers.
        # Make the buffer the size of the window, with 4 channels (RGBA)
        self.channel0 = self.box_shadertoy.ctx.framebuffer(
            color_attachments=[self.box_shadertoy.ctx.texture(window_size, components=4)])
        self.channel1 = self.box_shadertoy.ctx.framebuffer(
            color_attachments=[self.box_shadertoy.ctx.texture(window_size, components=4)])

        # Assign the frame buffers to the channels
        self.box_shadertoy.channel_0 = self.channel0.color_attachments[0]
        self.box_shadertoy.channel_1 = self.channel1.color_attachments[0]

    def load_heart_frames(self):
        for i in range(0, 7):
            self.heart_frames.append(arcade.load_texture(f"assets/heart/heart-{i}.png"))

    def generate_walls(self, map_width, map_height):
        map_width = int(map_width * self.level_map.tile_width * s.SPRITE_SCALING)
        map_height = int(map_height * self.level_map.tile_height * s.SPRITE_SCALING)
        for i in range(70):
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
                elif wall.collides_with_list(self.player_list):
                    overlap = True
                    break
                elif wall.collides_with_list(self.boss_list):
                    overlap = True
                    break
            if not overlap:
                if random.random() > 0.9:
                    # Ensure wall.scale is numeric before modifying it
                    if isinstance(wall.scale, (int, float)):
                        wall.scale *= random.randint(50, 200) / 100
                    if random.random() > 0.95 and isinstance(wall.scale, (int, float)):
                        wall.scale *= random.randint(150, 400) / 100
                if random.random() > 0.9 and isinstance(wall.scale, (int, float)):
                    wall.scale *= random.randint(50, 200) / 100
                self.wall_list.append(wall)
            else:
                x = random.randint(100, map_width - 100)
                y = random.randint(100, map_height - 100)
                wall.center_x = x
                wall.center_y = y

    def generate_secret_door(self):
        secret_door = arcade.Sprite("assets/level/wall.png", 0.55)
        secret_door.center_x = 2493
        secret_door.center_y = 66
        self.secret_door_list.append(secret_door)

    @staticmethod
    def lerp(a, b, t):
        return a + (b - a) * t

    def handle_player_damage(self):
        self.health -= 3
        if self.health <= 0 and self.heart_list:
            self.heart_list.pop()
            self.health = s.HEART_HEALTH
        if self.health < 0:
            self.is_dead = True

    @staticmethod
    def handle_boss_damage(boss: darkfairy.DarkFairy, projectile):
        if projectile.type == "swordslash":
            boss.health -= 1
        elif projectile.type == "flameslash":
            boss.health -= 2
        boss.is_being_hurt = True

    @staticmethod
    def handle_ghost_damage(ghost: g.GhostMonster, projectile):
        if projectile.type == "swordslash" or projectile.type == "spell":
            ghost.health -= 1
        elif projectile.type == "flameslash":
            ghost.health -= 2
        ghost.is_being_hurt = True

    def move_ghost(self, ghost: g.GhostMonster):
        if not self.is_dead and \
                arcade.get_distance_between_sprites(ghost, self.player) < s.MONSTER_VISION_RANGE:
            if not ghost.is_hunting:
                ghost.is_hunting = True

            self.path = arcade.astar_calculate_path(ghost.position,
                                                    self.player.position,
                                                    self.barrier_list,
                                                    diagonal_movement=False)

            # Figure out where we want to go
            try:
                if ghost.current_path_position < len(self.path) - 1:
                    next_x = self.path[ghost.current_path_position + 1][0]
                    next_y = self.path[ghost.current_path_position + 1][1]
                else:

                    # We are at the end of the path
                    next_x = self.player.center_x
                    next_y = self.player.center_y
            except TypeError:
                next_x = self.player.center_x
                next_y = self.player.center_y

            # What's the difference between the two
            diff_x = next_x - ghost.center_x
            diff_y = next_y - ghost.center_y

            # What's our angle
            angle = math.atan2(diff_y, diff_x)

            # Calculate the travel vector
            ghost.change_x = math.cos(angle) * s.MONSTER_MOVEMENT_SPEED
            ghost.change_y = math.sin(angle) * s.MONSTER_MOVEMENT_SPEED
            if (ghost.change_y ** 2 + ghost.change_x ** 2) ** 0.5 > s.MONSTER_MOVEMENT_SPEED:
                ghost.change_x += s.MONSTER_MOVEMENT_SPEED * ghost.change_x / abs(ghost.change_x)
                ghost.change_y += s.MONSTER_MOVEMENT_SPEED * ghost.change_y / abs(ghost.change_y)

            # Recalculate distance after the move
            distance = math.sqrt((ghost.center_x - next_x) ** 2 + (ghost.center_y - next_y) ** 2)

            # If we're close enough, move to the next point
            if distance < s.MONSTER_MOVEMENT_SPEED:
                ghost.current_path_position += 1

                # If we're at the end of the path, start over
                if ghost.current_path_position >= len(self.path):
                    ghost.current_path_position = 0

        # If we can't find a path, or are far enough away from the player just move randomly:
        else:
            ghost.is_hunting = False
            if random.randint(0, 100) == 0:
                ghost.change_x = random.uniform(-s.MONSTER_MOVEMENT_SPEED, s.MONSTER_MOVEMENT_SPEED)
                ghost.change_y = random.uniform(-s.MONSTER_MOVEMENT_SPEED, s.MONSTER_MOVEMENT_SPEED)

    def move_spell(self, spell: darkfairy_spell.DarkFairySpell):
        if spell.change_x == 0 and spell.change_y == 0:
            angle = math.atan2(self.player.center_y - spell.center_y,
                               self.player.center_x - spell.center_x)
            spell.change_x = math.cos(angle) * s.SPELL_MOVEMENT_SPEED
            spell.change_y = math.sin(angle) * s.SPELL_MOVEMENT_SPEED
        elif spell.current_frame == int(len(spell.phase_1_frames) / 2):
            angle = math.atan2(self.player.center_y - spell.center_y,
                               self.player.center_x - spell.center_x)
            spell.change_x = math.cos(angle) * s.SPELL_MOVEMENT_SPEED
            spell.change_y = math.sin(angle) * s.SPELL_MOVEMENT_SPEED

    def move_boss(self):
        for boss in self.boss_list:
            if random.randint(0, 60) == 0:
                boss.change_x = random.randint(int(-s.BOSS_MOVEMENT_SPEED * boss.movement_speed_modifier),
                                               int(s.BOSS_MOVEMENT_SPEED * boss.movement_speed_modifier))
                boss.change_y = random.randint(int(-s.BOSS_MOVEMENT_SPEED * boss.movement_speed_modifier),
                                               int(s.BOSS_MOVEMENT_SPEED * boss.movement_speed_modifier))

    def spawn_ghosts(self, level: int):
        for i in range(int(self.ghosts_to_spawn)):
            random_x = random.uniform(self.player.center_x - 50, self.player.center_x + 50)
            random_y = random.uniform(self.player.center_y - 50, self.player.center_y + 50)
            if random_x < 0 or random_x > self.level_map.width or random_y < 0 or \
                    random_y > self.level_map.height:
                random_x = random.uniform(0, self.width)
                random_y = random.uniform(0, self.height)
            ghost = g.GhostMonster(random_x, random_y, s.MONSTER_SCALING)
            ghost.texture = arcade.load_texture("assets/enemies/ghost/g_south-0.png")
            ghost.health *= 1 + level * 0.5

            # Check if the new ghost collides with any existing ghosts, wall sprites or player
            collision = False
            for wall in self.wall_list:
                if ghost.collides_with_sprite(wall):
                    collision = True
                    break
            if ghost.collides_with_sprite(self.player):
                collision = True
            if not collision:
                if isinstance(ghost.scale, (int, float)) and random.random() > 0.95:
                    ghost.scale *= random.uniform(0.8, 1.4)
                self.ghost_list.append(ghost)
            else:

                # If there is a collision, Don't spawn the ghost and try again
                self.ghosts_to_spawn += 1

            # If there are too many ghosts, don't spawn more, instead increase the movement
            over_ghosts = len(self.ghost_list) - 25
            if over_ghosts > 0:
                for ghost in self.ghost_list:
                    if over_ghosts >= 0:
                        break
                    elif ghost.movement_speed_modifier < 1.9:
                        ghost.movement_speed_modifier += 0.1
                        over_ghosts -= 1
                    else:
                        over_ghosts -= 1
            if self.ghosts_to_spawn > ((25 * s.bosses_killed) / 2) + 25:
                self.ghosts_to_spawn = ((25 * s.bosses_killed) / 2) + 25
            if self.ghosts_to_spawn > 40:
                self.ghosts_to_spawn = 40

    def spawn_ghosts_on_empty_list(self):

        # Handle spawning in more ghosts if there aren't any on the screen, and it's been a few seconds
        if not self.ghost_list:
            if self.no_ghost_timer != 0:
                self.no_ghost_timer = time.time()
            elif time.time() - self.no_ghost_timer > 5:
                self.spawn_ghosts(self.level)

                # Reset the timer and increase the number of ghosts to spawn
                self.ghosts_to_spawn += 0.5
            self.ghosts_to_spawn *= self.ghosts_to_spawn_multiplier
            self.no_ghost_timer = 0.0

    def spawn_boss(self):
        for i in range(s.bosses_to_spawn):

            # Always spawn the first boss
            if s.bosses_killed == 0:
                if len(self.boss_list) > 5:
                    break
                boss_x = self.player.center_x + random.randint(-500, 500)
                boss_y = self.player.center_y + random.randint(-500, 500)
                boss = darkfairy.DarkFairy(boss_x, boss_y, s.BOSS_SCALING)

                # Make the boss move into the play area if they are outside it
                distance = arcade.get_distance_between_sprites(boss, self.player)
                if distance > boss.min_spawn_distance and boss.left > 32 and boss.top < 2527 and \
                        boss.right < 2527 and boss.bottom > 32:
                    self.boss_list.append(boss)
                else:
                    while distance <= boss.min_spawn_distance or boss.left < 32 or boss.top > 2527 or \
                            boss.right > 2527 or boss.bottom < 32:
                        boss_x = self.player.center_x + random.randint(-500, 500)
                        boss_y = self.player.center_y + random.randint(-500, 500)
                        boss.center_x, boss.center_y = boss_x, boss_y
                        distance = arcade.get_distance_between_sprites(boss, self.player)
                    self.boss_list.append(boss)

            # Otherwise, let there be a chance to spawn a boss
            else:
                if len(self.boss_list) > 5:
                    break
                if random.randint(0, 5) == 0:
                    boss_x = self.player.center_x + random.randint(-500, 500)
                    boss_y = self.player.center_y + random.randint(-500, 500)
                    boss = darkfairy.DarkFairy(boss_x, boss_y, s.BOSS_SCALING)

                    distance = arcade.get_distance_between_sprites(boss, self.player)
                    # Make the ghost move into the play area if they are outside it
                    if distance > boss.min_spawn_distance and boss.left > 32 and boss.top < 2527 and \
                            boss.right < 2527 and boss.bottom > 32:
                        self.boss_list.append(boss)
                    else:
                        while distance <= boss.min_spawn_distance or boss.left < 32 or boss.top > 2527 or \
                                boss.right > 2527 or boss.bottom < 32:
                            boss_x = self.player.center_x + random.randint(-500, 500)
                            boss_y = self.player.center_y + random.randint(-500, 500)
                            boss.center_x, boss.center_y = boss_x, boss_y
                            distance = arcade.get_distance_between_sprites(boss, self.player)
                        self.boss_list.append(boss)

        if random.randint(0, 3) == 0:
            s.bosses_to_spawn += 1

    def scroll_to_player(self):
        self.camera.position = (self.player.center_x, self.player.center_y)

    def restart_game(self):

        # Reset all the variables
        self.level = 1
        self.player_list.clear()
        self.ghosts_to_spawn_multiplier = 1.4
        self.ghosts_to_spawn = 4.0
        self.spawn_ghosts(self.level)
        self.heart_list.clear()
        self.swordslash_list.clear()
        self.flameslash_list.clear()
        self.dark_fairy_spell_list.clear()
        self.boss_list.clear()
        self.player = player.Player(self.map_center_x, self.map_center_y, s.PLAYER_SCALING)
        self.score = 0
        s.ghosts_killed = 0
        self.is_faded_out = False
        self.has_spawned_player_death_ghost = False
        s.bosses_killed = 0
        s.bosses_to_spawn = 1
        self.no_ghost_timer = 0.0
        self.player_list.append(self.player)
        self.player_and_wall_collider = arcade.PhysicsEngineSimple(self.player, self.wall_list)
        self.health = s.PLAYER_STARTING_HEALTH
        for i in range(int(self.health / 10)):
            heart = arcade.Sprite("assets/heart/heart-0.png", s.HEART_SCALING)
            heart.center_x = (self.width - 200) + i * 40
            heart.center_y = 45
            self.heart_list.append(heart)
        self.heart_list.reverse()
        self.is_dead = False
        self.load_shader(self.level)

        # Reset the ghost list minus the death ghost
        death_ghosts = arcade.SpriteList()
        for ghost in self.ghost_list:
            if getattr(ghost, 'is_player_death_ghost', False):
                death_ghosts.append(ghost)

        self.ghost_list = death_ghosts

        self.restart = False

    def process_key_presses(self):
        self.player.change_x = 0
        self.player.change_y = 0

        # Handle the title screen
        if self.key_press_buffer:
            self.title_screen = False

        # Restart the game if x is pressed and the restart text is drawn
        if arcade.key.X in self.key_press_buffer and self.restart:
            self.restart_game()

        # Handle slashing, hold the c key for SLASH_CHARGE_TIME to activate
        # This discourages spamming the slash key
        if arcade.key.C in self.key_press_buffer:
            if self.player.c_key_timer == 0:
                self.player.c_key_timer = time.time()
            elif time.time() - self.player.c_key_timer >= s.SLASH_CHARGE_TIME:
                self.player.is_slashing = True
                self.player.c_key_timer = 0

        # Handle running, use the arrow keys
        if arcade.key.LEFT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer \
                and not arcade.key.LSHIFT in self.key_press_buffer:
            self.player.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            self.player.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            if self.player.is_slashing:
                self.player.change_x *= s.SLASH_SPEED_MODIFIER
                self.player.change_y *= s.SLASH_SPEED_MODIFIER
            self.player.current_direction = "northwest"
            self.player.is_running = True
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer \
                and not arcade.key.LSHIFT in self.key_press_buffer:
            self.player.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            self.player.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            if self.player.is_slashing:
                self.player.change_x *= s.SLASH_SPEED_MODIFIER
                self.player.change_y *= s.SLASH_SPEED_MODIFIER
            self.player.current_direction = "southwest"
            self.player.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer \
                and not arcade.key.LSHIFT in self.key_press_buffer:
            self.player.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            self.player.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            if self.player.is_slashing:
                self.player.change_x *= s.SLASH_SPEED_MODIFIER
                self.player.change_y *= s.SLASH_SPEED_MODIFIER
            self.player.current_direction = "northeast"
            self.player.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer \
                and not arcade.key.LSHIFT in self.key_press_buffer:
            self.player.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            self.player.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            if self.player.is_slashing:
                self.player.change_x *= s.SLASH_SPEED_MODIFIER
                self.player.change_y *= s.SLASH_SPEED_MODIFIER
            self.player.current_direction = "southeast"
            self.player.is_running = True
        elif arcade.key.UP in self.key_press_buffer and not arcade.key.LSHIFT in self.key_press_buffer:
            self.player.change_y = s.PLAYER_MOVEMENT_SPEED * s.PLAYER_RUN_SPEED_MODIFIER
            if self.player.is_slashing:
                self.player.change_y *= s.SLASH_SPEED_MODIFIER
            self.player.current_direction = "north"
            self.player.is_running = True
        elif arcade.key.DOWN in self.key_press_buffer and not arcade.key.LSHIFT in self.key_press_buffer:
            self.player.change_y = -s.PLAYER_MOVEMENT_SPEED * s.PLAYER_RUN_SPEED_MODIFIER
            self.player.current_direction = "south"
            if self.player.is_slashing:
                self.player.change_y *= s.SLASH_SPEED_MODIFIER
            self.player.is_running = True
        elif arcade.key.LEFT in self.key_press_buffer and not arcade.key.LSHIFT in self.key_press_buffer:
            self.player.change_x = -s.PLAYER_MOVEMENT_SPEED * s.PLAYER_RUN_SPEED_MODIFIER
            self.player.current_direction = "west"
            if self.player.is_slashing:
                self.player.change_x *= s.SLASH_SPEED_MODIFIER
            self.player.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and not arcade.key.LSHIFT in self.key_press_buffer:
            self.player.change_x = s.PLAYER_MOVEMENT_SPEED * s.PLAYER_RUN_SPEED_MODIFIER
            if self.player.is_slashing:
                self.player.change_x *= s.SLASH_SPEED_MODIFIER
            self.player.current_direction = "east"
            self.player.is_running = True

        # Handle walking, hold the shift key
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer:
            self.player.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7
            self.player.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.player.is_slashing:
                self.player.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.player.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player.current_direction = "northwest"
            self.player.is_walking = True
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer:
            self.player.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7
            self.player.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.player.is_slashing:
                self.player.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.player.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player.current_direction = "southwest"
            self.player.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer:
            self.player.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7
            self.player.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.player.is_slashing:
                self.player.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.player.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player.current_direction = "northeast"
            self.player.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer:
            self.player.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7
            self.player.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.player.is_slashing:
                self.player.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.player.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player.current_direction = "southeast"
            self.player.is_walking = True
        elif arcade.key.UP in self.key_press_buffer:
            self.player.change_y = s.PLAYER_MOVEMENT_SPEED
            self.player.current_direction = "north"
            if self.player.is_slashing:
                self.player.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player.is_walking = True
        elif arcade.key.DOWN in self.key_press_buffer:
            self.player.change_y = -s.PLAYER_MOVEMENT_SPEED
            self.player.current_direction = "south"
            if self.player.is_slashing:
                self.player.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player.is_walking = True
        elif arcade.key.LEFT in self.key_press_buffer:
            self.player.change_x = -s.PLAYER_MOVEMENT_SPEED
            self.player.current_direction = "west"
            if self.player.is_slashing:
                self.player.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer:
            self.player.change_x = s.PLAYER_MOVEMENT_SPEED
            self.player.current_direction = "east"
            if self.player.is_slashing:
                self.player.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player.is_walking = True

        # Modify the movement speed again to make a charge effect when c is pressed
        if arcade.key.C in self.key_press_buffer:
            self.player.change_x *= s.SLASH_CHARGE_SPEED_MODIFIER
            self.player.change_y *= s.SLASH_CHARGE_SPEED_MODIFIER

        # Make sure the player is not running if the shift key is pressed
        if arcade.key.LSHIFT in self.key_press_buffer:
            self.player.is_running = False


if __name__ == "__main__":
    window = MyGame(s.SCREEN_WIDTH, s.SCREEN_HEIGHT, s.SCREEN_TITLE)
    window.set_location(0, 30)
    arcade.run()
