import requests

def ask_ollama(context, question):
    prompt = f"""
Use the following medical document to answer the question.

--- Document Content ---
{context[:2000]}
--- End ---

Question: {question}
Answer:"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "tinyllama",  # or gemma, phi, etc.
            "prompt": prompt,
            "stream": False
        }
    )
    data = response.json()
    return data.get("response", "No answer generated.")
