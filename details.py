import requests
import pandas as pd
import os
import logging
import json
import uuid

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
logging.info("Results received: %s", len(data.get("results", [])))
logging.info("Total hits: %s", data.get("totalHits"))

# GET FIRST PROPERTY
properties = data["results"]

property_data = properties[0]

def create_property_details(property_data):
    featured = property_data.get("featured") or []

    # Convert featured list into a dictionary
    featured_dict = {}

    for item in featured:
        item = item.strip()

        if ":" in item:
            key, value = item.split(":", 1)
            featured_dict[key.strip()] = value.strip()

    details = []

    # Property Type
    property_type = (
        property_data.get("mtipoinmueble", {}).get("nombre")
    )
    if property_type:
        details.append({
            "label": "Property Type",
            "value": property_type
        })

    # Condition
    condition = property_data.get("mestadoinmueble")
    if condition:
        details.append({
            "label": "Condition",
            "value": condition
        })

    # Bathrooms
    bathrooms = property_data.get("mnrobanos")
    if bathrooms:
        details.append({
            "label": "Bathrooms",
            "value": str(bathrooms)
        })

    # Bedrooms
    bedrooms = property_data.get("mnrocuartos")
    if bedrooms:
        details.append({
            "label": "Bedrooms",
            "value": str(bedrooms)
        })

    # Parking Spaces
    parking = property_data.get("mnrogarajes")
    if parking:
        details.append({
            "label": "Parking Spaces",
            "value": str(parking)
        })

    # Private Area
    private_area = (
        property_data.get("areaPrivada")
        or property_data.get("areaprivada")
    )

    if private_area:
        details.append({
            "label": "Private Area",
            "value": f"{private_area} m2"
        })

    # Area
    area = property_data.get("marea")
    if area:
        details.append({
            "label": "Area",
            "value": f"{area} m2"
        })

    # Socioeconomic Stratum
    stratum = property_data.get("estrato")
    if stratum is not None:
        details.append({
            "label": "Socioeconomic Stratum",
            "value": str(stratum)
        })

    # Floor Number
    floor_number = featured_dict.get("nroPiso")
    if floor_number:
        details.append({
            "label": "Floor Number",
            "value": floor_number
        })

    # Number of Floors
    number_of_floors = featured_dict.get("nroPisos")
    if number_of_floors:
        details.append({
            "label": "Number of Floors",
            "value": number_of_floors
        })

    # Price
    price = property_data.get("mvalorventa")
    if price:
        details.append({
            "label": "Price (COP)",
            "value": str(price)
        })

    # Construction Age
    construction_age = featured_dict.get("tiempoConstruido")
    if construction_age:
        details.append({
            "label": "Construction Age",
            "value": construction_age
        })

    # Balcony / Terrace
    balcony = featured_dict.get("terrazaBalcon")
    if balcony:
        details.append({
            "label": "Balcony/Terrace",
            "value": balcony
        })

    return json.dumps(details, ensure_ascii=False)


# CREATE ROW

row = {
    "id": None,
    "uuid": str(uuid.uuid4()),   #generates universally unique id(idk needed or not)
    
    "title": property_data.get("title"),
    
    "link": (
        "https://www.metrocuadrado.com" + property_data.get("link")
    ),

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
            property_data.get("localizacion", {}).get("lat") is not None
            or
            property_data.get("localizacion", {}).get("lon") is not None
        )
        else 0
    ),

    "type": property_data.get("mtiponegocio"),

    "phone": property_data.get("contactPhone"),

    "price": property_data.get("mvalorventa"),

    "price_unit": None,

    "details": property_data.get("comment"),

    "img_src": property_data.get("mgaleriainmueble"),

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

    "property_details": create_property_details(property_data),

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
#     # METROCUADRADO-SPECIFIC FIELDS other thana sample

#     "whatsapp": property_data.get("whatsapp"),

#     "imageLink": property_data.get("imageLink"),

#     "whatsappMessage": property_data.get(
#         "whatsappMessage"
#     ),

#     "badge": property_data.get("badge"),

#     "areaPrivada": property_data.get(
#         "areaPrivada"
#     ),

#     "mtipoinmueble_id": (
#         property_data.get(
#             "mtipoinmueble", {}
#         ).get("id")
#     ),

#     "mtiponegocio": property_data.get(
#         "mtiponegocio"
#     ),

#     "mvalorventa": property_data.get(
#         "mvalorventa"
#     ),

#     "mvalorarriendo": property_data.get(
#         "mvalorarriendo"
#     ),

#     "marea": property_data.get("marea"),

#     "mareac": property_data.get("mareac"),

#     "areaprivada": property_data.get(
#         "areaprivada"
#     ),

#     "mnrogarajes": property_data.get(
#         "mnrogarajes"
#     ),

#     "mciudad_id": (
#         property_data.get(
#             "mciudad", {}
#         ).get("id")
#     ),

#     "mzona": property_data.get("mzona"),

#     "mnombrecomunbarrio": property_data.get(
#         "mnombrecomunbarrio"
#     ),

#     "mnombreproyecto": property_data.get(
#         "mnombreproyecto"
#     ),

#     "midempresa": property_data.get(
#         "midempresa"
#     ),

#     "mestadoinmueble": property_data.get(
#         "mestadoinmueble"
#     ),

#     "mgaleriainmueble": property_data.get(
#         "mgaleriainmueble"
#     ),

#     "tipovivienda": property_data.get(
#         "tipovivienda"
#     ),

#     "mnumero_contactos": property_data.get(
#         "mnumero_contactos"
#     ),

#     "CPL": property_data.get("CPL"),

#     "featured": property_data.get("featured"),

#     "categoria": property_data.get("categoria"),

#     "estrato": property_data.get("estrato"),

#     "geopoints": property_data.get("geopoints"),

#     "localizacion": property_data.get(
#         "localizacion"
#     ),

#     "OwnerType": property_data.get(
#         "OwnerType"
#     ),
# }

# NORMALIZE DATA TYPES

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

# CREATE DATAFRAME
df = pd.DataFrame([row])
print("\nHG COLUMNS:")
print(df[hg_columns].T)

print("\nDataFrame:")
print(df)

print("\nData types:")
print(df.dtypes)

print("\nMissing count:")
print(row["missing_count"])
# LOG RESULT
logging.info(
    "Successfully created DataFrame with %s columns",
    len(df.columns)
)

logging.info(
    "Missing HG fields for first property: %s",
    row["missing_count"]
)

logging.info(
    "Property processed: %s",
    row["web_id"]
)

# SAVE DATAFRAME TO CSV
df.to_csv(
    "metrocuadrado_properties.csv",
    index=False
)

print("\nCSV saved successfully.")