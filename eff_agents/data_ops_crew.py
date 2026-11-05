import os
from crewai import Agent, Task, Crew, Process

EFF_CONTEXT = """
eff (Equipment Fitness Framework) calculates health and economics of heavy machinery.
Inputs require precise measurements: rated_output, load_factor, annual_run_hours, etc.
Missing data is left blank (never zero-filled).
"""

def create_data_parser():
    return Agent(
        role='Data Extraction Specialist',
        goal='Extract asset information from unstructured client text/emails and map it to eff CSV fields.',
        backstory='You are meticulous. You know that eff requires accurate data. You never guess or hallucinate numbers. If a value is missing, you leave it blank.',
        verbose=True,
        allow_delegation=False
    )

def create_assessment_reviewer():
    return Agent(
        role='Engineering Assessment Reviewer',
        goal='Read the output of the eff CLI and draft an executive summary for the client.',
        backstory='You are a senior reliability engineer. You can translate raw scores and economic EAC (Equivalent Annual Cost) into business insights for the client.',
        verbose=True,
        allow_delegation=False
    )

def create_data_parsing_task(parser, client_text):
    return Task(
        description=f"Extract data from this client message into eff fields (asset_id, name, rated_output, load_factor, etc). Leave unknown fields blank.\nMessage: {client_text}",
        expected_output="A structured JSON or CSV format representing the extracted data.",
        agent=parser
    )

def create_review_task(reviewer, eff_output):
    return Task(
        description=f"Analyze this eff CLI output and write a 3-paragraph executive summary in professional Arabic (MSA) for the client's management.\nOutput: {eff_output}",
        expected_output="A professional executive summary in Arabic explaining the verdicts and economic impact.",
        agent=reviewer
    )

def run_data_ops(client_input=None, eff_results=None):
    agents = []
    tasks = []
    
    if client_input:
        parser = create_data_parser()
        agents.append(parser)
        tasks.append(create_data_parsing_task(parser, client_input))
        
    if eff_results:
        reviewer = create_assessment_reviewer()
        agents.append(reviewer)
        tasks.append(create_review_task(reviewer, eff_results))
        
    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential
    )
    return crew.kickoff()
