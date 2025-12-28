"""
Nigerian Pidgin Monolingual Data Generator

Generates diverse, long-form Nigerian Pidgin text for language model training.
Uses dimensional combinations to create 64,800 unique examples.
"""

import itertools
import random

from pydantic import BaseModel

from fastdata.core import FastData

# =============================================================================
# SCHEMA
# =============================================================================


class PidginText(BaseModel):
    """Long-form Nigerian Pidgin text"""

    title: str  # Short title in Pidgin
    content: str  # The main text (target: 200-500 words)
    # summary: str  # Brief summary in Pidgin (1-2 sentences)


# =============================================================================
# DIMENSIONS
# =============================================================================

topics = [
    "family_and_home",  # Family life, household, children
    "market_and_trading",  # Buying, selling, bargaining, prices
    "health_and_wellness",  # Sickness, traditional medicine, hospital
    "food_and_cooking",  # Recipes, eating, local dishes
    "religion_and_faith",  # Church, mosque, prayers, spirituality
    "work_and_hustle",  # Jobs, business, money problems
    "love_and_relationships",  # Dating, marriage, heartbreak
    "education_and_school",  # Learning, teachers, students
    "transport_and_travel",  # Buses, okada, traffic, journeys
    "entertainment",  # Music, Nollywood, parties, football
    "community_and_neighbors",  # Village life, disputes, helping others
    "technology_and_phones",  # Mobile phones, internet, social media
    "politics_and_government",  # Elections, leaders, corruption
    "weather_and_farming",  # Rain, planting, harvest, seasons
    "celebrations_and_events",  # Weddings, funerals, naming ceremonies
]

genres = [
    "story",  # Narrative with beginning, middle, end
    "dialogue",  # Conversation between 2+ people
    "monologue",  # One person speaking at length (advice, rant, reflection)
    "instructions",  # How-to, step-by-step guide
    "news_report",  # Reporting an event or situation
    "letter",  # Written communication to someone
    "folklore",  # Traditional tales, myths, legends
    "life_advice",  # Elder wisdom, lessons learned
]

settings = [
    "lagos_urban",  # City life, fast-paced, modern
    "village_rural",  # Countryside, farming, traditional
    "market",  # Busy trading environment
    "church_mosque",  # Religious setting
    "workplace",  # Office, shop, construction site
    "home",  # Domestic setting
]

tones = [
    "happy_excited",  # Joy, celebration, good news
    "sad_reflective",  # Loss, disappointment, nostalgia
    "angry_frustrated",  # Complaints, injustice, vexation
    "funny_playful",  # Humor, teasing, jokes
    "serious_urgent",  # Important matters, warnings
    "hopeful_inspiring",  # Encouragement, motivation
]

speakers = [
    "elder_wise",  # Older person sharing wisdom
    "young_adult",  # Someone navigating adult life
    "parent",  # Mother or father perspective
    "trader_business",  # Market woman/man, entrepreneur
    "community_member",  # Regular person in society
]

time_periods = [
    "present_day",  # Modern Nigeria, current events
    "past_memory",  # Recalling old times, "back in the day"
    "future_hopes",  # Plans, dreams, what will happen
]


# =============================================================================
# PROMPTS
# =============================================================================

system_prompt = """
You are a native Nigerian Pidgin speaker and storyteller. You write authentic,
natural-sounding Pidgin text that captures the rhythm and expressions of how
real Nigerians speak.

Your writing should:
- Use common Pidgin words and phrases (wetin, dey, na, abi, walahi, etc.)
- Include natural exclamations (Chei!, Haba!, Ehen!, etc.)
- Feel conversational and warm
- Avoid formal or academic language
- Never mix in full English sentences - stay in Pidgin throughout
"""

prompt_template = """
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
"""


# =============================================================================
# COMBINATION FILTERING
# =============================================================================


def is_valid_combination(combo):
    """Filter out invalid or nonsensical combinations."""
    topic, genre, setting, tone, speaker, time_period = combo

    # Folklore should be past/timeless, not future
    if genre == "folklore" and time_period == "future_hopes":
        return False

    # News reports are typically present day
    if genre == "news_report" and time_period == "past_memory":
        return False

    # Instructions don't usually have past tense
    if genre == "instructions" and time_period == "past_memory":
        return False

    return True


# =============================================================================
# INPUT GENERATION
# =============================================================================


def generate_inputs(shuffle=True, seed=42):
    """Generate all valid dimension combinations as input dictionaries."""

    # Generate all combinations
    all_combinations = list(
        itertools.product(topics, genres, settings, tones, speakers, time_periods)
    )

    # Filter invalid combinations
    valid_combinations = [c for c in all_combinations if is_valid_combination(c)]

    # Shuffle for randomness
    if shuffle:
        random.seed(seed)
        random.shuffle(valid_combinations)

    # Convert to input dictionaries
    inputs = [
        {
            "topic": combo[0],
            "genre": combo[1],
            "setting": combo[2],
            "tone": combo[3],
            "speaker": combo[4],
            "time_period": combo[5],
        }
        for combo in valid_combinations
    ]

    return inputs


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import json
    import sys

    # Generate inputs
    inputs = generate_inputs()
    print(f"Total valid combinations: {len(inputs)}")

    # Initialize FastData
    # NOTE: Free models on OpenRouter have issues with structured output
    # Recommended paid alternatives for better quality:
    # - "openrouter/anthropic/claude-3-haiku" ($0.25/M input tokens)
    # - "openrouter/google/gemini-flash-1.5" ($0.075/M input tokens)
    # - "openrouter/deepseek/deepseek-chat" ($0.14/M input tokens)

    fd = FastData(
        provider="litellm",
        model="openrouter/google/gemini-flash-1.5",  # Better structured output support
        calls=5,  # Conservative rate limit
        period=60,
    )

    # Check if we should run in test mode (local generation only)
    test_mode = "--test" in sys.argv
    num_examples = 3 if test_mode else 100

    if test_mode:
        print(
            f"\n🧪 TEST MODE: Generating {num_examples} examples locally (not pushing to HF)"
        )
        results = fd.generate(
            prompt_template=prompt_template,
            inputs=inputs[:num_examples],
            schema=PidginText,
            sp=system_prompt,
            max_workers=4,
        )

        # Print results
        for i, result in enumerate(results[:3], 1):  # Show first 3
            if result:
                print(f"\n{'=' * 60}")
                print(f"Example {i}:")
                print(f"{'=' * 60}")
                print(json.dumps(result, indent=2, ensure_ascii=False))

        print(
            f"\n✅ Generated {len([r for r in results if r])} valid examples out of {num_examples}"
        )
    else:
        print(f"\n📤 Generating {num_examples} examples and pushing to HuggingFace")
        # Generate data and push to HuggingFace
        results = fd.generate_to_hf(
            prompt_template=prompt_template,
            inputs=inputs[:num_examples],
            schema=PidginText,
            sp=system_prompt,
            repo_id="Aletheia-ng/nigerian-pidgin-corpus-synth",
            max_workers=16,
        )

        print(f"✅ Generated {len(results)} examples")
