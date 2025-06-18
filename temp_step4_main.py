#!/usr/bin/env python3
import pygame
import random
import sys
import os
import numpy
import wave
from note import Note

# --- Sound Generation Function (from Step 3) ---
def create_placeholder_sound_file(filepath, frequency=440, duration_sec=0.2, sample_rate=44100):
    current_mixer_settings = pygame.mixer.get_init()
    if not current_mixer_settings or \
       current_mixer_settings[0] != sample_rate or \
       current_mixer_settings[2] != 1:
        if current_mixer_settings: pygame.mixer.quit()
        try:
            pygame.mixer.init(frequency=sample_rate, size=-16, channels=1)
        except pygame.error as e:
            print(f"Mixer init error in create_placeholder_sound_file: {e}. Sound file creation may fail.")
            pass
    num_samples = int(sample_rate * duration_sec)
    bits = 16
    max_amplitude = 2**(bits - 1) - 1
    buffer_data = numpy.zeros((num_samples,), dtype=numpy.int16)
    for i in range(num_samples):
        t_val = float(i) / sample_rate
        buffer_data[i] = int(max_amplitude * numpy.sin(2 * numpy.pi * frequency * t_val))
    try:
        with wave.open(filepath, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(buffer_data.tobytes())
    except Exception as e:
        print(f"Error writing WAV file {filepath}: {e}")

# --- Constants (from Step 3) ---
SCREEN_WIDTH, SCREEN_HEIGHT, FPS = 1280, 720, 60
BLACK, DARK_BLUE, WHITE, GREY, LIGHT_GREY, CYAN, YELLOW = (0,0,0), (10,20,40), (255,255,255), (100,100,100), (200,200,200), (0,255,255), (255,255,0)
HEADER_HEIGHT_PERCENT, CONTROL_PANEL_HEIGHT_PERCENT = 0.10, 0.15
HEADER_HEIGHT = int(SCREEN_HEIGHT * HEADER_HEIGHT_PERCENT)
CONTROL_PANEL_HEIGHT = int(SCREEN_HEIGHT * CONTROL_PANEL_HEIGHT_PERCENT)
MAIN_VIEW_TOP_Y = HEADER_HEIGHT
MAIN_VIEW_HEIGHT = SCREEN_HEIGHT - HEADER_HEIGHT - CONTROL_PANEL_HEIGHT
KEYBOARD_AREA_HEIGHT_RATIO = 0.4
KEYBOARD_AREA_HEIGHT = int(MAIN_VIEW_HEIGHT * KEYBOARD_AREA_HEIGHT_RATIO)
KEYBOARD_TOP_Y = MAIN_VIEW_TOP_Y + (MAIN_VIEW_HEIGHT - KEYBOARD_AREA_HEIGHT)
ACTION_LINE_Y = KEYBOARD_TOP_Y
KEYBOARD_START_MIDI = 60 # C4
NUM_OCTAVES = 3
NOTE_FALL_SPEED = 150.0
WHITE_KEYS_PER_OCTAVE = 7
NUM_STARS = 150
stars_data = []

# --- Starfield Functions (from Step 3) ---
def initialize_starfield():
    global stars_data
    stars_data.clear()
    for _ in range(NUM_STARS):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        size = random.randint(1, 3)
        stars_data.append({"rect": pygame.Rect(x, y, size, size), "color": LIGHT_GREY})

def render_starfield(surface, s_list):
    for star_item in s_list:
        pygame.draw.rect(surface, star_item["color"], star_item["rect"])

# --- Keyboard Layout Generation (from Step 3) ---
def generate_keyboard_maps(kb_y_pos, kb_height, scr_width, num_oct, start_midi_note):
    white_keys_map, black_keys_map = {}, {}
    visual_total_white_keys = num_oct * WHITE_KEYS_PER_OCTAVE
    white_key_width = scr_width / visual_total_white_keys
    white_key_height = kb_height
    black_key_width = white_key_width * 0.60
    black_key_height = white_key_height * 0.65
    white_key_midi_offsets_from_c = [0, 2, 4, 5, 7, 9, 11]
    current_visual_white_key_index = 0
    for octave_idx in range(num_oct):
        for midi_offset_in_octave in white_key_midi_offsets_from_c:
            actual_midi_note = start_midi_note + (octave_idx * 12) + midi_offset_in_octave
            x_coordinate = current_visual_white_key_index * white_key_width
            key_rect = pygame.Rect(x_coordinate, kb_y_pos, white_key_width, white_key_height)
            white_keys_map[actual_midi_note] = key_rect
            current_visual_white_key_index += 1
    black_key_midi_offsets_from_c = [1, 3, 6, 8, 10]
    for octave_idx in range(num_oct):
        for midi_offset_in_octave in black_key_midi_offsets_from_c:
            actual_midi_note = start_midi_note + (octave_idx * 12) + midi_offset_in_octave
            preceding_white_key_midi = actual_midi_note - 1
            if preceding_white_key_midi in white_keys_map:
                reference_white_key_rect = white_keys_map[preceding_white_key_midi]
                bk_x_pos = reference_white_key_rect.right - (black_key_width / 2)
                key_rect_black = pygame.Rect(bk_x_pos, kb_y_pos, black_key_width, black_key_height)
                black_keys_map[actual_midi_note] = key_rect_black
    return white_keys_map, black_keys_map

# --- PC Keyboard Mapping to MIDI (from Step 3) ---
KEY_TO_MIDI_MAP = {
    pygame.K_a: 60, pygame.K_w: 61, pygame.K_s: 62, pygame.K_e: 63, pygame.K_d: 64,
    pygame.K_f: 65, pygame.K_t: 66, pygame.K_g: 67, pygame.K_y: 68, pygame.K_h: 69,
    pygame.K_u: 70, pygame.K_j: 71,
    pygame.K_k: 72, pygame.K_o: 73, pygame.K_l: 74, pygame.K_p: 75, pygame.K_SEMICOLON: 76,
    pygame.K_LEFTBRACKET: 77, pygame.K_QUOTE: 78, pygame.K_RIGHTBRACKET: 79, pygame.K_BACKSLASH: 80,
    pygame.K_z: 84, pygame.K_x: 86, pygame.K_c: 88
}

# --- Drawing Functions (modified for Step 4) ---
def render_keyboard(surface, wh_map, bl_map, active_set): # Active set includes user + autoplay highlights
    for midi_val, rect_obj in wh_map.items():
        key_color = CYAN if midi_val in active_set else WHITE
        pygame.draw.rect(surface, key_color, rect_obj)
        pygame.draw.rect(surface, GREY, rect_obj, 1)
    for midi_val, rect_obj in bl_map.items():
        key_color = CYAN if midi_val in active_set else BLACK
        pygame.draw.rect(surface, key_color, rect_obj)

def find_key_attributes_for_midi(midi_val, wh_map, bl_map):
    if midi_val in wh_map: return wh_map[midi_val], "white"
    if midi_val in bl_map: return bl_map[midi_val], "black"
    return None, None

def render_piano_roll(surface, notes_list, current_t_sec, wh_map, bl_map, fall_speed_pps, hit_line_y, view_area_top_y, view_area_bottom_y, game_mode, waiting_for_input_flag, expected_midi_note_in_play_mode):
    for music_note_obj in notes_list:
        if current_t_sec > music_note_obj.start_time + music_note_obj.duration + 3: continue # Optimization
        key_rectangle, key_type_str = find_key_attributes_for_midi(music_note_obj.note_midi, wh_map, bl_map)
        if key_rectangle:
            note_rect_x = key_rectangle.left
            note_rect_width = key_rectangle.width
            note_color = CYAN # Default color
            if key_type_str == "black":
                note_rect_width *= 0.75
                note_rect_x += key_rectangle.width * 0.125

            note_top_y_raw = hit_line_y - ((music_note_obj.start_time - current_t_sec) * fall_speed_pps)
            note_height_raw = music_note_obj.duration * fall_speed_pps

            # Highlighting for Play Mode waiting note
            if game_mode == "play" and waiting_for_input_flag and music_note_obj.note_midi == expected_midi_note_in_play_mode:
                # Make it blink or change color distinctly
                blinking_interval = 600 # ms
                is_visible_blink = (pygame.time.get_ticks() % blinking_interval) < (blinking_interval / 2)
                note_color = YELLOW if is_visible_blink else DARK_BLUE # Blink with background or another color
                # Ensure the waiting note is drawn at the action line if time is frozen for it
                note_top_y_raw = hit_line_y # Keep it at the action line

            actual_draw_top_y = max(view_area_top_y, note_top_y_raw)
            actual_draw_bottom_y = min(view_area_bottom_y, note_top_y_raw + note_height_raw)
            display_height = actual_draw_bottom_y - actual_draw_top_y
            if display_height > 0:
                pygame.draw.rect(surface, note_color, (note_rect_x, actual_draw_top_y, note_rect_width, display_height))

# --- Main Application Function (Modified for Step 4) ---
def main_application():
    pygame.init()
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
    except pygame.error as mixer_error:
        print(f"Mixer init error: {mixer_error}. Sound might not work.")
    main_screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Piano Tutor - Step 4")
    master_clock = pygame.time.Clock()
    initialize_starfield()

    # Sound File Setup
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    sound_asset_dir_path = os.path.join(current_script_dir, "..", "assets", "sounds")
    if not os.path.exists(sound_asset_dir_path): os.makedirs(sound_asset_dir_path, exist_ok=True)
    placeholder_sound_filepath = os.path.join(sound_asset_dir_path, "placeholder_note.wav")
    if not os.path.exists(placeholder_sound_filepath): create_placeholder_sound_file(placeholder_sound_filepath)
    main_placeholder_sound = None
    if os.path.exists(placeholder_sound_filepath):
        try: main_placeholder_sound = pygame.mixer.Sound(placeholder_sound_filepath)
        except pygame.error as e: print(f"Failed to load sound: {e}")

    # Keyboard and Game State Setup
    white_keys_map, black_keys_map = generate_keyboard_maps(KEYBOARD_TOP_Y, KEYBOARD_AREA_HEIGHT, SCREEN_WIDTH, NUM_OCTAVES, KEYBOARD_START_MIDI)
    currently_active_midis_user = set() # Keys pressed by user
    autoplay_active_midis_visual = set() # Keys highlighted by autoplay in Watch mode
    autoplay_sound_played_for_note = set() # Tracks note indices for which sound played in current Watch mode activation
    pc_keys_held_down = set()
    mouse_button_held_midi = None
    playback_time_seconds = 0.0
    game_mode = "watch" # Default mode
    is_paused_by_system = False # For Play mode waiting logic
    next_note_idx_in_play_mode = 0
    expected_midi_in_play_mode = None

    sample_notes_sequence = [
        Note(60, 2.0, 0.5), Note(62, 2.5, 0.5), Note(64, 3.0, 0.5),
        Note(65, 3.5, 0.5), Note(67, 4.0, 0.5), Note(61, 4.5, 0.4), Note(72, 5.0, 0.5)
    ]

    app_is_running = True
    # --- Main Game Loop ---
    while app_is_running:
        time_step_seconds = master_clock.tick(FPS) / 1000.0

        # --- Time Progression ---
        if not is_paused_by_system: # Time advances unless Play mode is waiting for input
            playback_time_seconds += time_step_seconds

        # --- Mode Logic ---
        autoplay_active_midis_visual.clear()
        if game_mode == "watch":
            is_paused_by_system = False # Ensure time flows
            for note_idx, note_obj in enumerate(sample_notes_sequence):
                is_active_now = note_obj.start_time <= playback_time_seconds < note_obj.start_time + note_obj.duration
                if is_active_now:
                    autoplay_active_midis_visual.add(note_obj.note_midi)
                    if note_idx not in autoplay_sound_played_for_note:
                        if main_placeholder_sound: main_placeholder_sound.play()
                        autoplay_sound_played_for_note.add(note_idx)
                else:
                    autoplay_sound_played_for_note.discard(note_idx)
        elif game_mode == "play":
            if next_note_idx_in_play_mode < len(sample_notes_sequence):
                expected_note = sample_notes_sequence[next_note_idx_in_play_mode]
                expected_midi_in_play_mode = expected_note.note_midi
                if playback_time_seconds >= expected_note.start_time:
                    is_paused_by_system = True # Pause time, wait for user input
                else:
                    is_paused_by_system = False # Time flows until next note
                    expected_midi_in_play_mode = None # Not waiting for a specific note yet
            else: # Song finished in play mode
                print("Play mode: Song finished!")
                is_paused_by_system = True # Stop time
                expected_midi_in_play_mode = None
                # Optionally, switch to watch mode or show a message
                game_mode = "watch" # Revert to watch mode
                playback_time_seconds = 0 # Reset time for watch mode
                next_note_idx_in_play_mode = 0 # Reset play mode progress
                autoplay_sound_played_for_note.clear()

        # --- Event Handling ---
        user_pressed_midi_this_event = None # To track what user actually pressed in current event
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT: app_is_running = False

            # Mode Toggle Key
            if evt.type == pygame.KEYDOWN and evt.key == pygame.K_m:
                if game_mode == "watch":
                    game_mode = "play"
                    print("Switched to PLAY mode")
                else:
                    game_mode = "watch"
                    print("Switched to WATCH mode")
                playback_time_seconds = 0 # Reset time on mode switch
                next_note_idx_in_play_mode = 0
                is_paused_by_system = False
                expected_midi_in_play_mode = None
                currently_active_midis_user.clear()
                autoplay_sound_played_for_note.clear()
                pc_keys_held_down.clear()

            # Mouse Button Down (User Input)
            if evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
                mouse_pos = evt.pos; found_key_midi = None
                for midi, rect in black_keys_map.items():
                    if rect.collidepoint(mouse_pos): found_key_midi = midi; break
                if not found_key_midi:
                    for midi, rect in white_keys_map.items():
                        if rect.collidepoint(mouse_pos): found_key_midi = midi; break
                if found_key_midi is not None:
                    user_pressed_midi_this_event = found_key_midi
                    currently_active_midis_user.add(found_key_midi)
                    mouse_button_held_midi = found_key_midi
                    if main_placeholder_sound: main_placeholder_sound.play()

            # Mouse Button Up
            if evt.type == pygame.MOUSEBUTTONUP and evt.button == 1:
                if mouse_button_held_midi is not None:
                    currently_active_midis_user.discard(mouse_button_held_midi)
                    mouse_button_held_midi = None

            # Key Down (PC Keyboard - User Input)
            if evt.type == pygame.KEYDOWN:
                pk_code = evt.key
                if pk_code in KEY_TO_MIDI_MAP and pk_code not in pc_keys_held_down:
                    midi_to_play = KEY_TO_MIDI_MAP[pk_code]
                    m_min, m_max = KEYBOARD_START_MIDI, KEYBOARD_START_MIDI + (NUM_OCTAVES * 12) - 1
                    if m_min <= midi_to_play <= m_max and (midi_to_play in white_keys_map or midi_to_play in black_keys_map):
                        user_pressed_midi_this_event = midi_to_play
                        currently_active_midis_user.add(midi_to_play)
                        pc_keys_held_down.add(pk_code)
                        if main_placeholder_sound: main_placeholder_sound.play()

            # Key Up (PC Keyboard)
            if evt.type == pygame.KEYUP:
                rk_code = evt.key
                if rk_code in KEY_TO_MIDI_MAP and rk_code in pc_keys_held_down:
                    midi_to_deactivate = KEY_TO_MIDI_MAP[rk_code]
                    currently_active_midis_user.discard(midi_to_deactivate)
                    pc_keys_held_down.remove(rk_code)

            # Play Mode: Check if user pressed the correct key
            if game_mode == "play" and is_paused_by_system and user_pressed_midi_this_event is not None:
                if user_pressed_midi_this_event == expected_midi_in_play_mode:
                    print(f"Correct! Played: {user_pressed_midi_this_event}")
                    next_note_idx_in_play_mode += 1
                    is_paused_by_system = False # Resume time progression
                    expected_midi_in_play_mode = None # No longer waiting for this specific note
                    # playback_time_seconds can be set to the start of the next note or allowed to flow
                    if next_note_idx_in_play_mode < len(sample_notes_sequence):
                         playback_time_seconds = sample_notes_sequence[next_note_idx_in_play_mode].start_time # Jump time to next note
                    else: # Song finished
                         playback_time_seconds = sample_notes_sequence[-1].start_time + sample_notes_sequence[-1].duration # End of last note
                else:
                    print(f"Incorrect. Expected {expected_midi_in_play_mode}, got {user_pressed_midi_this_event}")
                    # Add visual/audio feedback for incorrect press later

        # --- Drawing ---
        main_screen.fill(DARK_BLUE)
        render_starfield(main_screen, stars_data)
        pygame.draw.rect(main_screen, GREY, (0, 0, SCREEN_WIDTH, HEADER_HEIGHT))
        pygame.draw.rect(main_screen, GREY, (0, SCREEN_HEIGHT - CONTROL_PANEL_HEIGHT, SCREEN_WIDTH, CONTROL_PANEL_HEIGHT))

        # Determine active highlights for keyboard rendering
        keys_to_highlight_on_keyboard = set(currently_active_midis_user) # User presses always show
        if game_mode == "watch":
            keys_to_highlight_on_keyboard.update(autoplay_active_midis_visual)
        elif game_mode == "play" and is_paused_by_system and expected_midi_in_play_mode is not None:
            # In play mode, if waiting, we might want to highlight the expected key on keyboard too
            # keys_to_highlight_on_keyboard.add(expected_midi_in_play_mode) # Optional: highlight expected key on keyboard

        render_piano_roll(main_screen, sample_notes_sequence, playback_time_seconds, white_keys_map, black_keys_map, NOTE_FALL_SPEED, ACTION_LINE_Y, MAIN_VIEW_TOP_Y, SCREEN_HEIGHT - CONTROL_PANEL_HEIGHT, game_mode, is_paused_by_system, expected_midi_in_play_mode)
        render_keyboard(main_screen, white_keys_map, black_keys_map, keys_to_highlight_on_keyboard)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main_application()
