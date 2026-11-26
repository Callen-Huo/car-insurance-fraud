# Data

## File

Place the raw dataset at:

```
data/carclaims.csv
```

## Source

- Dataset name: *Vehicle Insurance Fraud Detection*
- Data file: [carclaims.csv @ Saharaxi/insurance-claims-analysis](https://github.com/Saharaxi/insurance-claims-analysis/blob/main/data/carclaims.csv)
- Original provider: Saharaxi
- Licence: not declared by the source repository. **The data file is included in this repository under `data/`** and can be used directly.

> To re-download: open the link above → click Raw / Download → save as `data/carclaims.csv`.

## Size

| Item | Value |
|---|---|
| Rows | 15,420 |
| Columns | 33 |
| Positive class (fraud) | 923 (5.99%) |

## Key fields

| Field | Type | Description |
|---|---|---|
| `FraudFound_P` | int | Target variable, 1 = fraudulent claim |
| `Fault` | category | Party at fault (policyholder / third party) |
| `VehicleCategory` | category | Vehicle type (Sedan / Sport / Utility) |
| `VehiclePrice` | category | Vehicle price band |
| `AccidentArea` | category | Area of accident (Urban / Rural) |
| `Age` | int | Claimant age (0 in the raw data is treated as missing) |
| `AgeGroup` | category | Derived by binning `Age` |
| `NumberOfSuppliments` | category | Number of supplementary claims |
| `PastNumberOfClaims` | category | Number of previous claims |

## Data processing notes

1. `Age = 0` (320 rows) is treated as missing and grouped into `AgeGroup = Unknown`.
2. The `Utility` vehicle category (391 rows) is merged into `Sedan` to avoid complete separation caused by sparse interaction cells.
3. The six `VehiclePrice` bands are collapsed into `low` / `high` for the interaction analysis.
4. `AgeGroup = Dependent` (15 rows) is merged into `Unknown`.

## Notes

- The data is historical; there is no timestamp that would allow out-of-time validation.
- If the data is subject to copyright, do not commit it to a public repository — link to the source instead.
