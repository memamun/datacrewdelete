from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import ScrapeElementFromWebsiteTool, ScrapeWebsiteTool
from emailscrape.tools.link_scraper import LinkScraperTool
from emailscrape.tools.email_tools import EmailSenderTool
from emailscrape.tools.email_reader import EmailReaderTool

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
			verbose=True
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


	@crew
	def crew(self) -> Crew:
		"""Creates the Emailscrape crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=[
				# self.website_scraper(),
				# self.email_analyzer(),
				# self.deletion_request_composer(),
				# self.email_sender(),
				self.email_reader()
			],
			tasks=[
				# self.scrape_task(),
				# self.analyze_task(),
				# self.compose_deletion_request(),
				# self.email_sender_task(),
				self.email_reader_task()
			],
			process=Process.sequential,
			verbose=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
