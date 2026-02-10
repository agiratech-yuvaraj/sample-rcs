import json
import os
from datetime import datetime

DATA_FILE = 'appointments.json'

class DataManager:
    def __init__(self):
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w') as f:
                json.dump({}, f)

    def load_data(self):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_data(self, data):
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def is_slot_available(self, time_slot, date=None):
        """
        Checks if a time slot is available.
        For simplicity, we track by 'date_time' key.
        If date is None, assumes today or a generic date.
        """
        data = self.load_data()
        # Create a unique key for the slot. E.g., "2023-10-27_2:00 PM"
        # For this demo, we might just use the time if date isn't strictly managed yet.
        # But to be robust, let's assume valid ISO date or just Time for the MVP.
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        slot_key = f"{date}_{time_slot}"
        return slot_key not in data

    def book_slot(self, time_slot, phone_number, date=None):
        """
        Books a slot if available. Returns True if successful, False if taken.
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        slot_key = f"{date}_{time_slot}"
        
        data = self.load_data()
        if slot_key in data:
            return False # Already taken
            
        data[slot_key] = {
            "phone": phone_number,
            "booked_at": datetime.now().isoformat(),
            "status": "confirmed"
        }
        self.save_data(data)
        return True

    def get_available_slots(self, all_slots, date=None):
        """
        Given a list of possible slots, returns only the available ones.
        """
        return [slot for slot in all_slots if self.is_slot_available(slot, date)]
