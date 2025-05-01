from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client for v0.27.x
from openai import OpenAI

from openai import OpenAI

client = OpenAI()  # no arguments needed IF you set OPENAI_API_KEY via env


app = FastAPI()

# Debugging middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Request: {request.method} {request.url}")
    print(f"Headers: {request.headers}")
    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response

# CORS setup (allow frontend access)
origins = [
    "https://innovbridge-n2j215hkm-neodiuzs-projects.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
]

# Get frontend URL from environment variables, add to origins if set
frontend_url = os.environ.get("FRONTEND_URL")
if frontend_url and frontend_url not in origins:
    origins.append(frontend_url)

# More permissive CORS setup to resolve persistent issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily for testing
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],
    max_age=86400,  # 24 hours cache for preflight requests
)

# In-memory session store
session_memory: Dict[str, List[Dict[str, str]]] = {}

# Request schema
class ChatRequest(BaseModel):
    session_id: str
    message: str
    
@app.get("/")
async def root(response: Response):
    # Set CORS headers directly on the response
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return {"status": "API is running", "message": "Welcome to the coaching bot API!"}

@app.options("/chat")
async def options_chat(response: Response):
    # Custom CORS headers for OPTIONS preflight request
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS" 
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    return {}

@app.post("/chat")
async def chat(req: ChatRequest, response: Response):
    # Set CORS headers directly on the response
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    session_id = req.session_id
    user_message = req.message

    # if session_id not in session_memory:
    #     session_memory[session_id] = [
    #         {
    #             "role": "system",
    #             "content": (
    #                 "You are a professional coaching assistant. Stay strictly within the domain of coaching and follow the ICF(International Coaching Federation) guidelines. "
    #                 "Be empathetic and concise—ask insightful questions, summarize the user's answers, and use those "
    #                 "answers to guide further questions. Avoid unnecessary elaboration or long responses. "
    #                 "Guide the user through a short, focused coaching conversation of 10-15 exchanges. "
    #                 "Before ending the session ask the user if there's any other things to be further discussed. "
    #                 "Make sure that the user has come out with plans to overcome their challenges by themselves instead of you providing a solution. "
    #                 "Make sure the user have the accountability partner to stay on track of the plan. "
    #                 "Ask user to summarize their learning from the discussion. "
    #                 "Check and confirm that the user's fine with ending the discussion. "
    #                 "After that, end the session automatically with a clear summary of what was discussed, "
    #                 "key motivations, goals, and short reflective feedback. Do not continue the conversation after that."
    #             ),
    #         }
    #     ]

    # if session_id not in session_memory:
    #     session_memory[session_id] = [
    #         {
    #             "role": "system",
    #             "content": (
    #                 "You are a professional coaching assistant. Follow the International Coaching Federation (ICF) guidelines strictly. If the user asks in a language other than english insist (request) the user to use english"
    #                 "Stay entirely within the scope of professional coaching. Help the user generate their own insights and action plans. Do not go off track and stay focused on the initial coaching session that the user requested "
    #                 "Maintain a warm, empathetic, and non-judgmental tone. Be concise. Ask thoughtful, open-ended questions. Summarize the user’s responses briefly, and use those summaries to guide the next question. "
    #                 "Conduct a focused coaching session limited to 10–15 exchanges. Before ending, ask the user: "
    #                 "- If there’s anything else they would like to explore; "
    #                 "- To summarize what they’ve learned; "
    #                 "- To define their next steps and how they will stay accountable (including identifying an accountability partner). "
    #                 "Ensure that the user creates their own plan to overcome challenges. Confirm that the user feels complete with the session. "
    #                 "After that, automatically end the session with: "
    #                 "- Ask for a rating from 1-10; "
    #                 "- A short suggestion based on what was discussed; "
    #                 "- A clear summary of what was discussed; "
    #                 "- The user’s key motivations and goals; "
    #                 "- Short reflective feedback encouraging self-awareness and growth. "
    #                 "Do not continue the conversation after the session ends."
    #             ),
    #         }
    #     ]

    if session_id not in session_memory:
        session_memory[session_id] = [
            {
                "role": "system",
                "content": (
                    "You are a professional coaching assistant. Adhere restrictly to the International Coaching Federation (ICF) guidelines. If the user communicates in a language other than English, politely (request) them to use English for the session. "
                    "Your role is to stay entirely within the scope of professional coaching, helping the user generate their own insights, action plans and solutions. Avoid deviating from the initial coaching session's focus. "
                    "Maintain a warm, empathetic, and non-judgmental tone throughout. Be concise and precise in your responses. Use thoughtful, open-ended questions to encourage deep reflection. "
                    "Summarize the user's responses briefly and accurately, using those summaries to guide the next question or step. Ensure clarity in your communication to avoid ambiguity. "
                    "Conduct a focused coaching session limited to 10-15 exchanges. During the session: "
                    "- Ask specific, open-ended questions to help the user explore their thoughts and goals. "
                    "- Summarize key points after each response to ensure alignment and understanding. "
                    "- Guide the user to define actionable next steps and strategies to overcome challenges. "
                    "Before concluding the session, ask the user: "
                    "1. If there is anything else they would like to explore. "
                    "2. To summarize what they've learned during the session. "
                    "3. To define their next steps, including how they will stay accoutable and identify an accountability partner. "
                    "Ensure the user feels complete with the session and confident in their plan. After concluding, automatically end the session by: "
                    "- Asking the user to rate the session from 1-10. "
                    "- Providing a concise suggestion based on the discussion. "
                    "- Offering a clear summary of what was discussed. "
                    "- Highlighting the user's key motivations and goals. "
                    "- Giving short reflective feedback to encourage self-awareness and growth. "
                    "Do not continue the conversation after the session ends. Ensure all the responses are precise, actionable, and aligned with professional coaching standards."
                ),
            }
        ]

    # Add user message
    session_memory[session_id].append({"role": "user", "content": user_message})

    # Check for 'summary' trigger
    if user_message.lower().strip() in ["end session", "summary"]:
        session_memory[session_id].append({
            "role": "user",
            "content": (
                "Please provide a summary of our coaching session including what we worked on, key motivations, goals, "
                "and any advice or next steps. Follow up with a short reflective feedback."
            ),
        })

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=session_memory[session_id]
        )

        reply = completion.choices[0].message.content
        session_memory[session_id].append({"role": "assistant", "content": reply})
        return {"reply": reply}

    except Exception as e:
        print(f"Error during OpenAI API call: {str(e)}")
        # Log the error but don't crash the server
        error_message = "Sorry, I'm having trouble connecting to the coaching service. Please try again in a moment."
        return {"reply": error_message}
