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
    print(beschikbare_bestemmingen)

    #vragen voor chatbot
    vragen = [
        "Wat is je naam?",
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
        "Klantnaam\n"
        "Bestemming (1 stad/land)\n"
        "Type reis (citytrip, zonvakantie, rondreis)\n"
        "Korte motivatie waarom deze bestemming past.\n\n"
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
    clientname_mt = regels[0].replace("Klantnaam:", "").strip()
    destination_mt = regels[1].replace("Bestemming:", "").strip()
    traveltype_mt = regels[2].replace("Type reis:", "").strip()
    motivation_mt = regels[3].replace("Motivatie:", "").strip()

    #interne info
    print("INTERNE INFO:")
    print(f"Klantnaam: {clientname_mt}")
    print(f"Bestemming: {destination_mt}")
    print(f"Type reis: {traveltype_mt}")
    print(f"Motivatie: {motivation_mt}")

    #interne info naar database
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO InternalInfo (clientname_mt, destination_mt, traveltype_mt, motivation_mt)
                VALUES (?, ?, ?, ?)
            """, (clientname_mt, destination_mt, traveltype_mt, motivation_mt))
            conn.commit()

  

    
    def genereer_paklijst_tekst(clientname_mt, antwoorden, destination_mt, traveltype_mt):
        prompt2 = (
            f"Maak een duidelijke paklijst voor een {traveltype_mt} naar {destination_mt}. "
            f"Houd rekening met: periode ({antwoorden.get('Wanneer?')}), "
            f"aantal dagen ({antwoorden.get('Hoeveel dagen wil je weg?')}), "
            f"vervoer ({antwoorden.get('Hoe wil je reizen? (vliegtuig of auto)')}), "
            f"voorkeuren ({antwoorden.get('Specifieke voorkeuren? (strand, cultuur, natuur, avontuur)')}). "
            "Geef de lijst netjes in categorieën (Kleding, Documenten, Gadgets, Extra)."
            "Je mag NOOIT de daadwerkelijke bestemming verraden."
        )

        completion2 = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=400,
            messages=[
                {"role": "system", "content": "Je bent een reisexpert en maakt een praktische paklijst."},
                {"role": "user", "content": prompt2}
            ]
        )

        return completion2.choices[0].message.content.strip()
        
    paklijst_tekst = genereer_paklijst_tekst(client, antwoorden, destination_mt, traveltype_mt)
    
      #teaser voor klant
    print(f"TEASER VOOR DE KLANT:")
    print(f"De reis is bepaald! Binnekort kun jij genieten van je ideale {traveltype_mt}")
    print("Paklijst:\n", paklijst_tekst)
start()



