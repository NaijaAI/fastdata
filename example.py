#!/usr/bin/env python3
"""
Example script demonstrating FastData usage

Requirements:
- Install dependencies: pip install -e .
- Set up API credentials for your chosen provider (OpenAI, Anthropic, etc.)
"""

from pydantic import BaseModel
from fastdata.core import FastData


dimensions = [
  ("Shopping", "Short simple sentence (4–6 words)", "Present simple", "Positive statement"),
  ("Work & office", "Medium sentence (7–10 words)", "Past simple", "Negative statement"),
  ("Banking & finance", "Question (short)", "Present simple", "Positive question"),
  ("Logistics & delivery", "Imperative command (long)", "Future simple", "Positive command"),
  ("Retail & sales", "Dialogue-style utterance (short)", "Present continuous", "Affirmation"),
  ("Business negotiation", "Long descriptive sentence (11–15 words)", "Conditional present", "Neutral/hedged statement"),
  ("Customer support", "Exclamatory (short)", "Present simple", "Strong negative emphasis"),
  ("Marketing & advertising", "Compound sentence (2 clauses)", "Future simple", "Positive statement"),
  ("E-commerce", "Medium sentence (7–10 words)", "Past perfect", "Negative statement"),
  ("Banking & finance", "Dialogue-style utterance (short)", "Future simple", "Affirmation"),
  ("Retail & sales", "Exclamatory (long)", "Present simple", "Strong positive emphasis"),
  ("Work & office", "Imperative command (short)", "Present simple", "Positive command"),
  ("Shopping", "Question (long)", "Future simple", "Positive question"),
  ("Logistics & delivery", "Complex sentence (with subordinate clause)", "Past continuous", "Denial"),
  ("Customer support", "Medium sentence (7–10 words)", "Present continuous", "Positive statement"),
  ("Banking & finance", "Imperative command (long)", "Future perfect", "Negative command"),
  ("Work & office", "Exclamatory (short)", "Present perfect", "Affirmation"),
  ("Business negotiation", "Dialogue-style utterance (long)", "Conditional past", "Hypothetical polarity"),
  ("E-commerce", "Question (short)", "Past simple", "Negative question"),
  ("Retail & sales", "Medium sentence (7–10 words)", "Near future", "Positive statement"),
  ("Banking & finance", "Dialogue-style utterance (short)", "Conditional present", "Positive question"),
  ("Shopping", "Exclamatory (short)", "Present continuous", "Strong positive emphasis"),
  ("Customer support", "Question (short)", "Future continuous", "Negative question"),
  ("Marketing & advertising", "Long descriptive sentence (11–15 words)", "Conditional future", "Affirmation"),
  ("Retail & sales", "Medium sentence (7–10 words)", "Habitual past", "Denial"),
  ("Work & office", "Complex sentence (with subordinate clause)", "Past perfect", "Contradiction"),
  ("Logistics & delivery", "Imperative command (short)", "Imperative mood", "Positive command"),
  ("Banking & finance", "Dialogue-style utterance (long)", "Future simple", "Uncertainty"),
  ("Customer support", "Question (short)", "Present perfect", "Positive question"),
  ("Business negotiation", "Compound sentence (2 clauses)", "Present continuous", "Neutral/hedged statement"),
  ("A family gathered for dinner when the lights went out", 
   "Medium sentence (7–10 words)", "Past simple", "Negative statement"),
  ("A teacher explaining homework to a distracted student", 
   "Long descriptive sentence (11–15 words)", "Past continuous", "Positive statement"),
  ("A passenger missing the last bus of the night", 
   "Short simple sentence (4–6 words)", "Past simple", "Negative statement"),
  ("A farmer planting seeds before the rain started", 
   "Compound sentence (2 clauses)", "Past perfect", "Affirmation"),
  ("A shopkeeper giving change to a customer", 
   "Dialogue-style utterance (short)", "Present simple", "Positive statement"),
  ("A doctor telling a patient about their test results", 
   "Question (short)", "Present simple", "Positive question"),
  ("Two children arguing about who should clean the room", 
   "Exclamatory (short)", "Present simple", "Strong negative emphasis"),
  ("A manager praising an employee for finishing early", 
   "Medium sentence (7–10 words)", "Past simple", "Positive statement"),
  ("A traveler realizing they forgot their passport at home", 
   "Exclamatory (long)", "Past perfect", "Negative statement"),
  ("A mother reminding her son to lock the door", 
   "Imperative command (short)", "Present simple", "Positive command"),
  ("A student asking a friend for help with an assignment", 
   "Question (long)", "Present continuous", "Positive question"),
  ("A customer complaining that their food order was late", 
   "Dialogue-style utterance (long)", "Past continuous", "Negative statement"),
  ("A musician performing while the audience clapped loudly", 
   "Complex sentence (with subordinate clause)", "Past continuous", "Affirmation"),
  ("A worker delivering a package to the wrong address", 
   "Medium sentence (7–10 words)", "Past simple", "Denial"),
  ("A politician making promises during a campaign speech", 
   "Long descriptive sentence (11–15 words)", "Future simple", "Neutral/hedged statement"),
  ("A group of friends celebrating a birthday at a restaurant", 
   "Exclamatory (short)", "Past simple", "Strong positive emphasis"),
  ("A driver stopping suddenly because of heavy traffic", 
   "Compound sentence (2 clauses)", "Past continuous", "Affirmation"),
  ("A shop assistant helping someone find the right size", 
   "Short simple sentence (4–6 words)", "Present simple", "Positive statement"),
  ("A family rushing to the hospital after an accident", 
   "Dialogue-style utterance (short)", "Past simple", "Negative statement"),
  ("A student remembering to submit homework just in time", 
   "Medium sentence (7–10 words)", "Past perfect", "Positive statement")
]

prompt = """
You are a translation assistant.

Always return translations in this format:
English: <sentence>
Scratchpad: <scratchpad>
Nigerian Pidgin: <translation>

Here are some examples:

English: She cooks rice every morning.
Nigerian Pidgin: She dey cook rice for morning.

English: Do you want to travel tomorrow?
Nigerian Pidgin: Shey you want travel tomorrow?

English: Please write the report today.
Nigerian Pidgin: Abeg write this report today.

Now create ONE new pair under these conditions:
- Topic/Domain: {topic}
- Sentence Length: {length}
- Tense: {tense}
- Polarity: {polarity}

Return in the same format:
English: <sentence>
Scratchpad: <use this space to think about the translation. try out other possible translations. you can have an 'aha' moment where you self correct yourself on what the translation could be from what you initially thought. express how confident you are. do not hesitate to correct yourself when you get initial translation wrong.>
Pidgin: <translation>
"""

inputs = [{"topic": dim[0], "length": dim[1], "tense": dim[2], "polarity": dim[3]} for dim in dimensions]

def main():
    # Initialize FastData
    fd = FastData(
        provider="litellm", 
        model="ollama_chat/gemma3:27b",
    )
    # deepseek-r1:8b
    # Define the data schema
    class Translation(BaseModel):
        english: str
        scratchpad: str
        pidgin: str
    
    # Generate data
    print("Generating translation pairs...")
    results = fd.generate_to_hf(
        prompt_template=prompt, 
        inputs=inputs,
        schema=Translation,
        sp="You are a translation assistant.",
        repo_id="Aletheia-ng/synthetic",
    )
    
    # Display results
    print("\nGenerated recommendations:")
    for i, result in enumerate(results, 1):
        if result:
            print(f"{i}. {result}")
        else:
            print(f"{i}. Failed to generate recommendation")

if __name__ == "__main__":
    print(inputs[0])
    main()