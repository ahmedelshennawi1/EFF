import os
from crewai import Agent, Task, Crew, Process

EFF_CONTEXT = """
eff (Equipment Fitness Framework) is a B2B SaaS tool for large facilities.
It evaluates heavy machinery using 8 weighted indicators.
Tone: Professional Arabic (Fusha - MSA), never Egyptian slang.
Brand: eff (lowercase), colors are Ink and Ember. No hallucinated data.
"""

def create_content_strategist():
    return Agent(
        role='Marketing Content Strategist',
        goal='Develop a content calendar and strategy for eff to attract Facility Managers.',
        backstory='You are a B2B marketing expert who understands the engineering and facility management sector. You focus on pain points like energy costs and maintenance downtime.',
        verbose=True,
        allow_delegation=True
    )

def create_copywriter():
    return Agent(
        role='B2B Copywriter',
        goal='Write engaging, highly technical yet accessible LinkedIn posts and marketing copy in professional Arabic (MSA).',
        backstory='You are an expert Arabic copywriter for B2B engineering SaaS. You know how to talk to engineers and financial decision-makers.',
        verbose=True,
        allow_delegation=False
    )

def create_marketing_campaign_task(strategist, copywriter, topic):
    plan_task = Task(
        description=f"Plan a LinkedIn post strategy about: {topic}. Target audience: Facility Managers in Egypt.",
        expected_output="A brief content strategy and angle for the post.",
        agent=strategist
    )
    
    write_task = Task(
        description=f"Based on the strategist's plan, write a LinkedIn post in professional Arabic (MSA). Context: {EFF_CONTEXT}",
        expected_output="A ready-to-publish LinkedIn post in Arabic.",
        agent=copywriter
    )
    
    return [plan_task, write_task]

def run_marketing_crew(topic):
    strategist = create_content_strategist()
    copywriter = create_copywriter()
    tasks = create_marketing_campaign_task(strategist, copywriter, topic)
    
    crew = Crew(
        agents=[strategist, copywriter],
        tasks=tasks,
        process=Process.sequential
    )
    return crew.kickoff()
