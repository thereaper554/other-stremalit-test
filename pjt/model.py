
def load_models(model_dir: str = "models"):
    risk_model = joblib.load(f"{model_dir}/risk_model.joblib")
    reg_model = joblib.load(f"{model_dir}/reg_model.joblib")
    return risk_model, reg_model

def infer(risk_model, reg_model, features_df: pd.DataFrame):
    prisk = risk_model.predict(features_df)
    prem = reg_model.predict(features_df)

    return prisk, prem
