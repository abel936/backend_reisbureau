from flask import request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os
from connect_with_db import get_connection

load_dotenv()
apikey = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=apikey)

def start():
    # Haal JSON uit de POST-body
    data = request.get_json()
    if not data:
        return jsonify({"error": "Geen JSON ontvangen"}), 400

    # Lees velden uit data
    naam = data.get("naam")
    soort_reis = data.get("soort_reis")
    wanneer = data.get("wanneer")
    aantal_personen = data.get("aantal_personen")
    vervoer = data.get("vervoer")
    regio = data.get("regio")
    uitgesloten_landen = data.get("uitgesloten_landen", "")
    budget_pp_eur = data.get("budget_pp_eur")
    aantal_dagen = data.get("aantal_dagen")
    voorkeuren = data.get("voorkeuren", "")
    opmerkingen = data.get("opmerkingen", "")

    # connectie database
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT Countries.name AS CountryName, Cities.name AS CityName
                FROM Cities
                LEFT JOIN Countries ON Countries.country_id = Cities.country_id;
            """)
            rows = cur.fetchall()
    beschikbare_bestemmingen = [f"{row.CityName}, {row.CountryName}" for row in rows]

    # Bestemming prompt
    antwoorden = {
        "Wat is je naam?": naam,
        "Wat voor soort reis?": soort_reis,
        "Wanneer?": wanneer,
        "Met hoeveel personen?": aantal_personen,
        "Hoe wil je reizen?": vervoer,
        "Binnen of buiten Europa?": regio,
        "Welke landen niet?": uitgesloten_landen,
        "Budget": budget_pp_eur,
        "Hoeveel dagen wil je weg?": aantal_dagen,
        "Specifieke voorkeuren?": voorkeuren,
        "Vrije opmerkingen?": opmerkingen
    }

    prompt = (
        "Je bent een reisconsulent voor een mysterytrip. "
        "Analyseer alle antwoorden en kies een bestemming die perfect past bij de wensen. "
        f"Je mag ALLEEN kiezen uit deze lijst:\n{beschikbare_bestemmingen}\n\n"
        "Geef als output:\n"
        "Klantnaam\nBestemming\nType reis\nMotivatie\n\n"
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

    #advies splitten
    advies = completion.choices[0].message.content.strip()
    regels = advies.split("\n")
    klantnaam = regels[0].replace("Klantnaam:", "").strip()
    bestemming = regels[1].replace("Bestemming:", "").strip()
    type_reis = regels[2].replace("Type reis:", "").strip()
    motivatie = regels[3].replace("Motivatie:", "").strip()

    # Opslaan in DB
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO InternalInfo (clientname_mt, destination_mt, traveltype_mt, motivation_mt)
                VALUES (?, ?, ?, ?)
            """, (klantnaam, bestemming, type_reis, motivatie))
            conn.commit()

    #Paklijst prompt
    prompt2 = (
        f"Maak een duidelijke paklijst voor een {type_reis} naar {bestemming}. "
        f"Houd rekening met: periode ({wanneer}), aantal dagen ({aantal_dagen}), vervoer ({vervoer}), voorkeuren ({voorkeuren}). "
        "Geef de lijst netjes in categorieën (Kleding, Documenten, Gadgets, Extra). "
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

    paklijst = completion2.choices[0].message.content.strip()

    #JSON
    return jsonify({
        "klantnaam": klantnaam,
        "bestemming": bestemming,
        "type_reis": type_reis,
        "motivatie": motivatie,
        "paklijst": paklijst
    })


