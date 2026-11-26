from pathlib import Path

import pandas as pd
import numpy as np

DATA = Path(__file__).resolve().parent.parent / "data" / "carclaims.csv"


def get_data():
    data = pd.read_csv(DATA)
    return data


def load_data():
    data = get_data()
    return data


def inspect_data(data):
    ## print first 5 rows of data
    print("First 5 rows:")
    print(data.head(5))
    ## check columns and rows
    print("\nData shape:")
    print(data.shape)
    ## check all columns' names
    print("\nColumns name:")
    print(data.columns)
    ## check data types
    print("\nColumn data types:")
    print(data.dtypes)
    ##
    print("\n Data information:")
    data.info()
    ##
    print("\nDescriptive Statistics:")
    print(data.describe(include="all"))


def check_special_letter(data):
    for column in data.columns:
        print(f"\n{column}:")
        print(data.groupby(column, dropna=False).size())


def check_duplicate_records(data):
    duplicate_count = data.duplicated().sum()
    print("\nDuplicate Records Check:")
    print(f"Number of duplicated records: {duplicate_count}")

    duplicate_policy = data["PolicyNumber"].duplicated().sum()
    print("\nDuplicate PolicyNumber Check:")
    print(f"Number of duplicated policies: {duplicate_policy}")

def zero_check_clean(data):
    # Search the whole dataset for numeric 0 and string '0'
    for column in data.columns:
        zero_counts = (data[column] == 0).sum()
        string_zero_counts = (data[column] == "0").sum()

        if zero_counts > 0 or string_zero_counts > 0:
            print(
                f"{column}: "
                f"numeric 0 = {zero_counts}, "
                f"string '0' = {string_zero_counts}"
            )

    # Only replace zero values that are known to be invalid
    invalid_zero_values = {
        "Age": 0,
        "DayOfWeekClaimed": "0",
        "MonthClaimed": "0",
    }

    for column, invalid_value in invalid_zero_values.items():
        data[column] = data[column].replace(
            invalid_value,
            np.nan,
        )

def missing_value_check(data):
    missing_counts = data.isna().sum()
    missing_rate = data.isna().mean()

    print(f"\nMissing counts:\n" f"{missing_counts[missing_counts > 0]}")
    print(
        f"\nMissing rate:\n" f"{missing_rate[missing_rate > 0].map(lambda x: f'{x:.2%}')}"
    )

def AgeGrouping(data):
    condlist = [
        data['Age'].isna(),
        data['Age'] < 18,
        (
            (data['Age'] >= 18)
            & (data['Age'] <= 24)
            ),
        data['Age'].between(25, 34),
        data['Age'].between(35, 44),
        data['Age'].between(45, 54),
        data['Age'].between(55, 64),
        data['Age'] >= 65
    ]
    choicelist = [
        'Unknown',
        'Dependent',
        '18-24',
        '25-34',
        '35-44',
        '45-54',
        '55-64',
        '65+'
    ]
    data['AgeGroup'] = np.select(
        condlist,
        choicelist,
        default='Check'
    )


def prepare_data():
    data = load_data()
    zero_check_clean(data)
    missing_value_check(data)
    AgeGrouping(data)
    return data
