import cv2
import numpy as np
import os
import time

class CardIdentifier:
    def __init__(self):
        self.templates = {} 
        self.debug_dir = "src/debug_captures"
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)

    def preprocess(self, img):
        if img is None: return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        # Using a fixed threshold for now, can be tuned
        _, thresh = cv2.threshold(blur, 150, 255, cv2.THRESH_BINARY)
        return thresh

    def process_frame(self, img):
        if img is None: return img, []
        
        display_img = img.copy()
        thresh = self.preprocess(img)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected_cards = []
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Filter by area: Adjust these values based on your screen resolution
            # Cards shouldn't be too small (chips) or too big (dealer/shoe)
            if area > 2000 and area < 50000: 
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = float(w)/h
                
                # Filter by Aspect Ratio (Card is approx 0.7 or 1.4)
                # Allow some tolerance
                is_card_shape = (0.5 < aspect_ratio < 0.9) or (1.1 < aspect_ratio < 1.8)
                
                if is_card_shape:
                    cv2.rectangle(display_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(display_img, f"A:{int(area)} AR:{aspect_ratio:.2f}", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    
                    # Extract card
                    card_img = img[y:y+h, x:x+w]
                    detected_cards.append(card_img)
                else:
                    # Draw rejected contours in red for debug
                    cv2.rectangle(display_img, (x, y), (x+w, y+h), (0, 0, 255), 1)
        
        return display_img, detected_cards

    def save_sample(self, img):
        timestamp = int(time.time() * 1000)
        filename = os.path.join(self.debug_dir, f"sample_{timestamp}.png")
        cv2.imwrite(filename, img)
        print(f"Saved sample to {filename}")

    def save_template(self, card_img, label):
        path = "src/templates"
        if not os.path.exists(path):
            os.makedirs(path)
        
        filename = os.path.join(path, f"{label}.png")
        # Save as grayscale
        gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(filename, gray)
        print(f"Saved template for {label} to {filename}")
        
        # Reload immediately
        self.templates[label] = gray

    def load_templates(self, path="src/templates"):
        self.templates = {}
        if not os.path.exists(path):
            print(f"Template path {path} does not exist")
            return

        for f in os.listdir(path):
            if f.endswith(".png") or f.endswith(".jpg"):
                # Filename format: "K.png" or "10_hearts.png"
                name = os.path.splitext(f)[0].split('_')[0]
                img = cv2.imread(os.path.join(path, f), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    self.templates[name] = img
        print(f"Loaded {len(self.templates)} templates")

    def match_card(self, card_img):
        if not self.templates:
            return None
            
        gray_card = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
        best_match = None
        max_val = 0
        
        for rank, template in self.templates.items():
            # Resize template if needed or use multi-scale matching
            # For this MVP, we assume template is smaller than card_img
            if template.shape[0] > gray_card.shape[0] or template.shape[1] > gray_card.shape[1]:
                continue
                
            res = cv2.matchTemplate(gray_card, template, cv2.TM_CCOEFF_NORMED)
            _, val, _, _ = cv2.minMaxLoc(res)
            
            if val > max_val:
                max_val = val
                best_match = rank
        
        if max_val > 0.6: # Confidence threshold
            return best_match
        return None

