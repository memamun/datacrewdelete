from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import ScrapeElementFromWebsiteTool, ScrapeWebsiteTool
from emailscrape.tools.link_scraper import LinkScraperTool
from emailscrape.tools.email_tools import EmailSenderTool
from emailscrape.tools.email_reader import EmailReaderTool
from crewai.tasks.conditional_task import ConditionalTask
from crewai.tasks.task_output import TaskOutput
from datetime import datetime, timedelta
import json
import time

ScrapeWebsiteTool = ScrapeWebsiteTool()
ScrapeElementFromWebsiteTool = ScrapeElementFromWebsiteTool()
LinkScraperTool = LinkScraperTool()
EmailSenderTool = EmailSenderTool()
EmailReaderTool = EmailReaderTool()

# If you want to run a snippet of code before or after the crew starts, 
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@CrewBase
class Emailscrape():
	"""Emailscrape crew"""

	# Learn more about YAML configuration files here:
	# Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
	# Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	# If you would like to add tools to your agents, you can learn more about it here:
	# https://docs.crewai.com/concepts/agents#agent-tools
	@agent
	def website_scraper(self) -> Agent:
		return Agent(
			config=self.agents_config['website_scraper'],
			tools=[LinkScraperTool, ScrapeWebsiteTool, ScrapeElementFromWebsiteTool],
			memory=True,
			verbose=True
		)



	@agent
	def email_analyzer(self) -> Agent:
		return Agent(
			config=self.agents_config['email_analyzer'],
			memory=True,
			verbose=True
		)


	@agent
	def deletion_manager(self) -> Agent:
		return Agent(
			role="Data Deletion Process Manager",
			goal="Monitor and manage the data deletion request process",
			backstory="Senior process manager specialized in data privacy compliance",
			tools=[EmailReaderTool],
			memory=True,
			verbose=True
		)

	@agent
	def deletion_request_composer(self) -> Agent:
		return Agent(
			config=self.agents_config['deletion_request_composer'],
			memory=True,
			verbose=True,
			output_file='deletion_request_email.json'
		)
	
	@agent
	def email_sender(self) -> Agent:
		return Agent(
			config=self.agents_config['email_sender'],
			tools=[EmailSenderTool],
			memory=True,
			verbose=True
		)


	@agent
	def email_reader(self) -> Agent:
		return Agent(
			config=self.agents_config['email_reader'],
			tools=[EmailReaderTool],
			memory=True,
			verbose=True,
			output_file='email_reader_output.json'
		)
	

	# To learn more about structured task outputs, 
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task
	@task
	def scrape_task(self) -> Task:
		return Task(
			config=self.tasks_config['scrape_task']
		)


	@task
	def analyze_task(self) -> Task:
		return Task(
			config=self.tasks_config['analyze_task']
		)


	@task
	def compose_deletion_request(self) -> Task:
		return Task(
			config=self.tasks_config['compose_deletion_request'],
			output_file='deletion_request_email.json'
		)


	@task
	def email_sender_task(self) -> Task:
		return Task(
			config=self.tasks_config['email_sender_task']
		)

	@task
	def email_reader_task(self) -> Task:
		return Task(
			config=self.tasks_config['email_reader_task']
		)

	@task
	def monitor_emails_task(self) -> Task:
		return Task(
			description="Monitor inbox for deletion confirmation emails",
			agent=self.deletion_manager(),
			expected_output="Status of deletion confirmation"
		)
	

	@crew
	def crew(self) -> Crew:
		"""Creates the Emailscrape crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=[
				self.website_scraper(),
				self.email_analyzer(),
				self.deletion_request_composer(),
				self.email_sender(),
				self.email_reader()
			],
			tasks=[
				self.scrape_task(),
				self.analyze_task(),
				self.compose_deletion_request(),
				self.email_sender_task(),
				self.email_reader_task(),
				self.monitor_emails_task()
			],
			process=Process.sequential,
			verbose=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)

class DeletionManagerCrew:
    def __init__(self):
        self.agents_config = 'config/agents.yaml'
        self.tasks_config = 'config/tasks.yaml'
        
    @agent
    def deletion_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['deletion_manager'],
            tools=[EmailReaderTool],
            memory=True,
            verbose=True
        )

    def check_deletion_status(self, output: TaskOutput) -> bool:
        try:
            result = json.loads(output.raw_output)
            return not result.get('deletion_confirmed', False)
        except:
            return True

    def create_monitoring_crew(self, website: str, max_attempts: int = 5) -> Crew:
        # Create monitoring task
        monitor_task = ConditionalTask(
            description=f"Monitor inbox for deletion confirmation from {website}",
            expected_output="Deletion status and next actions",
            condition=self.check_deletion_status,
            agent=self.deletion_manager(),
            context={
                "website": website,
                "max_attempts": max_attempts
            }
        )

        # Create the monitoring crew
        monitoring_crew = Crew(
            agents=[self.deletion_manager()],
            tasks=[monitor_task],
            process=Process.hierarchical,
            verbose=True
        )

        return monitoring_crew

    def monitor_deletion_process(self, website: str, check_interval: int = 24) -> dict:
        """
        Monitor the deletion process with periodic email checks
        
        Args:
            website: The website to monitor responses from
            check_interval: Hours between checks
        """
        monitoring_crew = self.create_monitoring_crew(website)
        max_duration = timedelta(days=30)  # Maximum monitoring duration
        start_time = datetime.now()
        
        while datetime.now() - start_time < max_duration:
            result = monitoring_crew.kickoff()
            
            try:
                status = json.loads(result)
                if status.get('deletion_confirmed'):
                    return {
                        "status": "complete",
                        "website": website,
                        "confirmation_received": True,
                        "completion_date": datetime.now().isoformat()
                    }
                
                # Wait for next check interval
                time.sleep(check_interval * 3600)
                
            except Exception as e:
                return {
                    "status": "error",
                    "website": website,
                    "error": str(e)
                }
        
        return {
            "status": "timeout",
            "website": website,
            "message": "Monitoring period exceeded without confirmation"
        }
