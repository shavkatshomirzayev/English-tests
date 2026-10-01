import asyncio
import logging
import os
import sqlite3
from datetime import datetime
from random import sample
from typing import Any

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession  # <-- Qo'shildi

# PythonAnywhere bepul tarifi uchun proxy
session = AiohttpSession(proxy="http://proxy.server:3128")  # <-- Qo'shildi
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

BOT_TOKEN = ""
ADMIN_ID_RAW = 6403372647



ADMIN_ID = None

if ADMIN_ID_RAW:
    try:
        ADMIN_ID = int(ADMIN_ID_RAW)
    except ValueError:
        raise RuntimeError("ADMIN_ID must be a Telegram numeric user ID")


DB_NAME = "english_quest_v3.db"

TOTAL_QUESTIONS = 40
POINTS_PER_QUESTION = 10
MAX_SCORE = TOTAL_QUESTIONS * POINTS_PER_QUESTION


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("english_quest")


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage REAL NOT NULL,
            grammar_score INTEGER DEFAULT 0,
            vocabulary_score INTEGER DEFAULT 0,
            everyday_score INTEGER DEFAULT 0,
            reading_score INTEGER DEFAULT 0,
            final_score INTEGER DEFAULT 0,
            level TEXT NOT NULL,
            completed_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def save_result(
    user_id: int,
    username: str | None,
    first_name: str | None,
    score: int,
    section_scores: dict[str, int],
    level: str,
):
    percentage = round((score / MAX_SCORE) * 100, 1)

    conn = get_db()

    conn.execute(
        """
        INSERT INTO results (
            user_id,
            username,
            first_name,
            score,
            total,
            percentage,
            grammar_score,
            vocabulary_score,
            everyday_score,
            reading_score,
            final_score,
            level,
            completed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            username,
            first_name,
            score,
            MAX_SCORE,
            percentage,
            section_scores.get("grammar", 0),
            section_scores.get("vocabulary", 0),
            section_scores.get("everyday", 0),
            section_scores.get("reading", 0),
            section_scores.get("final", 0),
            level,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )

    conn.commit()
    conn.close()


def get_latest_result(user_id: int):
    conn = get_db()

    result = conn.execute(
        """
        SELECT *
        FROM results
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()

    conn.close()

    return result


# ============================================================
# QUESTION DATA
# ============================================================

def option(text: str, correct: bool, explanation: str):
    return {
        "text": text,
        "correct": correct,
        "explanation": explanation,
    }


def question(
    qid: int,
    section: str,
    difficulty: str,
    topic: str,
    text: str,
    options: list[dict[str, Any]],
    passage: str | None = None,
):
    return {
        "id": qid,
        "section": section,
        "difficulty": difficulty,
        "topic": topic,
        "text": text,
        "options": options,
        "passage": passage,
    }


# ============================================================
# 40 QUESTION V3 TEST
# ============================================================

TEST_DATA = [

    # ========================================================
    # 1–10 GRAMMAR — A2 FOUNDATION
    # ========================================================

    question(
        1,
        "grammar",
        "A2_FOUNDATION",
        "present_simple",
        "My brother _____ to work by bus every day.",
        [
            option(
                "go",
                False,
                "With 'my brother', we need the third-person singular form 'goes'.",
            ),
            option(
                "goes",
                True,
                "Correct. We use 'goes' with he/she/it in the Present Simple.",
            ),
            option(
                "going",
                False,
                "'Going' cannot follow the subject like this without an auxiliary verb.",
            ),
            option(
                "gone",
                False,
                "'Gone' is a past participle and does not fit here.",
            ),
        ],
    ),

    question(
        2,
        "grammar",
        "A2_FOUNDATION",
        "present_continuous",
        "Look! The children _____ football in the garden.",
        [
            option(
                "play",
                False,
                "For an action happening now, we normally use the Present Continuous.",
            ),
            option(
                "are playing",
                True,
                "Correct. 'Are playing' describes an action happening now.",
            ),
            option(
                "played",
                False,
                "'Played' is Past Simple.",
            ),
            option(
                "plays",
                False,
                "'Plays' is Present Simple and does not fit the context.",
            ),
        ],
    ),

    question(
        3,
        "grammar",
        "A2_FOUNDATION",
        "past_simple",
        "We _____ a great film last night.",
        [
            option(
                "watch",
                False,
                "The time expression 'last night' requires a past form.",
            ),
            option(
                "watched",
                True,
                "Correct. 'Watched' is the Past Simple form.",
            ),
            option(
                "are watching",
                False,
                "This is Present Continuous.",
            ),
            option(
                "have watched",
                False,
                "Present Perfect is not normally used with a finished past time such as 'last night'.",
            ),
        ],
    ),

    question(
        4,
        "grammar",
        "A2_FOUNDATION",
        "future",
        "I think it _____ rain tomorrow.",
        [
            option(
                "will",
                True,
                "Correct. 'Will' is commonly used for predictions.",
            ),
            option(
                "did",
                False,
                "'Did' is a past auxiliary.",
            ),
            option(
                "was",
                False,
                "'Was' is a past form of 'be'.",
            ),
            option(
                "has",
                False,
                "'Has' does not form this future prediction.",
            ),
        ],
    ),

    question(
        5,
        "grammar",
        "A2_FOUNDATION",
        "present_perfect",
        "She _____ just finished her homework.",
        [
            option(
                "has",
                True,
                "Correct. Present Perfect uses 'has/have + past participle'.",
            ),
            option(
                "is",
                False,
                "'Is' does not form the Present Perfect.",
            ),
            option(
                "did",
                False,
                "'Did' forms questions and negatives in Past Simple.",
            ),
            option(
                "was",
                False,
                "'Was' is not used to form Present Perfect.",
            ),
        ],
    ),

    question(
        6,
        "grammar",
        "A2_FOUNDATION",
        "modal_verbs",
        "You _____ wear a seat belt in a car.",
        [
            option(
                "should",
                False,
                "'Should' can express advice, but the sentence describes a requirement.",
            ),
            option(
                "must",
                True,
                "Correct. 'Must' expresses a strong obligation.",
            ),
            option(
                "could",
                False,
                "'Could' expresses possibility or ability, not this obligation.",
            ),
            option(
                "might",
                False,
                "'Might' expresses possibility.",
            ),
        ],
    ),

    question(
        7,
        "grammar",
        "A2_FOUNDATION",
        "comparatives",
        "My new phone is _____ than my old one.",
        [
            option(
                "expensive",
                False,
               "A comparative form is needed because we are comparing two phones.",
            ),
            option(
                "more expensive",
                True,
                "Correct. Long adjectives normally use 'more + adjective'.",
            ),
            option(
                "most expensive",
                False,
                "'Most expensive' is a superlative, used when comparing three or more things.",
            ),
            option(
                "expensiver",
                False,
                "'Expensive' does not normally form its comparative with '-er'.",
            ),
        ],
    ),

    question(
        8,
        "grammar",
        "A2_FOUNDATION",
        "first_conditional",
        "If it rains tomorrow, we _____ at home.",
        [
            option(
                "stay",
                False,
               "The result clause needs a future form in this first conditional sentence.",
            ),
            option(
                "will stay",
                True,
                "Correct. First conditional: If + Present Simple, will + verb.",
            ),
            option(
                "stayed",
                False,
               "This is Past Simple and does not fit the future situation.",
            ),
            option(
                "would stay",
                False,
               "'Would' is normally associated with the second conditional here.",
            ),
        ],
    ),

    question(
        9,
        "grammar",
        "A2_FOUNDATION",
        "used_to",
        "I _____ play football every weekend when I was younger.",
        [
            option(
                "use to",
                False,
               "After 'I', the correct form in this positive sentence is 'used to'.",
            ),
            option(
                "used to",
                True,
                "Correct. 'Used to' describes a past habit or situation that is no longer true.",
            ),
            option(
                "am used to",
                False,
               "'Be used to' means being accustomed to something and has a different meaning.",
            ),
            option(
                "was used",
                False,
               "This does not express a past habit.",
            ),
        ],
    ),

    question(
        10,
        "grammar",
        "A2_FOUNDATION",
        "question_forms",
        "_____ you ever been to Turkey?",
        [
            option(
                "Did",
                False,
               "Present Perfect questions use 'have/has', not 'did'.",
            ),
            option(
                "Have",
                True,
                "Correct. 'Have you ever been...?' asks about life experience.",
            ),
            option(
                "Are",
                False,
               "'Are' cannot form this Present Perfect question.",
            ),
            option(
                "Do",
                False,
               "'Do' is not used with 'been' in this structure.",
            ),
        ],
    ),

    # ========================================================
    # 11–20 VOCABULARY — A2
    # ========================================================

    question(
        11,
        "vocabulary",
        "A2",
        "travel",
        "Our flight was _____ for three hours because of bad weather.",
        [
            option(
                "delayed",
                True,
                "Correct. A delayed flight leaves later than planned.",
            ),
            option(
                "borrowed",
                False,
               "'Borrowed' means taken temporarily from someone.",
            ),
            option(
                "repaired",
                False,
               "'Repaired' means fixed.",
            ),
            option(
                "invited",
                False,
               "'Invited' does not describe a flight's departure time.",
            ),
        ],
    ),

    question(
        12,
        "vocabulary",
        "A2",
        "travel",
        "We need to leave our hotel early because our _____ is at 7:30 a.m.",
        [
            option(
                "departure",
                True,
                "Correct. 'Departure' is the time or act of leaving.",
            ),
            option(
                "luggage",
                False,
               "Luggage means bags and suitcases.",
            ),
            option(
                "receipt",
                False,
               "A receipt is proof of payment.",
            ),
            option(
                "neighbourhood",
                False,
               "A neighbourhood is an area where people live.",
            ),
        ],
    ),

    question(
        13,
        "vocabulary",
        "A2",
        "education",
        "I have an English _____ every Tuesday and Thursday.",
        [
            option(
                "course",
                True,
                "Correct. A course is a series of lessons about a subject.",
            ),
            option(
                "salary",
                False,
               "A salary is money earned from a job.",
            ),
            option(
                "deadline",
                False,
               "A deadline is the latest time something must be completed.",
            ),
            option(
                "ingredient",
                False,
               "An ingredient is used to make food.",
            ),
        ],
    ),

    question(
        14,
        "vocabulary",
        "A2",
        "work",
        "My manager asked me to finish the report before the _____.",
        [
            option(
                "deadline",
                True,
                "Correct. A deadline is the required finishing time.",
            ),
            option(
                "device",
                False,
               "A device is a piece of electronic equipment.",
            ),
            option(
                "appointment",
                False,
               "An appointment is an arranged meeting or visit.",
            ),
            option(
                "journey",
                False,
               "A journey is travel from one place to another.",
            ),
        ],
    ),

    question(
        15,
        "vocabulary",
        "A2",
        "food",
        "This soup is very _____. I need some water!",
        [
            option(
                "spicy",
                True,
                "Correct. Spicy food contains strong hot flavours.",
            ),
            option(
                "crowded",
                False,
               "Crowded describes a place with many people.",
            ),
            option(
                "quiet",
                False,
               "Quiet describes a place or sound with little noise.",
            ),
            option(
                "late",
                False,
               "Late describes time.",
            ),
        ],
    ),

    question(
        16,
        "vocabulary",
        "A2",
        "health",
        "I have a terrible headache. I should make a doctor's _____.",
        [
            option(
                "appointment",
                True,
                "Correct. You make an appointment to arrange a visit with a doctor.",
            ),
            option(
                "salary",
                False,
               "A salary is payment for work.",
            ),
            option(
                "booking",
                False,
               "A booking can be a reservation, but 'doctor's appointment' is the natural expression.",
            ),
            option(
                "course",
                False,
               "A course is a series of lessons.",
            ),
        ],
    ),

    question(
        17,
        "vocabulary",
        "A2",
        "technology",
        "I forgot my _____, so I can't log in to my account.",
        [
            option(
                "password",
                True,
                "Correct. A password is used to access an account.",
            ),
            option(
                "luggage",
                False,
               "Luggage means bags.",
            ),
            option(
                "ingredient",
                False,
               "An ingredient is part of a recipe.",
            ),
            option(
                "salary",
                False,
               "A salary is payment from employment.",
            ),
        ],
    ),

    question(
        18,
        "vocabulary",
        "A2",
        "daily_life",
        "I usually _____ at 6:30 and have breakfast before work.",
        [
            option(
                "get up",
                True,
                "Correct. 'Get up' means leave your bed after sleeping.",
            ),
            option(
                "find out",
                False,
               "'Find out' means discover information.",
            ),
            option(
                "turn off",
                False,
               "'Turn off' means stop a machine or light.",
            ),
            option(
                "look for",
                False,
               "'Look for' means try to find something.",
            ),
        ],
    ),

    question(
        19,
        "vocabulary",
        "A2",
        "phrasal_verbs",
        "I'm _____ my keys. Have you seen them?",
        [
            option(
                "looking for",
                True,
                "Correct. 'Look for' means try to find something.",
            ),
            option(
                "getting up",
                False,
               "'Get up' means leave your bed or stand.",
            ),
            option(
                "turning on",
                False,
               "'Turn on' means activate a device.",
            ),
            option(
                "finding out",
                False,
               "'Find out' means discover information.",
            ),
        ],
    ),

    question(
        20,
        "vocabulary",
        "A2",
        "phrasal_verbs",
        "Please _____ the lights before you leave the room.",
        [
            option(
                "turn off",
                True,
                "Correct. 'Turn off' means stop a light or electrical device.",
            ),
            option(
                "pick up",
                False,
               "'Pick up' has several meanings, including lifting something.",
            ),
            option(
                "find out",
                False,
               "'Find out' means discover information.",
            ),
            option(
                "put on",
                False,
               "'Put on' means place clothes or something similar on your body.",
            ),
        ],
    ),

    # ========================================================
    # 21–24 EVERYDAY ENGLISH
    # ========================================================

    question(
        21,
        "everyday",
        "STRONG_A2",
        "restaurant_problem",
        "You ordered chicken soup, but the waiter brought tomato soup. What is the most natural thing to say?",
        [
            option(
                "Excuse me, I think I ordered chicken soup.",
                True,
                "Correct. This is a polite way to point out the mistake.",
            ),
            option(
                "You bring me chicken soup!",
                False,
               "This is understandable, but it sounds too direct and unnatural in this situation.",
            ),
            option(
                "Chicken soup is brought by me.",
                False,
               "This passive structure does not express what you want to say.",
            ),
            option(
                "I don't want any soup ever.",
                False,
               "This does not politely explain the problem.",
            ),
        ],
    ),

    question(
        22,
        "everyday",
        "STRONG_A2",
        "hotel",
        "Your hotel room is very noisy because of loud music next door. What would you say to reception?",
        [
            option(
                "Could you help me? My room is very noisy.",
                True,
                "Correct. This is polite and clearly explains the problem.",
            ),
            option(
                "Stop the hotel!",
                False,
               "This does not clearly or politely explain the problem.",
            ),
            option(
                "My room makes music.",
                False,
               "This changes the meaning: the room is not making the music.",
            ),
            option(
                "I am noisy my room.",
                False,
               "This is grammatically incorrect.",
            ),
        ],
    ),

    question(
        23,
        "everyday",
        "STRONG_A2",
        "invitations",
        "A colleague invites you to a party, but you cannot go. What is the most natural response?",
        [
            option(
                "I'd love to, but I can't. Thanks for inviting me.",
                True,
                "Correct. This politely accepts the invitation in principle while explaining that you cannot attend.",
            ),
            option(
                "No. Party impossible.",
                False,
               "This is understandable but sounds abrupt and unnatural.",
            ),
            option(
                "I don't go your party.",
                False,
               "This is grammatically and socially unnatural.",
            ),
            option(
                "You must go without me.",
                False,
               "This does not directly and politely decline the invitation.",
            ),
        ],
    ),

    question(
        24,
        "everyday",
        "STRONG_A2",
        "phone_conversation",
        "You cannot hear someone clearly during a phone call. What should you say?",
        [
            option(
                "Sorry, could you say that again?",
                True,
                "Correct. This is a common polite way to ask someone to repeat themselves.",
            ),
            option(
                "What are you talking?",
                False,
               "The natural form would be 'What are you talking about?', but that would not be the normal request here.",
            ),
            option(
                "You speak bad.",
                False,
               "This is impolite and grammatically incorrect.",
            ),
            option(
                "Repeat your voice.",
                False,
               "This is not natural English.",
            ),
        ],
    ),

    # ========================================================
    # 25–32 READING
    # ========================================================

    question(
        25,
        "reading",
        "STRONG_A2",
        "reading_detail",
        "Why did Daniel leave home early?",
        passage=(
            "Daniel usually starts work at nine o'clock. On Monday, he left home "
            "at seven because he had an important meeting with a new customer. "
            "The meeting was in another part of the city, so Daniel decided to "
            "take an earlier bus. The bus was crowded, but it arrived on time. "
            "Daniel reached the office twenty minutes before the meeting."
        ),
        options=[
            option(
                "Because he had an important meeting.",
                True,
                "Correct. The passage directly says he left early because of the meeting.",
            ),
            option(
                "Because his bus was late.",
                False,
               "The bus was crowded but arrived on time.",
            ),
            option(
                "Because he started work at seven.",
                False,
               "His normal work time was nine o'clock.",
            ),
            option(
                "Because he wanted to meet a friend.",
                False,
               "The passage does not mention a friend.",
            ),
        ],
    ),

    question(
        26,
        "reading",
        "STRONG_A2",
        "reading_detail",
        "How did Daniel travel to work?",
        passage=(
            "Daniel usually starts work at nine o'clock. On Monday, he left home "
            "at seven because he had an important meeting with a new customer. "
            "The meeting was in another part of the city, so Daniel decided to "
            "take an earlier bus. The bus was crowded, but it arrived on time. "
            "Daniel reached the office twenty minutes before the meeting."
        ),
        options=[
            option(
                "By bus.",
                True,
                "Correct. He decided to take an earlier bus.",
            ),
            option(
                "By train.",
                False,
               "The passage says he took a bus.",
            ),
            option(
                "By taxi.",
                False,
               "No taxi is mentioned.",
            ),
            option(
                "By bicycle.",
                False,
               "No bicycle is mentioned.",
            ),
        ],
    ),

    question(
        27,
        "reading",
        "STRONG_A2",
        "reading_inference",
        "Why was the earlier bus useful for Daniel?",
        passage=(
            "Daniel usually starts work at nine o'clock. On Monday, he left home "
            "at seven because he had an important meeting with a new customer. "
            "The meeting was in another part of the city, so Daniel decided to "
            "take an earlier bus. The bus was crowded, but it arrived on time. "
            "Daniel reached the office twenty minutes before the meeting."
        ),
        options=[
            option(
                "It helped him arrive before the meeting.",
                True,
                "Correct. He arrived twenty minutes before the meeting.",
            ),
            option(
                "It was less crowded than other buses.",
                False,
               "The passage says the bus was crowded.",
            ),
            option(
                "It was cheaper than walking.",
                False,
               "The passage does not discuss the price.",
            ),
            option(
                "It took him to another city.",
                False,
               "The meeting was in another part of the same city.",
            ),
        ],
    ),

    question(
        28,
        "reading",
        "STRONG_A2",
        "reading_vocabulary",
        "In the passage, what does 'crowded' mean?",
        passage=(
            "Daniel usually starts work at nine o'clock. On Monday, he left home "
            "at seven because he had an important meeting with a new customer. "
            "The meeting was in another part of the city, so Daniel decided to "
            "take an earlier bus. The bus was crowded, but it arrived on time. "
            "Daniel reached the office twenty minutes before the meeting."
        ),
        options=[
            option(
                "Full of people.",
                True,
                "Correct. 'Crowded' means a place or vehicle has many people in it.",
            ),
            option(
                "Very expensive.",
                False,
               "This meaning does not fit the context.",
            ),
            option(
                "Very slow.",
                False,
               "The bus was actually on time.",
            ),
            option(
                "Completely empty.",
                False,
               "This is the opposite of crowded.",
            ),
        ],
    ),

    question(
        29,
        "reading",
        "STRONG_A2",
        "reading_main_idea",
        "What is the main reason Emma changed her weekend plans?",
        passage=(
            "Emma had planned to spend Saturday at home and finish a book. "
            "On Friday evening, her friend Sara called and said that she had "
            "two tickets for a music festival. Emma wanted to go, but she was "
            "worried about the weather because rain was expected. On Saturday "
            "morning, the weather was sunny, so Emma decided to go to the "
            "festival with Sara. She took an umbrella just in case."
        ),
        options=[
            option(
                "Her friend offered her a ticket.",
                True,
                "Correct. Sara called with two festival tickets, which changed Emma's plan.",
            ),
            option(
                "Her book was lost.",
                False,
               "The book was not lost.",
            ),
            option(
                "The festival was cancelled.",
                False,
               "The festival happened and Emma went.",
            ),
            option(
                "She wanted to stay at home because of rain.",
                False,
               "Rain was expected, but the sunny weather encouraged her to go.",
            ),
        ],
    ),

    question(
        30,
        "reading",
        "STRONG_A2",
        "reading_inference",
        "Why did Emma take an umbrella?",
        passage=(
            "Emma had planned to spend Saturday at home and finish a book. "
            "On Friday evening, her friend Sara called and said that she had "
            "two tickets for a music festival. Emma wanted to go, but she was "
            "worried about the weather because rain was expected. On Saturday "
            "morning, the weather was sunny, so Emma decided to go to the "
            "festival with Sara. She took an umbrella just in case."
        ),
        options=[
            option(
                "She thought it might rain later.",
                True,
                "Correct. Rain had been expected, so she took an umbrella as a precaution.",
            ),
            option(
                "She needed it to enter the festival.",
                False,
               "The passage does not say this.",
            ),
            option(
                "It was sunny and she wanted shade.",
                False,
               "The passage specifically connects the umbrella with possible rain.",
            ),
            option(
                "Sara told her to bring one.",
                False,
               "The passage does not say Sara told her to bring it.",
            ),
        ],
    ),

    question(
        31,
        "reading",
        "A2_B1_BRIDGE",
        "reading_detail",
        "What had Emma originally planned to do on Saturday?",
        passage=(
            "Emma had planned to spend Saturday at home and finish a book. "
            "On Friday evening, her friend Sara called and said that she had "
            "two tickets for a music festival. Emma wanted to go, but she was "
            "worried about the weather because rain was expected. On Saturday "
            "morning, the weather was sunny, so Emma decided to go to the "
            "festival with Sara. She took an umbrella just in case."
        ),
        options=[
            option(
                "Stay home and finish a book.",
                True,
                "Correct. That was her original plan.",
            ),
            option(
                "Go shopping with Sara.",
                False,
               "No shopping trip is mentioned.",
            ),
            option(
                "Work at the festival.",
                False,
               "Emma went as a visitor.",
            ),
            option(
                "Visit another city.",
                False,
               "No other city is mentioned.",
            ),
        ],
    ),

    question(
        32,
        "reading",
        "A2_B1_BRIDGE",
        "reading_reasoning",
        "Which statement best describes Emma's decision?",
        passage=(
            "Emma had planned to spend Saturday at home and finish a book. "
            "On Friday evening, her friend Sara called and said that she had "
            "two tickets for a music festival. Emma wanted to go, but she was "
            "worried about the weather because rain was expected. On Saturday "
            "morning, the weather was sunny, so Emma decided to go to the "
            "festival with Sara. She took an umbrella just in case."
        ),
        options=[
            option(
                "She changed her plans after the weather improved.",
                True,
                "Correct. The sunny weather helped her decide to go.",
            ),
            option(
                "She changed her plans because she disliked books.",
                False,
               "The passage does not say she disliked books.",
            ),
            option(
                "She went because the festival was free.",
                False,
               "The price is not mentioned.",
            ),
            option(
                "She cancelled the festival.",
                False,
               "She attended the festival.",
            ),
        ],
    ),

    # ========================================================
    # 33–40 FINAL CHALLENGE
    # ========================================================

    question(
        33,
        "final",
        "A2_B1_BRIDGE",
        "present_perfect_vs_past",
        "I've lived here _____ 2021.",
        [
            option(
                "for",
                False,
               "'For' is normally used with a period of time, such as 'three years'.",
            ),
            option(
                "since",
                True,
               "Correct. 'Since' is used with the starting point of an action.",
            ),
            option(
                "from",
                False,
               "'From' is not normally used in this Present Perfect structure.",
            ),
            option(
                "during",
                False,
               "'During' refers to a period/event rather than the starting point.",
            ),
        ],
    ),

    question(
        34,
        "final",
        "A2_B1_BRIDGE",
        "gerund_infinitive",
        "I enjoy _____ English with people from other countries.",
        [
            option(
                "speak",
                False,
               "'Enjoy' is followed by a gerund (-ing form).",
            ),
            option(
                "speaking",
                True,
               "Correct. We say 'enjoy doing something'.",
            ),
            option(
                "to speak",
                False,
               "'Enjoy' is not normally followed by the infinitive.",
            ),
            option(
                "spoke",
                False,
               "Past Simple does not fit after 'enjoy'.",
            ),
        ],
    ),

    question(
        35,
        "final",
        "A2_B1_BRIDGE",
        "second_conditional",
        "If I _____ more free time, I'd learn another language.",
        [
            option(
                "have",
                False,
               "This sentence describes an unreal or hypothetical situation, so Past Simple is used.",
            ),
            option(
                "had",
                True,
               "Correct. Second conditional: If + Past Simple, would + verb.",
            ),
            option(
                "will have",
                False,
               "'Will have' does not fit the second conditional structure.",
            ),
            option(
                "am having",
                False,
               "Present Continuous does not fit this hypothetical structure.",
            ),
        ],
    ),

    question(
        36,
        "final",
        "A2_B1_BRIDGE",
        "modal_meaning",
        "You look tired. You _____ take a break.",
        [
            option(
                "should",
                True,
               "Correct. 'Should' is used to give advice.",
            ),
            option(
                "mustn't",
                False,
               "'Mustn't' means something is prohibited.",
            ),
            option(
                "can't",
                False,
               "'Can't' expresses inability or impossibility.",
            ),
            option(
                "wouldn't",
                False,
               "'Wouldn't' does not fit this advice.",
            ),
        ],
    ),

    question(
        37,
        "final",
        "A2_B1_BRIDGE",
        "question_form",
        "How long _____ you been learning English?",
        [
            option(
                "do",
                False,
               "'Do' is not used to form this Present Perfect question.",
            ),
            option(
                "have",
                True,
               "Correct. 'How long have you been...?' asks about duration continuing until now.",
            ),
            option(
                "did",
                False,
               "'Did' would require a different past-time structure.",
            ),
            option(
                "are",
                False,
               "'Are' does not form this question with 'been learning'.",
            ),
        ],
    ),

    question(
        38,
        "final",
        "A2_B1_BRIDGE",
        "contextual_vocabulary",
        "The train was cancelled, so we had to _____ another way to get home.",
        [
            option(
                "find out",
                False,
               "'Find out' means discover information.",
            ),
            option(
                "look for",
                True,
               "Correct. 'Look for' means try to find something. Here, they needed to search for another way home.",
            ),
            option(
                "turn off",
                False,
               "'Turn off' means deactivate something.",
            ),
            option(
                "get up",
                False,
               "'Get up' means leave your bed or stand.",
            ),
        ],
    ),

    question(
        39,
        "final",
        "A2_B1_BRIDGE",
        "pragmatic_english",
        "Your friend says, 'I'm sorry I'm late.' What is the most natural response?",
        [
            option(
                "That's OK. Don't worry.",
                True,
               "Correct. This is a natural and friendly response to an apology.",
            ),
            option(
                "You are apology.",
                False,
               "This is grammatically incorrect.",
            ),
            option(
                "Late is impossible.",
                False,
               "This does not form a natural response.",
            ),
            option(
                "I am sorry late.",
                False,
               "This is grammatically incomplete.",
            ),
        ],
    ),

    question(
        40,
        "final",
        "A2_B1_BRIDGE",
        "mixed_grammar",
        "By the time we arrived at the cinema, the film _____.",
        [
            option(
                "started",
                False,
               "Past Simple does not clearly show that the film started before our arrival.",
            ),
            option(
                "had started",
                True,
               "Correct. Past Perfect shows that one past event happened before another past event.",
            ),
            option(
                "has started",
                False,
               "Present Perfect does not fit this completed past sequence.",
            ),
            option(
                "is starting",
                False,
               "Present Continuous does not fit the completed past situation.",
            ),
        ],
    ),
]


# ============================================================
# VALIDATE QUESTION BANK
# ============================================================

def validate_questions():
    if len(TEST_DATA) != TOTAL_QUESTIONS:
        raise RuntimeError(
            f"Expected {TOTAL_QUESTIONS} questions, "
            f"found {len(TEST_DATA)}"
        )

    ids = [q["id"] for q in TEST_DATA]

    if len(set(ids)) != len(ids):
        raise RuntimeError("Duplicate question IDs detected")

    for q in TEST_DATA:
        if len(q["options"]) != 4:
            raise RuntimeError(
                f"Question {q['id']} must have exactly 4 options"
            )

        correct_count = sum(
            1 for opt in q["options"] if opt["correct"]
        )

        if correct_count != 1:
            raise RuntimeError(
                f"Question {q['id']} must have exactly 1 correct answer"
            )


# ============================================================
# USER SESSIONS
# ============================================================

user_sessions: dict[int, dict[str, Any]] = {}


def create_session(user_id: int):
    """
    Creates a fresh test session.

    We randomize the order of questions within each assessment
    while preserving the overall difficulty progression.
    """

    foundation = [q for q in TEST_DATA if q["id"] <= 10]
    a2 = [q for q in TEST_DATA if 11 <= q["id"] <= 20]
    strong_a2 = [q for q in TEST_DATA if 21 <= q["id"] <= 30]
    bridge = [q for q in TEST_DATA if 31 <= q["id"] <= 40]

    # We randomize only inside each difficulty block.
    questions = (
        sample(foundation, len(foundation))
        + sample(a2, len(a2))
        + sample(strong_a2, len(strong_a2))
        + sample(bridge, len(bridge))
    )

    # Randomize options for every question.
    prepared_questions = []

    for q in questions:
        copied = dict(q)
        copied["options"] = sample(
            q["options"],
            len(q["options"]),
        )
        prepared_questions.append(copied)

    user_sessions[user_id] = {
        "questions": prepared_questions,
        "current": 0,
        "score": 0,
        "section_scores": {
            "grammar": 0,
            "vocabulary": 0,
            "everyday": 0,
            "reading": 0,
            "final": 0,
        },
        "answered": 0,
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }

    return user_sessions[user_id]


def get_session(user_id: int):
    return user_sessions.get(user_id)


def clear_session(user_id: int):
    user_sessions.pop(user_id, None)


# ============================================================
# LEVEL / DIAGNOSTIC
# ============================================================

def calculate_level(score: int) -> str:
    percentage = (score / MAX_SCORE) * 100

    if percentage >= 85:
        return "A2 → B1 bridge"

    if percentage >= 70:
        return "Strong A2"

    if percentage >= 55:
        return "A2"

    return "A2 Foundation"


def difficulty_label(index: int) -> str:
    if index < 10:
        return "🟢 A2 Foundation"

    if index < 20:
        return "🟢 A2"

    if index < 30:
        return "🟡 Strong A2"

    return "🟠 A2 → B1"


# ============================================================
# KEYBOARDS
# ============================================================

def start_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Start Test",
                    callback_data="start_test",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 My Last Result",
                    callback_data="last_result",
                )
            ],
        ]
    )


def question_keyboard(
    question_data: dict[str, Any],
    question_index: int,
):
    buttons = []

    for index, opt in enumerate(question_data["options"]):
        buttons.append(
            [
                InlineKeyboardButton(
                    text=opt["text"],
                    callback_data=f"answer:{question_index}:{index}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="❌ Cancel Test",
                callback_data="cancel_test",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def after_answer_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➡️ Next Question",
                    callback_data="next_question",
                )
            ]
        ]
    )


# ============================================================
# TEXT HELPERS
# ============================================================

SECTION_NAMES = {
    "grammar": "Grammar",
    "vocabulary": "Vocabulary",
    "everyday": "Everyday English",
    "reading": "Reading",
    "final": "Final Challenge",
}


def progress_bar(current: int, total: int) -> str:
    filled = int((current / total) * 10)

    return "🟩" * filled + "⬜" * (10 - filled)


def format_section_score(score: int, question_count: int) -> str:
    possible = question_count * POINTS_PER_QUESTION
    percentage = round((score / possible) * 100)

    return f"{score}/{possible} ({percentage}%)"


# ============================================================
# BOT
# ============================================================

bot = Bot(
    token=BOT_TOKEN,
    session=session,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
    ),
)

dp = Dispatcher()


# ============================================================
# /START
# ============================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user

    if not user:
        return

    text = (
        "🎓 <b>English Quest V3</b>\n\n"
        "Welcome!\n\n"
        "This is an English placement-style diagnostic test "
        "designed around A2 → B1 skills.\n\n"
        "📚 <b>40 questions</b>\n"
        "💯 <b>400 maximum points</b>\n"
        "⏱️ No strict time limit\n\n"
        "The test covers:\n"
        "• Grammar\n"
        "• Vocabulary\n"
        "• Everyday English\n"
        "• Reading\n"
        "• Final Challenge\n\n"
        "⚠️ Your result is a diagnostic estimate, "
        "not an official CEFR certification."
    )

    await message.answer(
        text,
        reply_markup=start_keyboard(),
    )


# ============================================================
# /TEST
# ============================================================

@dp.message(Command("test"))
async def cmd_test(message: Message):
    user = message.from_user

    if not user:
        return

    create_session(user.id)

    await message.answer(
        "🚀 <b>Your V3 test is starting!</b>\n\n"
        "Choose the best answer for each question.\n"
        "You will receive a short explanation after every answer."
    )

    await send_question(message, user.id)


# ============================================================
# START TEST CALLBACK
# ============================================================

@dp.callback_query(F.data == "start_test")
async def callback_start_test(callback: CallbackQuery):
    user = callback.from_user

    create_session(user.id)

    await callback.answer("Test started!")

    await callback.message.edit_text(
        "🚀 <b>English Quest V3 started!</b>\n\n"
        "Choose the best answer for each question."
    )

    await send_question(callback.message, user.id)


# ============================================================
# SEND QUESTION
# ============================================================

async def send_question(message: Message, user_id: int):
    session = get_session(user_id)

    if not session:
        await message.answer(
            "There is no active test.\n\n"
            "Use /start to begin."
        )
        return

    current = session["current"]
    questions = session["questions"]

    if current >= len(questions):
        await finish_test(message, user_id)
        return

    q = questions[current]

    section = SECTION_NAMES[q["section"]]

    header = (
        f"{difficulty_label(current)}\n"
        f"📚 <b>{section}</b>\n\n"
        f"<b>Question {current + 1}/{len(questions)}</b>\n"
        f"{progress_bar(current, len(questions))}\n\n"
    )

    passage_text = ""

    if q.get("passage"):
        passage_text = (
            f"📖 <b>Read the passage:</b>\n\n"
            f"<i>{q['passage']}</i>\n\n"
        )

    text = (
        header
        + passage_text
        + f"❓ <b>{q['text']}</b>"
    )

    await message.answer(
        text,
        reply_markup=question_keyboard(q, current),
    )


# ============================================================
# ANSWER CALLBACK
# ============================================================

@dp.callback_query(F.data.startswith("answer:"))
async def callback_answer(callback: CallbackQuery):
    user = callback.from_user

    session = get_session(user.id)

    if not session:
        await callback.answer(
            "Your test session is no longer active.",
            show_alert=True,
        )
        return

    try:
        _, question_index_raw, option_index_raw = callback.data.split(":")
        question_index = int(question_index_raw)
        option_index = int(option_index_raw)
    except (ValueError, AttributeError):
        await callback.answer(
            "Invalid answer.",
            show_alert=True,
        )
        return

    if question_index != session["current"]:
        await callback.answer(
            "This question is no longer active.",
            show_alert=True,
        )
        return

    question_data = session["questions"][question_index]
    selected_option = question_data["options"][option_index]

    is_correct = selected_option["correct"]

    if is_correct:
        session["score"] += POINTS_PER_QUESTION
        session["section_scores"][question_data["section"]] += (
            POINTS_PER_QUESTION
        )

    session["answered"] += 1

    # Disable answer buttons after answering.
    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    if is_correct:
        result = "✅ <b>Correct!</b>"
    else:
        correct_option = next(
            opt
            for opt in question_data["options"]
            if opt["correct"]
        )

        result = (
            "❌ <b>Not quite.</b>\n\n"
            f"Correct answer: "
            f"<b>{correct_option['text']}</b>"
        )

    explanation = selected_option["explanation"]

    await callback.answer(
        "Correct!" if is_correct else "Incorrect!",
        show_alert=False,
    )

    await callback.message.answer(
        f"{result}\n\n"
        f"💡 <b>Explanation:</b>\n"
        f"{explanation}",
        reply_markup=after_answer_keyboard(),
    )


# ============================================================
# NEXT QUESTION
# ============================================================

@dp.callback_query(F.data == "next_question")
async def callback_next_question(callback: CallbackQuery):
    user = callback.from_user

    session = get_session(user.id)

    if not session:
        await callback.answer(
            "No active test.",
            show_alert=True,
        )
        return

    session["current"] += 1

    await callback.answer()

    if session["current"] >= len(session["questions"]):
        await finish_test(callback.message, user.id)
        return

    await send_question(callback.message, user.id)


# ============================================================
# CANCEL
# ============================================================

@dp.callback_query(F.data == "cancel_test")
async def callback_cancel_test(callback: CallbackQuery):
    user = callback.from_user

    clear_session(user.id)

    await callback.answer("Test cancelled.")

    await callback.message.edit_text(
        "❌ <b>Test cancelled.</b>\n\n"
        "You can start a new test with /start."
    )


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message):
    user = message.from_user

    if not user:
        return

    if get_session(user.id):
        clear_session(user.id)

        await message.answer(
            "❌ Your current test has been cancelled.\n\n"
            "Use /start to begin again."
        )
    else:
        await message.answer(
            "You don't have an active test."
        )


# ============================================================
# FINISH TEST
# ============================================================

async def finish_test(message: Message, user_id: int):
    session = get_session(user_id)

    if not session:
        return

    user = message.chat

    score = session["score"]
    section_scores = session["section_scores"]

    level = calculate_level(score)

    percentage = round(
        (score / MAX_SCORE) * 100
    )

    save_result(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
        score=score,
        section_scores=section_scores,
        level=level,
    )

    text = build_result_text(
        score=score,
        percentage=percentage,
        level=level,
        section_scores=section_scores,
    )

    await message.answer(text)

    # Admin notification
    if ADMIN_ID:
        username = (
            f"@{user.username}"
            if user.username
            else "no username"
        )

        admin_text = (
            "📥 <b>New English Quest result</b>\n\n"
            f"👤 {user.first_name or 'Unknown'}\n"
            f"🔹 {username}\n"
            f"🆔 <code>{user_id}</code>\n\n"
            f"🏆 Score: <b>{score}/{MAX_SCORE}</b>\n"
            f"📊 Accuracy: <b>{percentage}%</b>\n"
            f"🎯 Diagnostic: <b>{level}</b>"
        )

        try:
            await bot.send_message(
                ADMIN_ID,
                admin_text,
            )
        except Exception as e:
            logger.error(
                "Could not send admin notification: %s",
                e,
            )

    clear_session(user_id)


# ============================================================
# RESULT TEXT
# ============================================================

def build_result_text(
    score: int,
    percentage: int,
    level: str,
    section_scores: dict[str, int],
):
    section_max = {
        "grammar": 100,
        "vocabulary": 100,
        "everyday": 40,
        "reading": 80,
        "final": 80,
    }

    section_percentages = {}

    for section, value in section_scores.items():
        maximum = section_max[section]
        section_percentages[section] = round(
            (value / maximum) * 100
        )

    strong_areas = sorted(
        section_percentages.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:2]

    practice_areas = sorted(
        section_percentages.items(),
        key=lambda x: x[1],
    )[:2]

    strong_text = "\n".join(
        f"• {SECTION_NAMES[name]} — {percentage_value}%"
        for name, percentage_value in strong_areas
    )

    practice_text = "\n".join(
        f"• {SECTION_NAMES[name]} — {percentage_value}%"
        for name, percentage_value in practice_areas
    )

    return (
        "🏆 <b>ENGLISH QUEST V3 COMPLETE!</b>\n\n"
        f"Score: <b>{score}/{MAX_SCORE}</b>\n"
        f"Accuracy: <b>{percentage}%</b>\n\n"
        f"🎯 <b>Diagnostic level</b>\n"
        f"{level}\n\n"
        "📊 <b>SKILLS</b>\n"
        f"Grammar: {format_section_score(section_scores['grammar'], 10)}\n"
        f"Vocabulary: {format_section_score(section_scores['vocabulary'], 10)}\n"
        f"Everyday English: {format_section_score(section_scores['everyday'], 4)}\n"
        f"Reading: {format_section_score(section_scores['reading'], 8)}\n"
        f"Final Challenge: {format_section_score(section_scores['final'], 8)}\n\n"
        "💪 <b>Strong areas</b>\n"
        f"{strong_text}\n\n"
        "📚 <b>Practice areas</b>\n"
        f"{practice_text}\n\n"
        "ℹ️ This is a diagnostic placement result. "
        "It is not an official CEFR certification."
    )


# ============================================================
# LAST RESULT
# ============================================================

@dp.callback_query(F.data == "last_result")
async def callback_last_result(callback: CallbackQuery):
    result = get_latest_result(callback.from_user.id)

    await callback.answer()

    if not result:
        await callback.message.answer(
            "📊 You don't have a completed test yet.\n\n"
            "Press /start to begin."
        )
        return

    text = (
        "📊 <b>Your latest English Quest result</b>\n\n"
        f"🏆 Score: <b>{result['score']}/{result['total']}</b>\n"
        f"Accuracy: <b>{result['percentage']}%</b>\n"
        f"🎯 Diagnostic: <b>{result['level']}</b>\n\n"
        "📚 <b>Skills</b>\n"
        f"Grammar: {result['grammar_score']}/100\n"
        f"Vocabulary: {result['vocabulary_score']}/100\n"
        f"Everyday English: {result['everyday_score']}/40\n"
        f"Reading: {result['reading_score']}/80\n"
        f"Final Challenge: {result['final_score']}/80\n\n"
        f"🕐 Completed: {result['completed_at']}"
    )

    await callback.message.answer(text)


# ============================================================
# /RESULTS
# ============================================================

@dp.message(Command("results"))
async def cmd_results(message: Message):
    result = get_latest_result(message.from_user.id)

    if not result:
        await message.answer(
            "📊 You don't have any completed tests yet.\n\n"
            "Use /start to begin."
        )
        return

    await message.answer(
        "📊 <b>Your latest result</b>\n\n"
        f"🏆 <b>{result['score']}/{result['total']}</b>\n"
        f"Accuracy: {result['percentage']}%\n"
        f"Diagnostic: <b>{result['level']}</b>\n\n"
        f"Grammar: {result['grammar_score']}/100\n"
        f"Vocabulary: {result['vocabulary_score']}/100\n"
        f"Everyday: {result['everyday_score']}/40\n"
        f"Reading: {result['reading_score']}/80\n"
        f"Final: {result['final_score']}/80"
    )


# ============================================================
# UNKNOWN TEXT
# ============================================================

@dp.message()
async def unknown_message(message: Message):
    await message.answer(
        "👋 Use /start to begin English Quest V3."
    )


# ============================================================
# MAIN
# ============================================================

async def main():
    validate_questions()
    init_db()

    logger.info(
        "English Quest V3 starting with %s questions",
        len(TEST_DATA),
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped.")