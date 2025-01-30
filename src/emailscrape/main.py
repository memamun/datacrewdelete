#!/usr/bin/env python
import sys
import warnings
import logging
import time
import os
import csv
import json
from datetime import datetime
from dotenv import load_dotenv

from crewai import Crew, Process
from crewai_tools import FileWriterTool
from emailscrape.crew import Emailscrape
from emailscrape.manager import DeletionManagerCrew
from emailscrape.utils.status_tracker import WorkflowStatus

# Load environment variables and configure logging
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

class TaskTracker:
    def __init__(self):
        self.tracker_file = "data/task_tracker.json"
        self._load_or_create_tracker()
    
    def _load_or_create_tracker(self):
        os.makedirs(os.path.dirname(self.tracker_file), exist_ok=True)
        if os.path.exists(self.tracker_file):
            with open(self.tracker_file, 'r') as f:
                self.completed_tasks = json.load(f)
        else:
            self.completed_tasks = {}
            self._save_tracker()
    
    def _save_tracker(self):
        with open(self.tracker_file, 'w') as f:
            json.dump(self.completed_tasks, f, indent=2)
    
    def is_completed(self, website: str, email: str) -> bool:
        task_key = f"{website}:{email}"
        return self.completed_tasks.get(task_key, {}).get('status') == 'complete'
    
    def mark_completed(self, website: str, email: str, status: str, details: dict = None):
        task_key = f"{website}:{email}"
        self.completed_tasks[task_key] = {
            'status': status,
            'completion_date': datetime.now().isoformat(),
            'details': details or {}
        }
        self._save_tracker()

class DataHandler:
    def __init__(self):
        self.writer = FileWriterTool()
        self.csv_path = os.getenv('CSV_PATH', 'data/users.csv')
        self.task_tracker = TaskTracker()
        self._ensure_data_dir()
        self._load_data()
    
    def _ensure_data_dir(self):
        directory = os.path.dirname(self.csv_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        if not os.path.exists(self.csv_path):
            logger.info(f"Creating new CSV file at {self.csv_path}")
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['website', 'user_name', 'user_location', 'user_email', 'status'])
    
    def _load_data(self):
        try:
            with open(self.csv_path, 'r') as f:
                reader = csv.DictReader(f)
                self.data = [row for row in reader if not self.task_tracker.is_completed(
                    row['website'], row['user_email']
                )]
            logger.info(f"Loaded {len(self.data)} unprocessed users from {self.csv_path}")
        except Exception as e:
            logger.error(f"Error loading CSV from {self.csv_path}: {e}")
            self.data = []
    
    def process_users(self):
        for user_data in self.data:
            try:
                if self.task_tracker.is_completed(user_data['website'], user_data['user_email']):
                    continue
                
                status_tracker = WorkflowStatus(user_data['website'], user_data['user_email'])
                
                # Send deletion request
                logger.info(f"Sending deletion request to {user_data['website']}")
                crew_result = Emailscrape().crew().kickoff(inputs=user_data)
                status_tracker.update_step("request_sent", "complete", str(crew_result))
                
                # Start monitoring
                manager = DeletionManagerCrew()
                monitoring_result = manager.monitor_deletion_process(
                    website=user_data['website'],
                    check_interval=1
                )
                
                # Update status
                status_tracker.update_step("monitoring", monitoring_result["status"], monitoring_result)
                self.task_tracker.mark_completed(
                    user_data['website'],
                    user_data['user_email'],
                    monitoring_result["status"],
                    monitoring_result
                )
                status_tracker.complete_workflow(monitoring_result["status"] == "complete")
                
                # Wait before next request
                logger.info("Waiting 180 second before next request")
                time.sleep(100)
                
            except Exception as e:
                logger.error(f"Error processing {user_data['website']}: {str(e)}")
                status_tracker.update_step("error", "failed", {"error": str(e)})
                self.task_tracker.mark_completed(
                    user_data['website'],
                    user_data['user_email'],
                    "failed",
                    {"error": str(e)}
                )

def run():
    """Main execution function"""
    try:
        data_handler = DataHandler()
        data_handler.process_users()
        logger.info("Completed processing all users")
    except Exception as e:
        logger.error(f"Fatal error in main process: {str(e)}")
        raise

def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs"
    }
    try:
        Emailscrape().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        Emailscrape().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs"
    }
    try:
        Emailscrape().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

if __name__ == "__main__":
    run()
