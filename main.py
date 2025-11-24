import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from langchain.agents import initialize_agent, AgentType, Tool
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.utilities import WikipediaAPIWrapper

# --- 1. SET UP YOUR API KEY ---
# IMPORTANT: Replace "YOUR_API_KEY_HERE" with your actual OpenAI API key
# You can get one from platform.openai.com
os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY_HERE"

# --- 2. INITIALIZE THE APP AND AI MODELS ---
app = Flask(__name__)
CORS(app)  # Allows your frontend to talk to your backend

# Initialize the Wikipedia API wrapper
wikipedia = WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=4000)

# Model for "Fast Mode" (faster, cheaper, dumber)
llm_fast = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

# Model for "Thinking Mode" (slower, smarter, more expensive)
llm_thinking = ChatOpenAI(model_name="gpt-4o", temperature=0.3)

# --- 3. DEFINE THE WIKIPEDIA "TOOL" ---
# This is the tool the "Thinking Mode" agent can decide to use.
tools = [
    Tool(
        name="Wikipedia Search",
        func=wikipedia.run,
        description="Useful for when you need to answer factual questions about people, places, companies, historical events, or scientific concepts."
    ),
]

# --- 4. CREATE THE AGENTS/CHAINS ---

# "Thinking Mode" Agent (Smarter, uses tools)
# This agent can reason, decide to use the Wikipedia tool, and synthesize an answer.
agent_thinking = initialize_agent(
    tools,
    llm_thinking,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True  # Set to True to see the "thinking" process in your terminal
)

# "Fast Mode" Chain (Simpler, just summarizes)
# This chain is simpler. It will *always* search Wikipedia first, then summarize.
fast_mode_template = """
You are a 'Fast Mode' AI assistant. Your job is to directly answer the user's question.
1. I will give you a user's question.
2. I will provide you with relevant search results from Wikipedia.
3. You must use *only* this information to answer the question as concisely as possible.
4. If the information is not in the search results, just say 'I couldn't find a quick answer for that.'

Question: {question}
Wikipedia Results: {wikipedia_results}

Your concise answer:
"""
fast_mode_prompt = PromptTemplate(template=fast_mode_template, input_variables=["question", "wikipedia_results"])
chain_fast = LLMChain(llm=llm_fast, prompt=fast_mode_prompt)


# --- 5. DEFINE THE API ENDPOINT ---
# This is the "door" your frontend will knock on.
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message')
        mode = data.get('mode')  # 'fast' or 'thinking'

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        print(f"Received message: '{user_message}' in mode: '{mode}'")

        if mode == 'fast':
            # 1. Search Wikipedia first
            wiki_results = wikipedia.run(user_message)
            # 2. Run the simple summarization chain
            response = chain_fast.run(question=user_message, wikipedia_results=wiki_results)
        
        elif mode == 'thinking':
            # 1. Let the smart agent decide what to do
            # It might search Wikipedia once, multiple times, or not at all.
            response = agent_thinking.run(user_message)
        
        else:
            return jsonify({"error": "Invalid mode"}), 400

        return jsonify({"answer": response})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

# A simple route to serve the HTML file
@app.route('/')
def index():
    return render_template('index.html')

# --- 6. RUN THE APP ---
if __name__ == '__main__':
    print("Starting Flask server... Go to http://127.0.0.1:5000")
    app.run(port=5000, debug=True)
