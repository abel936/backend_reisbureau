from openai import OpenAI
from dotenv import load_dotenv
import os 
from connect_with_db import get_connection
load_dotenv() 

apikey = os.getenv("OPENAI_API_KEY")

def start():
    client = OpenAI(api_key=apikey)

    #connectie database
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT Countries.name AS CountryName, Cities.name AS CityName
                FROM Cities
                LEFT JOIN Countries ON Countries.country_id = Cities.country_id;
                """)
            rows = cur.fetchall()


    # lijst beschikbare bestemmingen
    beschikbare_bestemmingen = [f"{row.CityName}, {row.CountryName}" for row in rows]

    #vragen voor chatbot
    vragen = [
        "Wat voor soort reis? (zonvakantie, citytrip, rondreis)",
        "Wanneer?",
        "Met hoeveel personen?",
        "Hoe wil je reizen? (vliegtuig of auto)",
        "Binnen of buiten Europa?",
        "Welke landen niet?",
        "Budget (per persoon in euro's)?",
        "Hoeveel dagen wil je weg?",
        "Specifieke voorkeuren? (strand, cultuur, natuur, avontuur)",
        "Vrije opmerkingen?"
    ]

    antwoorden = {}
    print("Mysterytrip vragenlijst:\n")
    for vraag in vragen:
        antwoord = input(f"{vraag}\n> ")
        antwoorden[vraag] = antwoord

    prompt = (
        "Je bent een reisconsulent voor een mysterytrip. "
        "Analyseer alle antwoorden en kies een bestemming die perfect past bij de wensen. "
        "Je mag ALLEEN kiezen uit deze lijst:\n"
        f"{beschikbare_bestemmingen}\n\n"
        "Houd rekening met: type reis, periode, aantal personen, vervoer, regio, uitgesloten landen, budget, duur, voorkeuren. "
        "Geef als output:\n"
        "- Bestemming (stad/land)\n"
        "- Type reis (citytrip, zonvakantie, rondreis)\n"
        "- Korte motivatie waarom deze bestemming past.\n\n"
        f"Antwoorden van klant:\n{antwoorden}"
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=300,
        messages=[
            {"role": "system", "content": "Je bent een reisexpert en geeft een concreet advies."},
            {"role": "user", "content": prompt}
        ]
    )

    #antwoord splitten
    advies =completion.choices[0].message.content.strip()

    regels = advies.split("\n")
    bestemming = regels[0].replace("Bestemming:", "").strip()
    reistype = regels[1].replace("Type reis:", "").strip()
    motivatie = regels[2].replace("Motivatie:", "").strip()

    #interne info
    print("INTERNE INFO:")
    print(f"Bestemming: {bestemming}")
    print(f"Type reis: {reistype}")
    print(f"Motivatie: {motivatie}")

    #teaser voor klant
    print(f"TEASER VOOR DE KLANT:")
    print(f"De reis is bepaald! Binnekort kun jij genieten van je ideale {reistype}")


    #database 




    #print("\nAI-advies:")
    #print(completion.choices[0].message.content.strip())
# start()



