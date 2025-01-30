from crewai import Agent, Crew, Process
from crewai.tasks.conditional_task import ConditionalTask
from crewai.tasks.task_output import TaskOutput
from emailscrape.tools.email_reader import EmailReaderTool
from datetime import datetime, timedelta
import json
import time
import logging

logger = logging.getLogger(__name__)

class DeletionManagerCrew:
    def __init__(self):
        self.agents_config = 'config/agents.yaml'
        self.tasks_config = 'config/tasks.yaml'
        
    def monitor_deletion_process(self, website: str, check_interval: int = 24) -> dict:
        """Monitor email responses for deletion confirmation."""
        try:
            # Initialize email reader tool
            email_reader = EmailReaderTool()
            start_time = datetime.now()
            max_duration = timedelta(days=30)

            while datetime.now() - start_time < max_duration:
                # Check emails
                emails = email_reader._run(max_results=20)
                
                # Process response
                if "deletion confirmed" in emails.lower():
                    return {
                        "status": "complete",
                        "website": website,
                        "confirmation_received": True,
                        "completion_date": datetime.now().isoformat()
                    }
                
                # Wait for next check
                time.sleep(check_interval * 3600)
            
            return {"status": "timeout", "website": website}
            
        except Exception as e:
            logger.error(f"Error monitoring deletion: {e}")
            return {"status": "error", "website": website, "error": str(e)} 