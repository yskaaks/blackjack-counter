import tkinter as tk
from tkinter import Toplevel
from capture import ScreenCapture
import threading
import time
import cv2
import ctypes

try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass

class ROISelector:
    def __init__(self, master, callback):
        self.master = master
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        self.top = Toplevel(master)
        self.top.attributes('-fullscreen', True)
        self.top.attributes('-alpha', 0.3)
        self.top.configure(background='grey')
        
        self.canvas = tk.Canvas(self.top, cursor="cross", bg="grey")
        self.canvas.pack(fill="both", expand=True)
        
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        
        # Exit on Escape
        self.top.bind("<Escape>", lambda e: self.top.destroy())

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='red', width=3)

    def on_move_press(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        self.top.destroy()
        
        # Calculate ROI
        x = min(self.start_x, end_x)
        y = min(self.start_y, end_y)
        w = abs(self.start_x - end_x)
        h = abs(self.start_y - end_y)
        
        if w > 5 and h > 5:
            self.callback(x, y, w, h)

class BlackjackCounterUI:
    def __init__(self, master):
        self.master = master
        
        # Game State
        from game import GameState
        self.game_state = GameState()
        
        master.title("Blackjack Counter")
        master.geometry("300x350")
        master.attributes('-topmost', True)
        
        self.capture_tool = ScreenCapture()
        
        self.label = tk.Label(master, text="Select the area with cards", pady=5)
        self.label.pack()

        self.select_btn = tk.Button(master, text="Select Region", command=self.open_roi_selector)
        self.select_btn.pack(pady=5)
        
        self.roi_label = tk.Label(master, text="ROI: Not Set")
        self.roi_label.pack(pady=2)

        # Count Display
        self.count_frame = tk.Frame(master)
        self.count_frame.pack(pady=10)
        
        self.rc_label = tk.Label(self.count_frame, text="Running Count: 0", font=("Arial", 14, "bold"))
        self.rc_label.pack()
        
        self.tc_label = tk.Label(self.count_frame, text="True Count: 0.0", font=("Arial", 12))
        self.tc_label.pack()
        
        
        self.decks_frame = tk.Frame(master)
        self.decks_frame.pack()
        
        self.deck_minus_btn = tk.Button(self.decks_frame, text="-", command=self.dec_deck)
        self.deck_minus_btn.pack(side="left")
        
        self.decks_label = tk.Label(self.decks_frame, text="Decks Remaining: 6.0")
        self.decks_label.pack(side="left", padx=5)
        
        self.deck_plus_btn = tk.Button(self.decks_frame, text="+", command=self.inc_deck)
        self.deck_plus_btn.pack(side="left")

        # Controls
        self.control_frame = tk.Frame(master)
        self.control_frame.pack(pady=5)
        
        self.reset_btn = tk.Button(self.control_frame, text="Reset Count", command=self.reset_count, bg="#ffcccc")
        self.reset_btn.pack(side="left", padx=5)

        self.start_btn = tk.Button(master, text="Start Counting", state="disabled", command=self.start_counting, bg="#ccffcc")
        self.start_btn.pack(pady=10)
        
        self.running = False
        
        # Start UI update loop
        self.update_ui()

    def dec_deck(self):
        new_decks = max(0.5, self.game_state.decks_remaining - 0.5)
        self.game_state.set_decks_remaining(new_decks)
        self.update_decks_label()

    def inc_deck(self):
        new_decks = self.game_state.decks_remaining + 0.5
        self.game_state.set_decks_remaining(new_decks)
        self.update_decks_label()
        
    def update_decks_label(self):
        self.decks_label.config(text=f"Decks Remaining: {self.game_state.decks_remaining}")

    def reset_count(self):
        self.game_state.reset()
        self.update_decks_label()
        print("Count Reset")

    def open_roi_selector(self):
        self.master.withdraw() # Hide main window
        ROISelector(self.master, self.on_roi_selected)

    def on_roi_selected(self, x, y, w, h):
        self.master.deiconify() # Show main window
        self.capture_tool.set_roi(x, y, w, h)
        self.roi_label.config(text=f"ROI: {x},{y} {w}x{h}")
        self.start_btn.config(state="normal")
        print(f"ROI Selected: {x}, {y}, {w}, {h}")

    def start_counting(self):
        if not self.running:
            self.running = True
            self.start_btn.config(text="Stop Counting", bg="#ffcccc")
            # Start processing thread
            threading.Thread(target=self.processing_loop, daemon=True).start()
        else:
            self.running = False
            self.start_btn.config(text="Start Counting", bg="#ccffcc")

    def update_ui(self):
        # Update labels from game state
        self.rc_label.config(text=f"Running Count: {self.game_state.running_count}")
        self.tc_label.config(text=f"True Count: {self.game_state.true_count:.1f}")
        # Schedule next update
        self.master.after(200, self.update_ui)

    def processing_loop(self):
        print("Starting processing loop...")
        
        # Initialize identifier
        from vision import CardIdentifier
        self.identifier = CardIdentifier()
        self.identifier.load_templates() # Load templates
        
        # Simple buffer to avoid double counting same card frame-to-frame
        # In a real app, we need tracking (ID + position)
        # Here we just use a cool-down for position
        processed_cards = [] # List of {'rect': (x,y,w,h), 'time': t, 'rank': r}
        
        while self.running:
            frame = self.capture_tool.capture()
            if frame is not None:
                # Process frame
                debug_img, card_images = self.identifier.process_frame(frame)
                
                # We need the rectangles too for tracking, but process_frame only returns images
                # I should update process_frame to return rects or objects.
                # For now, let's just show debug info.
                
                # To actually count, I need to match
                # Let's do a simplified version: assuming separate cards
                # I will modify vision to return contours or handle matching internally?
                # No, let's keep it simple.
                
                # Redoing process_frame logic here partly because I need rects
                thresh = self.identifier.preprocess(frame)
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Use a fresh copy for debug drawing
                debug_img = frame.copy()
                detected_count = 0
                current_time = time.time()
                
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area > 500:
                        x, y, w, h = cv2.boundingRect(cnt)
                        cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        
                        # Extract and match
                        card_img = frame[y:y+h, x:x+w]
                        rank = self.identifier.match_card(card_img)
                        
                        if rank:
                            cv2.putText(debug_img, str(rank), (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                            
                            # Check if we already counted this card (spatially close and recent)
                            is_new = True
                            for p in processed_cards:
                                # Overlap check or distance check
                                dist = ((p['x'] - x)**2 + (p['y'] - y)**2)**0.5
                                if dist < 50 and (current_time - p['time']) < 2.0: # 2 seconds buffer
                                    is_new = False
                                    p['time'] = current_time # Update timestamp to keep it "alive"
                                    break
                            
                            if is_new:
                                self.game_state.update_count(rank)
                                processed_cards.append({'x': x, 'y': y, 'time': current_time, 'rank': rank})
                                print(f"Counted: {rank}")
                
                # Clean up old processed cards
                processed_cards = [p for p in processed_cards if (current_time - p['time']) < 5.0]

                # Show debug window
                cv2.imshow("Debug View", debug_img)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.running = False
                    break
                elif key == ord('s'):
                    self.identifier.save_sample(frame)
                
                # Training keys
                # Check if we have a detected card frame to save
                if len(card_images) > 0:
                     # Use the first detected card for training (simplification)
                     # In reality, user should mouse-over, but cv2.imshow handling is tricky.
                     # We assume the user creates a small ROI with ONE card for training.
                     training_card = card_images[0]
                     
                     label = None
                     if key >= ord('2') and key <= ord('9'):
                         label = chr(key)
                     elif key == ord('0'): 
                         label = '10'
                     elif key == ord('j'): label = 'J'
                     elif key == ord('q'): label = 'Q'
                     elif key == ord('k'): label = 'K'
                     elif key == ord('a'): label = 'A'
                     
                     if label:
                         self.identifier.save_template(training_card, label)
                         # Visual feedback
                         cv2.circle(debug_img, (50, 50), 20, (0, 255, 0), -1)
                         cv2.imshow("Debug View", debug_img)
                         cv2.waitKey(200) # Pause to show green light
            else:
                time.sleep(0.1)
        
        cv2.destroyAllWindows()
        # Reset button state in main thread (not safe, but usually fine in Python/tk)
        # self.start_btn.config(text="Start Counting")

