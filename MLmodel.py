import urllib.request
import json
from dotenv import load_dotenv
import os

# Request data goes here
# The example below assumes JSON formatting which may be updated
# depending on the format your endpoint expects.
# More information can be found here:
# https://docs.microsoft.com/azure/machine-learning/how-to-deploy-advanced-entry-script


# Load environment variables and initialize client globally



#
#
# issue met het predicten van capaciteit ????
#
#


load_dotenv()
api_key = os.getenv("MLWORKSPACE_API_KEY")

def predict_capacity_percentage(flight_number, 
                                scheduled_departure,
                                airline_name,
                                departure_airport,
                                arrival_airport):
    
    data = {
    "input_data": {
        "columns": [
        "flight_number",
        "scheduled_departure",
        "airline_name",
        "departure_airport",
        "arrival_airport"
        ],
        "index": [0],
        "data": [
            [flight_number, 
            scheduled_departure.isoformat(),
            airline_name,
            departure_airport,
            arrival_airport]
        ]
        }
    }

    body = str.encode(json.dumps(data))

    url = 'https://ack2511travel-wrmmx.westeurope.inference.ml.azure.com/score'
    # Replace this with the primary/secondary key, AMLToken, or Microsoft Entra ID token for the endpoint
    if not api_key:
        raise Exception("A key should be provided to invoke the endpoint")


    headers = {'Content-Type':'application/json', 'Accept': 'application/json', 'Authorization':('Bearer '+ api_key)}

    req = urllib.request.Request(url, body, headers)

    try:
        response = urllib.request.urlopen(req)
        result = response.read()
        print(result)
        decoded = result.decode('utf-8')
        print(decoded)
        predicted_value = float(decoded.strip('[]'))
        print(round(predicted_value, 2), type(predicted_value))
        return round(predicted_value, 2)

    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))


        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))

# predict_capacity_percentage("", 
#                             "",
#                             "KLM Royal Dutch Airlines",
#                             "Eindhoven Airport",
#                             "Adolfo Suarez Madrid-Barajas")