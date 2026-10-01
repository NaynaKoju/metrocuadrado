import requests
import pandas as pd
import os
import logging
import json
import uuid
import re

from dotenv import load_dotenv

# LOAD API KEY from .env
load_dotenv()

API_KEY = os.getenv("API_KEY")

API_URL = "https://www.metrocuadrado.com/rest-search/search"

# LOGGER

# Creates a log file for this scraper
logging.basicConfig(
    filename="../scraper_logs/property_details.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# API PARAMETERS

params = {
    "size": 50,
    "from": 0,
    "realEstateTypeList": (
        "casalote,edificio-de-oficinas,"
        "edificio-de-apartamentos,apartamento,"
        "apartaestudio,casa,oficina,local,"
        "bodega,lote,finca,consultorio"
    )
}

headers = {
    "x-api-key": API_KEY
}

# Function to create property details

def create_property_details(property_data):

    # Get the "featured" list from the property data.
    # If "featured" does not exist or is None, use an empty list instead.
    featured = property_data.get("featured") or []

    # Create an empty dictionary where we will store the featured information as key-value pairs.
    featured_dict = {}

    # Go through each item inside the featured list.
    for item in featured:

        # Remove extra spaces from the beginning and end of the text.
        item = item.strip()

        # Check whether the item contains a ":"
        if ":" in item:

            # Split the text only at the first ":"
            key, value = item.split(":", 1)

            # Remove extra spaces and store the result in the dictionary.
            featured_dict[key.strip()] = value.strip()

    # Create an empty list to store each prop.detail as dict
    details = []

    # PROPERTY TYPE
    # Get the property type from the nested "mtipoinmueble" dictionary.
    # {"mtipoinmueble": {"nombre": "Apartamento"}}
    # will give us "Apartamento".
    property_type = (
        property_data.get("mtipoinmueble", {}).get("nombre")
    )

    if property_type:

        details.append({
            "label": "Property Type",
            "value": property_type
        })

    # CONDITION

    # Get the condition/status of the property. "Nuevo", "Usado", etc.
    condition = property_data.get("mestadoinmueble")

    if condition:
        details.append({
            "label": "Condition",
            "value": condition
        })

    # BATHROOMS

    bathrooms = property_data.get("mnrobanos")

    if bathrooms:
        details.append({
            "label": "Bathrooms",
            "value": str(bathrooms)
        })

    # BEDROOMS

    bedrooms = property_data.get("mnrocuartos")

    if bedrooms:
        details.append({
            "label": "Bedrooms",
            "value": str(bedrooms)
        })

    # PARKING SPACES

    parking = property_data.get("mnrogarajes")

    if parking:
        details.append({
            "label": "Parking Spaces",
            "value": str(parking)
        })

    # PRIVATE AREA

    private_area = (
        property_data.get("areaPrivada")
        or property_data.get("areaprivada")
    )

    if private_area:
        details.append({
            "label": "Private Area",
            "value": f"{private_area} m2"
        })

    # AREA

    area = property_data.get("marea")

    if area:
        details.append({
            "label": "Area",
            "value": f"{area} m2"
        })

    # SOCIOECONOMIC STRATUM

    stratum = property_data.get("estrato")

    if stratum is not None:
        details.append({
            "label": "Socioeconomic Stratum",
            "value": str(stratum)
        })

    # FLOOR NUMBER

    # Gets the floor number from the dictionary we created from the "featured" list.
    # Example: featured_dict = {"nroPiso": "5"} -> floor_number will become "5".
    floor_number = featured_dict.get("nroPiso")

    if floor_number:
        details.append({
            "label": "Floor Number",
            "value": floor_number
        })

    # NUMBER OF FLOORS

    # Get the total number of floors of the property from featured_dict
    number_of_floors = featured_dict.get("nroPisos")

    if number_of_floors:
        details.append({
            "label": "Number of Floors",
            "value": number_of_floors
        })

    # PRICE

    price = property_data.get("mvalorventa")

    if price:
        details.append({
            "label": "Price (COP)",
            "value": str(price)
        })

    # CONSTRUCTION AGE

    construction_age = featured_dict.get("tiempoConstruido")

    if construction_age:
        details.append({
            "label": "Construction Age",
            "value": construction_age
        })

    # BALCONY / TERRACE

    balcony = featured_dict.get("terrazaBalcon")

    if balcony:
        details.append({
            "label": "Balcony/Terrace",
            "value": balcony
        })

    # Converts the Python list of dictionaries into a JSON string.
    # ensure_ascii=False sabai characters allow garcha
    return json.dumps(details, ensure_ascii=False)

# Function to get image URLs from an individual property page.

def get_property_images(property_url):

    # Request the property page
    response = requests.get(property_url)
    response.raise_for_status()

    html = response.text

    # Find the images array
    match = re.search(
        r'\\"images\\":(\[.*?\])',
        html
    )

    if not match:
        return None

    # Extract the array
    images_json = match.group(1)

    # Convert escaped JSON into normal JSON
    images_json = images_json.replace('\\"', '"')

    # Convert JSON string to Python list of dictionaries
    images = json.loads(images_json)

    # Extract image URLs
    image_urls = []

    for image in images:

        image_url = image.get("image")

        if image_url:
            image_urls.append(image_url)

    return image_urls

# MAIN FUNCTION

def main():

    # SEND REQUEST TO METROCUADRADO API

    logging.info("Sending request to Metrocuadrado API")

    response = requests.get(
        API_URL,
        params=params,
        headers=headers
    )

    response.raise_for_status()

    data = response.json()

    print("Status:", response.status_code)
    print("Results:", len(data.get("results", [])))
    print("Total hits:", data.get("totalHits"))

    logging.info("API request successful")
    logging.info(
        "Results received: %s",
        len(data.get("results", []))
    )
    logging.info(
        "Total hits: %s",
        data.get("totalHits")
    )

    # GET PROPERTIES
    properties = data.get("results", [])
    print (data)
    rows = []


    # PROCESS FIRST 10 PROPERTIES

    # for property_data in properties[:10]:
    for id, property_data in enumerate(properties[:10], start=1):

        print(
            "\nProcessing property:",
            property_data.get("midinmueble")
        )


        # PROPERTY URL

        property_link = property_data.get("link")

        if property_link:

            property_url = (
                "https://www.metrocuadrado.com"
                + property_link
            )

        else:

            property_url = None


        # GET IMAGE URLS

        if property_url:

            images = get_property_images(property_url)

        else:

            images = None


        # CREATE ROW

        row = {

            "id": id,

            "uuid": str(uuid.uuid4()),   #generates universally unique id(idk needed or not)

            "title": property_data.get("title"),

            "link": property_url,

            "location": (
                f"{property_data.get('mbarrio')}, "
                f"{property_data.get('mciudad', {}).get('nombre')}"
            ),

            "country": "Colombia",

            "lat": property_data.get(
                "localizacion", {}
            ).get("lat"),

            "lng": property_data.get(
                "localizacion", {}
            ).get("lon"),

            "latLng_status": (
                1
                if (
                    property_data.get(
                        "localizacion", {}
                    ).get("lat") is not None
                    and
                    property_data.get(
                        "localizacion", {}
                    ).get("lon") is not None
                )
                else 0
            ),

            "type": property_data.get("mtiponegocio"),

            "phone": property_data.get("contactPhone"),

            #1cop=0.00029869 usd 
            # 1 COP = 0.00029869 USD
            "price": (
                property_data.get("mvalorventa") * 0.00029869
                if property_data.get("mvalorventa") is not None
                else None
            ),

            "price_unit": None,

            "details": property_data.get("comment"),

            "img_src": images,

            "about": None,

            "exterior_acres": None,

            "web_id": property_data.get("midinmueble"),

            "mls_id": None,  #multiple listing service

            "bedrooms": property_data.get("mnrocuartos"),

            "full_baths": property_data.get("mnrobanos"),

            "property_type": (
                property_data.get(
                    "mtipoinmueble", {}
                ).get("nombre")
            ),

            "interior_sq_ft": property_data.get("marea"),

            "amneties": property_data.get("featured"),

            "features": None,

            "partial_baths": None,

            "change_price": None,

            "sold_date": None,

            "deleted_at": None,

            "created_at": None,

            "updated_at": None,

            "city": (
                property_data.get(
                    "mciudad", {}
                ).get("nombre")
            ),

            "new_features": None,

            "property_details": create_property_details(
                property_data
            ),

            "exterior_details": None, #Zonas comunes y Exteriores(common areas and outdoor spaces )

            "interior_details": property_data.get("featured"),

            "city_checked": None,

            "province": None,

            "property_status": property_data.get(
                "mestadoinmueble"
            ),

            "neighbourhood": property_data.get(
                "mbarrio"
            ),

            "commercial_units": None,

            "source_hash": None,

            "first_seen_at": None,

            "last_seen_at": None,

            "missing_count": None,

            "admin_price": None,
        }

        # Converts latitude and longitude to strings

        row["lat"] = (
            str(row["lat"])
            if row["lat"] is not None
            else None
        )

        row["lng"] = (
            str(row["lng"])
            if row["lng"] is not None
            else None
        )

        # Convert bedrooms and full_baths to strings

        row["bedrooms"] = (
            str(row["bedrooms"])
            if row["bedrooms"] is not None
            else None
        )

        row["full_baths"] = (
            str(row["full_baths"])
            if row["full_baths"] is not None
            else None
        )

        # Convert multiple-value fields into JSON-formatted strings

        for column in [
            "img_src",
            "amneties",
            "exterior_details",
            "interior_details"
        ]:

            row[column] = (
                json.dumps(
                    row[column],
                    ensure_ascii=False
                )
                if row[column] is not None
                else None
            )

        # Convert date fields to strings if they contain a value

        for column in [
            "change_price",
            "sold_date",
            "deleted_at",
            "created_at",
            "updated_at",
            "first_seen_at",
            "last_seen_at"
        ]:

            row[column] = (
                str(row[column])
                if row[column] is not None
                else None
            )

        # COUNT MISSING FIELDS
        # We count how many of these fields have no value.
        hg_columns = [
            "id",
            "uuid",
            "title",
            "link",
            "location",
            "country",
            "lat",
            "lng",
            "latLng_status",
            "type",
            "phone",
            "price",
            "price_unit",
            "details",
            "img_src",
            "about",
            "exterior_acres",
            "web_id",
            "mls_id",
            "bedrooms",
            "full_baths",
            "property_type",
            "interior_sq_ft",
            "amneties",
            "features",
            "partial_baths",
            "change_price",
            "sold_date",
            "deleted_at",
            "created_at",
            "updated_at",
            "city",
            "new_features",
            "property_details",
            "exterior_details",
            "interior_details",
            "city_checked",
            "province",
            "property_status",
            "neighbourhood",
            "commercial_units",
            "source_hash",
            "first_seen_at",
            "last_seen_at",
            "missing_count",
            "admin_price"
        ]

        row["missing_count"] = sum(
            row[column] is None
            for column in hg_columns
            if column != "missing_count"
        )

        # ADD ROW TO LIST
        rows.append(row)

        logging.info(
            "Property processed: %s",
            row["web_id"]
        )

    # CREATE DATAFRAME

    df = pd.DataFrame(rows)

    print("\nHG COLUMNS:")
    print(df[hg_columns].T)

    print("\nDataFrame:")
    print(df)

    print("\nData types:")
    print(df.dtypes)

    print("\nNumber of properties:")
    print(len(df))

    print("\nMissing count:")
    print(df["missing_count"])


    # LOG RESULT

    logging.info(
        "Successfully created DataFrame with %s columns",
        len(df.columns)
    )


    # SAVE DATAFRAME TO CSV

    df.to_csv(
        "metrocuadrado_properties.csv",
        index=False
    )

    print("\nCSV saved successfully.")

# RUN MAIN FUNCTION
if __name__ == "__main__":
    main()