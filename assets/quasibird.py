import time
import _thread
import random

from mpos.apps import Activity
import mpos.ui

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

    # Game state
    score = 0
    game_over = False
    game_started = False
    running = False

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
    game_over_label = None
    start_label = None

    def onCreate(self):
        print("Quasi Bird starting...")

        self.screen = lv.obj()
        self.screen.set_style_bg_color(lv.color_hex(0x87CEEB), 0)  # Sky blue

        # Make screen focusable for keyboard input
        focusgroup = lv.group_get_default()
        if focusgroup:
            focusgroup.add_obj(self.screen)

        # Event handlers
        self.screen.add_event_cb(self.on_tap, lv.EVENT.CLICKED, None)
        self.screen.add_event_cb(self.on_key, lv.EVENT.KEY, None)

        # Create ground (will be scrolling)
        self.ground_img = lv.image(self.screen)
        self.ground_img.set_src(f"{self.ASSET_PATH}ground.png")
        self.ground_img.set_pos(0, self.SCREEN_HEIGHT - 40)

        # Create bird
        self.bird_img = lv.image(self.screen)
        self.bird_img.set_src(f"{self.ASSET_PATH}bird.png")
        self.bird_img.set_pos(self.BIRD_X, int(self.bird_y))

        # Create pipe image pool (pre-create all pipe images)
        for i in range(self.MAX_PIPES):
            # Top pipe (using flipped image)
            top_pipe = lv.image(self.screen)
            top_pipe.set_src(f"{self.ASSET_PATH}pipe_top.png")
            top_pipe.add_flag(lv.obj.FLAG.HIDDEN)  # Start hidden

            # Bottom pipe
            bottom_pipe = lv.image(self.screen)
            bottom_pipe.set_src(f"{self.ASSET_PATH}pipe.png")
            bottom_pipe.add_flag(lv.obj.FLAG.HIDDEN)  # Start hidden

            self.pipe_images.append({
                'top': top_pipe,
                'bottom': bottom_pipe,
                'in_use': False
            })

        # Create score label
        self.score_label = lv.label(self.screen)
        self.score_label.set_text("0")
        self.score_label.set_style_text_font(lv.font_montserrat_32, 0)
        self.score_label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        self.score_label.align(lv.ALIGN.TOP_MID, 0, 10)

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
        self.bird_y = self.SCREEN_HEIGHT / 2
        self.bird_velocity = 0
        self.pipes = []
        self.last_time = time.ticks_ms()

        # Hide start label
        self.update_ui_threadsafe_if_foreground(self.start_label.add_flag, lv.obj.FLAG.HIDDEN)

        # Hide all pipe images
        for pipe_img in self.pipe_images:
            pipe_img['in_use'] = False
            self.update_ui_threadsafe_if_foreground(pipe_img['top'].add_flag, lv.obj.FLAG.HIDDEN)
            self.update_ui_threadsafe_if_foreground(pipe_img['bottom'].add_flag, lv.obj.FLAG.HIDDEN)

        # Spawn initial pipes
        for i in range(min(3, self.MAX_PIPES)):
            gap_y = random.randint(80, self.SCREEN_HEIGHT - 120)
            pipe = Pipe(self.SCREEN_WIDTH + i * self.PIPE_SPAWN_DISTANCE, gap_y, self.PIPE_GAP_SIZE)
            self.pipes.append(pipe)

    def restart_game(self):
        """Restart after game over"""
        # Hide game over label
        self.update_ui_threadsafe_if_foreground(self.game_over_label.add_flag, lv.obj.FLAG.HIDDEN)

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
            pipe_img['in_use'] = False

        # Map visible pipes to image slots
        for i, pipe in enumerate(self.pipes):
            if i < self.MAX_PIPES:
                pipe_imgs = self.pipe_images[i]
                pipe_imgs['in_use'] = True

                # Show and update top pipe
                self.update_ui_threadsafe_if_foreground(
                    pipe_imgs['top'].remove_flag,
                    lv.obj.FLAG.HIDDEN
                )
                self.update_ui_threadsafe_if_foreground(
                    pipe_imgs['top'].set_pos,
                    int(pipe.x),
                    int(pipe.gap_y - 200)
                )

                # Show and update bottom pipe
                self.update_ui_threadsafe_if_foreground(
                    pipe_imgs['bottom'].remove_flag,
                    lv.obj.FLAG.HIDDEN
                )
                self.update_ui_threadsafe_if_foreground(
                    pipe_imgs['bottom'].set_pos,
                    int(pipe.x),
                    int(pipe.gap_y + pipe.gap_size)
                )

        # Hide unused pipe images
        for pipe_img in self.pipe_images:
            if not pipe_img['in_use']:
                self.update_ui_threadsafe_if_foreground(
                    pipe_img['top'].add_flag,
                    lv.obj.FLAG.HIDDEN
                )
                self.update_ui_threadsafe_if_foreground(
                    pipe_img['bottom'].add_flag,
                    lv.obj.FLAG.HIDDEN
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
                    self.bird_img.set_y,
                    int(self.bird_y)
                )

                # Update pipes
                for pipe in self.pipes:
                    pipe.x -= self.PIPE_SPEED * delta_time

                    # Check if pipe was passed (for scoring)
                    if not pipe.passed and pipe.x + pipe.width < self.BIRD_X:
                        pipe.passed = True
                        self.score += 1
                        self.update_ui_threadsafe_if_foreground(
                            self.score_label.set_text,
                            str(self.score)
                        )

                # Remove off-screen pipes and spawn new ones
                if self.pipes and self.pipes[0].x < -self.pipes[0].width:
                    # Remove the first pipe
                    self.pipes.pop(0)

                    # Spawn new pipe at the end
                    if self.pipes:
                        last_pipe = self.pipes[-1]
                        gap_y = random.randint(80, self.SCREEN_HEIGHT - 120)
                        new_pipe = Pipe(last_pipe.x + self.PIPE_SPAWN_DISTANCE, gap_y, self.PIPE_GAP_SIZE)
                        self.pipes.append(new_pipe)

                # Update pipe image positions and visibility
                self.update_pipe_images()

                # Update ground scrolling
                self.ground_x -= self.PIPE_SPEED * delta_time
                if self.ground_x <= -320:
                    self.ground_x = 0
                self.update_ui_threadsafe_if_foreground(
                    self.ground_img.set_x,
                    int(self.ground_x)
                )

                # Check collision
                if self.check_collision():
                    self.game_over = True
                    self.update_ui_threadsafe_if_foreground(
                        self.game_over_label.remove_flag,
                        lv.obj.FLAG.HIDDEN
                    )

            # Control frame rate (target ~30 FPS, but physics are framerate-independent)
            time.sleep_ms(33)
