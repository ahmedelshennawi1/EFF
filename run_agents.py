import os
import sys

# Ensure the parent directory is in the path so we can import eff_agents
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from eff_agents.sales_crew import run_sales_campaign

def main():
    print("========================================")
    print("   eff Agents Orchestrator - B2B Sales  ")
    print("========================================\n")
    
    # API Key Validation
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("[تحذير] لم يتم العثور على مفتاح API.")
        print("لتشغيل الوكلاء فعلياً، يجب تعيين OPENAI_API_KEY أو ANTHROPIC_API_KEY كمتغير بيئة.\n")
        print("الشركات المستهدفة في حملة اليوم:")
    else:
        print("[✓] API Key detected. Starting Sales Agents...\n")

    # Target Companies Profile for Facility Management Pivot
    targets = [
        {
            "name": "EFS Facilities Services Egypt", 
            "context": "Manages huge corporate HQs, banks, and premium residential compounds. They deal with massive central cooling and pumping needs across multiple locations."
        },
        {
            "name": "Contrack FM", 
            "context": "Manages massive retail spaces like Mall of Egypt and Mall of Arabia. Their chiller plants and HVAC systems consume enormous amounts of electricity constantly."
        },
        {
            "name": "Smart Villages Development & Management", 
            "context": "Manages dozens of glass-facade administrative buildings in October city. Energy efficiency and cooling costs are a top priority for their management board."
        },
        {
            "name": "Al-Futtaim Group Real Estate (Cairo Festival City)", 
            "context": "Manages the CFC Mall and the adjacent administrative business parks. They need predictive maintenance to avoid any downtime in premium commercial spaces."
        },
        {
            "name": "JLL Egypt", 
            "context": "Global real estate consultant managing premium grade-A office buildings in New Cairo. They need high-tech reporting to present to the building owners."
        }
    ]
    
    for idx, t in enumerate(targets, 1):
        print(f"{idx}. {t['name']}")
        
    print("\n----------------------------------------")
    
    # If no API key, exit gracefully
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("يرجى تثبيت مكتبة (crewai) عبر الأمر: pip install crewai langchain-anthropic")
        print("ثم إضافة الـ API Key لتشغيل الحملة واستخراج الإيميلات.")
        return

    # Run the campaign
    try:
        result = run_sales_campaign(targets)
        
        # Save output to marketing folder
        output_path = os.path.join("marketing", "Generated-Cold-Emails.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# حملة الإيميلات المولدة عبر الوكلاء\n\n")
            f.write(str(result))
            
        print(f"\n[نجاح] تم إرسال النتائج إلى: {output_path}")
        
    except Exception as e:
        print(f"\n[خطأ] حدث خطأ أثناء تشغيل الوكلاء: {e}")

if __name__ == "__main__":
    main()
