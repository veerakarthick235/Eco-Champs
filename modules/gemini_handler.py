import os
import google.generativeai as genai
import json

def generate_quiz_questions(topic):
    """
    Generates a 25-question quiz by directly calling the Google Gemini API.

    If the API call fails for any reason (e.g., invalid API key, rate limit,
    network error), it will print an error and return an empty structure.
    """
    try:
        # 1. Get the API key from the .env file.
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY not found in .env file.")
            return {"questions": []}

        # 2. Configure the Gemini client.
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # 3. Create a detailed prompt instructing the AI.
        prompt = f"""
        Generate 25 unique multiple-choice quiz questions about the environmental topic: '{topic}' for Indian school students (Grade 8-12).
        The questions should be practical and relevant to India.
        Provide the output in a valid JSON format.
        The JSON object should have a single key "questions" which is an array of objects.
        Each object in the array should have the following keys:
        - "question_text": The question string.
        - "options": An array of 4 string options.
        - "correct_answer": The string of the correct option.
        """

        # 4. Make the live API call. 📞
        response = model.generate_content(prompt)
        
        # 5. Clean and parse the JSON response.
        json_text = response.text.strip().replace('```json', '').replace('```', '')
        quiz_data = json.loads(json_text)

        # 6. Validate the response to ensure it's usable.
        if "questions" in quiz_data and len(quiz_data["questions"]) > 10:
            print(f"✅ Successfully generated a new quiz for '{topic}' from Gemini API.")
            return quiz_data
        else:
            print(f"❌ API returned invalid or insufficient data for '{topic}'.")
            return {"questions": []}

    except Exception as e:
        # 7. If any step fails, catch the error and return an empty structure.
        print(f"❌ An error occurred while calling the Gemini API: {e}")
        return {"questions": []}
        
