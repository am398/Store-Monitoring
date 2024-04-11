import requests
import csv
from io import StringIO
from models import db
from app import app
from models.business_hour import BusinessHour
from models.store_status import StoreStatus
from datetime import datetime
from models.store_timezone import StoreTimezone
import pandas as pd



def seed_business_hours():
    # Define the URL
    url = 'https://drive.google.com/file/d/1va1X3ydSh-0Rt1hsy2QSnHRA4w57PcXg/view?usp=sharing'

    # Extract file ID from URL
    file_id = url.split('/')[-2]

    # Construct the direct download URL
    download_url = f'https://drive.google.com/uc?id={file_id}'
    
    response = requests.get(download_url)
    if response.status_code == 200:
        csv_data = StringIO(response.text)
        reader = csv.reader(csv_data)
        next(reader)  # Skip the header row
        for row in reader:
            store_id, day_of_week, start_time_local, end_time_local = row
            start_time_local = datetime.strptime(start_time_local, '%H:%M:%S').time()
            end_time_local = datetime.strptime(end_time_local, '%H:%M:%S').time()
            business_hour = BusinessHour(
                store_id=int(store_id),
                day_of_week=int(day_of_week),
                start_time_local=start_time_local,
                end_time_local=end_time_local
            )
            db.session.add(business_hour)
    db.session.commit()

def seed_store_status():
    file_path = "/home/anuj/Pictures/store status.csv"
    # Read the CSV file into a DataFrame
    # Define chunk size
    chunk_size = 10000  # Adjust the chunk size as needed

    # Create an iterator to read the CSV file in chunks
    chunk_iterator = pd.read_csv(file_path, chunksize=chunk_size)
    for chunk in chunk_iterator:
        # Iterate over each row in the chunk
        for index, row in chunk.iterrows():
            # Extract values from the DataFrame row
            store_id = int(row['store_id'])
            timestamp_utc = row['timestamp_utc']
            status = row['status']

            # Create a new StoreStatus object
            store_status = StoreStatus(
                store_id=store_id,
                timestamp_utc = pd.to_datetime(row['timestamp_utc']),
                status=status
            )

            # Add the StoreStatus object to the session
            db.session.add(store_status)
        db.session.commit()

def seed_store_timezones():
    # Define the URL
    url = 'https://drive.google.com/file/d/101P9quxHoMZMZCVWQ5o-shonk2lgK1-o/view?usp=sharing'

    # Extract file ID from URL
    file_id = url.split('/')[-2]

    # Construct the direct download URL
    download_url = f'https://drive.google.com/uc?id={file_id}'
    response = requests.get(download_url)
    if response.status_code == 200:
        csv_data = StringIO(response.text)
        reader = csv.reader(csv_data)
        next(reader)  
        for row in reader:
            store_id, timezone_str = row
            store_timezone = StoreTimezone(
                store_id=int(store_id),
                timezone_str=timezone_str
            )
            db.session.add(store_timezone)
    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        seed_business_hours()
        seed_store_timezones()
        seed_store_status()
        