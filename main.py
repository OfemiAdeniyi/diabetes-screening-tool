from fastapi import FastAPI
from pydantic import BaseModel, Field, computed_field
from typing import Literal, Annotated
import pickle
import pandas as pd
import requests
import os

app = FastAPI()

# ===============================
# Google Drive direct download URLs
# ===============================
MODEL_URL = "https://drive.google.com/uc?id=1o0dPggLeTrdVy7dESmsvP6IDk_Q5SeGF"
THRESHOLD_URL = "https://drive.google.com/uc?id=1poS0OD5Z6lhl1pfgg1AyG_GmHGEweYu8"

MODEL_PATH = "rf_screening_model.pkl"
THRESHOLD_PATH = "screening_threshold.pkl"


def download_file(url: str, output_path: str):
    if not os.path.exists(output_path):
        response = requests.get(url)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)


# Download files once at startup
download_file(MODEL_URL, MODEL_PATH)
download_file(THRESHOLD_URL, THRESHOLD_PATH)


# Load model and threshold locally
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

with open(THRESHOLD_PATH, "rb") as f:
    threshold = pickle.load(f)


app = FastAPI()

# pydantic model to validate incoming data
class DiabetesScreeningInput(BaseModel):
    age: Annotated[float, Field(..., gt=0, lt=120, description="Age of the patient in years", examples=[45])]
    gender: Annotated[Literal["Male", "Female", "Other"], Field(..., description="Biological sex of the patient")]
    height: Annotated[float, Field(..., gt=0.5, lt=2.5, description="Height in meters", examples=[1.72])]
    weight: Annotated[float, Field(..., gt=20, lt=300, description="Weight in kilograms", examples=[75])]
    smoking_history: Annotated[Literal["never", "former", "current", "ever", "not current"], Field(..., description="Smoking history of the patient")]
    hypertension: Annotated[Literal["Yes", "No"], Field(..., description="Does the patient have hypertension?")]
    heart_disease: Annotated[Literal["Yes", "No"], Field(..., description="Does the patient have heart disease?")]


    # Computed BMI
    
    @computed_field
    @property
    def bmi(self) -> float:
        """
        Body Mass Index calculated as weight / height^2
        """
        return round(self.weight / (self.height ** 2), 2)
    
    #____Convert Yes/No to 1/0 for model #
    
    @computed_field
    @property
    def hypertension_bin(self) -> int:
        return 1 if self.hypertension == "Yes" else 0

    @computed_field
    @property
    def heart_disease_bin(self) -> int:
        return 1 if self.heart_disease == "Yes" else 0

@app.post("/screen-diabetes")
def Screen_Patient_for_Diabetes(data: DiabetesScreeningInput):

    input_df = pd.DataFrame([{
        "age": data.age,
        "gender": data.gender,
        "smoking_history": data.smoking_history,
        "bmi": data.bmi,
        "hypertension": data.hypertension_bin,
        "heart_disease": data.heart_disease_bin
    }])

    # Get probability of diabetes
    prob = model.predict_proba(input_df)[:, 1][0]

    # Apply screening threshold
    screening_result = "High Risk" if prob >= threshold else "Low Risk"

    return {
        "diabetes_risk_probability": round(float(prob), 3),
        "screening_result": screening_result,
        "screening_threshold": round(float(threshold), 3)
    }






