import requests
import pandas as pd
import os
import logging
import json
import uuid
import re

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("API_KEY")

API_URL = "https://www.metrocuadrado.com/rest-search/search"


# LOGGER

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


# translates text from Spanish to English

MODEL_NAME = "Helsinki-NLP/opus-mt-es-en"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)


# Translation cache

translation_cache = {}


# Function to translate a single value from Spanish to English

def translate_value(value):

    if value is None:
        return None

    if not isinstance(value, str):
        return value

    value = value.strip()

    if not value:
        return value

    # Check if this value was already translated
    if value in translation_cache:
        return translation_cache[value]

    try:

        # Translate value using Helsinki-NLP
        inputs = tokenizer(
            value,
            return_tensors="pt",
            padding=True,
            truncation=True
        )

        outputs = model.generate(
            **inputs,
            max_length=512
        )

        translated = tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )

        # Save translation in cache
        translation_cache[value] = translated

        return translated

    except Exception as e:

        print(
            f"Translation failed for '{value}': {e}"
        )

        logging.error(
            "Translation failed for '%s': %s",
            value,
            e
        )

        # Return original value if translation fails
        return value


# Function to translate a single key from Spanish to English

def translate_key(key):

    if key is None:
        return None

    key = str(key).strip()

    if not key:
        return key

    # Translate key using Helsinki-NLP
    return translate_value(key)


def translate_featured(featured):

    translated_featured = []

    for item in featured:

        if not item:
            continue

        item = str(item).strip()

        if ":" in item:

            key, value = item.split(":", 1)

            key = key.strip()
            value = value.strip()

            # Translate the key using Helsinki-NLP
            translated_key = translate_key(key)

            # Translate the value using Helsinki-NLP
            translated_value = translate_value(value)

            translated_featured.append(
                f"{translated_key}:{translated_value}"
            )

        else:

            translated_featured.append(
                translate_value(item)
            )

    return translated_featured


# Function to create property details

def create_property_details(property_data):

    featured = property_data.get("featured") or []

    # Creates an empty dictionary where we will store the featured information as key-value pairs.

    featured_dict = {}

    # Go through each item inside the featured list.

    for item in featured:

        if not item:
            continue

        item = str(item).strip()

        if ":" in item:

            key, value = item.split(":", 1)

            featured_dict[key.strip()] = value.strip()

    # empty list to store each prop.detail as dict

    details = []


    # PROPERTY TYPE

    mtipoinmueble = property_data.get(
        "mtipoinmueble"
    ) or {}

    property_type = mtipoinmueble.get(
        "nombre"
    )

    if property_type:

        details.append({
            "label": "Property Type",
            "value": translate_value(property_type)
        })


    # CONDITION

    # Get the condition/status of the property. "Nuevo", "Usado", etc.

    condition = property_data.get("mestadoinmueble")

    if condition:

        details.append({
            "label": "Condition",
            "value": translate_value(condition)
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

        try:

            details.append({
                "label": "Private Area",
                "value": f"{float(private_area) * 10.7639:.2f} sq ft"
            })

        except (ValueError, TypeError):

            pass


    # AREA

    area = property_data.get("marea")

    if area:

        try:

            details.append({
                "label": "Area",
                "value": f"{float(area) * 10.7639:.2f} sq ft"
            })

        except (ValueError, TypeError):

            pass


    # SOCIOECONOMIC STRATUM

    stratum = property_data.get("estrato")

    if stratum is not None:

        details.append({
            "label": "Socioeconomic Stratum",
            "value": str(stratum)
        })


    # FLOOR NUMBER

    # Gets the floor number from the dictionary we created from the "featured" list. featured_dict = {"nroPiso": "5"} -> floor_number will become "5".

    floor_number = featured_dict.get("nroPiso")

    if floor_number:

        details.append({
            "label": "Floor Number",
            "value": floor_number
        })


    # NUMBER OF FLOORS

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
            "value": translate_value(construction_age)
        })


    # BALCONY / TERRACE

    balcony = featured_dict.get("terrazaBalcon")

    if balcony:

        details.append({
            "label": "Balcony/Terrace",
            "value": translate_value(balcony)
        })


    # Converts the Python list of dictionaries into a JSON string.

    return json.dumps(details, ensure_ascii=False)


# Function to get image URLs from an individual property page.

# def get_property_images(property_url):

#     # Request the property page

#     response = requests.get(property_url)

#     response.raise_for_status()

#     html = response.text

#     # Find the images array

#     match = re.search(
#         r'\\"images\\":(\[.*?\])',
#         html
#     )

#     if not match:
#         return None

#     # Extracts the array

#     images_json = match.group(1)

#     # Convert escaped JSON into normal JSON

#     images_json = images_json.replace('\\"', '"')

#     # Convert JSON string to Python list of dictionaries

#     images = json.loads(images_json)

#     # Extract image URLs

#     image_urls = []

#     for image in images:

#         image_url = image.get("image")

#         if image_url:

#             image_urls.append(image_url)

#     return image_urls


# concating from api

def get_property_images(property_data):

    property_id = property_data.get("midinmueble")

    image_ids = property_data.get(
        "mgaleriainmueble"
    ) or []

    image_url = []

    base_url = "https://multimedia.metrocuadrado.com/"

    if not property_id:
        return image_url

    for image in image_ids:

        if not image:
            continue

        url = (
            base_url
            + str(property_id)
            + "/"
            + str(image)
            + ".jpg"
        )

        image_url.append(url)

    # print(image_ids)
    # print(property_id)
    # print(image_url)

    return image_url


# def get_admin_price(property_url):

#     # Request the property page

#     response = requests.get(property_url)

#     response.raise_for_status()

#     html = response.text

#     # Find the administration price

#     match = re.search(
#         r'Administración:\s*\$\\?\s*([\d\.]+)\s*COP',
#         html
#     )

#     if not match:
#         return None

#     # Extract the price

#     admin_price = match.group(1)

#     # Remove dots from the Colombian number format

#     admin_price = admin_price.replace(".", "")

#     # Convert to integer

#     return int(admin_price)


# def get_admin_price(property_url):

#     try:
#         response = requests.get(
#             property_url,
#             timeout=15
#         )
#         response.raise_for_status()

#         html = response.text

#         match = re.search(
#             r'Administración:\s\***\\$\\\\**?\s\*([\d**\\.**]+)\s\*COP',
#             html
#         )

#         if not match:
#             return None

#         admin_price = match.group(1)

#         admin_price = admin_price.replace(".", "")

#         return int(admin_price)

#     except requests.exceptions.RequestException as e:
#         print(
#             f"Admin price request failed for {property_url}: {e}"
#         )

#         logging.error(
#             "Admin price request failed for %s: %s",
#             property_url,
#             e
#         )

#         return None


# Function to get the current USD to COP exchange rate

def get_cop_usd_rate():

    response = requests.get(
        "https://api.frankfurter.dev/v2/rates?base=usd",
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    # Find the USD -> COP exchange rate
    usd_cop_rate = next(
        item["rate"]
        for item in data
        if item["quote"] == "COP"
    )

    # Get the date of the exchange rate
    rate_date = next(
        item["date"]
        for item in data
        if item["quote"] == "COP"
    )

    print(
        f"USD to COP exchange rate: {usd_cop_rate} "
        f"(rate date: {rate_date})"
    )

    # Convert USD -> COP rate into COP -> USD rate
    cop_usd_rate = 1 / usd_cop_rate

    return cop_usd_rate


# MAIN FUNCTION

def main():

    # Get current COP to USD exchange rate
    cop_usd_rate = get_cop_usd_rate()

    rows = []

    # Pagination starting point
    from_value = 0

    # Count total properties scraped
    total_scraped = 0


    # GET PROPERTIES

    while True:

        params["from"] = from_value

        logging.info(
            "Sending request to Metrocuadrado API. Offset: %s",
            from_value
        )

        response = requests.get(
            API_URL,
            params=params,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        properties = data.get("results", [])

        # Stop if API returns no properties

        if not properties:
            break


        print(
            f"\nOffset {from_value}: "
            f"{len(properties)} properties"
        )

        print(
            "Total hits:",
            data.get("totalHits")
        )


        logging.info(
            "Offset %s: %s properties",
            from_value,
            len(properties)
        )

        logging.info(
            "Total hits: %s",
            data.get("totalHits")
        )


        # PROCESS EACH PROPERTY

        for property_data in properties:

            # Safely get nested dictionaries

            localizacion = (
                property_data.get("localizacion")
                or {}
            )

            mciudad = (
                property_data.get("mciudad")
                or {}
            )

            mtipoinmueble = (
                property_data.get("mtipoinmueble")
                or {}
            )


            # PROPERTY URL

            property_link = property_data.get("link")

            if property_link:

                if property_link.startswith("http"):

                    property_url = property_link

                else:

                    property_url = (
                        "https://www.metrocuadrado.com"
                        + property_link
                    )

            else:

                property_url = None


            # GET IMAGE URLS

            images = get_property_images(
                property_data
            )


            # GET ADMIN PRICE

            # if property_url:

            #     admin_price = get_admin_price(property_url)

            # else:

            #     admin_price = None

            admin_price = None


            # CREATE ROW

            row = {

                # Database ID is AUTO_INCREMENT
                "id": None,

                "uuid": str(uuid.uuid4()),

                "title": property_data.get("title"),

                "link": property_url,

                "location": (
                    f"{property_data.get('mbarrio')}, "
                    f"{mciudad.get('nombre')}"
                ),

                "country": "Colombia",

                # "lat": property_data.get(
                #     "localizacion", {}
                # ).get("lat"),

                # "lng": property_data.get(
                #     "localizacion", {}
                # ).get("lon"),

                # "latLng_status": (
                #     1
                #     if (
                #         property_data.get(
                #             "localizacion", {}
                #         ).get("lat") is not None

                #         and

                #         property_data.get(
                #             "localizacion", {}
                #         ).get("lon") is not None
                #     )

                #     else 0

                "lat": localizacion.get("lat"),

                "lng": localizacion.get("lon"),

                "latLng_status": (
                    1
                    if (
                        localizacion.get("lat") is not None
                        and
                        localizacion.get("lon") is not None
                    )
                    else 0
                ),

                "type": property_data.get(
                    "mtiponegocio"
                ),

                "phone": property_data.get(
                    "contactPhone"
                ),

                "price": (
                    round(
                        property_data.get(
                            "mvalorventa"
                        ) * cop_usd_rate,
                        3
                    )
                    if property_data.get(
                        "mvalorventa"
                    ) is not None
                    else None
                ),

                "price_unit": None,

                "details": property_data.get(
                    "comment"
                ),

                "img_src": images,

                "about": None,

                "exterior_acres": None,

                "web_id": property_data.get(
                    "midinmueble"
                ),

                "mls_id": None,

                "bedrooms": property_data.get(
                    "mnrocuartos"
                ),

                "full_baths": property_data.get(
                    "mnrobanos"
                ),

                "property_type": (
                    mtipoinmueble.get(
                        "nombre"
                    )
                ),

                "interior_sq_ft": (
                    float(
                        property_data.get("marea")
                    ) * 10.7639
                    if property_data.get(
                        "marea"
                    ) is not None
                    else None
                ),

                "amenities": None,

                "features": translate_featured(
                    property_data.get("featured") or []
                ),

                "partial_baths": None,

                "change_price": None,

                "sold_date": None,

                "deleted_at": None,

                "created_at": None,

                "updated_at": None,

                "city": mciudad.get(
                    "nombre"
                ),

                "new_features": None,

                "property_details": (
                    create_property_details(
                        property_data
                    )
                ),

                "exterior_details": None,

                # "interior_details": translate_featured(
                #     property_data.get("featured") or []
                # ),

                "interior_details": None,

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

                "missing_count": 0,

                "admin_price": admin_price,

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
                "amenities",
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


            # ADD ROW TO LIST

            rows.append(row)


            # LOG PROPERTY

            logging.info(
                "Property processed: %s",
                row["web_id"]
            )


            # Increase total scraped count

            total_scraped += 1

            print(
                f"Scraped: {total_scraped}/500",
                end="\r"
            )


            # STOP AFTER 500 PROPERTIES

            if total_scraped >= 500:

                break


        print()


        # STOP THE WHILE LOOP

        if total_scraped >= 500:

            print(
                "Reached 500 properties. "
                "Stopping scraper."
            )

            break


        # MOVE TO NEXT OFFSET

        from_value += len(properties)

        print(
            "Moving to next offset:",
            from_value
        )


    # CREATE DATAFRAME

    df = pd.DataFrame(rows)

    print(
        f"\nTotal properties collected: "
        f"{len(df)}"
    )


    # TRANSLATE SPANISH COLUMNS TO ENGLISH

    translate_columns = [
        "title",
        "type",
        "details",
        "property_type",
        "property_status",
    ]


    for column in translate_columns:

        # Get unique non-empty values

        values = (
            df[column]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        if not values:
            continue

        try:

            # Translate each unique value using Helsinki-NLP

            translation_map = {}

            for value in values:

                translation_map[value] = (
                    translate_value(value)
                )


            # Replace Spanish values with English translations

            df[column] = df[column].map(
                lambda x:
                translation_map.get(
                    str(x),
                    x
                )
                if pd.notna(x)
                else x
            )

            print(
                f"Translated column: {column}"
            )

        except Exception as e:

            print(
                f"Translation failed for column "
                f"{column}: {e}"
            )

            logging.error(
                "Translation failed for column %s: %s",
                column,
                e
            )


    # SAVE DATAFRAME TO CSV

    os.makedirs(
        "./csv_files",
        exist_ok=True
    )

    df.to_csv(
        "./csv_files/metrocuadrado_properties.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print(
        "\nCSV saved successfully."
    )


# RUN MAIN FUNCTION

if __name__ == "__main__":

    main()