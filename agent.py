import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import requests
from streamlit_lottie import st_lottie

# --- CONFIGURATION & SETUP ---
load_dotenv()
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = os.getenv("GEMINI_API_KEY")


FILE_NAME = "chef_xora_memory.json"

# [cite: 19] Professional look and feel configuration
st.set_page_config(page_title="Chef AI-Xora", page_icon="🍲", layout="wide")

# --- DATA PERSISTENCE LOGIC (The "Human" Connection) ---
def load_data():
    #  Ensures the personality remembers lifestyle and allergies
    if os.path.exists(FILE_NAME) and os.path.getsize(FILE_NAME) > 0:
        with open(FILE_NAME, "r") as f:
            return json.load(f)
    return []

def save_data(chat_history):
    new_memory = []
    for message in chat_history:
        role_to_save = "model" if message["role"] == "assistant" else "user"
        new_memory.append({
            "role": role_to_save,
            "parts": [{"text": message["content"]}]
        })
    with open(FILE_NAME, "w") as diary:
        json.dump(new_memory, diary, indent=4)
    print("📁 Data successfully saved to JSON!")

# --- GEMINI AI SETUP ---
genai.configure(api_key=api_key)

# [cite: 35, 40] Clever System Instructions - The "Soul" of the Agent
instructions = """
Role:
You are 'Chef AI-Xora', a professional, Strategic Kitchen Assistant. 
You are wise, smart, and "bossy" about food waste.

Strict Response Guidelines:
1. GREETING MODE: If the user says Hi, Hello, or similar small talk, ONLY respond with a 1-sentence bossy greeting. Example: "Hello! I am Chef AI-Xora. Stop wasting time and tell me what's expiring in your fridge!" 
   - CRITICAL: In this mode, NO tables, NO recipes, and NO strategy.
2. STRATEGY MODE: Only active if the user asks for a recipe or kitchen advice.
3. INTENT CHECK: First, detect the user's intent. 
   - If it's a greeting (Hi/Hello), reply with a short, professional greeting only.
   - If it's a question about a specific dish, give the recipe table.
   - If it's a general tip, keep it under 3 sentences.
4. NO FLUFF: Do not give long introductions. Get straight to the point.
5. THE HUMAN CONNECTION: Use past memory to keep suggestions relevant (allergies/goals).
6. WASTE-WARRIOR: Always prioritize the 'Rescue Ingredient' if provided.
7. MISSING LINK: Only show the shopping list if the user asks "how to cook" or "what to buy".

Response Standards:
- MANDATORY TABLE: Only for recipes. Format: | Ingredients | Time | Calories |
- Use Bold Headings and 🥦, ⏱️, 💰 icons.
- Tone: Professional, direct, and senior mentor style.
"""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=instructions
)

def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_soup = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_S69f49.json")

with st.sidebar:
    st.image("https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExN3Y3enM3NmViMmhobzNmb2trdXo2ZnZscGJzcTdieDlldXU5dGJqdCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/m530QoD3Sp6TB2PpAS/giphy.gif", 
             use_container_width=True)
    st.title("Chef AI-Xora")
    st.markdown("*The Living Kitchen Assistant*")
    st.markdown("---")
    
    st.info("### Deployed by: ZARA MAHAD")
    st.markdown("---")
    
    st.subheader("📍 Kitchen Strategy")
    rescue_item = st.text_input("🚨 Expiring Item?", placeholder="e.g., Spinach")
    budget = st.number_input("💰 Budget (Rs)", min_value=0, value=500)

    st.markdown("""
        <div style="text-align: center;">
            <h1>🥣 Chef AI-Xora</h1>
            <p style="font-size: 1.2rem; color: #555;">The Strategic Kitchen Assistant that actually manages.</p>
        </div>
        """, unsafe_allow_html=True)
        
        
    if st.button("🗑️ Clear Kitchen Memory"):
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)
        st.session_state.messages = []
        st.rerun()

    # Main UI Header
st.title("👨‍🍳 Strategic Kitchen Assistant")
st.caption("Waste-aware and budget-conscious meal planning.")

# Initialize Session State
if "messages" not in st.session_state:
    saved_history = load_data()
    st.session_state.messages = []
    for msg in saved_history:
        st.session_state.messages.append({
            "role": "assistant" if msg["role"] == "model" else "user",
            "content": msg["parts"][0]["text"]
        })

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CHAT LOGIC ---
# User Input
if prompt := st.chat_input("Ask Chef AI-Xora..."):
    
    # Strictly define greetings
    greetings = ["hi", "hello", "hey", "salam", "hey there", "hola"]
    user_said = prompt.lower().strip().replace("!", "").replace(".", "")
    is_greeting = user_said in greetings
    
    if is_greeting:
        # AI ko force karna ke sirf greet kare
        full_prompt = f"ACT IN GREETING MODE: The user said '{prompt}'. Just give a 1-sentence bossy greeting."
    else:
        # Strategy mode activate karna
        full_prompt = f"ACT IN STRATEGY MODE: User Request: {prompt}. (Rescue: {rescue_item}, Budget: Rs.{budget})."
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Chef AI-Xora is thinking..."):
            history_for_gemini = [
                {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                for m in st.session_state.messages[:-1]
            ]
            
            chat_session = model.start_chat(history=history_for_gemini)
            try:
                response = chat_session.send_message(full_prompt)
                full_response = response.text
                st.markdown(full_response)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                save_data(st.session_state.messages) 
            except Exception as e:
                st.error(f"Error: {e}")



