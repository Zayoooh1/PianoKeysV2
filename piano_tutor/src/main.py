#!/usr/bin/env python3
import pygame
import random
import sys
import os
import numpy
import wave
from note import Note # Assuming note.py is in the same directory (src/)

# --- Sound Generation Function ---
def create_placeholder_sound_file(filepath, frequency=440, duration_sec=0.2, sample_rate=44100):
    current_mixer_settings = pygame.mixer.get_init()
    if not current_mixer_settings or \
       current_mixer_settings[0] != sample_rate or \
       current_mixer_settings[2] != 1: # Check for mono
        if current_mixer_settings: pygame.mixer.quit()
        try:
            pygame.mixer.init(frequency=sample_rate, size=-16, channels=1) # Force mono
        except pygame.error as e:
            print(f"Mixer init error in create_placeholder_sound_file: {e}. Sound file creation may fail.")
            # If mixer failed to init, we probably can't make a sound object/file with it.
            # Depending on requirements, we might return or raise here.
            # For now, let it proceed to wave.open, which will likely fail or create an empty/invalid file.
            # A more robust solution would be to not attempt file creation if mixer is unavailable.
            pass # Or return False / raise an exception

    num_samples = int(sample_rate * duration_sec)
    bits = 16
    max_amplitude = 2**(bits - 1) - 1

    buffer_data = numpy.zeros((num_samples,), dtype=numpy.int16)

    for i in range(num_samples):
        t_val = float(i) / sample_rate
        buffer_data[i] = int(max_amplitude * numpy.sin(2 * numpy.pi * frequency * t_val))

    try:
        with wave.open(filepath, "w") as wf:
            wf.setnchannels(1) # Mono
            wf.setsampwidth(2) # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(buffer_data.tobytes())
    except Exception as e:
        print(f"Error writing WAV file {filepath}: {e}")
        # If we are here, it means mixer might have initialized, but file writing failed.
        # Or, mixer failed, and we proceeded, and this is numpy/wave failing.

# --- Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT, FPS = 1280, 720, 60
BLACK = (0,0,0)
DARK_BLUE = (10,20,40)
WHITE = (255,255,255)
GREY = (100,100,100)
LIGHT_GREY = (200,200,200)
CYAN = (0,255,255)
HEADER_HEIGHT_PERCENT, CONTROL_PANEL_HEIGHT_PERCENT = 0.10, 0.15
HEADER_HEIGHT = int(SCREEN_HEIGHT * HEADER_HEIGHT_PERCENT)
CONTROL_PANEL_HEIGHT = int(SCREEN_HEIGHT * CONTROL_PANEL_HEIGHT_PERCENT)
MAIN_VIEW_TOP_Y = HEADER_HEIGHT
MAIN_VIEW_HEIGHT = SCREEN_HEIGHT - HEADER_HEIGHT - CONTROL_PANEL_HEIGHT
KEYBOARD_AREA_HEIGHT_RATIO = 0.4
KEYBOARD_AREA_HEIGHT = int(MAIN_VIEW_HEIGHT * KEYBOARD_AREA_HEIGHT_RATIO)
KEYBOARD_TOP_Y = MAIN_VIEW_TOP_Y + (MAIN_VIEW_HEIGHT - KEYBOARD_AREA_HEIGHT)
ACTION_LINE_Y = KEYBOARD_TOP_Y # Notes "hit" this line
KEYBOARD_START_MIDI = 60 # C4 (Middle C)
NUM_OCTAVES = 3
NOTE_FALL_SPEED = 150.0 # Pixels per second
WHITE_KEYS_PER_OCTAVE = 7
NUM_STARS = 150
stars_data = []

# --- Starfield Functions ---
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

# --- Keyboard Layout Generation ---
def generate_keyboard_maps(kb_y_pos, kb_height, scr_width, num_oct, start_midi_note):
    white_keys_map, black_keys_map = {}, {}
    visual_total_white_keys = num_oct * WHITE_KEYS_PER_OCTAVE
    white_key_width = scr_width / visual_total_white_keys
    white_key_height = kb_height
    black_key_width = white_key_width * 0.60
    black_key_height = white_key_height * 0.65

    white_key_midi_offsets_from_c = [0, 2, 4, 5, 7, 9, 11] # C,D,E,F,G,A,B

    current_visual_white_key_index = 0
    for octave_idx in range(num_oct):
        for midi_offset_in_octave in white_key_midi_offsets_from_c:
            actual_midi_note = start_midi_note + (octave_idx * 12) + midi_offset_in_octave
            x_coordinate = current_visual_white_key_index * white_key_width
            key_rect = pygame.Rect(x_coordinate, kb_y_pos, white_key_width, white_key_height)
            white_keys_map[actual_midi_note] = key_rect
            current_visual_white_key_index += 1

    black_key_midi_offsets_from_c = [1, 3, 6, 8, 10] # C#,D#,F#,G#,A#
    for octave_idx in range(num_oct):
        for midi_offset_in_octave in black_key_midi_offsets_from_c:
            actual_midi_note = start_midi_note + (octave_idx * 12) + midi_offset_in_octave
            # Find preceding white key to position this black key
            preceding_white_key_midi = actual_midi_note - 1
            if preceding_white_key_midi in white_keys_map:
                reference_white_key_rect = white_keys_map[preceding_white_key_midi]
                bk_x_pos = reference_white_key_rect.right - (black_key_width / 2)
                key_rect_black = pygame.Rect(bk_x_pos, kb_y_pos, black_key_width, black_key_height)
                black_keys_map[actual_midi_note] = key_rect_black

    return white_keys_map, black_keys_map

# --- PC Keyboard Mapping to MIDI ---
KEY_TO_MIDI_MAP = {
    pygame.K_a: 60, pygame.K_w: 61, pygame.K_s: 62, pygame.K_e: 63, pygame.K_d: 64,
    pygame.K_f: 65, pygame.K_t: 66, pygame.K_g: 67, pygame.K_y: 68, pygame.K_h: 69,
    pygame.K_u: 70, pygame.K_j: 71, # End of 1st Octave (C4-B4)
    # 2nd Octave (C5-B5) - MIDI 72-83
    pygame.K_k: 72, pygame.K_o: 73, pygame.K_l: 74, pygame.K_p: 75, pygame.K_SEMICOLON: 76,
    pygame.K_LEFTBRACKET: 77, pygame.K_QUOTE: 78, pygame.K_RIGHTBRACKET: 79, pygame.K_BACKSLASH: 80,
    # Add more keys if needed for 3rd octave, for now this covers ~2 octaves of PC keys
    # Example for a few keys in 3rd Octave (C6-B6) - MIDI 84-95
    pygame.K_z: 84, pygame.K_x: 86, pygame.K_c: 88 # C6, D6, E6 as example
}

# --- Drawing Functions ---
def render_keyboard(surface, wh_map, bl_map, active_set):
    # Draw white keys first
    for midi_val, rect_obj in wh_map.items():
        key_color = CYAN if midi_val in active_set else WHITE
        pygame.draw.rect(surface, key_color, rect_obj)
        pygame.draw.rect(surface, GREY, rect_obj, 1) # Border
    # Then draw black keys so they appear on top
    for midi_val, rect_obj in bl_map.items():
        key_color = CYAN if midi_val in active_set else BLACK
        pygame.draw.rect(surface, key_color, rect_obj)

def find_key_attributes_for_midi(midi_val, wh_map, bl_map):
    if midi_val in wh_map: return wh_map[midi_val], "white"
    if midi_val in bl_map: return bl_map[midi_val], "black"
    return None, None

def render_piano_roll(surface, notes_list, current_t_sec, wh_map, bl_map, fall_speed_pps, hit_line_y, view_area_top_y, view_area_bottom_y):
    for music_note_obj in notes_list:
        # Only process notes that are potentially visible or active
        if current_t_sec > music_note_obj.start_time + music_note_obj.duration + 2: # Add buffer for notes just off screen
            continue

        key_rectangle, key_type_str = find_key_attributes_for_midi(music_note_obj.note_midi, wh_map, bl_map)

        if key_rectangle:
            note_rect_x = key_rectangle.left
            note_rect_width = key_rectangle.width
            # Corrected line:
            if key_type_str == "black":
                note_rect_width *= 0.75
                note_rect_x += key_rectangle.width * 0.125 # Center it a bit

            # Calculate Y position based on current time and note start time
            note_top_y_raw = hit_line_y - ((music_note_obj.start_time - current_t_sec) * fall_speed_pps)
            note_height_raw = music_note_obj.duration * fall_speed_pps

            # Clip rendering to the visible piano roll area
            actual_draw_top_y = max(view_area_top_y, note_top_y_raw)
            actual_draw_bottom_y = min(view_area_bottom_y, note_top_y_raw + note_height_raw)

            display_height = actual_draw_bottom_y - actual_draw_top_y

            if display_height > 0:
                pygame.draw.rect(surface, CYAN, (note_rect_x, actual_draw_top_y, note_rect_width, display_height))

# --- Main Application Function ---
def main_application():
    pygame.init()
    # Explicitly set mixer to avoid issues in some environments, before creating Sound objects
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
    except pygame.error as mixer_error:
        print(f"Mixer init error: {mixer_error}. Sound might not work.")

    main_screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Piano Tutor")
    master_clock = pygame.time.Clock()

    initialize_starfield()

    # --- Sound File Setup ---
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    # Correct path assuming this script will be in src/ and assets/ is parallel to src/
    sound_asset_dir_path = os.path.join(current_script_dir, "..", "assets", "sounds")

    if not os.path.exists(sound_asset_dir_path):
        try:
            os.makedirs(sound_asset_dir_path)
            print(f"Created sound assets directory: {sound_asset_dir_path}")
        except OSError as e:
            print(f"Could not create sound assets directory: {e}")
            # Optionally handle this more gracefully, e.g. by disabling sound

    placeholder_sound_filepath = os.path.join(sound_asset_dir_path, "placeholder_note.wav")
    if not os.path.exists(placeholder_sound_filepath):
        # Ensure mixer is initialized with correct settings BEFORE creating the sound file via numpy
        create_placeholder_sound_file(placeholder_sound_filepath, sample_rate=44100)

    main_placeholder_sound = None
    if os.path.exists(placeholder_sound_filepath):
        try:
            main_placeholder_sound = pygame.mixer.Sound(placeholder_sound_filepath)
        except pygame.error as sound_error:
            print(f"Failed to load placeholder sound '{placeholder_sound_filepath}': {sound_error}")
    else:
        print(f"Placeholder sound file not found after attempting creation: {placeholder_sound_filepath}")

    # --- Keyboard and Game State Setup ---
    white_keys_map, black_keys_map = generate_keyboard_maps(
        KEYBOARD_TOP_Y, KEYBOARD_AREA_HEIGHT, SCREEN_WIDTH, NUM_OCTAVES, KEYBOARD_START_MIDI
    )

    currently_active_midis = set()
    pc_keys_held_down = set()
    mouse_button_held_midi = None
    playback_time_seconds = 0.0

    # Notes for the piano roll
    sample_notes_sequence = [
        Note(note_midi=60, start_time=2.0, duration=0.5), # C4
        Note(note_midi=62, start_time=2.5, duration=0.5), # D4
        Note(note_midi=64, start_time=3.0, duration=0.5), # E4
        Note(note_midi=65, start_time=3.5, duration=0.5), # F4
        Note(note_midi=67, start_time=4.0, duration=0.5), # G4
        Note(note_midi=61, start_time=4.5, duration=0.4), # C#4
        Note(note_midi=72, start_time=5.0, duration=0.5)  # C5
    ]

    app_is_running = True
    # --- Main Game Loop ---
    while app_is_running:
        time_step_seconds = master_clock.tick(FPS) / 1000.0
        playback_time_seconds += time_step_seconds

        # --- Event Handling ---
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                app_is_running = False

            # Mouse Button Down
            if evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
                mouse_pos = evt.pos
                key_found_by_mouse = False
                # Check black keys first (drawn on top, so preferred for clicks)
                for midi_note_val, key_rect_obj in black_keys_map.items():
                    if key_rect_obj.collidepoint(mouse_pos):
                        currently_active_midis.add(midi_note_val)
                        mouse_button_held_midi = midi_note_val
                        if main_placeholder_sound: main_placeholder_sound.play()
                        key_found_by_mouse = True
                        break
                if not key_found_by_mouse:
                    for midi_note_val, key_rect_obj in white_keys_map.items():
                        if key_rect_obj.collidepoint(mouse_pos):
                            currently_active_midis.add(midi_note_val)
                            mouse_button_held_midi = midi_note_val
                            if main_placeholder_sound: main_placeholder_sound.play()
                            break # Found key

            # Mouse Button Up
            if evt.type == pygame.MOUSEBUTTONUP and evt.button == 1:
                if mouse_button_held_midi is not None:
                    currently_active_midis.discard(mouse_button_held_midi)
                    mouse_button_held_midi = None

            # Key Down (PC Keyboard)
            if evt.type == pygame.KEYDOWN:
                pressed_key_code = evt.key
                if pressed_key_code in KEY_TO_MIDI_MAP and pressed_key_code not in pc_keys_held_down:
                    midi_note_to_play = KEY_TO_MIDI_MAP[pressed_key_code]
                    # Check if the MIDI note is within the displayable keyboard range
                    min_midi_on_keyboard = KEYBOARD_START_MIDI
                    max_midi_on_keyboard = KEYBOARD_START_MIDI + (NUM_OCTAVES * 12) -1 # -1 because 12 notes is C to B
                    if min_midi_on_keyboard <= midi_note_to_play <= max_midi_on_keyboard:
                        if midi_note_to_play in white_keys_map or midi_note_to_play in black_keys_map:
                            currently_active_midis.add(midi_note_to_play)
                            pc_keys_held_down.add(pressed_key_code)
                            if main_placeholder_sound: main_placeholder_sound.play()

            # Key Up (PC Keyboard)
            if evt.type == pygame.KEYUP:
                released_key_code = evt.key
                if released_key_code in KEY_TO_MIDI_MAP and released_key_code in pc_keys_held_down:
                    midi_note_to_deactivate = KEY_TO_MIDI_MAP[released_key_code]
                    currently_active_midis.discard(midi_note_to_deactivate)
                    pc_keys_held_down.remove(released_key_code)

        # --- Drawing ---
        main_screen.fill(DARK_BLUE)
        render_starfield(main_screen, stars_data)

        # Draw Header and Control Panel (placeholders)
        pygame.draw.rect(main_screen, GREY, (0, 0, SCREEN_WIDTH, HEADER_HEIGHT))
        pygame.draw.rect(main_screen, GREY, (0, SCREEN_HEIGHT - CONTROL_PANEL_HEIGHT, SCREEN_WIDTH, CONTROL_PANEL_HEIGHT))

        # Draw Piano Roll
        piano_roll_view_area_bottom_y = SCREEN_HEIGHT - CONTROL_PANEL_HEIGHT # Where piano roll drawing should end
        render_piano_roll(main_screen, sample_notes_sequence, playback_time_seconds,
                          white_keys_map, black_keys_map, NOTE_FALL_SPEED, ACTION_LINE_Y,
                          MAIN_VIEW_TOP_Y, piano_roll_view_area_bottom_y)

        # Draw Keyboard
        render_keyboard(main_screen, white_keys_map, black_keys_map, currently_active_midis)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main_application()
