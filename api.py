import requests
import csv
import logging
import os

from dotenv import load_dotenv


# Load environment variables
load_dotenv()


# API key
API_KEY = os.getenv("API_KEY")


# Output file
OUTPUT_FILE = "product_urls.csv"


# API URL
API_URL = "https://www.metrocuadrado.com/rest-search/search"


# Configuring logging
logging.basicConfig(
    filename="../scraper_logs/api.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# Function to get properties from the API
def get_properties(from_value, extra_params=None):

    # Parameters required by the API
    params = {
        "size": 50,
        "from": from_value,
        "realEstateTypeList": (
            "casalote,edificio-de-oficinas,"
            "edificio-de-apartamentos,apartamento,"
            "apartaestudio,casa,oficina,local,"
            "bodega,lote,finca,consultorio"
        )
    }

    # Add extra filters if provided
    if extra_params:
        params.update(extra_params)

    # Headers required by the API
    headers = {
        "x-api-key": API_KEY
    }

    # Send GET request to the API
    response = requests.get(
        API_URL,
        params=params,
        headers=headers
    )

    # Check if the request was successful
    response.raise_for_status()

    # Convert JSON response into a Python dictionary
    data = response.json()

    # Log successful request
    logger.info(
        "Offset %s collected successfully",
        from_value
    )

    # Get the properties from the response
    properties = data["results"]

    # Return properties and API information
    return properties, data


# Function to extract URLs from properties
def extract_urls(properties):

    urls = []

    # Go through every property
    for property_data in properties:

        # Get the relative property link
        link = property_data.get("link")

        # Make sure a link exists
        if link:

            # Add the website domain
            full_url = "https://www.metrocuadrado.com" + link

            # Add URL to the list
            urls.append(full_url)

    return urls


# Function to save URLs to CSV
def save_urls(urls):

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        # Write column name
        writer.writerow(["url"])

        # Write URLs
        for url in urls:
            writer.writerow([url])

    logger.info(
        "Total URLs saved: %s",
        len(urls)
    )

    logger.info(
        "URLs saved to %s",
        OUTPUT_FILE
    )
# Main function
def main():

    all_urls = []

    from_value = 0

    # Extra filters can be added here later
    extra_params = {}

    while True:

        # Get properties from API
        properties, data = get_properties(
            from_value,
            extra_params
        )

        # Stop when API returns no properties
        if not properties:
            break

        # Extract URLs
        urls = extract_urls(properties)

        # Add URLs to main list
        all_urls.extend(urls)

        # Log progress
        logger.info(
            "Offset %s: %s URLs collected",
            from_value,
            len(urls)
        )

        print(
            f"Offset {from_value}: "
            f"{len(urls)} URLs collected"
        )

        # Move to next offset
        from_value += 50

    # Remove duplicate URLs
    all_urls = list(dict.fromkeys(all_urls))

    # Save all URLs
    save_urls(all_urls)

    print(f"Total unique URLs: {len(all_urls)}")

    logger.info(
        "Total unique URLs: %s",
        len(all_urls)
    )

    logger.info("API scraping completed successfully")


# Run main function
if __name__ == "__main__":
    main()