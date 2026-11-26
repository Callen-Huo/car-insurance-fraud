CREATE DATABASE IF NOT EXISTS motor_insurance;
USE motor_insurance;
SELECT CONNECTION_ID();
CREATE TABLE IF NOT EXISTS claims(
    Month VARCHAR(3),
    WeekOfMonth INT,
    DayOfWeek VARCHAR(10),
    Make VARCHAR(10),
    AccidentArea ENUM("Urban","Rural") NOT NULL,
    DayOfWeekClaimed VARCHAR(20),
    MonthClaimed VARCHAR(3),
    WeekOfMonthClaimed INT,
    Sex ENUM("Male","Female") NOT NULL,
    MaritalStatus ENUM("Single","Married","Divorced","Widow") NOT NULL,
    Age INT,
    Fault VARCHAR(20),
    PolicyType VARCHAR(20),
    VehicleCategory VARCHAR(10),
    VehiclePrice VARCHAR(20),
    FraudFound_P INT,
    PolicyNumber INT AUTO_INCREMENT,
    RepNumber INT,
    Deductible INT,
    DriverRating INT,
    Days_Policy_Accident VARCHAR(20),
    Days_Policy_Claim VARCHAR(20),
    PastNumberOfClaims VARCHAR(20),
    AgeOfVehicle VARCHAR(20),
    AgeOfPolicyHolder VARCHAR(20),
    PoliceReportFiled ENUM("Yes","No"),
    WitnessPresent ENUM("Yes","No"),
    AgentType ENUM("External","Internal"),
    NumberOfSuppliments VARCHAR(20),
    AddressChange_Claim VARCHAR(20),
    NumberOfCars VARCHAR(20),
    Year YEAR NOT NULL,
    BasePolicy VARCHAR(10),
    PRIMARY KEY(PolicyNumber)
);

SELECT * FROM claims;
DESC claims;
SET SESSION group_concat_max_len = 1000000;
-- Generate dynamic SQL
-- to check existing NULL values for all columns
SELECT CONCAT(
    'SELECT ',
    GROUP_CONCAT(
        CONCAT(
            'SUM(`', COLUMN_NAME, '`IS NULL) AS`',
            COLUMN_NAME,
            '_NULL`'
        )
        ORDER BY ORDINAL_POSITION
        SEPARATOR ','
    ),
    ' FROM `motor_insurance`.`claims`'
)
INTO @sql
FROM information_schema.COLUMNS
WHERE table_schema = 'motor_insurance' AND
table_name = 'claims';
SELECT @sql;
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
-- Total claim counts
SELECT 
    COUNT(*) AS total_record,
    COUNT(PolicyNumber)
FROM claims;
-- Claims by fault status
SELECT
    COUNT(*) AS fraud_record
FROM motor_insurance.claims AS c
    WHERE c.FraudFound_P = 1;
-- Overall Fraud Rate 
SELECT
    c.claim_records,
    c.fraud_records,
    ROUND(
        c.fraud_records * 100 / c.claim_records,
        2
    ) AS fraud_rate
FROM (
    SELECT
        COUNT(*) AS claim_records,
        (
            SELECT COUNT(*)
            FROM motor_insurance.claims
            WHERE FraudFound_P = 1
        ) AS fraud_records
    FROM motor_insurance.claims
) AS c;
-- Fraud rate by fault status
SELECT
    c.claim_records,
    c.fault_fraud_records,
    ROUND(
        c.fault_fraud_records * 100 / c.claim_records,
        2
    ) AS fraud_rate
FROM (
    SELECT
        COUNT(*) AS claim_records,
        (
            SELECT COUNT(*)
            FROM motor_insurance.claims
            WHERE FraudFound_P = 1 AND
            Fault LIKE "%Policy Holder%"
        ) AS fault_fraud_records
    FROM motor_insurance.claims
) AS c;

-- Fraud rate by accident area
SELECT
    c.urban_claim_records,
    c.rural_claim_records,
    c.urban_fraud,
    c.rural_fraud,
    CONCAT(ROUND(
        c.urban_fraud*100 / c.urban_claim_records, 2
    ), "%") AS urban_fraud_rate,
    CONCAT(ROUND(
        c.rural_fraud*100 / c.rural_claim_records, 2
    ), "%" )AS rural_fraud_rate
FROM (
    SELECT COUNT(*) AS urban_claim_records,
    (
        SELECT COUNT(*)
        FROM motor_insurance.claims
        WHERE AccidentArea LIKE "%Rural%"
    ) AS rural_claim_records,
    (
        SELECT COUNT(*)
        FROM motor_insurance.claims
        WHERE FraudFound_P = 1 AND
        AccidentArea LIKE "%Urban%"
    ) AS urban_fraud,
    (
        SELECT COUNT(*)
        FROM motor_insurance.claims
        WHERE FraudFound_P = 1 AND
        AccidentArea LIKE "%Rural%"
    ) AS rural_fraud
    FROM motor_insurance.claims
    WHERE AccidentArea LIKE "%Urban%"
) AS c;

-- Fraud rate by vehicle category(cte)
WITH claim_records AS(
    SELECT VehicleCategory,
    COUNT(*) AS total_claim_records
    FROM motor_insurance.claims
    GROUP BY VehicleCategory
),
fraud_counts AS (
    SELECT VehicleCategory,
    COUNT(*) AS fraud_recordsBy_cartype
    FROM motor_insurance.claims
    WHERE FraudFound_P = 1
    GROUP BY VehicleCategory
)
SELECT c.VehicleCategory,
    c.total_claim_records AS claim_records,
    COALESCE(f.fraud_recordsby_cartype, 0 ) AS fraud_records,
    ROUND(
        f.fraud_recordsBy_cartype *100/ c.total_claim_records,
        2
    ) AS fraud_rate
FROM claim_records AS c LEFT JOIN fraud_counts AS f
ON c.VehicleCategory = f.VehicleCategory;
-- Fraud rate by policy type
WITH Policy_Type AS (
    SELECT PolicyType,
    COUNT(*) AS policytype_counts
    FROM motor_insurance.claims
    GROUP BY PolicyType
),
policytype_fraud AS (
    SELECT PolicyType,
    COUNT(*) AS policytype_fraud
    FROM motor_insurance.claims
    WHERE FraudFound_P = 1
    GROUP BY PolicyType
)

SELECT 
    p.PolicyType,
    p.policytype_counts,
    COALESCE(pf.policytype_fraud, 0) AS policytype_fraud,
    IFNULL(
        ROUND(
            pf.policytype_fraud*100 / NULLIF(p.policytype_counts, 0),
            2
        ),
    0) AS fraud_rate
FROM Policy_Type AS p LEFT JOIN policytype_fraud AS pf
ON p.PolicyType = pf.PolicyType;
-- Claims by vehicle make
SELECT
    Make,
    COUNT(*) AS claim_records
FROM motor_insurance.claims 
GROUP BY Make;
-- Average claimant age
SELECT 
    ROUND(AVG(Age)) AS average_Age
FROM motor_insurance.claims;




