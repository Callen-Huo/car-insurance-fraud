USE motor_insurance;
SELECT CONNECTION_ID();

-- Fraud rate by driver rating
-- Correlated Subquery
SELECT
    d.DriverRating,
    d.claim_records,
    d.fraud_count,
    IFNULL(
        ROUND(
            d.fraud_count*100 / NULLIF(d.claim_records, 0),
            2
        ),
    0) AS fraud_rate
FROM (
    SELECT
    c.DriverRating,
    c.claim_records,
    (
        SELECT
            COUNT(*)
        FROM motor_insurance.claims AS f
        WHERE FraudFound_P = 1
        AND f.DriverRating = c.DriverRating
    ) AS fraud_count
    FROM (
        SELECT
            DriverRating,
            COUNT(*) AS claim_records
            FROM motor_insurance.claims
            GROUP BY DriverRating
    ) AS c
) AS d ORDER BY fraud_rate DESC;
-- Fraud rate by police report status
SELECT
    d.PoliceReportFiled,
    d.claim_records,
    d.fraud_counts,
    ROUND(
        fraud_counts*100 / NULLIF(claim_records, 0),
        2
    ) AS fraud_rate
FROM (
    SELECT
        c.claim_records,
        c.PoliceReportFiled,
        (
            SELECT COUNT(*)
            FROM motor_insurance.claims AS f
            WHERE FraudFound_P = 1
            AND f.PoliceReportFiled = c.PoliceReportFiled
        ) AS fraud_counts
        FROM (
            SELECT COUNT(*) AS claim_records,
            PoliceReportFiled
            FROM motor_insurance.claims
            GROUP BY PoliceReportFiled
        ) AS c
) AS d ORDER BY fraud_rate DESC;
-- Fraud rate by witness presence
-- CTE
WITH w AS(
    SELECT 
        WitnessPresent,
        COUNT(*) AS claim_records
    FROM
        motor_insurance.claims
        GROUP BY WitnessPresent
),
fc AS(
    SELECT
        WitnessPresent,
        COUNT(*) AS fraud_counts
    FROM motor_insurance.claims
        WHERE FraudFound_P = 1
        GROUP BY WitnessPresent
)
SELECT
    w.WitnessPresent,
    w.claim_records,
    IFNULL(fc.fraud_counts, 0) AS fraud_counts,
    ROUND(
        IFNULL(fc.fraud_counts, 0)*100 / NULLIF(w.claim_records, 0),
        2
    ) AS fraud_rate
FROM w LEFT JOIN fc
ON w.WitnessPresent = fc.WitnessPresent
ORDER BY fraud_rate DESC;
-- Fraud rate by previous claim history
WITH p AS(
    SELECT PastNumberOfClaims,
        COUNT(*) AS claim_records
    FROM motor_insurance.claims
        GROUP BY PastNumberOfClaims
),
fc AS(
    SELECT PastNumberOfClaims,
        COUNT(*) AS fraud_counts
    FROM motor_insurance.claims
        WHERE FraudFound_P = 1
        GROUP BY PastNumberOfClaims
)
SELECT
    p.PastNumberOfClaims,
    p.claim_records,
    IFNULL(fc.fraud_counts, 0) AS fraud_counts,
    ROUND(
        IFNULL(fc.fraud_counts, 0)*100 / NULLIF(p.claim_records, 0),
        2
    ) AS fraud_rate
FROM p LEFT JOIN fc
ON p.PastNumberOfClaims = fc.PastNumberOfClaims
ORDER BY fraud_rate DESC;
-- Fraud rate by vehicle age
WITH a AS(
    SELECT AgeOfVehicle,
        COUNT(*) AS claim_records
    FROM motor_insurance.claims
        GROUP BY AgeOfVehicle
),
fc AS(
    SELECT AgeOfVehicle,
        COUNT(*) AS fraud_counts
    FROM motor_insurance.claims
        WHERE FraudFound_P = 1
        GROUP BY AgeOfVehicle
)
SELECT
    a.AgeOfVehicle,
    a.claim_records,
    IFNULL(fc.fraud_counts, 0) AS fraud_counts,
    ROUND(
        IFNULL(fc.fraud_counts, 0)*100 / NULLIF(a.claim_records, 0),
        2
    ) AS fraud_rate
FROM a LEFT JOIN fc
ON a.AgeOfVehicle <=> fc.AgeOfVehicle
ORDER BY fraud_rate DESC, 
    fc.fraud_counts DESC;
-- Age-group segmentation using "CASE WHEN"
WITH base AS(
    SELECT
        CASE
            WHEN Age IS NULL OR Age = 0 THEN "Unknown"
            WHEN Age < 18 THEN "Dependent"
            WHEN Age BETWEEN 18 AND 24 THEN "18-24"
            WHEN Age BETWEEN 25 AND 34 THEN "25-34"
            WHEN Age BETWEEN 35 AND 44 THEN "35-44"
            WHEN Age BETWEEN 45 AND 54 THEN "45-54"
            WHEN Age BETWEEN 55 AND 64 THEN "55-64"
            ELSE "65+"
        END AS AgeGroup,
        FraudFound_P
    FROM motor_insurance.claims
),
a AS(
    SELECT
        AgeGroup,
        COUNT(*) AS claim_records
    FROM base 
    GROUP BY AgeGroup
),
fc AS(
    SELECT
        AgeGroup,
        COUNT(*) AS fraud_counts
    FROM base
    WHERE FraudFound_P = 1
    GROUP BY AgeGroup
)
SELECT
    a.AgeGroup,
    a.claim_records,
    fc.fraud_counts,
    ROUND(
        IFNULL(fc.fraud_counts, 0)*100 / NULLIF(a.claim_records, 0),
        2
    ) AS fraud_rate
FROM a LEFT JOIN fc
ON a.AgeGroup = fc.AgeGroup
ORDER BY fraud_rate DESC;
-- Combined risk-factor analysis
-- 1. Age & Sex
-- extension: ranking the claims records and fraud counts to identify higher risk categories
DROP TEMPORARY TABLE IF EXISTS age_sex_combined;
CREATE TEMPORARY TABLE age_sex_combined AS(
    WITH base AS(
        SELECT
            CASE
                WHEN Age IS NULL THEN "Unknown"
                WHEN Age < 18 THEN "Dependent"
                WHEN Age BETWEEN 18 AND 24 THEN "18-24"
                WHEN Age BETWEEN 25 AND 34 THEN "25-34"
                WHEN Age BETWEEN 35 AND 44 THEN "35-44"
                WHEN Age BETWEEN 45 AND 54 THEN "45-54"
                WHEN Age BETWEEN 55 AND 64 THEN "55-64"
                ELSE "65+"
            END AS AgeGroup,
            FraudFound_P,
            Sex
        FROM motor_insurance.claims
    ),
    a AS(
        SELECT
            AgeGroup,
            Sex,
            COUNT(*) AS claim_records
        FROM base
         GROUP BY AgeGroup, Sex
    ),
    fc AS(
        SELECT
            AgeGroup,
            Sex,
            COUNT(*) AS fraud_counts
        FROM base
        WHERE FraudFound_P = 1
        GROUP BY AgeGroup, Sex
    )
    SELECT
        a.AgeGroup,
        a.Sex,
        a.claim_records,
        COALESCE(fc.fraud_counts, 0) AS fraud_counts,
        ROUND(
            COALESCE(fc.fraud_counts, 0)*100 / NULLIF(a.claim_records, 0),
            2
        ) AS fraud_rate
    FROM a LEFT JOIN fc
        ON a.AgeGroup <=> fc.AgeGroup
        AND a.Sex <=> fc.Sex 
);
-- Window functions for fraud-risk ranking
SELECT *,
    DENSE_RANK() OVER(
        ORDER BY claim_records DESC
    ) AS claim_records_rank,
    DENSE_RANK() OVER(
        ORDER BY fraud_counts DESC
    ) AS fraud_counts_rank,
    DENSE_RANK() OVER(
        ORDER BY fraud_rate DESC
    ) AS fraud_rate_rank
FROM age_sex_combined;
-- Vehicle Type & Vehicle Price
DROP TEMPORARY TABLE IF EXISTS vehicle_type_price_combined;
CREATE TEMPORARY TABLE vehicle_type_price_combined AS(
WITH base AS(
    SELECT
        VehiclePrice,
        VehicleCategory,
        FraudFound_P
    FROM motor_insurance.claims
),
t AS(
    SELECT
        VehiclePrice,
        VehicleCategory,
        COUNT(*) AS claim_records
    FROM base
    GROUP BY VehiclePrice, VehicleCategory
),
fc AS(
    SELECT
        VehiclePrice,
        VehicleCategory,
        COUNT(*) AS fraud_counts
    FROM base
    WHERE FraudFound_P = 1
    GROUP BY VehiclePrice, VehicleCategory
)
SELECT
    t.VehiclePrice,
    t.VehicleCategory,
    t.claim_records,
    COALESCE(fc.fraud_counts, 0) AS fraud_counts,
    ROUND(
        COALESCE(fc.fraud_counts, 0)*100 / NULLIF(t.claim_records, 0),
        2
    ) AS fraud_rate
FROM t LEFT JOIN fc ON
t.VehiclePrice <=> fc.VehiclePrice AND
t.VehicleCategory <=> fc.VehicleCategory
);
-- Window functions for fraud-risk ranking
SELECT *,
    DENSE_RANK() OVER(
        ORDER BY claim_records DESC
    ) AS claim_records_rank,
    DENSE_RANK() OVER(
        ORDER BY fraud_counts DESC
    ) AS fraud_counts_rank,
    DENSE_RANK() OVER(
        ORDER BY fraud_rate DESC
    ) AS fraud_rate_rank
FROM vehicle_type_price_combined;
-- Higher-risk segment identification using Window Function
-- case 1: age_sex_combined
-- 2 measurements: 1. overall fraud rate; 2.average claim records per segment
SELECT *
FROM (
    SELECT *,
        SUM(a.fraud_counts) OVER() * 100.0
        / NULLIF(SUM(a.claim_records) OVER(), 0)
        AS Overall_fraud_rate,

        AVG(a.claim_records) OVER()
        AS Ave_claim_records

    FROM age_sex_combined AS a
) AS c
WHERE c.fraud_rate > c.Overall_fraud_rate
AND c.claim_records > c.Ave_claim_records
ORDER BY c.fraud_rate DESC;
-- case 2: vehicle_type_price_combined
-- 2 measurements: 1. overall fraud rate; 2. average claim records per segment
SELECT *
FROM (
    SELECT *,
        SUM(v.fraud_counts) OVER()*100 / NULLIF(SUM(v.claim_records) OVER(), 0) AS Overall_fraud_rate,
        AVG(v.claim_records) OVER() AS ave_claim_records
    FROM vehicle_type_price_combined AS v

) AS c
WHERE c.fraud_rate > c.Overall_fraud_rate
AND c.claim_records > c.ave_claim_records
ORDER BY fraud_Rate DESC;
