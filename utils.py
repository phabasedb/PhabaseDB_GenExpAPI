import os
import pandas
from constants import BASE_DIR

# Loads the requested dataset CSV file from the defined base path.
# If the file does not exist or reading fails, raises an exception with an message.

def read_dataset(dataset_name: str) -> pandas.DataFrame:
    path = os.path.join(BASE_DIR, dataset_name)
    if not os.path.exists(path):
        raise FileNotFoundError("The requested file was not found. Please try again later or contact an administrator.")
    try:
        return pandas.read_csv(path, dtype=str)
    except Exception as e:
        raise IOError("An error occurred while reading the dataset data. Please try again later or contact an administrator.")