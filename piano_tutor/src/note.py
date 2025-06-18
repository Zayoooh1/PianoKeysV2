# piano_tutor/src/note.py

class Note:
    """
    Represents a single musical note with its properties.
    """
    def __init__(self, note_midi: int, start_time: float, duration: float):
        """
        Initializes a Note object.

        Args:
            note_midi (int): The MIDI number of the note (e.g., 60 for Middle C).
            start_time (float): The time (in seconds) when the note should start playing
                                relative to the beginning of the song.
            duration (float): The duration (in seconds) for which the note should sound.
        """
        if not isinstance(note_midi, int):
            raise TypeError("note_midi must be an integer.")
        if not isinstance(start_time, (int, float)) or start_time < 0:
            raise ValueError("start_time must be a non-negative number.")
        if not isinstance(duration, (int, float)) or duration <= 0:
            raise ValueError("duration must be a positive number.")

        self.note_midi = note_midi
        self.start_time = start_time
        self.duration = duration

    def __repr__(self):
        return f"Note(midi={self.note_midi}, start={self.start_time:.2f}s, dur={self.duration:.2f}s)"

# Example usage (optional, for testing purposes):
if __name__ == '__main__':
    try:
        note1 = Note(60, 0.5, 0.25)
        print(note1)
        note2 = Note(note_midi=72, start_time=1.0, duration=0.5)
        print(note2)
        # Example of invalid input
        # invalid_note = Note(60.5, -0.1, 0)
    except (TypeError, ValueError) as e:
        print(f"Error creating note: {e}")
