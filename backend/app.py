# =========================
# BACKEND: app.py (FULL)
# Option: End session button + decline confirm step
# + Intro is Yes/No only
# + Extra blank line before "another word?" for a longer post-fortune beat
#
# FIXES (for bigger cluster sets):
# 1) NO repeats until ALL unseen clusters have been offered.
#    - Uses "remaining" = never-offered indices only
#    - "rejected" = previously offered & declined indices
# 2) Re-offer rejected words ONLY after remaining is empty.
# 3) Summary/closing ALWAYS appears when ending (No/Stop/Quit), if any words were accepted.
# 4) If the session ends because the re-offer limit (2) is reached,
#    and any words were accepted, we STILL return the closing summary.
#
# NEW NATURAL-LANGUAGE POLISH:
# - DECLINE_CONFIRM_PROMPTS: varied “offer another word?” lines
# - INVALID_YN_PROMPTS: varied “please choose Yes/No” lines
# - INVALID_YNE_PROMPTS: varied “please choose Yes/No/End session” lines
# - CONTINUE_Q_VARIANTS: varied “journey further?” question
# - REOFFER_PROMPTS: varied “offer declined words again?” lines
# =========================

from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Tuple
from uuid import uuid4
import random

app = FastAPI(title="Word Psychic API (Yes/No/End + Confirm)")

# Allow frontend on 127.0.0.1:5500 to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Canonical strings ----------
ANOTHER_WORD_PROMPTS = [
    "Would you like another word?",
    "Shall we draw another word?",
    "Do you want to receive another word?",
]
GOODBYES = [
    "Maybe another time.",
    "Very well — until we meet again.",
    "The veil closes. Come back when you’re ready.",
]
COURTEOUS_EXIT = [
    "Travel well — and keep your words sharp and kind.",
    "I wish you a fond goodbye. And may the words be with you.",
    "Farewell. May your vocabulary grow brighter every day.",
]

# Startup is Yes/No only
SHORT_HINT_OPENING = "Choose Yes or No."
# Later prompts can mention End session
SHORT_HINT = "Choose Yes, No, or End session."

# ---------- NEW: Natural-language variation pools ----------
DECLINE_CONFIRM_PROMPTS = [
    "Very well. Shall I offer another word?",
    "As you wish. Would you like another word?",
    "Understood. Shall I reveal another word?",
    "The word retreates into silence.  Shall I call forth another?",
    "So be it.  Shall we draw again from the beyond?",
    "Fair enough. Shall I offer you a new word?",
]

INVALID_YN_PROMPTS = [
    "Please choose Yes or No.",
    "A simple Yes or No will do.",
    "Click Yes or No to proceed.",
    "Yes opens the door, no keeps it shut.",
    "A single Yes or No will guide us forward.",
]

INVALID_YNE_PROMPTS = [
    "Please choose Yes, No, or End session.",
    "Click Yes, No, or End session.",
    "Choose Yes, No, or End session to continue.",
    "Yes, No, or End session — your call.",
    "The veil awaits: Yes, No, or End Session.",
]

CONTINUE_Q_VARIANTS = [
    "Shall we journey further with this word?",
    "Do you want to go deeper with this word?",
    "Would you like to explore this word a little further?",
    "Shall we go further with this word?",
    "Do you wish to continue the journey with this word?",
]

REOFFER_PROMPTS = [
    "You declined some words earlier. Shall I offer them again?",
    "Some words were set aside. Would you like me to bring them back?",
    "A few words still linger in the shadows. Shall I offer them again?",
    "You passed on some words before. Shall we revisit them?",
    "There are words you turned away. Would you like another chance at them?",
]

def choose_decline_confirm() -> str:
    return random.choice(DECLINE_CONFIRM_PROMPTS)

def choose_invalid_yn() -> str:
    return random.choice(INVALID_YN_PROMPTS)

def choose_invalid_yne() -> str:
    return random.choice(INVALID_YNE_PROMPTS)

def choose_continue_q() -> str:
    return random.choice(CONTINUE_Q_VARIANTS)

def choose_reoffer_prompt() -> str:
    return random.choice(REOFFER_PROMPTS)

# ---------- WORD CLUSTERS (unchanged; as provided) ----------
CLUSTERS = [
    {
        "title": "Antipathy → Vilify → Annihilate",
        "intro_line": "Your word is “antipathy.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Antipathy means a strong dislike.\n"
            "The rooster showed antipathy toward his alarm clock.\n\n"
            "I see another word. Vilify -- To attack someone’s reputation.\n"
            "Busted with a stolen ten percent off coupon for a nuclear reactor, the thief vilified the detective online.\n\n"
            "A final word. Annihilate -- To utterly destroy.\n"
            "After annihilating the town, the hurricane wondered if it should cut back on the caffeine.\n\n"
            "Antipathy. Vilify. Annihilate.\n"
            "Your fortune: Ill will destroys quietly, guarding against it leaves room for peace."
        ),
    },
    {
        "title": "Prudent → Revere → Venerate",
        "intro_line": "Your word is “prudent.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Prudent means being careful and wise.\n"
            "The demanding CEO wants a prudent business plan -- now!\n\n"
            "I see a second word. Revere -- To respect and honor deeply.\n"
            "Pizza was revered among the dogs for calming their hysterical disagreements.\n\n"
            "A final word. Venerate -- To hold as sacred.\n"
            "Because it thought its whistle sang wisdom, the frying pan venerated the old tea kettle.\n\n"
            "Prudent. Revere. Venerate.\n"
            "Your fortune: Choose carefully, cherish quality, and your name will inspire."
        ),
    },
    {
        "title": "Dearth → Paucity → Penury",
        "intro_line": "Your word is “dearth.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Dearth means a lack. A scarcity.\n"
            "A dearth of thrown darts made the target feel neglected.\n\n"
            "I see another word. Paucity -- A small amount.\n"
            "Not surprisingly, a paucity of snacks irritated the couch potatoes.\n\n"
            "A final word. Penury -- Extreme poverty.\n"
            "The novel's hero escaped penury through grit and kindness.\n\n"
            "Dearth. Paucity. Penury.\n"
            "Your fortune: Be mindful of waste, and you will prosper."
        ),
    },
    {
        "title": "Minuscule → Nominal → Insignificant",
        "intro_line": "Your word is “minuscule.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Minuscule means extremely small.\n"
            "Victory seemed minuscule thought the grass as it battled the weeds.\n\n"
            "I see another word. Nominal -- Small in name or importance.\n"
            "A nominal error unbeleivably ruined the mosquitos' family chicken dinner.\n\n"
            "A final word. Insignificant -- Too small or unimportant to matter.\n"
            "Looking up at the towering skyscrapers, even Godzilla felt insignificant.\n\n"
            "Minuscule. Nominal. Insignificant.\n"
            "Your fortune: Make your voice be heard. And the world leans in."
        ),
    },
    {
        "title": "Aggregate → Plethora → Prodigious",
        "intro_line": "Your word is “aggregate.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Aggregate means a collection, a sum, a total.\n"
            "The aggregate of the day’s sales had the calculator singing ka-ching, ka-ching.\n\n"
            "I see another word.  Plethora -- An excess. More than enough.\n"
            "A plethora of lettuce-eating rabbits made the hungry groundhog hopping mad.\n\n"
            "A final word. Prodigious -- Extraordinary large.\n"
            "Having drunk a prodigious amount of water, the athlete thirsted for a rest room.\n\n"
            "Aggregate. Plethora. Prodigious.\n"
            "Your fortune: Excess always makes itself known. Sometimes at inconvenient moments."
        ),
    },
    {
        "title": "Benevolence → Philanthropy → Largess",
        "intro_line": "Your word is “benevolence.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Benevolence means kindness. Inclination to do good.\n"
            "My dog showed great benevolence -- he only ate half of my sandwich lying on the counter.\n\n"
            "I see another word.  Philanthropy. Love of humankind as expressed by doing good deeds.\n"
            "The particpant at The Three Stooges Festical performed his own unique philanthropy -- on stage burping to the song, 'Pop Goes The Weasel.'\n\n"
            "A final word. Largess -- Generosity on a big scale. The gift itself.\n"
            "Giving the Earth a second moon was surprising largess, especially coming from the Plutonians.\n\n"
            "Benevolence. Philanthropy. Largess.\n"
            "Your fortune: Generosity may cost time and money, but its return can’t be bought."
        ),
    },
    {
        "title": "Insidious → Belligerent → Vitriolic",
        "intro_line": "Your word is “insidious.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Insidious means sneaky. Causing harm in a gradual way.\n"
            "The stomach’s insidious plan to grow larger was to ensure donuts were always next to the TV remote.\n\n"
            "I see another word.  Belligerent -- Combative; Quarrelsome; Warlike.\n"
            "Driving a tank across a neighbor’s lawn is certainly belligerent, especially when there’s a posted sign that says “Keep Off The Grass.”\n\n"
            "A final word. Vitriolic -- Nasty; Venomous. Burning like acid.\n"
            "Big Foot found the campers calling him Big Foot vitriolic –- his name is “George” –- they only had to ask.\n\n"
            "Insidious. Belligerent. Vitriolic.\n"
            "Your fortune: Attacks can feel good momentarily. But the damage they cause is not easily mended."
        ),
    },
    {
        "title": "Laconic → Perfunctory → Concise",
        "intro_line": "Your word is “laconic.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Laconic means using few words to the point of rudeness.\n"
            "The teenager suddenly wasn’t laconic when explaining why he needed twenty dollars.\n\n"
            "I see another word.  Perfunctory --  Lacking interest or enthusiasm.\n"
            "In 100-degree heat, the sled dogs grew perfunctory pulling the obese man up the hill.\n\n"
            "A final word. Concise -- Brief and to the point.\n"
            "Instead of going on about moisturizer benefits, the pinky was concise and told the thumb “it’s just good for you.”\n\n"
            "Laconic. Perfunctory. Concise.\n"
            "Your fortune: Interest and directness are often welcomed."
        ),
    },
    {
        "title": "Copious → Protract → Ponderous",
        "intro_line": "Your word is “copious.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Copious means abundant. Plentiful.\n"
            "The selfish violinist took copious notes, leaving the rest of the orchestra with hardly any music to play.\n\n"
            "I see another word. Protract -- To prolong. To lengthen.\n"
            "Hoping to increase popcorn sales, the theatre protracted the movie’s third act by playing it in slow motion.\n\n"
            "A final word. Ponderous -- Slow, heavy, or dull, especially in speech or thought.\n"
            "His ponderous speech on why he should be president of the Pie Eaters Club killed everyone’s appetite for electing him.\n\n"
            "Copious. Protract. Ponderous.\n"
            "Your fortune: Going one step too far can be fatal when you’re already at the edge."
        ),
    },
    {
        "title": "Apprehensive → Diffident → Capitulate",
        "intro_line": "Your word is “apprehensive.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Apprehensive means uneasy or anxious about what may happen.\n"
            "The worm felt apprehensive about crawling around at dawn –- the early bird might be out there.\n\n"
            "I see another word. Diffident -- Timid or lacking self-confidence. Shy.\n"
            "He stepped forward, ready to answer, but then the diffident boy quickly stepped back.\n\n"
            "A final word. Capitulate -- To give up or surrender.\n"
            "Faced with a hungry mouth, the piece of cake capitulated and said, “Farewell.”\n\n"
            "Apprehensive. Diffident. Capitulate.\n"
            "Your fortune: Fear itself isn’t dangerous, what you do because of it is."
        ),
    },
    {
        "title": "Dauntless → Imperious → Demagogue",
        "intro_line": "Your word is “dauntless.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Dauntless means fearless and confident.\n"
            "Texting his boss that he quit, the dauntless worker ended the message with a smiling emoji.\n\n"
            "I see another word. Imperious -- Bossy and arrogantly commanding.\n"
            "The imperious mustard told the relish and mayonnaise -- 'the coldest spot in the refrigerator is mine!'\n\n"
            "A final word. Demagogue -- A leader who gains support by manipulating emotions or fears.\n"
            "Vote for the devil, the demagogue said, or every angel loses its wings.\n\n"
            "Dauntless. Imperious. Demagogue.\n"
            "Your fortune: Self-confidence can be admired, but bullying, not so much."
        ),
    },
    {
        "title": "Reparation → Respite → Salutary",
        "intro_line": "Your word is “reparation.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Reparation means compensation for a wrong.\n"
            "For stealing the twinkie, the Court of Sweets ruled that the reparation would be a pint of fudge.\n\n"
            "I see another word. Respite -- A short period of rest or relief.\n"
            "The veterinarian ordered the tense turtle to take a month-long respite so he could slow down.\n\n"
            "A final word. Salutary -- Producing a beneficial or healing effect.\n"
            "Just hiding up in the attic for half-an-hour was salutary for the wife when the mother-in-law visited.\n\n"
            "Reparation. Respite. Salutary.\n"
            "Your fortune: Rest and relaxation calms the mind and soothes the body."
        ),
    },
    {
        "title": "Debilitate → Subjugate → Anguish",
        "intro_line": "Your word is “debilitate.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Debilitate means to weaken or cripple.\n"
            "The vampire was debilitated when the garlic-eating man said “hello.”\n\n"
            "I see another word. Subjugate -- To bring under control. To dominate.\n"
            "Boss Johnson subjugated his workers when he converted their breakroom into his own personal office man cave.\n\n"
            "A final word. Anguish -- Severe mental or emotional pain.\n"
            "Hearing “maybe” caused the amoeba some anguish when it was the paramecium's reply to a date.\n\n"
            "Debilitate. Subjugate. Anguish.\n"
            "Your fortune: It’s wise to save your strength for truly oppressive days."
        ),
    },
    {
        "title": "Verisimilitude → Apocryphal → Spurious",
        "intro_line": "Your word is “verisimilitude.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Verisimilitude means the appearance of being true or real.\n"
            "The anteater thought his painting of the cowhad verisimilitude –- except for the long tubular snout.\n\n"
            "I see another word. Apocryphal -- Of doubtful authenticity.\n"
            'Pointing to the Mona Lisa with a goatee and horns, "It is definitely apocryphal," uttered the counterfeiter.\n\n'
            "A final word. Spurious -- False or fake.\n"
            "“Totally spurious,” replied the ice box to the toaster’s claim that it could keep pickles cold.\n\n"
            "Verisimilitude. Apocryphal. Spurious.\n"
            "Your fortune: Examine carefully. There are tricks up some sleeves."
        ),
    },
    {
        "title": "Postulate → Veracity → Precept",
        "intro_line": "Your word is “postulate.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Postulate means to consider to be true without evidence. Assume.\n"
            "Despite the rat’s loud snoring, the scientist postulated that he was awake.\n\n"
            "I see another word. Veracity -- Truthfulness or accuracy.\n"
            "George Washington’s veracity about chopping down the cherry tree is admirable, but what about that peach tree?\n\n"
            "A final word. Precept -- A rule or principle guiding behavior.\n"
            "The aardvark lived by a twisted precept – do unto him before he does unto you.\n\n"
            "Postulate. Veracity. Precept.\n"
            "Your fortune: Finding truth is like striking gold."
        ),
    },
    {
        "title": "Inane → Awry → Quixotic",
        "intro_line": "Your word is “inane.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Inane means silly. Lacking sense.\n"
            "The peanut butter was inane, thinking it could go it alone as a sandwich without the jelly.\n\n"
            "I see another word. Awry -- Off course. Twisted to one side.\n"
            "It went awry, and the golf ball landed in the sock factory -- putting a hole in one.\n\n"
            "A final word. Quixotic -- Romantic or idealistic to a foolish degree.\n"
            "Frankenstein’s quixotic notion to become a hair stylist was pure fantasy -- he had no training in cosmetology.\n\n"
            "Inane. Awry. Quixotic.\n"
            "Your fortune: Turning onto a dirt road can pave the way for an imaginative adventure."
        ),
    },
    {
        "title": "Singular → Sublime → Apotheosis",
        "intro_line": "Your word is “singular.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Singular means unique. Extraordinary. Exceptional.\n"
            "His singular talent walking barefoot on Legos with a smile -- amazed the parents.\n\n"
            "I see another word. Sublime -- Awe-inspiring. Extremely high, lofty, and majestic.\n"
            "The sublime beaver not only built the dam, but had it produce enough hydroelectricity to power the nearby city.\n\n"
            "A final word. Apotheosis -- Ideal. The perfect or divine version.\n"
            "All the appliances agreed the vintage blender on the counter was the apotheosis, since the mob once used it to dispose of a body.\n\n"
            "Singular. Sublime. Apotheosis.\n"
            "Your fortune: Individual talents are what make you unique and special."
        ),
    },
    {
        "title": "Conventional → Adage → Renaissance",
        "intro_line": "Your word is “conventional.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Conventional means common. Customary. Unexceptional.\n"
            "A conventional hen, Betty turned down the offer for the free tattoo, “Born to Cluck.”\n\n"
            "I see another word. Adage -- An old saying. A familiar bit of wisdom.\n"
            "The organic medicine man’s updated adage: to keep the doctor away, drink an apple smoothie a day.\n\n"
            "A final word. Renaissance -- A rebirth. Revitalization.\n"
            "When the old turntable saw there was a renaissance in vinyl records, he reminisced about the good old days when songs skipped.\n\n"
            "Conventional. Adage. Renaissance.\n"
            "Your fortune: The tried-and-true way of doing things can be boring -- but dependable."
        ),
    },
    {
        "title": "Novel → Unprecedented → Visionary",
        "intro_line": "Your word is “novel.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Novel means new and original.\n"
            "The banana’s novel idea was a genetically modified banana peel with a non-slip coating.\n\n"
            "I see another word. Unprecedented -- Not done before, entirely new.\n"
            "In an unprecedented ruling, the judge ordered the litterbug to pick up after all the teenagers in Oh No County.\n\n"
            "A final word. Visionary -- A dreamer. Idealistic and usually impractical.\n"
            "Sam the Seagul fancied himself a visionary, constructing all ocean jetties out of spicy chili fries.\n\n"
            "Novel. Unprecedented. Visionary.\n"
            "Your fortune: For those who benefit from it, the new is exciting. For others, not really."
        ),
    },
    {
        "title": "Charisma → Complicity → Collusion",
        "intro_line": "Your word is “charisma.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Charisma means personal magnetism.\n"
            "At first, the new fire hydrant thought its charisma was why the dogs were attracted to him.\n\n"
            "I see another word. Complicity -- Participation in wrong doing.\n"
            "The raccoon denied complicity, but he did allow the cheese store robbers to lay low in his den for some cheddar.\n\n"
            "A final word. Collusion -- Secret cooperation.\n"
            "In collusion, the basketball cheerleaders cheered “offense,” instead of “defense,” to throw off the home team.\n\n"
            "Charisma. Complicity. Collusion.\n"
            "Your fortune: Manipulation thrives in secrecy – exposure changes everything."
        ),
    },
    {
        "title": "Autonomous → Reclusive → Sequester",
        "intro_line": "Your word is “autonomous.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Autonomous means independent. Self-governing.\n"
            "Eager to be autonomous, the toddler walked off –- then fell and cried “mommy.”\n\n"
            "I see another word. Reclusive -- Withdrawn from society. Avoiding contact.\n"
            "Peace and quiet were what the reclusive snake valued –- until a wandering foot came by.\n\n"
            "A final word. Sequester -- To set or keep apart.\n"
            "Tormented by drip, drip, drip, the sink longed to sequester the leaky faucet.\n\n"
            "Autonomous . Reclusive. Sequester.\n"
            "Your fortune: A life alone has its advantages –- until help is needed."
        ),
    },
    {
        "title": "Abstruse → Bemused → Cryptic",
        "intro_line": "Your word is “abstruse.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Abstruse means difficult to understand.\n"
            "The duck’s quacking was so abstruse that the pig asked him to repeat it in English.\n\n"
            "I see another word. Bemused -- To be confused. Bewildered.\n"
            "Bemused, the workers had to think about the foreman’s order to work faster, not smarter.\n\n"
            "A final word. Cryptic -- To be mystifying. Mysterious. Puzzling.\n"
            "Decoding the message of the cryptic creaking door, the ghost hunter said, “It wants oil.”\n\n"
            "Abstruse. Bemused. Cryptic.\n"
            "Your fortune: When life is puzzling, look for the  missing piece – it’s  out there."
        ),
    },
    {
        "title": "Blatant → Salient → Ostentatious",
        "intro_line": "Your word is “blatant.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Blatant means unpleasantly loud or obvious.\n"
            "At the town hall meeting discussing the school’s curriculum, the blatant man shouted, “When do we eat?”\n\n"
            "I see another word. Salient -- Jutting out. Conspicuous.\n"
            "When it heard the vacuum cleaner in the other room, the salient hair ball hid under the bed.\n\n"
            "A final word. Ostentatious -- Excessively conspicuous. Showy.\n"
            "“It’s not ostentatious,” said the buck to the bullfrog, wearing his new bull's eye sweater during hunting season.”\n\n"
            "Blatant. Salient. Ostentatious.\n"
            "Your fortune: Drawing attention to yourself isn’t always the advantage you think it is."
        ),
    },
    {
        "title": "Steadfast → Tenacious  → Dogmatic",
        "intro_line": "Your word is “steadfast.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Steadfast means unwaveringly loyal and faithful.\n"
            "Jimmy stayed steadfast, refusing to rat out his friend even when bribed with a Snickers bar.\n\n"
            "I see another word. Tenacious -- To be persistent. Stubborn.\n"
            "The tenacious cat kept trying to convince the dog the floor was more comfortable than the couch.\n\n"
            "A final word. Dogmatic -- Stubbornly assertive of unproven ideas.\n"
            "The bag of sugar was dogmatic, exclaiming that cavities make life better.\n\n"
            "Steadfast. Tenacious. Dogmatic.\n"
            "Your fortune: Determination can be a strong ally –- if it listens as well as it pushes."
        ),
    },
    {
        "title": "Capricious → Metamorphous  → Mercurial",
        "intro_line": "Your word is “capricious.”\n\n",
        "continue_q": "Shall we journey further with this word?",
        "script": (
            "Capricious means to be whimsical. Unpredictable.\n"
            "The capricious sink drain tormented the homeowner –- some days the water flowed freely, other days, a clog.\n\n"
            "I see another word. Metamorphous -- A magical change in appearance.\n"
            "Hoping the witch’s spell would transform him into a prince, the metamorphous backfired –- and the inchworm became a foot worm.\n\n"
            "A final word. Mercurial -- Emotionally unpredictable.\n"
            "Being mercurial, the gambler's mood swung rapidly from intense high-stakes Vegas poker to the sedate calm of local church bingo.\n\n"
            "Capricious. Metamorphous. Mercurial.\n"
            "Your fortune: Change is intoxicating, but surrendering to it can leave you spent."
        ),
    },
]

# ---------- Request model ----------
class YesNoRequest(BaseModel):
    answer: str
    context: Dict[str, Any] = {}

Session = Dict[str, Any]
SESSIONS: Dict[str, Session] = {}

# ---------- Session helpers ----------
def new_session() -> Session:
    idxs = list(range(len(CLUSTERS)))
    random.shuffle(idxs)
    return {
        "sid": None,  # set in /start

        "INSTRUCTION_SHOWN": False,
        "SHORT_HINT_SHOWN": False,

        # NEVER-OFFERED indices only (the core fix):
        "remaining": idxs,

        # Offered-and-declined indices only:
        "rejected": [],

        # Titles of accepted clusters:
        "words_revealed": [],

        "first_offer_done": False,
        "reoffer_attempts": 0,

        # Phases: intro → await_continue → decline_confirm → post_reveal → reoffer_prompt → done
        "phase": "intro",
        "current_idx": None,
    }

def normalize(a: str) -> str:
    a = a.strip().lower()
    if a in {"y", "yes"}: return "yes"
    if a in {"n", "no"}:  return "no"
    if a in {"q", "quit"}: return "quit"
    if a in {"s", "stop", "enough", "end"}: return "stop"
    return a

def reply(st: Session, text: str, *, done: bool = False) -> Dict[str, Any]:
    return {"text": text, "done": done, "context": {"session_id": st.get("sid")}}

def choose_another_word() -> str:
    return random.choice(ANOTHER_WORD_PROMPTS)

def choose_goodbye() -> str:
    return random.choice(GOODBYES)

def choose_exit_blessing() -> str:
    return random.choice(COURTEOUS_EXIT)

def guidance_flow(st: Session, *, opening: bool) -> Optional[str]:
    # Opening line is Yes/No only
    if opening and not st["INSTRUCTION_SHOWN"]:
        st["INSTRUCTION_SHOWN"] = True
        st["SHORT_HINT_SHOWN"] = False
        return "Yes opens the door, no keeps it shut."
    # After that, we can mention End session
    if st["INSTRUCTION_SHOWN"] and not st["SHORT_HINT_SHOWN"]:
        st["SHORT_HINT_SHOWN"] = True
        return SHORT_HINT
    return None

def summary_text(words: List[str]) -> str:
    if not words:
        return "No words were revealed this time. The veil remains for another day."
    lines = "\n\n".join(title for title in words)
    return "Here are the words that visited you from the beyond:\n\n" + lines

def closing_block(st: Session) -> str:
    closing = summary_text(st["words_revealed"])
    if st["words_revealed"]:
        closing += "\n\nCarry these words carefully; they will open doors when you need them."
    blessing = choose_exit_blessing().rstrip()
    closing += "\n" + (blessing if blessing[-1] in ".!?" else blessing + ".")
    return closing

def pick_continue_question(cluster: Dict[str, Any]) -> str:
    """
    Use the cluster's continue_q sometimes (keeps your authored phrasing in the mix),
    otherwise rotate in variants so the psychic doesn't sound robotic.
    """
    base = (cluster.get("continue_q") or "").strip()
    if base and random.random() < 0.35:
        return base
    return choose_continue_q()

def offer_next_word(st: Session) -> Dict[str, Any]:
    # Prefer NEVER-OFFERED clusters
    if st["remaining"]:
        idx = st["remaining"].pop()
        st["current_idx"] = idx
        st["phase"] = "await_continue"
        cluster = CLUSTERS[idx]

        if st["first_offer_done"]:
            head = cluster["title"].split(" → ")[0]
            intro = f"Your new word is “{head}.”\n\n"
        else:
            intro = cluster["intro_line"]

        # ✅ NEW: varied “journey further?” question
        continue_q = pick_continue_question(cluster)

        g = guidance_flow(st, opening=(not st["first_offer_done"]))
        text = f"{intro}{continue_q}" + (f"\n{g}" if g else "")
        return reply(st, text)

    # No unseen clusters left → handle rejected
    if st["rejected"]:
        # ✅ FIX: if we hit the re-offer limit, still return closing summary
        # whenever any words were revealed.
        if st["reoffer_attempts"] >= 2:
            st["phase"] = "done"
            if st["words_revealed"]:
                return reply(st, closing_block(st), done=True)
            return reply(
                st,
                "I have asked you twice about the words you set aside. The veil closes for today.",
                done=True,
            )

        st["phase"] = "reoffer_prompt"
        st["reoffer_attempts"] += 1
        st["SHORT_HINT_SHOWN"] = False
        # ✅ NEW: varied re-offer prompt
        return reply(st, choose_reoffer_prompt())

    # Truly nothing left
    st["phase"] = "done"
    closing = "You have received all available words for this session.\n" + closing_block(st)
    return reply(st, closing, done=True)

def get_session(request: Request, ctx: Dict[str, Any]) -> Tuple[str, Session]:
    sid = ctx.get("session_id") or request.cookies.get("wp_sid")
    if not sid or sid not in SESSIONS:
        sid = str(uuid4())
        st = new_session()
        st["sid"] = sid
        SESSIONS[sid] = st
        return sid, st
    return sid, SESSIONS[sid]

# ---------- Endpoints ----------
@app.get("/start")
def start(response: Response):
    sid = str(uuid4())
    st = new_session()
    st["sid"] = sid
    SESSIONS[sid] = st
    response.set_cookie("wp_sid", sid, httponly=False, samesite="Lax")

    guidance = (
        "Do you wish to summon the Word Psychic, who through the meanings of words deciphers your fortune?\n"
        + SHORT_HINT_OPENING
    )
    st["phase"] = "intro"
    return {"session_id": sid, "prompt": "", "guidance": guidance}

@app.post("/choose")
def choose(req: YesNoRequest, request: Request):
    sid, st = get_session(request, req.context)
    a = normalize(req.answer)

    # Always-available end: ALWAYS return closing (with summary if any)
    if a in {"quit", "stop"}:
        st["phase"] = "done"
        return reply(st, closing_block(st), done=True)

    # Phase: intro (summon?)
    if st["phase"] == "intro":
        if a == "yes":
            st["first_offer_done"] = False
            return offer_next_word(st)
        if a == "no":
            st["phase"] = "done"
            return reply(st, choose_goodbye(), done=True)
        # ✅ NEW: varied invalid input prompt (Yes/No)
        return reply(st, choose_invalid_yn())

    # Phase: await_continue
    if st["phase"] == "await_continue":
        idx = st.get("current_idx")
        cluster = CLUSTERS[idx] if idx is not None else None

        if a == "yes":
            if cluster is None:
                st["phase"] = "done"
                return reply(st, "The spirits are quiet. Please refresh to begin anew.", done=True)

            st["words_revealed"].append(cluster["title"])
            st["first_offer_done"] = True
            st["SHORT_HINT_SHOWN"] = False

            st["phase"] = "post_reveal"
            another = choose_another_word()
            g = guidance_flow(st, opening=False)

            # Extra blank line before the "another word?" prompt
            tail = f"\n\n{another}" + (f"\n{g}" if g else "")
            return reply(st, cluster["script"] + "\n\n" + tail)

        if a == "no":
            if idx is not None and idx not in st["rejected"]:
                st["rejected"].append(idx)

            st["first_offer_done"] = True
            st["phase"] = "decline_confirm"
            st["SHORT_HINT_SHOWN"] = False
            # ✅ NEW: varied decline-confirm prompt
            return reply(st, choose_decline_confirm())

        # ✅ NEW: varied invalid input prompt (Yes/No/End session)
        return reply(st, choose_invalid_yne())

    # Phase: decline_confirm
    if st["phase"] == "decline_confirm":
        if a == "yes":
            return offer_next_word(st)
        if a == "no":
            st["phase"] = "done"
            return reply(st, closing_block(st), done=True)
        # ✅ NEW: varied invalid input prompt (Yes/No/End session)
        return reply(st, choose_invalid_yne())

    # Phase: post_reveal
    if st["phase"] == "post_reveal":
        if a == "yes":
            return offer_next_word(st)
        if a == "no":
            st["phase"] = "done"
            return reply(st, closing_block(st), done=True)
        # ✅ NEW: varied invalid input prompt (Yes/No/End session)
        return reply(st, choose_invalid_yne())

    # Phase: reoffer_prompt
    if st["phase"] == "reoffer_prompt":
        if a == "yes":
            # Move rejected into remaining as a new (secondary) pool
            st["remaining"] = st["rejected"][:]
            random.shuffle(st["remaining"])
            st["rejected"] = []
            st["first_offer_done"] = True
            return offer_next_word(st)

        st["phase"] = "done"
        text = (
            "I have asked you twice about the words you set aside. The veil closes for today."
            if st["reoffer_attempts"] >= 2
            else "Very well. The session is complete. May the meanings serve you."
        )
        # And still provide closing summary if any accepted words exist
        if st["words_revealed"]:
            text = closing_block(st)
        return reply(st, text, done=True)

    st["phase"] = "done"
    return reply(st, "The spirits are quiet. Please refresh to begin anew.", done=True)

@app.get("/summary")
def summary(request: Request, session_id: Optional[str] = None):
    sid = session_id or request.cookies.get("wp_sid")
    if not sid or sid not in SESSIONS:
        return {"text": "Session expired.", "words": []}
    st = SESSIONS[sid]
    return {"text": summary_text(st["words_revealed"]), "words": st["words_revealed"]}