# SQL Scripts

## Prerequisites

The scripts assume that the `motor_insurance.claims` table already exists and that
the 15,420 records from `data/carclaims.csv` have been loaded into it.

The schema is defined at the top of `01_schema.sql`. To load the data you can use the
MySQL Workbench import wizard, or `LOAD DATA LOCAL INFILE` (both the client and the
server must allow local infile loading).

## Order

1. `01_schema.sql` — schema creation, field audit, basic dimensional fraud rates
2. `02_advanced_queries.sql` — CTEs, window functions, correlated subqueries

## Running

```bash
mysql -u <user> -p < sql/01_schema.sql
mysql -u <user> -p < sql/02_advanced_queries.sql
```
