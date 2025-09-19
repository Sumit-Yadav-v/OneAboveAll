from groq import Groq #  Groq is a library for Groq API interaction
from json import dump, load # for reading and writing JSON data
import datetime # for handling date and time
from dotenv import dotenv_values  # loads environment variables from a .env file

# Load environment variables from .env file
env_vars = dotenv_values(".env")

# RETRIEVE information from environment variables
creater = env_vars.get("Username")
PersonalAssistant = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Create a Groq client
client = Groq(api_key=GroqAPIKey)  # Groq API client for AI model interaction

# empty list to store the messages
messages = []

# define a system message to set the context for the AI model
System = f"""
Hello, I am {creater},You are personal assistant of {creater} named {PersonalAssistant} which also has real-time up-to-date information from the internet who only reply to {creater}.
*** if user asks who created you, say I was created by {creater}.***
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English , if user told you to talk in hindi than only reply in hindi only.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

# list of system instructions for the cahtbot
SystemChatBot = [
    {"role": "system", "content": System}
]

try:
    with open(r".\Data\ChatLog.json", "r") as f:
        messages = load(f)

except FileNotFoundError:
    # if the file does not exist, create an empty list
    with open(r".\Data\ChatLog.json", "w") as f:
        dump([], f)

# Function to real time date and time
def RealtimeInformation():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    #format the information into a string
    data = f"Please use this real-information if needed, \n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour}hours : {minute}minutes : {second}seconds\n"
    return data

#modify the chatbot's response for better formatting
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip() ]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

#main chatbot function to hamdle user queries
def ChatBot(Query):
    """Main function to handle user queries and generate responses using Groq API."""
     
    try:

        with open(r".\Data\ChatLog.json", "r") as f:
            messages = load(f)

            # Add the user's query to the messages list
        messages.append({"role": "user", "content": f"{Query}"})

        # make a request to the Groq API
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",# specify the model to use
            messages=SystemChatBot + [{"role": "user", "content": RealtimeInformation()}] + messages,#include system instructions and real-time information
            temperature=1,              # Controls creativity: 0 = factual, 1 = more creative
            max_completion_tokens=8192, # Maximum tokens the model can generate in the response
            top_p=1,                     # Nucleus sampling: 1 = no restriction
            reasoning_effort="high",     # Request higher reasoning effort from the model
            stream=True,                 # Stream tokens as they are generated for real-time output
            stop=None                    # No stop sequence: model decides when to stop
         )
        Answer = "" # initialize an empty string to store the response
            # process the streamed response chunks
        for chunk in completion:
            if chunk.choices[0].delta.content: # check if the chunk has content
                # append the content to the Answer string
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("\s", " ") # clean unwanted tokens

        #append the chatbot's response to the messages list
        messages.append({"role": "assistant", "content": Answer})

        #save the updated messages to the chat log file
        with open(r".\Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        # return the modified answer
        return AnswerModifier(Answer= Answer)
    
    except Exception as e:
        # handle any exceptions that occur during the API call
        print(f"An error occurred: {e}")
        with open(r".\Data\ChatLog.json", "w") as f:
            dump([], f, indent=4)
        return ChatBot(Query)  # retry the function with the same query
    #main prgram entry point
if __name__ == "__main__":
    while True:
        user_input = input("Enter your question: ")
        print(ChatBot(user_input)) #call the ChatBot function with user input

