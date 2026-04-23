import os
import google.generativeai as genai

def generate_response(query, context):
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            return "Error: Please update GOOGLE_API_KEY in your `.env` file with a valid Gemini API key!"
            
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""You are an intelligent documentation assistant. 
Please answer the user's question based strictly on the context provided below. 
If the context does not contain enough information to answer the question, say that you don't know based on the provided documents.

Context: 
{context}

User Question: 
{query}

Answer:"""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Sorry, there was an LLM error generating the response: {str(e)}"
