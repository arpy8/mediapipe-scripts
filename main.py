import cv2
import time
import threading
import pydirectinput as pg
from trackers.HandTrackingModule import HandDetector
from queue import Queue

def put_text(img, text, position, color=(0, 255, 0)):
    cv2.putText(img, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)

def get_hand_center(hand):
    lmList = hand["lmList"]
    cx = sum([lm[0] for lm in lmList]) // len(lmList)
    cy = sum([lm[1] for lm in lmList]) // len(lmList)
    return cx, cy

class KeyboardController:
    def __init__(self):
        self.command_queue = Queue()
        self.running = True
        self.current_keys = set()
        self.thread = threading.Thread(target=self._process_commands, daemon=True)
        self.thread.start()
    
    def _process_commands(self):
        while self.running:
            try:
                command = self.command_queue.get(timeout=0.01)
                
                if command['action'] == 'press':
                    key = command['key']
                    if key not in self.current_keys:
                        pg.keyDown(key)
                        self.current_keys.add(key)
                
                elif command['action'] == 'release':
                    key = command['key']
                    if key in self.current_keys:
                        pg.keyUp(key)
                        self.current_keys.discard(key)
                
                elif command['action'] == 'tap':
                    key = command['key']
                    pg.keyDown(key)
                    time.sleep(0.05)
                    pg.keyUp(key)
                
                elif command['action'] == 'release_all':
                    for key in list(self.current_keys):
                        pg.keyUp(key)
                    self.current_keys.clear()
                
            except:
                continue
    
    def press_key(self, key):
        self.command_queue.put({'action': 'press', 'key': key})
    
    def release_key(self, key):
        self.command_queue.put({'action': 'release', 'key': key})
    
    def tap_key(self, key):
        self.command_queue.put({'action': 'tap', 'key': key})
    
    def release_all(self):
        """Release all currently pressed keys"""
        self.command_queue.put({'action': 'release_all'})
    
    def stop(self):
        self.running = False
        self.release_all()
        self.thread.join(timeout=1)

def main():
    cap = cv2.VideoCapture(0)
    hand_detector = HandDetector(maxHands=1, detectionCon=0.6, minTrackCon=0.4)
    kb = KeyboardController()
    
    ret, frame = cap.read()
    h, w, _ = frame.shape
    
    state = {
        'forward': False,
        'backward': False,
        'left': False,
        'right': False,
        'jump': False,
        'run': False
    }
    
    active_keys = set()
    
    jump_cooldown = 0
    
    pg.keyDown('u')

    while True:
        ret, img = cap.read()
        img = cv2.flip(img, 1)
        hands, img = hand_detector.findHands(img, flipType=False)
        
        active_keys = set()
        state = {k: False for k in state}
        
        if hands:
            right_hands = [hand for hand in hands if hand["type"] == "Right"]

            if len(right_hands) == 1:
                hand = right_hands[0]
                fingers = hand_detector.fingersUp(hand)
                cx, cy = get_hand_center(hand)
                
                left_zone = w * 0.35
                right_zone = w * 0.65
                
                if sum(fingers) == 4:
                    active_keys.add('w')
                    state['forward'] = True
                    put_text(img, "FORWARD", (10, 30))
                
                elif sum(fingers) <= 1:
                    active_keys.add('s')
                    state['backward'] = True
                    put_text(img, "BACKWARD", (10, 30))
                
                if cx < left_zone:
                    active_keys.add('a')
                    state['left'] = True
                    put_text(img, "LEFT", (10, 60), (255, 0, 0))
                
                elif cx > right_zone:
                    active_keys.add('d')
                    state['right'] = True
                    put_text(img, "RIGHT", (10, 60), (0, 0, 255))
                
                if fingers == [0, 1, 1, 0, 0] and time.time() > jump_cooldown:
                    kb.tap_key('space')
                    state['jump'] = True
                    jump_cooldown = time.time() + 0.5
                    put_text(img, "FIRE", (10, 90), (0, 255, 255))
            
            # elif len(hands) == 2:
            #     hand1 = hands[0]
            #     hand2 = hands[1]
            #     fingers1 = hand_detector.fingersUp(hand1)
            #     fingers2 = hand_detector.fingersUp(hand2)
            #     cx1, cy1 = get_hand_center(hand1)
            #     cx2, cy2 = get_hand_center(hand2)
                
            #     if cx1 < cx2:
            #         left_hand, right_hand = hand1, hand2
            #         left_fingers, right_fingers = fingers1, fingers2
            #         left_cx, right_cx = cx1, cx2
            #     else:
            #         left_hand, right_hand = hand2, hand1
            #         left_fingers, right_fingers = fingers2, fingers1
            #         left_cx, right_cx = cx2, cx1
                
            #     if sum(left_fingers) >= 4:
            #         active_keys.add('w')sdsswswsdwswdwdwwwwswssswswss
            #         state['forward'] = True
            #         put_text(img, "FORWARD", (10, 30))
            #     elif sum(left_fingers) <= 1:
            #         active_keys.add('s')
            #         state['backward'] = True
            #         put_text(img, "BACKWARD", (10, 30))
                
            #     left_zone = w * 0.3
            #     if left_cx < left_zone:
            #         active_keys.add('a')
            #         state['left'] = True
            #         put_text(img, "LEFT", (10, 60), (255, 0, 0))
                
            #     if sum(right_fingers) >= 4:
            #         active_keys.add('shift')
            #         state['run'] = True
            #         put_text(img, "RUN (SHIFT)", (10, 90), (255, 255, 0))
                
            #     right_zone = w * 0.7
            #     if right_cx > right_zone:
            #         active_keys.add('d')
            #         state['right'] = True
            #         put_text(img, "RIGHT", (10, 120), (0, 0, 255))
                
            #     if (left_fingers == [0, 1, 1, 0, 0] or right_fingers == [0, 1, 1, 0, 0]) and time.time() > jump_cooldown:
            #         kb.tap_key('space')
            #         state['jump'] = True
            #         jump_cooldown = time.time() + 0.5
            #         put_text(img, "JUMP", (10, 150), (0, 255, 255))
        
        all_keys = {'w', 's', 'a', 'd', 'shift'}
        for key in all_keys:
            if key in active_keys:
                kb.press_key(key)
            else:
                kb.release_key(key)
        
        # guide_y = h - 150
        # put_text(img, "Open hand: Walk", (10, guide_y + 30), (200, 200, 200))
        # put_text(img, "Fist (0-1): Backward", (10, guide_y + 55), (200, 200, 200))
        # put_text(img, "Peace (2): Jump", (10, guide_y + 80), (200, 200, 200))
        # put_text(img, "Move hand left/right: Turn", (10, guide_y + 105), (200, 200, 200))
        
        cv2.imshow("GTA 5 Hand Control", img)
        
        if cv2.waitKey(5) & 0xFF == 27:
            kb.stop()
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()