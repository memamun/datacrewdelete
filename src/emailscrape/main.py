#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from emailscrape.crew import Emailscrape
from emailscrape.manager import DeletionManagerCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew with manager monitoring.
    """
    inputs = {
        'website': 'https://mamunwrites.com',
        'user_name': 'Abdullah',
        'user_location': 'San Francisco, California'
    }

    try:
        # Initial deletion request
        crew_result = Emailscrape().crew().kickoff(inputs=inputs)
        
        # Start monitoring process
        manager = DeletionManagerCrew()
        monitoring_result = manager.monitor_deletion_process(
            website=inputs['website'],
            check_interval=1  # Check every 24 hours
        )
        
        return monitoring_result
        
    except Exception as e:
        raise Exception(f"An error occurred: {e}")


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
