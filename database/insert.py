import pandas as pd
import mysql.connector

from connect import get_connection

CSV_FILE = "../csv_files/metrocuadrado_properties.csv"


def insert_properties():
    # Read CSV file
    df = pd.read_csv(CSV_FILE)

    print(f"Found {len(df)} properties in CSV.")

    # Create database connection
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO metrocuadrado_properties (
            uuid,
            title,
            link,
            location,
            country,
            lat,
            lng,
            latLng_status,
            type,
            phone,
            price,
            price_unit,
            details,
            img_src,
            about,
            exterior_acres,
            web_id,
            mls_id,
            bedrooms,
            full_baths,
            property_type,
            interior_sq_ft,
            amenities,
            features,
            partial_baths,
            sold_date,
            change_price,
            deleted_at,
            created_at,
            updated_at,
            city,
            new_features,
            property_details,
            exterior_details,
            interior_details,
            city_checked,
            province,
            property_status,
            neighbourhood,
            commercial_units,
            source_hash,
            first_seen_at,
            last_seen_at,
            missing_count,
            admin_price
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
    """

    for _, row in df.iterrows():

        # Convert pandas NaN values to None
        values = (
            row["uuid"],
            row["title"],
            row["link"],
            row["location"],
            row["country"],
            row["lat"],
            row["lng"],
            row["latLng_status"],
            row["type"],
            row["phone"],
            row["price"],
            row["price_unit"],
            row["details"],
            row["img_src"],
            row["about"],
            row["exterior_acres"],
            row["web_id"],
            row["mls_id"],
            row["bedrooms"],
            row["full_baths"],
            row["property_type"],
            row["interior_sq_ft"],
            row["amenities"],
            row["features"],
            row["partial_baths"],
            row["sold_date"],
            row["change_price"],
            row["deleted_at"],
            row["created_at"],
            row["updated_at"],
            row["city"],
            row["new_features"],
            row["property_details"],
            row["exterior_details"],
            row["interior_details"],
            row["city_checked"],
            row["province"],
            row["property_status"],
            row["neighbourhood"],
            row["commercial_units"],
            row["source_hash"],
            row["first_seen_at"],
            row["last_seen_at"],
            row["missing_count"],
            row["admin_price"]
        )

        # Replace NaN with None
        values = tuple(
            None if pd.isna(value) else value
            for value in values
        )

        cursor.execute(query, values)

        print(f"Inserted property: {row['web_id']}")

    # Save all changes
    connection.commit()

    print("\nAll properties inserted successfully.")

    # Close database connection
    cursor.close()
    connection.close()


if __name__ == "__main__":
    insert_properties()