#!/usr/bin/env python3
import pygame
import random
import sys
import os
import numpy
import wave
from note import Note
# New imports for Step 6 - will be added in Part B

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
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate); wf.writeframes(buffer_data.tobytes())
    except Exception as e: print(f"Error writing WAV file {filepath}: {e}")

# --- Constants (from Step 5) ---
SCREEN_WIDTH, SCREEN_HEIGHT, FPS = 1280, 720, 60
BLACK=(0,0,0); DARK_BLUE=(10,20,40); WHITE=(255,255,255); GREY=(100,100,100); LIGHT_GREY=(200,200,200); CYAN=(0,255,255); YELLOW=(255,255,0); RED=(255,0,0); GREEN=(0,255,0); LIGHT_BLUE=(173,216,230)
HEADER_HEIGHT_PERCENT, CONTROL_PANEL_HEIGHT_PERCENT = 0.10, 0.15
HEADER_HEIGHT = int(SCREEN_HEIGHT * HEADER_HEIGHT_PERCENT)
CONTROL_PANEL_HEIGHT = int(SCREEN_HEIGHT * CONTROL_PANEL_HEIGHT_PERCENT)
CONTROL_PANEL_Y_START = SCREEN_HEIGHT - CONTROL_PANEL_HEIGHT
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
control_panel_font = None

# --- Starfield Functions (Full from Step 5) ---
def initialize_starfield():
    global stars_data; stars_data.clear()
    for _ in range(NUM_STARS): stars_data.append({"rect": pygame.Rect(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.randint(1,3), random.randint(1,3)), "color": LIGHT_GREY})
def render_starfield(surface, s_list): [pygame.draw.rect(surface, star_item["color"], star_item["rect"]) for star_item in s_list]

# --- Keyboard Layout Generation (Full from Step 5) ---
def generate_keyboard_maps(kb_y_pos, kb_height, scr_width, num_oct, start_midi_note):
    white_keys_map, black_keys_map = {}, {}
    visual_total_white_keys = num_oct * WHITE_KEYS_PER_OCTAVE
    white_key_width = scr_width / visual_total_white_keys; white_key_height = kb_height
    black_key_width = white_key_width * 0.60; black_key_height = white_key_height * 0.65
    white_key_midi_offsets_from_c = [0, 2, 4, 5, 7, 9, 11]
    current_visual_white_key_index = 0
    for octave_idx in range(num_oct):
        for midi_offset_in_octave in white_key_midi_offsets_from_c:
            actual_midi_note = start_midi_note + (octave_idx * 12) + midi_offset_in_octave
            x_coordinate = current_visual_white_key_index * white_key_width
            key_rect = pygame.Rect(x_coordinate, kb_y_pos, white_key_width, white_key_height)
            white_keys_map[actual_midi_note] = key_rect; current_visual_white_key_index += 1
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

# --- PC Keyboard Mapping to MIDI (Full from Step 5) ---
KEY_TO_MIDI_MAP = { pygame.K_a:60, pygame.K_w:61, pygame.K_s:62, pygame.K_e:63, pygame.K_d:64, pygame.K_f:65, pygame.K_t:66, pygame.K_g:67, pygame.K_y:68, pygame.K_h:69, pygame.K_u:70, pygame.K_j:71, pygame.K_k:72, pygame.K_o:73, pygame.K_l:74, pygame.K_p:75, pygame.K_SEMICOLON:76, pygame.K_LEFTBRACKET:77, pygame.K_QUOTE:78, pygame.K_RIGHTBRACKET:79, pygame.K_BACKSLASH:80, pygame.K_z:84, pygame.K_x:86, pygame.K_c:88 }

# --- Button Data & Rendering (Full from Step 5) ---
buttons = []
def initialize_buttons():
    global buttons, control_panel_font
    if control_panel_font is None: control_panel_font = pygame.font.SysFont("Arial", 20)
    btn_w, btn_h, pad = 100,40,20; sx = pad; by = CONTROL_PANEL_Y_START+(CONTROL_PANEL_HEIGHT-btn_h)/2
    buttons = [{"id":"start","text":"Start","rect":pygame.Rect(sx,by,btn_w,btn_h),"base_color":GREEN,"hover_color":LIGHT_GREY},{"id":"pause","text":"Pause","rect":pygame.Rect(sx+(btn_w+pad),by,btn_w,btn_h),"base_color":YELLOW,"hover_color":LIGHT_GREY},{"id":"stop","text":"Stop","rect":pygame.Rect(sx+2*(btn_w+pad),by,btn_w,btn_h),"base_color":RED,"hover_color":LIGHT_GREY},{"id":"loop","text":"Loop: OFF","rect":pygame.Rect(sx+3*(btn_w+pad),by,btn_w+20,btn_h),"base_color":GREY,"hover_color":LIGHT_GREY}]
def render_buttons(surface, mouse_pos):
    global buttons, control_panel_font; # Ensure font is loaded
    if control_panel_font is None: return
    for btn in buttons:
        color = btn["hover_color"] if btn["rect"].collidepoint(mouse_pos) else btn["base_color"]
        pygame.draw.rect(surface, color, btn["rect"])
        text_surf = control_panel_font.render(btn["text"], True, BLACK)
        surface.blit(text_surf, text_surf.get_rect(center=btn["rect"].center))

# --- Drawing Functions (Full from Step 5, with render_piano_roll from Step 4) ---
def render_keyboard(surface, wh_map, bl_map, active_set):
    for m,r in wh_map.items(): pygame.draw.rect(surface,CYAN if m in active_set else WHITE,r); pygame.draw.rect(surface,GREY,r,1)
    for m,r in bl_map.items(): pygame.draw.rect(surface,CYAN if m in active_set else BLACK,r)
def find_key_attributes_for_midi(m,wm,bm): return (wm[m],"white") if m in wm else ((bm[m],"black") if m in bm else (None,None))
def render_piano_roll(sf,nl,ct,wm,bm,fsp,hly,vaty,vaby,gm,wf,enpm): # Args from Step 4
    for mno in nl:
        if ct > mno.start_time+mno.duration+3: continue
        kr,kt = find_key_attributes_for_midi(mno.note_midi,wm,bm)
        if kr:
            nrx,nrw = kr.left, kr.width; nc = CYAN
            if kt=="black": nrw*=0.75; nrx+=kr.width*0.125
            nty_raw = hly-((mno.start_time-ct)*fsp); nh_raw = mno.duration*fsp
            if gm=="play" and wf and mno.note_midi==enpm:
                nc = YELLOW if (pygame.time.get_ticks()%600)<300 else DARK_BLUE; nty_raw=hly
            ady,adby = max(vaty,nty_raw),min(vaby,nty_raw+nh_raw); dh = adby-ady
            if dh>0: pygame.draw.rect(sf,nc,(nrx,ady,nrw,dh))

# --- Main Application Function (Full from Step 5) ---
def main_application():
    global control_panel_font, buttons, sample_notes_sequence # Added sample_notes_sequence to global for modification by search
    pygame.init()
    try: pygame.mixer.init(frequency=44100,size=-16,channels=1)
    except pygame.error as e: print(f"Mixer error: {e}")
    screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT)); pygame.display.set_caption("Piano Tutor - Step 5 Base")
    clock = pygame.time.Clock()
    try: control_panel_font = pygame.font.SysFont("Arial",20)
    except: control_panel_font = pygame.font.Font(None, 24)
    initialize_starfield(); initialize_buttons()
    s_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","assets","sounds","placeholder_note.wav")
    if not os.path.exists(os.path.dirname(s_path)): os.makedirs(os.path.dirname(s_path),exist_ok=True)
    if not os.path.exists(s_path): create_placeholder_sound_file(s_path)
    sound = None;
    if os.path.exists(s_path):
        try: sound = pygame.mixer.Sound(s_path)
        except pygame.error as e: print(f"Failed to load sound {s_path}: {e}")
    wk_map,bk_map = generate_keyboard_maps(KEYBOARD_TOP_Y,KEYBOARD_AREA_HEIGHT,SCREEN_WIDTH,NUM_OCTAVES,KEYBOARD_START_MIDI)
    active_user,active_auto,played_auto,pc_keys = set(),set(),set(),set()
    mouse_midi,time_sec,mode = None,0.0,"watch"
    paused_user,paused_sys,next_idx_play,expected_midi,loop = False,False,0,None,False
    sample_notes_sequence = [Note(60,2,0.5),Note(62,2.5,0.5),Note(64,3,0.5),Note(65,3.5,0.5),Note(67,4,0.5),Note(61,4.5,0.4),Note(72,5,0.5)]
    song_end = max(n.start_time+n.duration for n in sample_notes_sequence) if sample_notes_sequence else 0
    running = True
    while running:
        dt = clock.tick(FPS)/1000.0; mouse_pos = pygame.mouse.get_pos()
        if not paused_user and not paused_sys: time_sec += dt
        if time_sec>=song_end and song_end>0:
            if loop: time_sec=0.0; next_idx_play=0; played_auto.clear(); paused_sys=False; print("Looping song.")
            # else: pass # Song ended, not looping
        active_auto.clear()
        if mode=="watch" and not paused_user:
            paused_sys=False
            for i,n in enumerate(sample_notes_sequence):
                if n.start_time<=time_sec<n.start_time+n.duration:
                    active_auto.add(n.note_midi)
                    if i not in played_auto and sound: sound.play(); played_auto.add(i)
                elif time_sec > n.start_time+n.duration: played_auto.discard(i)
        elif mode=="play" and not paused_user:
            if next_idx_play < len(sample_notes_sequence):
                en = sample_notes_sequence[next_idx_play]; expected_midi=en.note_midi
                if time_sec>=en.start_time: paused_sys=True
                else: paused_sys=False; expected_midi=None
            elif not loop: # Song finished in play mode and not looping
                print("Play mode: Song finished!"); paused_sys=True; expected_midi=None; mode="watch"; paused_user=True
                if buttons: buttons[1]["text"]="Pause"
        pressed_midi_event = None
        for e in pygame.event.get():
            if e.type==pygame.QUIT: running=False
            if e.type==pygame.KEYDOWN and e.key==pygame.K_m:
                mode="play" if mode=="watch" else "watch"; print(f"Mode: {mode}"); time_sec=0;next_idx_play=0;paused_user=False;paused_sys=False;expected_midi=None;active_user.clear();played_auto.clear();pc_keys.clear()
                if buttons: buttons[1]["text"]="Pause"
            clicked_btn=False
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                for bi,b in enumerate(buttons):
                    if b["rect"].collidepoint(e.pos):
                        clicked_btn=True; aid=b["id"]
                        if aid=="start": time_sec=0;next_idx_play=0;paused_user=False;buttons[1]["text"]="Pause";paused_sys=False;played_auto.clear();print("Start pressed")
                        elif aid=="pause": paused_user=not paused_user; b["text"]="Resume" if paused_user else "Pause"; print(f"Paused: {paused_user}")
                        elif aid=="stop": time_sec=0;next_idx_play=0;paused_user=True;buttons[1]["text"]="Pause";paused_sys=False;expected_midi=None;active_user.clear();active_auto.clear();played_auto.clear();print("Stop pressed")
                        elif aid=="loop": loop=not loop; b["text"]=f"Loop: {"ON" if loop else "OFF"}"; print(f"Loop: {loop}")
                        break
                if not clicked_btn:
                    fmid=None
                    for m,r in bk_map.items(): # Black keys first
                        if r.collidepoint(e.pos): fmid=m; break
                    if not fmid: # Then white keys
                        for m,r in wk_map.items():
                            if r.collidepoint(e.pos): fmid=m; break
                    if fmid is not None: pressed_midi_event=fmid; active_user.add(fmid); mouse_midi=fmid; # if sound: sound.play()
            if e.type==pygame.MOUSEBUTTONUP and e.button==1:
                is_over_btn = any(b["rect"].collidepoint(e.pos) for b in buttons)
                if mouse_midi is not None and not is_over_btn: active_user.discard(mouse_midi); mouse_midi=None
            if e.type==pygame.KEYDOWN and e.key!=pygame.K_m:
                if e.key in KEY_TO_MIDI_MAP and e.key not in pc_keys:
                    mid=KEY_TO_MIDI_MAP[e.key]; mnk,mxk=KEYBOARD_START_MIDI,KEYBOARD_START_MIDI+(NUM_OCTAVES*12)-1
                    if mnk<=mid<=mxk and (mid in wk_map or mid in bk_map): pressed_midi_event=mid; active_user.add(mid); pc_keys.add(e.key); # if sound: sound.play()
            if e.type==pygame.KEYUP and e.key in KEY_TO_MIDI_MAP and e.key in pc_keys:
                active_user.discard(KEY_TO_MIDI_MAP[e.key]); pc_keys.remove(e.key)
            if mode=="play" and paused_sys and pressed_midi_event is not None:
                if pressed_midi_event==expected_midi:
                    print(f"Correct! Expected {expected_midi}, Got {pressed_midi_event}")
                    next_idx_play+=1; paused_sys=False; expected_midi=None
                    if next_idx_play<len(notes): time_sec=notes[next_idx_play].start_time
                    elif not loop: print("Play mode: Song finished (all notes played)!"); paused_sys=True; mode="watch"; paused_user=True; buttons[1]["text"]="Pause"
                else: print(f"Incorrect. Expected {expected_midi}, Got {pressed_midi_event}")
        screen.fill(DARK_BLUE); render_starfield(screen,stars_data)
        pygame.draw.rect(screen,GREY,(0,0,SCREEN_WIDTH,HEADER_HEIGHT)); pygame.draw.rect(screen,GREY,(0,CONTROL_PANEL_Y_START,SCREEN_WIDTH,CONTROL_PANEL_HEIGHT))
        k_hl=set(active_user); # Keys to highlight
        if mode=="watch": k_hl.update(active_auto)
        render_piano_roll(screen,notes,time_sec,wk_map,bk_map,NOTE_FALL_SPEED,ACTION_LINE_Y,MAIN_VIEW_TOP_Y,KEYBOARD_TOP_Y,mode,paused_sys,expected_midi)
        render_keyboard(screen,wk_map,bk_map,k_hl); render_buttons(screen,mouse_pos)
        pygame.display.flip()
    pygame.quit(); sys.exit()

# --- Imports for Step 6 (Appended) ---
try:
    import requests
    import mido
    from bs4 import BeautifulSoup
    LIBS_LOADED_STEP6 = True
    print("Step 6 libraries (requests, mido, bs4) loaded successfully.")
except ImportError as import_err:
    print(f"Error importing Step 6 libraries: {import_err}")
    LIBS_LOADED_STEP6 = False

# --- Search Module UI Elements & Functions (New for Step 6) ---
search_input_text = ""
search_input_rect = None
search_button_rect = None
search_active = False # Is the search input field active?
search_status_messages = [] # To display messages like "Searching..." or results

def initialize_search_module_ui():
    global search_input_rect, search_button_rect, control_panel_font, buttons
    input_box_w = 200; input_box_h = 30; search_btn_w = 80; pad = 10
    if buttons and len(buttons) > 3: search_elements_start_x = buttons[3]["rect"].right + pad * 2
    else: search_elements_start_x = SCREEN_WIDTH - input_box_w - search_btn_w - pad * 2 # Fallback: align right
    search_input_rect = pygame.Rect(search_elements_start_x, CONTROL_PANEL_Y_START + (CONTROL_PANEL_HEIGHT - input_box_h) / 2, input_box_w, input_box_h)
    search_button_rect = pygame.Rect(search_elements_start_x + input_box_w + pad, CONTROL_PANEL_Y_START + (CONTROL_PANEL_HEIGHT - input_box_h) / 2, search_btn_w, input_box_h)

def render_search_module_ui(surface, mouse_pos):
    global search_input_text, search_active, search_input_rect, search_button_rect, control_panel_font, search_status_messages
    if not search_input_rect or not control_panel_font: return
    input_box_clr = LIGHT_BLUE if search_active else WHITE
    pygame.draw.rect(surface, input_box_clr, search_input_rect); pygame.draw.rect(surface, BLACK, search_input_rect, 2)
    txt_sf = control_panel_font.render(search_input_text, True, BLACK)
    surface.blit(txt_sf, (search_input_rect.x + 5, search_input_rect.y + 5))
    sbtn_clr = LIGHT_GREY if search_button_rect.collidepoint(mouse_pos) else GREY
    pygame.draw.rect(surface, sbtn_clr, search_button_rect)
    s_txt_sf = control_panel_font.render("Search", True, BLACK); surface.blit(s_txt_sf, s_txt_sf.get_rect(center=search_button_rect.center))
    msg_y_start = CONTROL_PANEL_Y_START - 25
    for idx, msg in enumerate(search_status_messages):
        status_surf = control_panel_font.render(msg, True, WHITE)
        status_rect = status_surf.get_rect(center=(SCREEN_WIDTH / 2, msg_y_start - idx * 20))
        surface.blit(status_surf, status_rect)

def search_songs_online(query):
    global search_status_messages, LIBS_LOADED_STEP6
    print(f"Attempting search for: {query}"); search_status_messages = [f"Searching for: {query}..."]
    if not LIBS_LOADED_STEP6: search_status_messages.append("Required libraries not loaded."); return []
    search_status_messages.append("Web search not yet implemented.")
    return [{"title": "Placeholder Song 1", "url": "dummy_placeholder1.mid"}, {"title": "Placeholder Song 2", "url": "dummy_placeholder2.mid"}]

def download_and_parse_midi(song_url):
    global search_status_messages, LIBS_LOADED_STEP6, sample_notes_sequence, song_end, playback_time_seconds, next_note_idx_in_play_mode, played_auto, paused_sys # Reset song-specific states
    print(f"Attempting to download/parse: {song_url}"); search_status_messages.append(f"Loading: {song_url}...")
    if not LIBS_LOADED_STEP6: search_status_messages.append("Required libraries not loaded."); return
    search_status_messages.append("MIDI download/parse not yet fully implemented.")
    # Example: Simulate loading a new song & reset relevant states
    if song_url == "dummy_placeholder1.mid":
        sample_notes_sequence = [Note(60,1,0.5), Note(64,1.5,0.5), Note(67,2,0.5), Note(72,2.5,0.5)] # New song
        search_status_messages.append("Loaded Placeholder Song 1!")
    elif song_url == "dummy_placeholder2.mid":
        sample_notes_sequence = [Note(72,1,0.5), Note(67,1.5,0.5), Note(64,2,0.5), Note(60,2.5,0.5)] # Another new song
        search_status_messages.append("Loaded Placeholder Song 2!")
    else: search_status_messages.append(f"Could not load {song_url}."); return
    song_end = max(n.start_time+n.duration for n in sample_notes_sequence) if sample_notes_sequence else 0
    playback_time_seconds = 0.0; next_note_idx_in_play_mode = 0; played_auto.clear(); paused_sys = False
    print(f"New song loaded. Duration: {song_end}s. Playback reset.")

# --- Modify main_application to integrate Step 6 ---
def main_application_step6_integrated():
    global control_panel_font, buttons, sample_notes_sequence, song_end, playback_time_seconds, next_note_idx_in_play_mode, played_auto, paused_sys # Step 5 globals
    global search_input_text, search_active, search_status_messages # Step 6 globals
    pygame.init()
    try: pygame.mixer.init(frequency=44100,size=-16,channels=1)
    except pygame.error as e: print(f"Mixer error: {e}")
    screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT)); pygame.display.set_caption("Piano Tutor - Step 6")
    clock = pygame.time.Clock()
    try: control_panel_font = pygame.font.SysFont("Arial",20)
    except: control_panel_font = pygame.font.Font(None, 24)
    initialize_starfield(); initialize_buttons(); initialize_search_module_ui() # Init all UI
    s_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","assets","sounds","placeholder_note.wav")
    if not os.path.exists(os.path.dirname(s_path)): os.makedirs(os.path.dirname(s_path),exist_ok=True)
    if not os.path.exists(s_path): create_placeholder_sound_file(s_path)
    sound = None;
    if os.path.exists(s_path):
        try: sound = pygame.mixer.Sound(s_path)
        except pygame.error as e: print(f"Failed to load sound {s_path}: {e}")
    wk_map,bk_map = generate_keyboard_maps(KEYBOARD_TOP_Y,KEYBOARD_AREA_HEIGHT,SCREEN_WIDTH,NUM_OCTAVES,KEYBOARD_START_MIDI)
    active_user,active_auto,played_auto,pc_keys = set(),set(),set(),set()
    mouse_midi,time_sec,mode = None,0.0,"watch"
    paused_user,paused_sys,next_idx_play,expected_midi,loop = False,False,0,None,False
    # Initial song (can be changed by search)
    sample_notes_sequence = [Note(60,2,0.5),Note(62,2.5,0.5),Note(64,3,0.5),Note(65,3.5,0.5),Note(67,4,0.5),Note(61,4.5,0.4),Note(72,5,0.5)]
    song_end = max(n.start_time+n.duration for n in sample_notes_sequence) if sample_notes_sequence else 0
    playback_time_seconds = time_sec # Align variable names
    running = True
    while running:
        dt = clock.tick(FPS)/1000.0; mouse_pos = pygame.mouse.get_pos()
        playback_time_seconds = time_sec # Keep time_sec for now, ensure consistency later
        if not paused_user and not paused_sys: time_sec += dt
        if time_sec>=song_end and song_end>0:
            if loop: time_sec=0.0; next_idx_play=0; played_auto.clear(); paused_sys=False; print("Looping song.")
        active_auto.clear()
        if mode=="watch" and not paused_user:
            # ... (Watch mode logic from Step 5) ...
            paused_sys=False
            for i,n in enumerate(sample_notes_sequence):
                if n.start_time<=time_sec<n.start_time+n.duration: active_auto.add(n.note_midi); # ... sound play
        elif mode=="play" and not paused_user:
            # ... (Play mode logic from Step 5) ...
            if next_idx_play < len(sample_notes_sequence): en = sample_notes_sequence[next_idx_play]; expected_midi=en.note_midi; # ... rest of logic
        pressed_midi_event = None
        for e in pygame.event.get():
            if e.type==pygame.QUIT: running=False
            # Search UI event handling (PRIORITY)
            clicked_ui_element = False # Flag to see if UI element was clicked (to prevent piano key presses)
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if search_input_rect and search_input_rect.collidepoint(e.pos): search_active = True; clicked_ui_element = True
                elif search_button_rect and search_button_rect.collidepoint(e.pos):
                    results = search_songs_online(search_input_text) # Call search
                    if results: download_and_parse_midi(results[0]["url"]) # Example: load first result
                    search_active = False; clicked_ui_element = True
                else: search_active = False # Click outside input box deactivates it
            if e.type == pygame.KEYDOWN and search_active:
                if e.key == pygame.K_RETURN: results = search_songs_online(search_input_text); search_active = False; # if results: download_and_parse_midi(results[0]["url"])
                elif e.key == pygame.K_BACKSPACE: search_input_text = search_input_text[:-1]
                else: search_input_text += e.unicode
                continue # Absorb key events if search is active

            # Regular event handling (Mode switch, Buttons, Piano keys) only if not search_active or click was not on search UI
            if e.type==pygame.KEYDOWN and e.key==pygame.K_m: # Mode Switch (already handles this)
                mode="play" if mode=="watch" else "watch"; print(f"Mode: {mode}"); time_sec=0;next_idx_play=0;paused_user=False;buttons[1]["text"]="Pause";paused_sys=False;expected_midi=None;active_user.clear();played_auto.clear();pc_keys.clear()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and not clicked_ui_element: # Control panel buttons & piano
                # ... (Full button click and piano key logic from Step 5, ensure clicked_btn logic is respected or adapted) ...
                # This part needs careful merging to avoid double processing or conflicts
                is_button_click_handled = False
                for bi,b in enumerate(buttons):
                    if b["rect"].collidepoint(e.pos): # ... (button actions) ...
                        is_button_click_handled = True; break
                if not is_button_click_handled: # Piano key click
                    # ... (piano key click logic) ...
                    pass
            if e.type == pygame.KEYDOWN and e.key != pygame.K_m: # Piano PC keys
                # ... (PC key logic for piano) ...
                pass
            if e.type == pygame.KEYUP: # Piano PC keys up
                # ... (PC key up logic for piano) ...
                pass
            # Play mode check (already part of Step 5 loop)
            if mode=="play" and paused_sys and pressed_midi_event is not None: # ... (play mode check logic) ...
                pass
        screen.fill(DARK_BLUE); render_starfield(screen,stars_data)
        pygame.draw.rect(screen,GREY,(0,0,SCREEN_WIDTH,HEADER_HEIGHT)); pygame.draw.rect(screen,GREY,(0,CONTROL_PANEL_Y_START,SCREEN_WIDTH,CONTROL_PANEL_HEIGHT))
        k_hl=set(active_user);
        if mode=="watch": k_hl.update(active_auto)
        render_piano_roll(screen,sample_notes_sequence,time_sec,wk_map,bk_map,NOTE_FALL_SPEED,ACTION_LINE_Y,MAIN_VIEW_TOP_Y,KEYBOARD_TOP_Y,mode,paused_sys,expected_midi)
        render_keyboard(screen,wk_map,bk_map,k_hl); render_buttons(screen,mouse_pos); render_search_module_ui(screen,mouse_pos) # Add search UI render
        pygame.display.flip()
    pygame.quit(); sys.exit()

if __name__ == "__main__": main_application_step6_integrated()
    LIBS_LOADED_STEP6 = False
search_input_rect = None
search_button_rect = None
search_active = False # Is the search input field active?
search_status_messages = [] # To display messages like 'Searching...' or results
