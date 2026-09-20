"""
neo/tools/web_researcher.py
===========================
Searches the live web and uses Neo's LLM to synthesize the data into a clean report.
"""
# FIXED: The new library import name
from ddgs import DDGS 
from neo.llm.model import get_model

def generate_research_report(topic: str) -> str:
    """Searches the live web for a topic and generates a summarized research report."""
    try:
        print(f"  [Web Researcher] Scraping live data for: '{topic}'...")
        results = DDGS().text(topic, max_results=5)
        
        if not results:
            return f"❌ Could not find any recent web data for '{topic}'."
            
        # Combine the scraped data
        raw_context = "\n".join([f"Source: {r.get('title')}\nInfo: {r.get('body')}\n" for r in results])
        
        print(f"  [Web Researcher] Synthesizing data into report...")
        llm = get_model()
        
        system_prompt = "You are a world-class research analyst. Keep your reports concise, factual, and strictly based on the provided data."
        user_prompt = f"""
        Analyze the following live web data regarding '{topic}':
        {raw_context}
        
        Write a professional research report. Do NOT use markdown symbols like ** or #, as this will be sent raw to a Notion API.
        Format it EXACTLY like this with clear spacing:
        
        EXECUTIVE SUMMARY:
        (Write 2 sentences here)
        
        MARKET TRENDS:
        (Write 2 sentences here)
        
        ACTION ITEMS:
        1. (Item 1)
        2. (Item 2)
        """
        
        report = llm.chat(system_prompt, [{"role": "user", "content": user_prompt}])
        return report
        
    except Exception as e:
        return f"❌ Research failed: {e}"
