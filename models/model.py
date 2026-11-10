from pathlib import Path

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from catboost import CatBoostClassifier

MODEL_DIR = Path(__file__).resolve().parent / "models"
DATASET_DIR = Path(__file__).resolve().parent / "datasets"
# Keep this order aligned with the mouse CSV/model schema; CatBoost receives
# one named row per browser session rather than individual pointer events.
MOUSE_FEATURES = [
    "mouse_event_count", "total_distance", "average_distance_per_move",
    "average_speed", "max_speed", "direction_changes", "average_time_gap",
    "pause_count", "left_clicks", "right_clicks", "middle_clicks",
]

def modelinit():
    #mouse model
    mouse=pd.read_csv(DATASET_DIR / "mouse_movement_dataset.csv")
    mousex=mouse.drop(columns=["session_id","label"])
    mousey=mouse["label"]
    mousextrain,mousextest,mouseytrain,mouseytest=train_test_split(mousex,mousey,test_size=0.1,random_state=42,stratify=mousey) 
    model=CatBoostClassifier(iterations=500,learning_rate=0.05,depth=6,loss_function="Logloss",auto_class_weights="Balanced",random_seed=42,verbose=0,thread_count=1,allow_writing_files=False)
    model.fit(mousextrain,mouseytrain)
    joblib.dump(model, MODEL_DIR / "mousemodel.pkl")
        
    #session model
    session=pd.read_csv(DATASET_DIR / "session.csv")
    sessionx=session.drop(columns=["ROBOT"])
    sessiony=session["ROBOT"]
    sessionxtrain,sessionxtest,sessionytrain,sessionytest=train_test_split(sessionx,sessiony,test_size=0.1,random_state=42,stratify=sessiony)
    sessionmodel=CatBoostClassifier(iterations=500,learning_rate=0.05,depth=6,loss_function="Logloss",auto_class_weights="Balanced",random_seed=42,verbose=0,thread_count=1,allow_writing_files=False)
    sessionmodel.fit(sessionxtrain,sessionytrain)
    joblib.dump(sessionmodel, MODEL_DIR / "sessionmodel.pkl")
    

def modeltrain(data,model):
    if model=="mouse":
        model=joblib.load("models/mousemodel.pkl")
        model.fit(data[xtrain],data[ytrain]) 
        joblib.dump(model,"models/mousemodel.pkl")
    if model=="session":
        model=joblib.load("models/sessionmodel.pkl")
        model.fit(data[xtrain],data[ytrain])
        joblib.dump(model,"models/sessionmodel.pkl")
    
def modelpredict(data,model):
    if model=="mouse":
        mousemodel=joblib.load(MODEL_DIR / "mousemodel.pkl")
        # Browser JSON is a dict, while CatBoost expects a table. Reindexing
        # also makes request key order irrelevant and exposes missing fields.
        frame = pd.DataFrame([data]) if isinstance(data, dict) else pd.DataFrame(data)
        frame = frame.reindex(columns=MOUSE_FEATURES)
        if frame.isnull().any().any():
            raise ValueError("Mouse features must include all 11 numeric model fields")
        # The rest of the mitigation code treats layer outputs as risk scores;
        # use the bot probability instead of throwing away confidence as 0/1.
        probabilities = mousemodel.predict_proba(frame)[0]
        classes = [str(label).lower() for label in mousemodel.classes_]
        if "bot" not in classes:
            raise ValueError("Mouse model has no 'bot' class")
        return float(probabilities[classes.index("bot")])
        
    if model=="session":
        sessionmodel=joblib.load(MODEL_DIR / "sessionmodel.pkl")
        frame = pd.DataFrame([data]) if isinstance(data, dict) else pd.DataFrame(data)
        frame = frame.reindex(columns=sessionmodel.feature_names_)
        if frame.isnull().any().any():
            raise ValueError("HTTP features do not match the session model schema")
        pred=sessionmodel.predict(frame)
        return int(pred[0]) 

