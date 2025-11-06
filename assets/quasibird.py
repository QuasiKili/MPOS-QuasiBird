import time
import _thread
import random

from mpos.apps import Activity
import mpos.ui
import mpos.config


class Pipe:
    """Represents a single pipe obstacle"""

    def __init__(self, x, gap_y, gap_size=60):
        self.x = x
        self.gap_y = gap_y
        self.gap_size = gap_size
        self.width = 40
        self.passed = False


class QuasiBird(Activity):
    # Asset path
    ASSET_PATH = "M:apps/com.quasikili.quasibird/assets/"

    # Screen dimensions
    SCREEN_WIDTH = 320
    SCREEN_HEIGHT = 240

    # Game physics constants
    GRAVITY = 200  # pixels per second^2
    FLAP_VELOCITY = -50  # pixels per second
    BIRD_X = 60  # Fixed X position

    # Bird properties
    bird_y = 120
    bird_velocity = 0
    bird_size = 32

    # Pipe properties
    PIPE_SPEED = 100  # pixels per second
    PIPE_SPAWN_DISTANCE = 200
    PIPE_GAP_SIZE = 80
    pipes = []

    # Cloud properties (parallax effect)
    CLOUD_SPEED = 30  # pixels per second (slower than pipes for depth)
    cloud_images = []
    cloud_positions = []

    # Game state
    score = 0
    highscore = 0
    game_over = False
    game_started = False
    running = False
    is_fire_bird = False  # Track if we're using the fire bird

    # Timing for framerate independence
    last_time = 0

    # UI Elements
    screen = None
    bird_img = None
    pipe_images = []
    MAX_PIPES = 4  # Maximum number of pipe pairs to display
    ground_img = None
    ground_x = 0
    score_label = None
    score_bg = None
    highscore_label = None
    highscore_bg = None
    game_over_label = None
    start_label = None
    fps_buffer = [0]  # To store the latest FPS value

    def onCreate(self):
        print("Quasi Bird starting...")

        # Load highscore from persistent storage
        print("Loading preferences...")
        prefs = mpos.config.SharedPreferences("com.quasikili.quasibird")
        self.highscore = prefs.get_int("highscore", 0)
        print(f"Loaded highscore: {self.highscore}")

        self.screen = lv.obj()
        self.screen.set_style_bg_color(lv.color_hex(0x87CEEB), 0)  # Sky blue
        self.screen.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        self.screen.remove_flag(lv.obj.FLAG.SCROLLABLE)  # Disable scrolling completely

        # Make screen focusable for keyboard input
        focusgroup = lv.group_get_default()
        if focusgroup:
            focusgroup.add_obj(self.screen)

        # Event handlers
        self.screen.add_event_cb(self.on_tap, lv.EVENT.CLICKED, None)
        self.screen.add_event_cb(self.on_key, lv.EVENT.KEY, None)

        # Create ground (will be scrolling with tiling)
        self.ground_img = lv.image(self.screen)
        self.ground_img.set_src(f"{self.ASSET_PATH}ground.png")
        self.ground_img.set_size(self.SCREEN_WIDTH, 40)  # Set size larger than image

        self.ground_img.set_inner_align(lv.image.ALIGN.TILE)
        self.ground_img.set_pos(0, self.SCREEN_HEIGHT - 40)

        # Create clouds for parallax scrolling (behind bird, in front of sky)
        cloud_start_positions = [
            ( 50, 30),  # Cloud 1: top right
            ( 180, 60),  # Cloud 2: middle right
            ( 320, 40),  # Cloud 3: far right
        ]
        for x, y in cloud_start_positions:
            cloud = lv.image(self.screen)
            cloud.set_src(f"{self.ASSET_PATH}cloud.png")
            cloud.set_pos(x, y)
            self.cloud_images.append(cloud)
            self.cloud_positions.append(x)

        # Create bird
        self.bird_img = lv.image(self.screen)
        self.bird_img.set_src(f"{self.ASSET_PATH}bird.png")
        self.bird_img.set_pos(self.BIRD_X, int(self.bird_y))

        # Create pipe image pool (pre-create all pipe images)
        for i in range(self.MAX_PIPES):
            # Top pipe (flipped using style transform)
            top_pipe = lv.image(self.screen)
            top_pipe.set_src(f"{self.ASSET_PATH}pipe.png")
            # transform image object this way to rotate
            top_pipe.set_rotation(1800)  # 180 degrees * 10

            # Alternative: use style transform rotation for 180 degree flip and pivot
            # top_pipe.set_style_transform_rotation(1800, 0)  # 180 degrees * 10
            # top_pipe.set_style_transform_pivot_x(20, 0)  # Center X (pipe is 40px wide)
            # top_pipe.set_style_transform_pivot_y(100, 0)  # Center Y (pipe is 200px tall)

            # you can also set width to stretch the image
            # top_pipe.set_width(200)
            # top_pipe.set_inner_align(lv.image.ALIGN.STRETCH)
            top_pipe.add_flag(lv.obj.FLAG.HIDDEN)  # Start hidden

            # Bottom pipe
            bottom_pipe = lv.image(self.screen)
            bottom_pipe.set_src(f"{self.ASSET_PATH}pipe.png")
            bottom_pipe.add_flag(lv.obj.FLAG.HIDDEN)  # Start hidden

            self.pipe_images.append(
                {"top": top_pipe, "bottom": bottom_pipe, "in_use": False}
            )

        # Create score display (top right, with frame background)
        self.score_bg = lv.obj(self.screen)
        self.score_bg.set_size(80, 50)
        self.score_bg.set_style_bg_color(lv.color_hex(0x000000), 0)  # Black background
        self.score_bg.set_style_bg_opa(180, 0)  # Semi-transparent
        self.score_bg.set_style_border_color(lv.color_hex(0xFFFFFF), 0)  # White border
        self.score_bg.set_style_border_width(2, 0)
        self.score_bg.set_style_radius(8, 0)  # Rounded corners
        self.score_bg.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)  # Disable scrollbar
        self.score_bg.align(lv.ALIGN.TOP_RIGHT, -10, 10)

        self.score_label = lv.label(self.score_bg)
        self.score_label.set_text("0")
        self.score_label.set_style_text_font(lv.font_montserrat_32, 0)
        self.score_label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        self.score_label.center()

        # Create highscore display (top left, with frame background)
        self.highscore_bg = lv.obj(self.screen)
        self.highscore_bg.set_size(90, 50)
        self.highscore_bg.set_style_bg_color(lv.color_hex(0x000000), 0)  # Black background
        self.highscore_bg.set_style_bg_opa(180, 0)  # Semi-transparent
        self.highscore_bg.set_style_border_color(lv.color_hex(0xFFD700), 0)  # Gold border
        self.highscore_bg.set_style_border_width(2, 0)
        self.highscore_bg.set_style_radius(8, 0)  # Rounded corners
        self.highscore_bg.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)  # Disable scrollbar
        self.highscore_bg.align(lv.ALIGN.TOP_LEFT, 10, 10)

        self.highscore_label = lv.label(self.highscore_bg)
        self.highscore_label.set_text(f"Hi:{self.highscore}")
        self.highscore_label.set_style_text_font(lv.font_montserrat_20, 0)
        self.highscore_label.set_style_text_color(lv.color_hex(0xFFD700), 0)  # Gold text
        self.highscore_label.center()

        # Create start instruction label
        self.start_label = lv.label(self.screen)
        self.start_label.set_text("Tap to Start!")
        self.start_label.set_style_text_font(lv.font_montserrat_20, 0)
        self.start_label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        self.start_label.align(lv.ALIGN.CENTER, 0, 0)

        # Create game over label (hidden initially)
        self.game_over_label = lv.label(self.screen)
        self.game_over_label.set_text("Game Over!\nTap to Restart")
        self.game_over_label.set_style_text_font(lv.font_montserrat_20, 0)
        self.game_over_label.set_style_text_color(lv.color_hex(0xFF0000), 0)
        self.game_over_label.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.game_over_label.align(lv.ALIGN.CENTER, 0, 0)
        self.game_over_label.add_flag(lv.obj.FLAG.HIDDEN)

        self.setContentView(self.screen)
        print("Quasi Bird created")

    def onResume(self, screen):
        super().onResume(screen)

        # lv.log_register_print_cb(self.log_callback)
        self.running = True
        try:
            _thread.stack_size(mpos.apps.good_stack_size())
            _thread.start_new_thread(self.game_loop, ())
        except Exception as e:
            print("Could not start thread:", e)

    def onStop(self, screen):
        super().onStop(screen)
        self.running = False

    def on_tap(self, event):
        """Handle tap/click events"""
        if not self.game_started:
            self.start_game()
        elif self.game_over:
            self.restart_game()
        else:
            self.flap()

    def on_key(self, event):
        """Handle keyboard input"""
        key = event.get_key()
        if key == lv.KEY.ENTER or key == lv.KEY.UP:
            if not self.game_started:
                self.start_game()
            elif self.game_over:
                self.restart_game()
            else:
                self.flap()

    def start_game(self):
        """Initialize game state"""
        self.game_started = True
        self.game_over = False
        self.score = 0
        self.is_fire_bird = False  # Reset to normal bird

        # Switch back to normal bird sprite
        self.update_ui_threadsafe_if_foreground(
            self.bird_img.set_src, f"{self.ASSET_PATH}bird.png"
        )

        self.update_ui_threadsafe_if_foreground(
            self.score_label.set_text, str(self.score)
        )
        self.bird_y = self.SCREEN_HEIGHT / 2
        self.bird_velocity = 0
        self.pipes = []
        self.last_time = time.ticks_ms()

        # Hide start label
        self.update_ui_threadsafe_if_foreground(
            self.start_label.add_flag, lv.obj.FLAG.HIDDEN
        )

        # Hide all pipe images
        for pipe_img in self.pipe_images:
            pipe_img["in_use"] = False
            self.update_ui_threadsafe_if_foreground(
                pipe_img["top"].add_flag, lv.obj.FLAG.HIDDEN
            )
            self.update_ui_threadsafe_if_foreground(
                pipe_img["bottom"].add_flag, lv.obj.FLAG.HIDDEN
            )

        # Spawn initial pipes
        for i in range(min(3, self.MAX_PIPES)):
            gap_y = random.randint(80, self.SCREEN_HEIGHT - 120)
            pipe = Pipe(
                self.SCREEN_WIDTH + i * self.PIPE_SPAWN_DISTANCE,
                gap_y,
                self.PIPE_GAP_SIZE,
            )
            self.pipes.append(pipe)

    def restart_game(self):
        """Restart after game over"""
        # Hide game over label
        self.update_ui_threadsafe_if_foreground(
            self.game_over_label.add_flag, lv.obj.FLAG.HIDDEN
        )

        # Start new game
        self.start_game()

    def flap(self):
        """Make the bird flap"""
        if not self.game_over:
            self.bird_velocity = self.FLAP_VELOCITY

    def update_pipe_images(self):
        """Update pipe image positions and visibility"""
        # First, mark all as not in use
        for pipe_img in self.pipe_images:
            pipe_img["in_use"] = False

        # Map visible pipes to image slots
        for i, pipe in enumerate(self.pipes):
            if i < self.MAX_PIPES:
                pipe_imgs = self.pipe_images[i]
                pipe_imgs["in_use"] = True

                # Show and update top pipe
                self.update_ui_threadsafe_if_foreground(
                    pipe_imgs["top"].remove_flag, lv.obj.FLAG.HIDDEN
                )
                self.update_ui_threadsafe_if_foreground(
                    pipe_imgs["top"].set_pos, int(pipe.x), int(pipe.gap_y - 200)
                )

                # Show and update bottom pipe
                self.update_ui_threadsafe_if_foreground(
                    pipe_imgs["bottom"].remove_flag, lv.obj.FLAG.HIDDEN
                )
                self.update_ui_threadsafe_if_foreground(
                    pipe_imgs["bottom"].set_pos,
                    int(pipe.x),
                    int(pipe.gap_y + pipe.gap_size),
                )

        # Hide unused pipe images
        for pipe_img in self.pipe_images:
            if not pipe_img["in_use"]:
                self.update_ui_threadsafe_if_foreground(
                    pipe_img["top"].add_flag, lv.obj.FLAG.HIDDEN
                )
                self.update_ui_threadsafe_if_foreground(
                    pipe_img["bottom"].add_flag, lv.obj.FLAG.HIDDEN
                )

    def check_collision(self):
        """Check if bird collides with pipes or boundaries"""
        # Check ground and ceiling
        if self.bird_y <= 0 or self.bird_y >= self.SCREEN_HEIGHT - 40 - self.bird_size:
            return True

        # Check pipe collision
        bird_left = self.BIRD_X
        bird_right = self.BIRD_X + self.bird_size
        bird_top = self.bird_y
        bird_bottom = self.bird_y + self.bird_size

        for pipe in self.pipes:
            pipe_left = pipe.x
            pipe_right = pipe.x + pipe.width

            # Check if bird is in horizontal range of pipe
            if bird_right > pipe_left and bird_left < pipe_right:
                # Check if bird is outside the gap
                if bird_top < pipe.gap_y or bird_bottom > pipe.gap_y + pipe.gap_size:
                    return True

        return False

    def game_loop(self):
        """Main game loop with framerate-independent physics"""
        self.last_time = time.ticks_ms()

        while self.running and self.has_foreground():
            current_time = time.ticks_ms()
            delta_ms = time.ticks_diff(current_time, self.last_time)
            delta_time = delta_ms / 1000.0  # Convert to seconds
            self.last_time = current_time

            if self.game_started and not self.game_over:
                # Update physics
                self.bird_velocity += self.GRAVITY * delta_time
                self.bird_y += self.bird_velocity * delta_time

                # Update bird position
                self.update_ui_threadsafe_if_foreground(
                    self.bird_img.set_y, int(self.bird_y)
                )

                # Update cloud parallax scrolling (slower than pipes for depth)
                for i, cloud_img in enumerate(self.cloud_images):
                    self.cloud_positions[i] -= self.CLOUD_SPEED * delta_time

                    # Wrap cloud when it goes off screen
                    if self.cloud_positions[i] < -60:  # Cloud width is ~50px
                        self.cloud_positions[i] = self.SCREEN_WIDTH + 20

                    # Update cloud position
                    self.update_ui_threadsafe_if_foreground(
                        cloud_img.set_x, int(self.cloud_positions[i])
                    )

                # Update pipes
                for pipe in self.pipes:
                    pipe.x -= self.PIPE_SPEED * delta_time

                    # Check if pipe was passed (for scoring)
                    if not pipe.passed and pipe.x + pipe.width < self.BIRD_X:
                        pipe.passed = True
                        self.score += 1
                        self.update_ui_threadsafe_if_foreground(
                            self.score_label.set_text, str(self.score)
                        )
                        self.update_ui_threadsafe_if_foreground(
                            self.score_label.center
                        )

                        # Switch to fire bird when beating highscore!
                        if self.score > self.highscore and not self.is_fire_bird:
                            self.is_fire_bird = True
                            print("🔥 FIRE BIRD ACTIVATED! 🔥")
                            self.update_ui_threadsafe_if_foreground(
                                self.bird_img.set_src, f"{self.ASSET_PATH}fire_bird.png"
                            )

                # Remove off-screen pipes and spawn new ones
                if self.pipes and self.pipes[0].x < -self.pipes[0].width:
                    # Remove the first pipe
                    self.pipes.pop(0)

                    # Spawn new pipe at the end
                    if self.pipes:
                        last_pipe = self.pipes[-1]
                        gap_y = random.randint(80, self.SCREEN_HEIGHT - 120)
                        new_pipe = Pipe(
                            last_pipe.x + self.PIPE_SPAWN_DISTANCE,
                            gap_y,
                            self.PIPE_GAP_SIZE,
                        )
                        self.pipes.append(new_pipe)

                # Update pipe image positions and visibility
                self.update_pipe_images()

                # Update ground scrolling (using tiling with offset)
                self.ground_x -= self.PIPE_SPEED * delta_time
                # No need to reset - tiling handles wrapping automatically
                self.update_ui_threadsafe_if_foreground(
                    self.ground_img.set_offset_x, int(self.ground_x)
                )

                # Check collision
                if self.check_collision():
                    self.game_over = True

                    # Update highscore if beaten
                    if self.score > self.highscore:
                        self.highscore = self.score
                        self.score = 0  # Reset score to avoid confusion
                        self.update_ui_threadsafe_if_foreground(
                            self.highscore_label.set_text, f"Hi:{self.highscore}"
                        )
                        self.update_ui_threadsafe_if_foreground(
                            self.highscore_label.center
                        )

                        # Save new highscore to persistent storage
                        print(f"New highscore: {self.highscore}! Saving...")
                        editor = mpos.config.SharedPreferences("com.quasikili.quasibird").edit()
                        editor.put_int("highscore", self.highscore)
                        editor.commit()

                    self.update_ui_threadsafe_if_foreground(
                        self.game_over_label.remove_flag, lv.obj.FLAG.HIDDEN
                    )

            # Control frame rate (target ~30 FPS, but physics are framerate-independent)
            time.sleep_ms(33)

    # Custom log callback to capture FPS
    def log_callback(self, level, log_str):
        # Convert log_str to string if it's a bytes object
        log_str = log_str.decode() if isinstance(log_str, bytes) else log_str
        # Optional: Print for debugging
        # print(f"Level: {level}, Log: {log_str}")
        # Log message format: "sysmon: 25 FPS (refr_cnt: 8 | redraw_cnt: 1), ..."
        if "sysmon:" in log_str and "FPS" in log_str:
            try:
                # Extract FPS value (e.g., "25" from "sysmon: 25 FPS ...")
                fps_part = log_str.split("FPS")[0].split("sysmon:")[1].strip()
                fps = int(fps_part)
                print("Current FPS:", fps)
                self.fps_buffer[0] = fps
            except (IndexError, ValueError):
                pass
