# ==================== IMPORTS ====================
# Import built-in modules for system operations, web access, subprocess handling, requests, keyboard inputs, and async programming.
import os
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import threading

import psutil
import win32gui
import win32process

import pywhatkit as kit
# Import external libraries for app control, browser handling, YouTube/Google search, environment variable management, HTML parsing, styled output, and AI interaction.
from AppOpener import close, open as appopen # Import functions to open and close apps.
from webbrowser import open as webopen  # Import web browser functionality.
from pywhatkit import search, playonyt  # Import functions for Google search and YouTube playback.
from dotenv import dotenv_values  # Import dotenv to manage environment variables.
from bs4 import BeautifulSoup  # Import BeautifulSoup for parsing HTML content. 
from rich import print  # Import rich for styled console output.
from groq import Groq  # Import Groq for AI chat functionalities.
from difflib import get_close_matches  # Import for fuzzy matching
from serpapi import GoogleSearch as SerpGoogleSearch


# ==================== ENV & API INIT ====================
# Load environment variables from .env file.
env_vars = dotenv_values(".env")
# Extract the Groq API key from the environment variables.
GroqAPIKey = env_vars.get("GroqAPIKey") 
SERPAPI_KEY = env_vars.get("SerpAPI")
classes = ["zCubwf", "hgKElc", "LTKOO sY7ric","Z0LcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee","tw-text-small tw-ta","IZ6rdc","O5uR6d LTKOO","vlzY6d", "webanswers-webanswers_table__webanswers-table","dDoNo ikbBd gsrt", "sXLaOe","LWkfKe", "VQF4g","qv3Wpe", "kno-rdesc", "SPZz6b" ]

# ==================== CONSTANTS ====================
# Define a User-Agent string for web requests.
useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'

client = Groq(api_key=GroqAPIKey)  


# ==================== PROFESSIONAL RESPONSES ====================
# Store predefined professional chatbot responses.
professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need—don't hesitate to ask."
]

# Initialize message list for chatbot conversation.
messages = []
# Define system message to guide the chatbot’s behavior.
SystemChatBot = [{"role": "system", "content": f"Hello, I am {os.environ.get('Username')}, You're a content writer. You have to write content like letters."}]

# ==================== FUNCTIONS ====================
# Perform a Google search using pywhatkit.
def GoogleSearch(Topic):
    search(Topic)
    return True



# Generate content with AI and open the result in Notepad.
def Content(Topic):
    # Open a file in Notepad.
    def OpenNotepad(File):
        default_text_editor = 'Notepad.exe'
        subprocess.Popen([default_text_editor,File])

    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )

        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})
        return Answer

    Topic: str = Topic.replace("Content", "")
    ContentByAI = ContentWriterAI(Topic)

    with open(rf"Data\{Topic.lower().replace(' ', '')}.txt", "w", encoding="utf-8") as file:
        file.write(ContentByAI)
        file.close()

    OpenNotepad(rf"Data\{Topic.lower().replace(' ', '')}.txt")
    return True


# Perform a YouTube search and open the results page.
def YouTubeSearch(Topic):
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}"
    webbrowser.open(Url4Search)
    return True

# Play the top result for a query directly on YouTube.
def PlayYoutube(query):
    try:
        # 🔍 Use YouTube search directly
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        response = requests.get(search_url).text

        # 🎯 Extract the first video id
        start = response.find("/watch?v=")
        if start == -1:
            print("❌ No video found.")
            return False

        video_id = response[start:start+20].split('"')[0]
        video_url = f"https://www.youtube.com{video_id}"

        # 🚀 Open first video directly
        webbrowser.open(video_url, new=1)
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False
    

# Attempt to open an application or web-based service.
def OpenApp(app):
    # ✅ Step 1: Try local app
    try:
        print(f"OPENING {app.upper()}")
        appopen(app, match_closest=True, output=True, throw_error=True )
        return True
    
    except:
        print(f"⚠️ {app} not found on system, searching web...")

        # ✅ Step 2: Use SerpApi
        api_key = SERPAPI_KEY
        if not api_key:
            print("❌ SERPAPI_KEY not set in .env file!")
            return False

        params = {
            "engine": "google",
            "q": app,
            "api_key": api_key
        }

        searched = SerpGoogleSearch(params)
        results = searched.get_dict()

        # Debug print to see structure
        print("🔍 Raw SerpApi keys:", results.keys())

        if "organic_results" in results:
            for result in results["organic_results"][:5]:
                link = result.get("link")
                print("➡️ Candidate:", link)
                if link:
                    print(f"🌐 Opening: {link}")
                    webopen(link)
                    return True

        print(f"❌ No valid website found for {app}")
        return False



# Attempt to close a running application.
def _enum_windows_callback(hwnd, results):
    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
        results.append((hwnd, win32gui.GetWindowText(hwnd)))

def CloseApp(app_name: str):
    app_name = app_name.lower().strip()
    
    # 🚫 Skip Chrome always
    if "chrome" in app_name:
        print("⚠️ Skipping Chrome – not allowed to close")
        return False

    closed = False

    # 1️⃣ Try to close processes directly
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if app_name in proc.info['name'].lower():
                proc.kill()
                closed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # 2️⃣ Check windows hosted inside ApplicationFrameHost.exe
    windows = []
    win32gui.EnumWindows(_enum_windows_callback, windows)
    for hwnd, title in windows:
        if app_name in title.lower():  # e.g. "Instagram"
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                psutil.Process(pid).kill()
                closed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    return closed
        

# Simulate system volume operations.
import keyboard

def System(command):
    def mute():
        keyboard.press_and_release("volume mute")

    def unmute():
        keyboard.press_and_release("volume mute")  # toggle mute

    def volume_up(steps=5):
        for _ in range(steps):
            keyboard.press_and_release("volume up")

    def volume_down(steps=5):
        for _ in range(steps):
            keyboard.press_and_release("volume down")

    command = command.lower().strip()
    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()
    else:
        return False

    return True




# ==================== EXECUTION ENGINE ====================
# Handle multiple commands asynchronously and route them to appropriate functions.
async def TranslateAndExecute(commands: list[str]):
    funcs = []
    for command in commands:
        if command.startswith("open "): 
            if "open it" in command:
                pass
                 
            if "open file" == command:
                pass
                
            else:
                fun = asyncio.to_thread(OpenApp, command.removeprefix("open "))
                funcs.append(fun)
        elif command.startswith("general "):
             pass
        
        elif command.startswith("realtime "):
             pass
            
        elif command.startswith("close "):
            fun = asyncio.to_thread(CloseApp, command.removeprefix("close "))
            funcs.append(fun)
        
        elif command.startswith("play "):
            fun = asyncio.to_thread(PlayYoutube, command.removeprefix("play ").strip())
            funcs.append(fun)
        
        elif command.startswith("content "):
            fun = asyncio.to_thread(Content, command.removeprefix("content "))
            funcs.append(fun)
        
        elif command.startswith("google search "):
            fun = asyncio.to_thread(GoogleSearch, command.removeprefix("google search "))
            funcs.append(fun)
        
        elif command.startswith("youtube search "):
            fun = asyncio.to_thread(YouTubeSearch, command.removeprefix("youtube search "))
            funcs.append(fun)
        
        elif command.startswith("system "):
            fun = asyncio.to_thread(System, command.removeprefix("system "))
            funcs.append(fun)
        
        else:
            print(f"No Function Found for: {command}")

    results = await asyncio.gather(*funcs)

    for result in results:
        if isinstance(result,str):
            yield result
        else:
            yield result


async def Automation(commands: list[str]):

    async for result in TranslateAndExecute(commands):
        pass
         
    return True 