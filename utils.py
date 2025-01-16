import time
import random
import logging
from typing import Optional
from datetime import datetime

class RateLimiter:
    def __init__(self, max_actions_per_hour: int):
        self.actions_count = 0
        self.last_action_time = time.time()
        self.MAX_ACTIONS_PER_HOUR = max_actions_per_hour

    def can_perform_action(self) -> bool:
        current_time = time.time()
        if current_time - self.last_action_time >= 3600:
            self.actions_count = 0
            self.last_action_time = current_time
        
        if self.actions_count >= self.MAX_ACTIONS_PER_HOUR:
            return False
            
        self.actions_count += 1
        return True

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'instagram_bot_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()
        ]
    )

def random_sleep(min_time: float = 3, max_time: float = 6):
    time.sleep(random.uniform(min_time, max_time))