import os
from crewai import Agent, Task, Crew, Process

# سياق عمل (eff) ليتم تمريره للوكلاء
EFF_CONTEXT = """
eff (Equipment Fitness Framework) is a B2B SaaS tool for large facilities, industrial plants, and commercial buildings.
It evaluates heavy machinery (chillers, boilers, generators, pumps, elevators) using 8 weighted indicators:
Age, Reliability, Efficiency, Capacity, Maintenance Cost, Physical Condition, Technical Support, Safety.
It answers one question: Keep, Monitor, Plan Replacement, or Retire?
It doesn't hallucinate data. If confidence is <60%, it outputs a measurement plan.
Current Offer: A 14-day Free Pilot evaluating 5 major machines, completely free, in exchange for a case study/reference.
Target Audience: Facility Managers and Operations Directors at large real estate management companies, malls, and administrative buildings in Egypt.
Pain Point: High energy costs (cooling/electricity) and unpredictable maintenance headaches.
Language: Professional Arabic (Fusha - MSA), never Egyptian slang.
Tone: Professional, direct, value-driven, consultative.
"""

def create_sales_agent():
    return Agent(
        role='Senior B2B SaaS Sales Executive & Consultant',
        goal='Craft highly personalized, persuasive cold emails to Facility Managers to secure a 14-day free pilot for eff.',
        backstory='You are an expert in industrial and facility B2B sales in Egypt. You understand the immense pressure Facility Managers face regarding energy costs (especially for chillers and central ACs). Your tone is professional, confident, not pushy, and speaks directly to technical and financial pain points.',
        verbose=True,
        allow_delegation=False
    )

def create_email_task(agent, company_name, company_context):
    return Task(
        description=f"""
        Write a highly targeted cold email in professional Arabic (MSA) to the Facility/Operations Manager of {company_name}.
        
        Company Context: {company_context}
        eff Context: {EFF_CONTEXT}
        
        The email must strictly follow these rules:
        1. Subject Line: Catchy, problem-focused, and mentions their specific industry or company name.
        2. Hook: Acknowledge their specific scale and challenges based on their context (e.g., cooling massive administrative buildings or malls).
        3. Value Proposition: Introduce eff not as software, but as a "fitness framework" that cuts energy and maintenance costs through precise data.
        4. The Offer: Clearly propose the 14-day free pilot for 5 machines (no strings attached).
        5. Call to Action (CTA): A clear, low-friction next step (e.g., a 15-minute introductory call or replying to the email).
        
        Formatting:
        - Use professional Arabic (MSA). No slang.
        - Keep paragraphs short (2-3 lines max).
        - No generic fluff. Be direct and respectful of their time.
        """,
        expected_output="A ready-to-send cold email in Arabic, properly formatted with subject and body.",
        agent=agent
    )

def run_sales_campaign(target_companies):
    """
    Runs the Crew to generate emails for a list of target companies.
    target_companies: list of dicts [{'name': 'Company A', 'context': 'Manages Malls'}]
    """
    sales_agent = create_sales_agent()
    tasks = []
    
    for company in target_companies:
        tasks.append(create_email_task(sales_agent, company['name'], company['context']))
        
    sales_crew = Crew(
        agents=[sales_agent],
        tasks=tasks,
        process=Process.sequential
    )
    
    print("🚀 Initiating Sales Crew...")
    result = sales_crew.kickoff()
    return result
