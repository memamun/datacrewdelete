from datetime import datetime
import json
import os
from typing import Dict, Any

class WorkflowStatus:
    def __init__(self, website: str, user_email: str):
        self.website = website
        self.user_email = user_email
        self.status_file = f"status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.status = {
            "website": website,
            "user_email": user_email,
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "completed": False
        }

    def update_step(self, step: str, status: str, details: Dict[str, Any] = None):
        step_info = {
            "step": step,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.status["steps"].append(step_info)
        self._save_status()

    def complete_workflow(self, success: bool = True):
        self.status["completed"] = success
        self.status["end_time"] = datetime.now().isoformat()
        self._save_status()

    def _save_status(self):
        os.makedirs("logs", exist_ok=True)
        with open(f"logs/{self.status_file}", "w") as f:
            json.dump(self.status, f, indent=2) 