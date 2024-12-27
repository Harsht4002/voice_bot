import spacy
import speech_recognition as sr
import pyttsx3
import time
from datetime import datetime
import pymongo
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import google.generativeai as genai
import os
import random
from config import GEMINI_API_KEY, MONGODB_URI

class AIAgent:
    def __init__(self):
        # Initialize spaCy
        self.nlp = spacy.load("en_core_web_sm")
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        
        # Lead information storage
        self.current_lead = {
            "name": None,
            "company": None,
            "phone": None,
            "email": None,
            "requirements": None,
            "budget": None,
            "timeline": None,
            "qualified": False,
            "meeting_scheduled": False,
            "meeting_date": None,
            "meeting_time": None
        }
        
        # Services offered (keep this for context)
        self.services = {
            "digital marketing": {
                "description": "Complete digital marketing solutions including SEO, PPC, and social media management",
                "starting_price": 1500,
                "minimum_contract": "3 months"
            },
            "web development": {
                "description": "Custom website development and e-commerce solutions",
                "starting_price": 5000,
                "minimum_contract": "1 month"
            },
            "consulting": {
                "description": "Business growth and digital transformation consulting",
                "starting_price": 2000,
                "minimum_contract": "1 month"
            }
        }
        
        # Initialize MongoDB connection
        self.client = pymongo.MongoClient(MONGODB_URI)
        self.db = self.client["sales_conversations"]
        self.conversations = self.db["conversations"]
        
        # Add conversation tracking
        self.conversation_history = {
            "lead_id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "start_time": datetime.now(),
            "messages": [],
            "lead_info": self.current_lead
        }
        
        # Add UI elements
        self.window = None
        self.conversation_display = None
        self.is_running = False
        
        # Replace OpenAI initialization with Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Update system prompt for Gemini
        self.system_prompt = """You are an AI assistant engaging in natural conversation. While you represent Toshal Infotech, 
your primary goal is to have genuine, helpful discussions with people. You should:

1. Be conversational and natural in your responses
2. Avoid repetitive or templated answers
3. Show personality and empathy in your interactions
4. Adapt your tone to match the user's style
5. Be helpful first, sales-focused second

Company Context:
- You represent Toshal Infotech
- Services: Digital Marketing, Web Development, and Consulting
- You can discuss pricing and services when relevant
- Focus on understanding needs before suggesting solutions

Remember to:
- Keep responses varied and natural
- Use conversational language
- Ask follow-up questions naturally
- Share relevant information when appropriate
- Be genuine and helpful
"""
        
    def create_ui(self):
        """Create an enhanced UI window and elements"""
        self.window = tk.Tk()
        self.window.title("AI Sales Agent - Toshal Infotech")
        self.window.geometry("800x600")
        self.window.configure(bg="#f0f0f0")  # Light gray background
        
        # Enhanced style configuration
        style = ttk.Style()
        style.configure("Title.TLabel", 
                       font=("Helvetica", 16, "bold"), 
                       background="#f0f0f0",
                       padding=10)
        style.configure("Status.TLabel", 
                       font=("Helvetica", 10), 
                       background="#f0f0f0",
                       foreground="#666666")
        style.configure("Start.TButton", 
                       font=("Helvetica", 10, "bold"),
                       padding=10)
        style.configure("Stop.TButton", 
                       font=("Helvetica", 10, "bold"),
                       padding=10)
        
        # Create main container
        main_container = ttk.Frame(self.window, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Add title
        title_label = ttk.Label(
            main_container,
            text="AI Sales Assistant",
            style="Title.TLabel"
        )
        title_label.pack(pady=(0, 10))
        
        # Add status indicator
        self.status_label = ttk.Label(
            main_container,
            text="Status: Ready",
            style="Status.TLabel"
        )
        self.status_label.pack(pady=(0, 10))
        
        # Create conversation frame with border and padding
        conversation_frame = ttk.Frame(
            main_container,
            relief="solid",
            borderwidth=1,
            padding=5
        )
        conversation_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Enhanced conversation display
        self.conversation_display = scrolledtext.ScrolledText(
            conversation_frame,
            wrap=tk.WORD,
            font=("Helvetica", 11),
            background="#ffffff",
            foreground="#333333",
            padx=10,
            pady=10,
            height=20
        )
        self.conversation_display.pack(fill=tk.BOTH, expand=True)
        
        # Create button frame with gradient-like background
        button_frame = ttk.Frame(main_container)
        button_frame.pack(pady=15)
        
        # Enhanced buttons
        start_button = tk.Button(
            button_frame,
            text="▶ Start Conversation",
            command=self.start_conversation,
            bg="#4CAF50",  # Green
            fg="white",
            font=("Helvetica", 10, "bold"),
            padx=20,
            pady=10,
            relief=tk.RAISED,
            cursor="hand2"
        )
        start_button.pack(side=tk.LEFT, padx=5)
        
        stop_button = tk.Button(
            button_frame,
            text="⬛ Stop Conversation",
            command=self.stop_conversation,
            bg="#f44336",  # Red
            fg="white",
            font=("Helvetica", 10, "bold"),
            padx=20,
            pady=10,
            relief=tk.RAISED,
            cursor="hand2"
        )
        stop_button.pack(side=tk.LEFT, padx=5)
        
        # Add clear button
        clear_button = tk.Button(
            button_frame,
            text="🗑 Clear Chat",
            command=self.clear_conversation,
            bg="#2196F3",  # Blue
            fg="white",
            font=("Helvetica", 10, "bold"),
            padx=20,
            pady=10,
            relief=tk.RAISED,
            cursor="hand2"
        )
        clear_button.pack(side=tk.LEFT, padx=5)

    def clear_conversation(self):
        """Clear the conversation display"""
        if self.conversation_display:
            self.conversation_display.delete(1.0, tk.END)
            self.update_conversation("System", "Conversation cleared")

    def update_conversation(self, speaker, message):
        """Enhanced update conversation display with colors"""
        if self.conversation_display:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Color-coded messages
            if speaker == "AI":
                self.conversation_display.tag_config("ai", foreground="#2196F3")  # Blue for AI
                self.conversation_display.insert(tk.END, f"[{timestamp}] {speaker}: ", "ai")
            elif speaker == "User":
                self.conversation_display.tag_config("user", foreground="#4CAF50")  # Green for User
                self.conversation_display.insert(tk.END, f"[{timestamp}] {speaker}: ", "user")
            else:
                self.conversation_display.tag_config("system", foreground="#666666")  # Gray for System
                self.conversation_display.insert(tk.END, f"[{timestamp}] {speaker}: ", "system")
            
            self.conversation_display.insert(tk.END, f"{message}\n")
            self.conversation_display.see(tk.END)

    def speak(self, text):
        """Modified speak method to update UI"""
        print(f"AI: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
        
        # Update conversation display
        self.update_conversation("AI", text)
        
        # Save AI's message to conversation history
        self.conversation_history["messages"].append({
            "speaker": "AI",
            "message": text,
            "timestamp": datetime.now()
        })

    def listen(self):
        """Modified listen method to update UI"""
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
            
        try:
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            
            # Update conversation display
            self.update_conversation("User", text)
            
            # Save user's message to conversation history
            self.conversation_history["messages"].append({
                "speaker": "User",
                "message": text,
                "timestamp": datetime.now()
            })
            
            return text.lower()
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand that.")
            return ""
        except sr.RequestError:
            print("Sorry, there was an error with the speech recognition service.")
            return ""

    def start_conversation(self):
        """Enhanced start conversation with status update"""
        if not self.is_running:
            self.is_running = True
            self.status_label.configure(text="Status: Active")
            threading.Thread(target=self.run, daemon=True).start()
            self.update_conversation("System", "Conversation started")

    def stop_conversation(self):
        """Enhanced stop conversation with status update"""
        self.is_running = False
        self.status_label.configure(text="Status: Stopped")
        self.save_to_db()
        self.update_conversation("System", "Conversation ended")

    def save_to_db(self):
        """Save the conversation to MongoDB"""
        self.conversation_history["end_time"] = datetime.now()
        self.conversation_history["lead_info"] = self.current_lead
        try:
            self.conversations.insert_one(self.conversation_history)
            print("Conversation saved to database")
        except Exception as e:
            print(f"Error saving to database: {e}")

    def process_input(self, user_input):
        """Process user input using Gemini AI for dynamic responses"""
        try:
            # Create conversation context
            context = self.system_prompt
            
            # Add lead information context if available
            if any(value for value in self.current_lead.values() if value):
                lead_context = "\nCurrent lead information:\n" + \
                    "\n".join([f"{k}: {v}" for k, v in self.current_lead.items() if v])
                context += lead_context
            
            # Add conversation history
            history = "\nRecent conversation:\n"
            for message in self.conversation_history["messages"][-5:]:
                history += f"{message['speaker']}: {message['message']}\n"
            context += history
            
            # Generate response using Gemini
            chat = self.model.start_chat(history=[])
            response = chat.send_message(
                f"{context}\n\nUser: {user_input}\n\nAssistant:",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=200,
                )
            )
            
            # Extract and process the response
            ai_response = response.text.strip()
            
            # Update lead information based on the response and user input
            self.update_lead_info(user_input, ai_response)
            
            return ai_response
            
        except Exception as e:
            print(f"Gemini AI Error: {e}")
            error_responses = [
                "I didn't quite catch that. Could you please rephrase?",
                "I'm having a bit of trouble understanding. Could you say that again?",
                "Sorry, I missed that. One more time, please?",
                "Could you please repeat that in a different way?",
                "I'm not sure I understood correctly. Could you elaborate?"
            ]
            return random.choice(error_responses)

    def update_lead_info(self, user_input, ai_response):
        """Update lead information based on conversation context"""
        # Extract name if not already set
        if not self.current_lead["name"] and "name is" in user_input.lower():
            name = user_input.lower().split("name is")[-1].strip()
            self.current_lead["name"] = name.title()
        
        # Extract company if not already set
        if not self.current_lead["company"] and "company" in user_input.lower():
            company = user_input.lower().split("company")[-1].strip()
            self.current_lead["company"] = company.title()
        
        # Update meeting information if present in AI response
        if "meeting" in ai_response.lower() and "scheduled" in ai_response.lower():
            self.current_lead["meeting_scheduled"] = True
            
            # Try to extract date and time from the response
            if "on" in ai_response and "at" in ai_response:
                try:
                    date_time = ai_response.split("on")[-1].split("at")
                    self.current_lead["meeting_date"] = date_time[0].strip()
                    self.current_lead["meeting_time"] = date_time[1].split(".")[0].strip()
                except:
                    pass

    def run(self):
        """Main loop for the AI agent"""
        self.speak("Hello! How may I assist you today?")
        
        while True:
            user_input = self.listen()
            
            if user_input:
                response = self.process_input(user_input)
                self.speak(response)
                
                # Check if the conversation should end
                if "goodbye" in response.lower() or "thank you for your time" in response.lower():
                    self.save_to_db()
                    break

def main():
    agent = AIAgent()
    agent.create_ui()
    agent.window.mainloop()

if __name__ == "__main__":
    main()