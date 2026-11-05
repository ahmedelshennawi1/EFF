import os
from crewai import Agent, Task, Crew, Process

EFF_CONTEXT = """
eff (Equipment Fitness Framework) is completely transparent.
We provide "DataKits" for users to fill in. 
If they have questions about how a score (e.g. Reliability or Capacity) is calculated, we explain it simply based on engineering principles.
Tone: Professional Arabic (Fusha - MSA), helpful, technical but accessible.
"""

def create_support_agent():
    return Agent(
        role='Technical Support & Onboarding Specialist',
        goal='Help clients understand how to collect data for eff and explain their results clearly.',
        backstory='You are a patient and knowledgeable engineer. You know the eff framework inside out. You help clients fill out their DataKits and answer their technical questions without using overly academic language.',
        verbose=True,
        allow_delegation=False
    )

def create_onboarding_task(agent, client_name, issue):
    return Task(
        description=f"Write an email in professional Arabic (MSA) to {client_name} addressing their issue: '{issue}'.\nContext: {EFF_CONTEXT}\nMake sure to guide them clearly.",
        expected_output="A helpful, clear support email in Arabic.",
        agent=agent
    )

def run_support_crew(client_name, issue):
    agent = create_support_agent()
    task = create_onboarding_task(agent, client_name, issue)
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential
    )
    return crew.kickoff()
