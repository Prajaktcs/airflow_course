import logging
import os

import pandas as pd
import requests
from airflow.decorators import dag, task
from airflow.utils.dates import days_ago

# Define constants for file paths
CSV_FILE_PATH = "output.csv"


# Define the DAG using the TaskFlow API
@dag(
    dag_id="fetch_and_save_data",
    description="Fetch data from a website and save it as a CSV file",
    schedule_interval="@once",
    start_date=days_ago(1),
    catchup=False,  # Disable backfill
    tags=["example", "web_scraping", "data_processing"],
)
def fetch_and_save_data():

    @task
    def fetch_data():
        """Fetch data from a website."""
        url = "https://jsonplaceholder.typicode.com/posts"  # Example API endpoint
        logging.info(f"Fetching data from {url}...")

        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()  # Assuming the data is in JSON format

        logging.info(f"Fetched {len(data)} records.")
        return data

    @task
    def process_data(data):
        """Process the fetched data."""
        logging.info("Processing data...")

        # Convert JSON data to a Pandas DataFrame
        df = pd.DataFrame(data)

        # Perform any necessary data transformations
        df["title_length"] = df["title"].apply(
            len
        )  # Example transformation: calculate title length

        logging.info(f"Processed {len(df)} records.")
        return df

    @task
    def save_to_csv(df):
        """Save the processed data to a CSV file."""
        logging.info(f"Saving data to {CSV_FILE_PATH}...")

        # Save the DataFrame to a CSV file
        df.to_csv(CSV_FILE_PATH, index=False)

        logging.info(f"Data saved to {CSV_FILE_PATH}.")
        return CSV_FILE_PATH

    @task
    def notify(csv_file_path):
        """Send a notification that the data has been saved."""
        logging.info(f"Data successfully saved to {csv_file_path}.")
        # Here, you could implement a notification logic, e.g., sending an email or Slack message

    # Define the task dependencies
    data = fetch_data()
    processed_data = process_data(data)
    csv_file_path = save_to_csv(processed_data)
    notify(csv_file_path)


# Instantiate the DAG
dag_instance = fetch_and_save_data()
