import extract as e

print("Using:", "Gemini" if e.G_KEY else "OpenRouter")
print("Result:", e.call('Return JSON only: {"hello": "world"}'))