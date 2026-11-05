import os
import sys

# Ensure the parent directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from eff_agents.sales_crew import run_sales_campaign
from eff_agents.marketing_crew import run_marketing_crew
from eff_agents.data_ops_crew import run_data_ops
from eff_agents.support_crew import run_support_crew

def main():
    print("==================================================")
    print("    eff AI Company Structure - Master Orchestrator")
    print("==================================================\n")
    
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("[تحذير] لم يتم العثور على مفتاح API. يرجى إعداد المتغيرات أولاً.")
        print("يمكنك تشغيل كل قسم من الشركة لاحقاً عند إضافة الـ API Key.\n")
    
    print("Available Departments:")
    print("1. Sales Department (B2B Cold Emails)")
    print("2. Marketing Department (LinkedIn Content Strategy)")
    print("3. Data Operations (Parsing raw data & Reviewing Reports)")
    print("4. Customer Support (Onboarding & Technical Explanations)\n")
    
    print("Select a department to run (1-4) or 0 to exit.")
    
    # In a real interactive scenario, we would use input(). 
    # For now, this is a structural entry point.
    print("\n[INFO] This script serves as the centralized hub to trigger any AI Agent Crew within the eff company structure.")
    print("Run this script interactively to manage the company.\n")

if __name__ == "__main__":
    main()
