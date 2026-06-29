"""
neo/tools/content_writer.py
===========================
Generates long-form, high-conversion SEO articles and technical content using Llama 3 70B.
"""
from neo.llm.model import get_model

def generate_article(topic: str, target_audience: str = "general", tone: str = "professional") -> str:
    """Generates a highly structured, 1000-word article for freelance clients."""
    try:
        print(f"  [Content Writer] Drafting article on: '{topic}'...")
        llm = get_model()
        
        system_prompt = f"""You are a world-class Technical Writer and SEO Expert. 
        Your job is to write a highly engaging, structured article.
        Target Audience: {target_audience}
        Tone: {tone}
        
        Rules:
        1. Use clear headings, bullet points, and short paragraphs.
        2. Keep the content deeply insightful and strictly avoid fluffy, generic AI language (e.g., 'In today's fast-paced digital world...').
        3. Do NOT use markdown symbols like ** or #, as this text will be pushed to the Notion API. Use CAPS for headings instead.
        """
        
        user_prompt = f"Write a comprehensive, professional article about: {topic}"
        
        article = llm.chat(system_prompt, [{"role": "user", "content": user_prompt}])
        return article
        
    except Exception as e:
        return f"❌ Content Generation failed: {e}"
