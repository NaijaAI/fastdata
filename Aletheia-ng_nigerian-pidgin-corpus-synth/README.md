---
tags:
- fastdata
- synthetic
configs:
- config_name: default
  data_files: data/*.jsonl
---

# Aletheia-ng/nigerian-pidgin-corpus-synth

_Note: This is an AI-generated dataset, so its content may be inaccurate or false._

**Source of the data:**

The dataset was generated using [Fastdata](https://github.com/AnswerDotAI/fastdata) library and openrouter/google/gemma-3-27b-it:free with the following input:

## System Prompt

```

You are a native Nigerian Pidgin speaker and storyteller. You write authentic,
natural-sounding Pidgin text that captures the rhythm and expressions of how
real Nigerians speak.

Your writing should:
- Use common Pidgin words and phrases (wetin, dey, na, abi, walahi, etc.)
- Include natural exclamations (Chei!, Haba!, Ehen!, etc.)
- Feel conversational and warm
- Avoid formal or academic language
- Never mix in full English sentences - stay in Pidgin throughout

```

## Prompt Template

```

Write a long {genre} in Nigerian Pidgin about {topic}.

Setting: {setting}
Mood/Tone: {tone}
Speaker: {speaker}
Time: {time_period}

IMPORTANT RULES:
1. Write ONLY in Nigerian Pidgin - no English sentences
2. Use simple, everyday Pidgin that everyone can understand
3. Make it LONG - at least 200 words, aim for 300-500 words
4. Make it natural - like how real Naija people talk
5. Include local expressions, greetings, and exclamations
6. The content should feel authentic to Nigerian culture

Generate a complete {genre} with a clear beginning, middle, and end.

```

## Sample Input

```json
[{'topic': 'market_and_trading', 'genre': 'life_advice', 'setting': 'lagos_urban', 'tone': 'hopeful_inspiring', 'speaker': 'young_adult', 'time_period': 'present_day'}, {'topic': 'technology_and_phones', 'genre': 'letter', 'setting': 'workplace', 'tone': 'angry_frustrated', 'speaker': 'trader_business', 'time_period': 'past_memory'}]
```

