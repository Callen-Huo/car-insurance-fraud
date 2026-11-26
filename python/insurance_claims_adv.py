#%%
from insurance_claims_load import prepare_data
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from statsmodels.stats.proportion import proportion_confint
from statsmodels.stats.contingency_tables import Table
from scipy.stats import chi2
from sklearn.model_selection import train_test_split
import statsmodels.formula.api as smf
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    roc_auc_score,
    roc_curve,
    precision_score,
    recall_score,
    f1_score
)

claims = prepare_data()

# Output directory for figures (project-root/images)
IMG = Path(__file__).resolve().parent.parent / "images"
IMG.mkdir(exist_ok=True)


# %%
def calculate_fraud_ci(data, column, Fraud):
    if isinstance(column, str):
        column = [column]
    stats = pd.crosstab(
        [data[col] for col in column],
        data[Fraud]
    ).reindex(columns=[0, 1], fill_value=0)
    total_fraud_counts = (data[Fraud] == 1).sum()
    result = []
    #print(stats)
    for categories in stats.index:
        k = int(stats.loc[categories, 1])
        n = int(stats.loc[categories].sum())
        ci_low, ci_up = proportion_confint(
            count= k,
            nobs= n,
            alpha= 0.05,
            method= 'wilson'
        )
        if not isinstance(categories, tuple):
            categories = (categories,)
        categories_label = '|'.join(
            f"{col}={value}" for col, value in zip(column, categories)
        )
        result.append({
            'Variable':'+'.join(column),
            'Category': categories_label,
            'Fraud Count': k,
            'Total Claim': n,
            'Fraud Rate': k/n,
            'Fraud Rate Contribution': k/total_fraud_counts,
            'CI low': ci_low,
            'CI up': ci_up
        })
    return pd.DataFrame(result)

#%% chi-square
def chi_square_testing(data, columns,fraud, alpha):
    if isinstance(columns, str):
        columns = [columns]

    stats = pd.crosstab(
        [data[col] for col in columns],
        data[fraud]
    ).reindex(columns=[0, 1], fill_value=0)

    table = Table(stats.to_numpy(), shift_zeros=False)

    table_result = table.test_nominal_association()
    critical_val = chi2.ppf(
        1-alpha,
        table_result.df
    )
    #sample size of number of levels
    n = stats.to_numpy().sum()
    levels = stats.shape[0]
    #Cramer V
    r,c = stats.shape

    cramers_v = np.sqrt(
        table_result.statistic / 
        (n * min(r-1, c-1))
    )

    result = pd.DataFrame([{
        'Variable': '+'.join(columns),
        'N': n,
        'Levels': levels,
        'Chi-square': table_result.statistic,
        'p-value': table_result.pvalue,
        'Degree of Freedom': table_result.df,
        'critical value': critical_val,
        'cramer v': cramers_v,
        'Significance': table_result.pvalue < alpha
    }])
    return result

#%% calculate information value
def calculate_IV(data, columns, fraud, smoothing):
    if isinstance(columns, str):
        columns = [columns]
    stats = pd.crosstab(
        [data[col] for col in columns],
        data[fraud]
    ).reindex(columns=[0,1], fill_value= 0)

    # non-fraud distritbuion
    non_fraud_dist = (
        stats[0] + smoothing
    )/(
        stats[0].sum() + smoothing * len(stats)
    )
    # fraud distribution
    fraud_dist = (
        stats[1] + smoothing
    )/(
        stats[1].sum() + smoothing * len(stats)
    )
    # compute weight of evidence
    woe = np.log(non_fraud_dist / fraud_dist)
    # information value distribution
    iv_dist = (non_fraud_dist - fraud_dist) * woe
    categories = []
    for category in stats.index:
        if not isinstance(category, tuple):
            category = (category,)
        category_label = '|'.join(
            f"{col}={value}"
            for col, value in zip(columns, category)
        )
        categories.append(category_label)

    result = pd.DataFrame([{
        'Variable': '+'.join(columns),
        'N': stats.to_numpy().sum(),
        'Levels': len(stats),
        'Information Value': iv_dist.sum()
    }])
    result_dist = pd.DataFrame({
        'Variable':'+'.join(columns),
        'Category': categories,
        'WOE': woe.to_numpy(),
        'Non Fraud Dist': non_fraud_dist.to_numpy(),
        'Fraud Dist': fraud_dist.to_numpy(),
        'IV Distribution': iv_dist.to_numpy()
    })

    return result, result_dist
    
#%% confident interval screening
def screen_ci(data, groups, fraud = 'FraudFound_P'):
    results = []
    for group in groups:
        result = calculate_fraud_ci(
            data,
            group,
            fraud
        )
        results.append(result)
    return pd.concat(
        results,
        ignore_index= True
    )

#%% chi-square screening
def screen_chisq(data, groups, fraud = 'FraudFound_P', alpha = 0.05):
    results = []
    for group in groups:
        result = chi_square_testing(
            data,
            group,
            fraud,
            alpha
        )
        results.append(result)
    return pd.concat(
        results,
        ignore_index= True
    )

#%% information value screening
def screen_iv(data, groups, fraud = 'FraudFound_P', smoothing = 0.5):
    results,dists = [],[]

    for group in groups:
        result, dist = calculate_IV(
            data,
            group,
            fraud,
            smoothing
        )
        results.append(result)
        dists.append(dist)
    return (
        pd.concat(results, ignore_index= True),
        pd.concat(dists, ignore_index= True),
    )
#%% Confident Interval -- 95%
##Overall Fraud Rate
total_claims_count = len(claims)
total_fraud_counts = (claims['FraudFound_P'] == 1).sum()
Overall_Fraud_Rate = (
    total_fraud_counts / total_claims_count
)

ci_low, ci_up = proportion_confint(
    count = total_fraud_counts,
    nobs = total_claims_count,
    alpha = 0.05,
    method = 'wilson'
)
print(f"Overall Fraud Rate: {Overall_Fraud_Rate:.2%}")
print(f"95% Confidence Interval: [{ci_low:.2%}, {ci_up:.2%}]")

#%% grouping elements of (
# AccidentArea, DriverRating, PoliceReportFiled, 
# WitnessPresent, PastNumberOfClaims
# AgeOfVehicle, Fault)
groups = [
    'AccidentArea',
    'DriverRating',
    'PoliceReportFiled',
    'WitnessPresent',
    'PastNumberOfClaims',
    'AgeOfVehicle',
    'Fault',
    'AgeGroup',
    'Sex',
    'VehicleCategory',
    'VehiclePrice',
    ['AgeGroup','Sex'],
    ['VehicleCategory','VehiclePrice']
]

rate_columns = [
    'Fraud Rate Contribution',
    'Fraud Rate',
    'CI low',
    'CI up'
]

ci_results = screen_ci(claims, groups)
ci_results_display = ci_results.copy()
ci_results_display = ci_results_display.sort_values(
    by= ['Total Claim','Fraud Rate'],
    ascending= [False, False]
)
ci_results_display[rate_columns] = ci_results_display[rate_columns].map(
    lambda x: f"{x:.2%}"
)
print(ci_results_display.head(20))

# %% chi-square testing
chisq_results = screen_chisq(claims, groups)
chisq_results_display = chisq_results.copy()
chisq_results_display = chisq_results_display.sort_values(
    by = 'cramer v',
    ascending = False
)
chisq_results_display['p-value'] = chisq_results_display['p-value'].map(
    lambda x: f"{x:.2g}"
)
print(chisq_results_display)
# %% Information value & Information value distribution
IV_result, IV_result_dist = screen_iv(claims, groups)
IV_result_display = IV_result.copy()
IV_dist_display = IV_result_dist.copy()
IV_result_display = IV_result_display.sort_values(
    by = 'Information Value',
    ascending = False
)
IV_result_display['Information Value'] = IV_result_display['Information Value'].map(
    lambda x: f"{x:.4f}"
)
IV_dist_display = IV_dist_display.sort_values(
    by = 'IV Distribution',
    ascending = False
)
IV_dist_display['IV Distribution'] = IV_dist_display['IV Distribution'].map(
    lambda x: f"{x:.4f}"
)
print(IV_result_display)
print(IV_dist_display)
# merging IV into chi-square table
combined_chisq_iv = chisq_results.merge(
    IV_result[['Variable','Information Value']],
    on = 'Variable',
    how = 'left'
)
# merging IV distribution into CI table
combined_ci_iv = ci_results.merge(
    IV_result_dist,
    on = ['Variable', 'Category'],
    how = 'left'
)
combined_ci_iv = combined_ci_iv.merge(
    IV_result[['Variable','Information Value']],
    on = 'Variable',
    how = 'left'
)
print(combined_ci_iv)
# export csv
RESULT = Path(__file__).resolve().parent.parent / "results"
RESULT.mkdir(exist_ok=True)
combined_ci_iv.to_csv(
    RESULT / 'combined_ci_iv_analysis.csv',
    index=False,
    encoding='utf-8-sig'
)
combined_chisq_iv.to_csv(
    RESULT / 'combined_chisq_iv_analysis.csv',
    index=False,
    encoding='utf-8-sig'
)
#%% logistic regression
# category grouping
claims['VehicleCat'] = claims['VehicleCategory'].replace({'Utility': 'Sedan'})
claims['AgeGroup'] = claims['AgeGroup'].replace({'Dependent': 'Unknown'})
claims['PriceBand'] = claims['VehiclePrice'].replace({
    'less than 20000': 'low',
    '20000 to 29000': 'low',
    '30000 to 39000': 'low',
    '40000 to 59000': 'high',
    '60000 to 69000': 'high',
    'more than 69000': 'high',
})

# features for logistic regression
features = [
    'VehicleCat',
    'PriceBand',
    'Fault',
    'PastNumberOfClaims',
    'AgeGroup',
    'Sex',
    'AccidentArea',
    'NumberOfSuppliments'
    #'Days_Policy_Accident',
    #'PolicyType'
]
# response y
target = claims['FraudFound_P']
x = claims[features].copy().reset_index(drop=True)
y = target.astype(int).reset_index(drop=True)

# spliting into train set and test set
X_train, X_test, y_train, y_test = train_test_split(
    x,
    y,
    test_size= 0.3,
    stratify= y,
    random_state=42
)

train_data = X_train.copy()
train_data['FraudFound_P'] = y_train

formula = """
FraudFound_P ~ C(Fault)+
C(PastNumberOfClaims)+
C(AccidentArea)+
C(AgeGroup)+
C(Sex)+
C(VehicleCat)+
C(PriceBand)
"""
variables = {
    'Fault': 'C(Fault)',
    'PastNumberOfClaims': 'C(PastNumberOfClaims)',
    'AccidentArea': 'C(AccidentArea)',
    'AgeGroup': 'C(AgeGroup)',
    'Sex': 'C(Sex)',
    'VehicleCat': 'C(VehicleCat)',
    'PriceBand': 'C(PriceBand)',
    #'NumberOfSuppliments': 'C(NumberOfSuppliments)'
    #'Days_Policy_Accident': 'C(Days_Policy_Accident)',
    #'PolicyType': 'C(PolicyType)'
}
# %% logistic equation
# %% Logistic Regression
def fit_logistic_model(formula, fit_data):
    model = smf.logit(
        formula,
        data=fit_data
    ).fit(disp=0)

    return model

def logistic_model_df(formula, train_data, outcome, variables):

    # Interaction formulas
    formula_inter1 = formula + ' + C(VehicleCat):C(PriceBand)'
    formula_inter2 = formula_inter1 + ' + C(AgeGroup):C(Sex)'

    def create_reduced_formula(outcome, variables):
        reduced_formula = {}

        for variable in variables:
            remaining_terms = [
                term for name, term in variables.items()
                if name != variable
            ]

            reduced_formula[variable] = (
                outcome + '~' + '+'.join(remaining_terms)
            )
        return reduced_formula
    reduced_formulas = create_reduced_formula(outcome, variables)

    def create_reduced_model(formulas, data):
        reduced_models = {}
        for variable, formula in formulas.items():
            reduced_model = fit_logistic_model(formula, data)
            reduced_models[variable] = reduced_model

        return reduced_models

    # Fit models
    main_model = fit_logistic_model(formula, train_data)
    model_inter1 = fit_logistic_model(formula_inter1, train_data)
    model_inter2 = fit_logistic_model(formula_inter2, train_data)

    # Generate and fit reduced models
    reduced_models = create_reduced_model(
        reduced_formulas,
        train_data
    )

    # Extract regression results
    def extract_results(model):
        ci = model.conf_int()

        return pd.DataFrame({
            'coef': model.params,
            'OR': np.exp(model.params),
            'CI_low': np.exp(ci[0]),
            'CI_up': np.exp(ci[1]),
            'p-value': model.pvalues
        })

    res = extract_results(main_model)
    res_inter1 = extract_results(model_inter1)
    res_inter2 = extract_results(model_inter2)

    # Likelihood Ratio Test
    def lr_test(reduced_model, full_model):

        lr = 2 * (full_model.llf - reduced_model.llf)
        df = len(full_model.params) - len(reduced_model.params)
        p = chi2.sf(lr, df)

        return {
            'LR': lr,
            'DF': df,
            'p-value': p
        }

    lr_results = pd.DataFrame([
        {
            'Comparison': 'Main vs Inter1',
            **lr_test(main_model, model_inter1)
        },
        {
            'Comparison': 'Inter1 vs Inter2',
            **lr_test(model_inter1, model_inter2)
        }
    ])
    variable_lr_table = []
    for variable, reduced_model in reduced_models.items():

        variable_lr_table.append({
            'Variable': variable,
            **lr_test(reduced_model, main_model)
        })
    variable_lr_table = pd.DataFrame(variable_lr_table)

    return (
        main_model, model_inter1, model_inter2,
        res, res_inter1, res_inter2,
        lr_results, reduced_models,
        variable_lr_table
    )
# %% Logistic Regression Analysis
#expanded formulas
e_formula1 = formula + '+ C(NumberOfSuppliments)'
#expanded variables
e_variables = {
    **variables,
    'NumberOfSuppliments': 'C(NumberOfSuppliments)'
}
(
    main_model,
    model_inter1,
    model_inter2,
    res,
    res_inter1,
    res_inter2,
    lr_results,
    reduced_models,
    variable_lr_table
) = logistic_model_df(e_formula1, train_data, outcome='FraudFound_P', variables = e_variables)

# Display regression results
print(res.round(4))
print(res_inter1.round(4))
print(res_inter2.round(4))

# Display LR Test
print(lr_results.round(4))
# Display LR Table
print(variable_lr_table.round(4))
# %% ROC_AUC
auc_score = roc_auc_score(y_test, main_model.predict(X_test))
auc_score_inter = roc_auc_score(y_test, model_inter1.predict(X_test))
auc_score_inter2 = roc_auc_score(y_test, model_inter2.predict(X_test))
print(
    f"AUC score: {auc_score:.4f},\
    inter AUC score:{auc_score_inter:.4f},\
    inter2 AUC score:{auc_score_inter2:.4f}"
)
# %% k-fold cross validation
def cross_validation(X, y, formula, n_splits = 5):
    sfk = StratifiedKFold(
        n_splits = n_splits,
        shuffle = True,
        random_state = 42
    )
    # create list of oof that fill with NaN
    oof_prob = np.full(len(X), np.nan)
    fold_auc = []
    for train_idx, valid_idx in sfk.split(X, y):
        #split data
        x_train_fold = X.iloc[train_idx]
        y_train_fold = y.iloc[train_idx]
        x_valid_fold = X.iloc[valid_idx]
        y_valid_fold = y.iloc[valid_idx]

        fold_train = x_train_fold.copy()
        fold_train['FraudFound_P'] = y_train_fold.to_numpy()
        fold_model = fit_logistic_model(formula, fold_train)

        fold_prob = fold_model.predict(x_valid_fold)
        oof_prob[valid_idx] = fold_prob
        # Calculate each fold AUC
        fold_auc.append(
            roc_auc_score(y_valid_fold, fold_prob)
        )

    print(np.isnan(oof_prob).sum())
    return oof_prob, fold_auc

# %% OOF Evaluation
def evaluate_oof(y, oof_prob):

    # ROC AUC
    auc = roc_auc_score(y, oof_prob)

    fpr, tpr, roc_thresholds = roc_curve(y, oof_prob)

    # Threshold evaluation
    threshold_result = []

    for cutoff in np.arange(0.01, 0.61, 0.01):

        pred = (oof_prob >= cutoff).astype(int)

        threshold_result.append({
            'Threshold': cutoff,
            'Precision': precision_score(y, pred, zero_division=0),
            'Recall': recall_score(y, pred, zero_division=0),
            'F1': f1_score(y, pred, zero_division=0)
        })

    threshold_result = pd.DataFrame(threshold_result)

    # Select the best threshold
    best_idx = threshold_result['F1'].idxmax()
    best_threshold = threshold_result.loc[best_idx, 'Threshold']

    threshold_result = threshold_result.sort_values(
        by='F1',
        ascending=False
    )

    # Confusion Matrix
    oof_pred = (oof_prob >= best_threshold).astype(int)

    cm = confusion_matrix(y, oof_pred)
    cm = pd.DataFrame(
        cm,
        index=['Actual 0', 'Actual 1'],
        columns=['Predicted 0', 'Predicted 1']
    )

    report = classification_report(
        y,
        oof_pred,
        zero_division=0
    )

    return {
        'AUC': auc,
        'FPR': fpr,
        'TPR': tpr,
        'ROC Threshold': roc_thresholds,
        'Threshold Results': threshold_result,
        'Best Threshold': best_threshold,
        'OOF Prediction': oof_pred,
        'Confusion Matrix': cm,
        'Classification Report': report
    }
# %% ROC Curve

def plot_roc_curve(fpr, tpr, auc):

    plt.figure(figsize=(7, 6))

    plt.plot(
        fpr,
        tpr,
        label=f'ROC Curve with AUC {auc:.4f}'
    )

    plt.plot(
        [0, 1], [0, 1],
        '--',
        color='gray',
        lw=1
    )

    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('5-Fold Cross-Validated ROC Curve')

    plt.legend(loc='lower right')
    plt.grid(alpha=0.3)
    plt.tight_layout()

    plt.savefig(IMG / "roc_curve.png", dpi=150, bbox_inches="tight")

    plt.show()

    # %% Cross Validation

oof_prob, fold_auc = cross_validation(
    X_train,
    y_train,
    e_formula1
)

# %% OOF Evaluation

oof_results = evaluate_oof(
    y_train,
    oof_prob
)

# %% Display Results

print(f"Mean Fold AUC: {np.mean(fold_auc):.4f}")
print(f"Fold AUC SD: {np.std(fold_auc, ddof=1):.4f}")

print(f"OOF AUC: {oof_results['AUC']:.4f}")
print(f"Best Threshold: {oof_results['Best Threshold']:.2f}")

print(oof_results['Threshold Results'].head(10))
print(oof_results['Confusion Matrix'])
print(oof_results['Classification Report'])

# %% Plot ROC
plot_roc_curve(
    oof_results['FPR'],
    oof_results['TPR'],
    oof_results['AUC']
)

#%% Prediction
def model_prediction(model, Xtest, Ytest, threshold):
    test_prob = model.predict(Xtest)
    test_pred = (test_prob > threshold).astype(int)

    #AUC
    test_auc = roc_auc_score(Ytest, test_prob)

    # Confusion Matrix
    cm = confusion_matrix(Ytest, test_pred)
    cm = pd.DataFrame(
        cm,
        index=['Actual 0', 'Actual 1'],
        columns=['Predicted 0', 'Predicted 1']
    )

    #Classification report
    report = classification_report(
        Ytest,
        test_pred,
        zero_division=0
    )

    return {
        'AUC': test_auc,
        'Confusion Matrix': cm,
        'Classification Report': report
    }

main_model_prediction = model_prediction(
    main_model,
    X_test,
    y_test,
    oof_results['Best Threshold']
)

print("AUC:")
print(main_model_prediction['AUC'])

print("Confusion Matrix:")
print(main_model_prediction['Confusion Matrix'])

print("Classification Report:")
print(main_model_prediction['Classification Report'])

#%%