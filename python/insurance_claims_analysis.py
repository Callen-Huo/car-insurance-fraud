# %% Imports
from insurance_claims_load import (
    inspect_data,
    check_special_letter,
    check_duplicate_records,
    prepare_data
)
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import pandas as pd
import numpy as np
from pathlib import Path

# Output directory for figures (project-root/images)
IMG = Path(__file__).resolve().parent.parent / "images"
IMG.mkdir(exist_ok=True)

# %% Load data
claims = prepare_data()

# %% Data inspection
inspect_data(claims)
check_special_letter(claims)
# %% Duplicate check
check_duplicate_records(claims)

# %% Functions
# Calculate number of fraud claims
def fraud_claims(data):
    Fraud_counts = 0

    for fraud in data['FraudFound_P']:
        if fraud == 1:
            Fraud_counts += 1

    return Fraud_counts
# Bar chart function
def bar_chart(categories, values, Xlabel, Ylabel, Title):
    plt.figure(figsize=(8, 5))

    bars = plt.bar(
        categories,
        values,
        color='skyblue',
        width=0.6
    )
    plt.title(Title)
    plt.xlabel(Xlabel)
    plt.ylabel(Ylabel)
    plt.gca().yaxis.set_major_formatter(
        PercentFormatter(1)
    )

    plt.bar_label(
        bars,
        labels=[
            f"{value:.2%}"
            for value in values
        ],
        padding=3
    )

    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save to images/, naming the file after the chart title (spaces -> underscores)
    filename = Title.replace(" ", "_").replace("&", "and") + ".png"
    plt.savefig(IMG / filename, dpi=150, bbox_inches="tight")

    plt.show()

# %% Overall fraud statistics
# Total claims
total_claims = len(claims)
print(
    f"Total claim records: "
    f"{total_claims}"
)

# Fraud claims
Total_Fraud_Counts = fraud_claims(claims)
print(
    f"\nTotal fraud claim records: "
    f"{Total_Fraud_Counts}"
)

# Non-fraud claims
Total_NonFraud_Counts = (
    claims['FraudFound_P'] == 0
).sum()
print(
    f"\nTotal non-fraud claim records: "
    f"{Total_NonFraud_Counts}"
)

# Overall fraud rate
Overall_Fraud_Rate = (
    Total_Fraud_Counts / total_claims
)

# Overall non-fraud rate
Non_Fraud_Rate = (
    Total_NonFraud_Counts / total_claims
)
print(
    f"\nFraud Rate: "
    f"{Overall_Fraud_Rate:.2%}"
    f"\nNon Fraud Rate: "
    f"{Non_Fraud_Rate:.2%}"
)

# %% AccidentArea
# Boolean filtering method
urban = claims[
    claims['AccidentArea'] == 'Urban'
]
urban_fraud_rate = (
    urban['FraudFound_P'].mean()
)
rural = claims[
    claims['AccidentArea'] == 'Rural'
]
rural_fraud_rate = (
    rural['FraudFound_P'].mean()
)
print(
    f"\nUrban Fraud Rate: "
    f"{urban_fraud_rate:.2%}"
    f"\nRural Fraud Rate: "
    f"{rural_fraud_rate:.2%}"
)
bar_chart(
    ['Urban', 'Rural'],
    [urban_fraud_rate, rural_fraud_rate],
    'Accident Area',
    'Fraud Rate',
    'Fraud Rate in Different Areas'
)

# %% DriverRating
# groupby method
rating_fraud_rate = claims.groupby(
    'DriverRating',
    dropna=False
)['FraudFound_P'].mean()
print(
    "\nFraud Rate for Drivers "
    "with Different Ratings\n"
    f"{rating_fraud_rate.map(lambda x: f'{x:.2%}')}"
)
bar_chart(
    rating_fraud_rate.index,
    rating_fraud_rate.values,
    'Driver Rating',
    'Fraud Rate',
    'Fraud Rate According to Driver Rating'
)

# %% PoliceReportFiled
# crosstab method
ReportFiled_fraud_rate = pd.crosstab(
    claims['PoliceReportFiled'],
    claims['FraudFound_P'],
    normalize='index'
)[1]
print(
    ReportFiled_fraud_rate.map(
        lambda x: f"{x:.2%}"
    )
)
bar_chart(
    ReportFiled_fraud_rate.index,
    ReportFiled_fraud_rate.values,
    'Report Filed',
    'Fraud Rate',
    'Fraud Rate According to Report Filed'
)

# %% WitnessPresent
# pivot_table method
witness_fraud_rate = claims.pivot_table(
    values='FraudFound_P',
    index='WitnessPresent',
    aggfunc='mean'
)
print(
    witness_fraud_rate.map(
        lambda x: f"{x:.2%}"
    )
)
bar_chart(
    witness_fraud_rate.index,
    witness_fraud_rate[
        'FraudFound_P'
    ].values,
    'Witness Presence',
    'Fraud Rate',
    'Fraud Rate According to Witness Presence'
)

# %% PastNumberOfClaims
past_claims_fraud = pd.crosstab(
    claims['PastNumberOfClaims'],
    claims['FraudFound_P'],
    normalize='index'
)
print(
    past_claims_fraud.map(
        lambda x: f"{x:.2%}"
    )
)
pc_rate = past_claims_fraud[1]
bar_chart(
    past_claims_fraud.index,
    pc_rate,
    'Past Claims History',
    'Fraud Rate',
    'Fraud Rate According to Past Claims'
)

# %% AgeOfVehicle
vehicle_age_fraud = pd.crosstab(
    claims['AgeOfVehicle'],
    claims['FraudFound_P'],
    normalize='index'
)
print(
    vehicle_age_fraud.map(
        lambda x: f"{x:.2%}"
    )
)
va_rate = vehicle_age_fraud[1]
bar_chart(
    vehicle_age_fraud.index,
    va_rate,
    'Vehicle Age',
    'Fraud Rate',
    'Fraud Rate According to Vehicle Age'
)
#%% Fault
fault_fraud_rate = pd.crosstab(
    claims['Fault'],
    claims['FraudFound_P'],
    normalize= 'index'
)
fault_rate = fault_fraud_rate[1]
print(fault_fraud_rate.map(
    lambda x: f"{x:.2%}"
    )
)
bar_chart(
    fault_fraud_rate.index,
    fault_rate,
    'Fault',
    'Fraud Rate',
    'Fraud Rate According to Fault'
)

# %% AgeGroup fraud analysis

AgeGroup_counts = (
    claims['AgeGroup']
    .value_counts()
)

AgeGroup_fraud = pd.crosstab(
    claims['AgeGroup'],
    claims['FraudFound_P'],
    normalize='index'
)
AgeGroup_fraud = AgeGroup_fraud.rename(
    columns={
        0: 'Non fraud rate',
        1: 'fraud rate'
    }
)
AgeGroup_fraud = AgeGroup_fraud.join(
    AgeGroup_counts.rename(
        'Total Claims'
    )
)
AgeGroup_fraud = (
    AgeGroup_fraud.sort_values(
        by='fraud rate',
        ascending=False
    )
)
# Create display version
display_table = AgeGroup_fraud.copy()
rate_columns = [
    'Non fraud rate',
    'fraud rate'
]
display_table[rate_columns] = (
    display_table[rate_columns]
    .map(
        lambda x: f"{x:.2%}"
    )
)
print(display_table)
# %% AgeGroup visualisation
AG_rate = AgeGroup_fraud[
    'fraud rate'
]
bar_chart(
    AgeGroup_fraud.index,
    AG_rate.values,
    'Age Group',
    'Fraud Rate',
    'Fraud Rate According to Different Age Groups'
)
#%% Combined risk factors analysis
## Combinine risk factors of Age and Sex
age_sex_fraud_rate = pd.crosstab(
    [claims['AgeGroup'], claims['Sex']],
    claims['FraudFound_P'],
    normalize= 'index'
)
age_sex_fraud_rate = age_sex_fraud_rate.rename(
    columns={
        0: 'Non Fraud Rate',
        1: 'Fraud Rate'
    }
)
age_sex_counts = claims.groupby(
    ['AgeGroup','Sex']
).size()
age_sex_fraud_rate = age_sex_fraud_rate.join(
    age_sex_counts.rename(
        'Total Counts'
    )
)
age_sex_fraud_rate = age_sex_fraud_rate.sort_values(
    by= 'Fraud Rate',
    ascending= False
)
age_sex_display = age_sex_fraud_rate.copy()
age_sex_rate_columns = [
    'Non Fraud Rate',
    'Fraud Rate'
]
age_sex_display[age_sex_rate_columns] = age_sex_display[age_sex_rate_columns].map(
    lambda x: f"{x:.2%}"
)
print(age_sex_display)
age_sex_rate = age_sex_fraud_rate['Fraud Rate']
age_sex_labels = [
    f"{age}-{sex}"
    for age, sex in age_sex_fraud_rate.index
]
bar_chart(
    age_sex_labels,
    age_sex_rate.values,
    'Age + Sex',
    'Fraud Rate',
    'Age & Sex Combined risk analysis'
)
# %% Combined risk factors analysis
## Combinine risk factors of Vehicle type and Vehicle price
type_price_fraud = pd.crosstab(
    [claims['VehicleCategory'],claims['VehiclePrice']],
    claims['FraudFound_P'],
    normalize= 'index'
)
type_price_counts = claims.groupby(
    ['VehicleCategory', 'VehiclePrice'], 
).size()
type_price_fraud = type_price_fraud.join(
    type_price_counts.rename(
        'Total counts'
    )
)
type_price_fraud = type_price_fraud.rename(
    columns={
        0: 'Non Fraud Rate',
        1: 'Fraud Rate'
    }
)
type_price_fraud = type_price_fraud.sort_values(
    by= 'Fraud Rate',
    ascending= False
)
type_price_display = type_price_fraud.copy()
type_price_columns = [
    'Non Fraud Rate',
    'Fraud Rate'
]
type_price_display[type_price_columns] = type_price_display[type_price_columns].map(
    lambda x: f"{x:.2%}"
)
print(type_price_display)

type_price_rate = type_price_fraud['Fraud Rate']
type_price_label = [
    f"{vehicle_type}-{price}"
    for vehicle_type,price in type_price_fraud.index
]
bar_chart(
    type_price_label,
    type_price_rate.values,
    'Vehicle type + price',
    'Fraud Rate',
    'Vehicle type & price combined risk analysis'
)
# %%
