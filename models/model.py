import pandas as pd 
import joblib 
from sklearn.model_selection import train_test_split
from catboost import CatBoostClassifier

def modelinit():
    #mouse model
    mouse=pd.read_csv("datasets/mouse_movement_dataset.csv")
    mousex=mouse.drop(columns=["session_id","label"])
    mousey=mouse["label"]
    mousextrain,mousextest,mouseytrain,mouseytest=train_test_split(mousex,mousey,test_size=0.1,random_state=42,stratify=mousey) 
    model=CatBoostClassifier(iterations=500,learning_rate=0.05,depth=6,loss_function="Logloss",auto_class_weights="Balanced",random_seed=42,verbose=0,thread_count=1,allow_writing_files=False)
    model.fit(mousextrain,mouseytrain)
    joblib.dump(model,"models/mousemodel.pkl")
        
    #session model
    session=pd.read_csv("datasets/session.csv")
    sessionx=session.drop(columns=["ROBOT"])
    sessiony=session["ROBOT"]
    sessionxtrain,sessionxtest,sessionytrain,sessionytest=train_test_split(sessionx,sessiony,test_size=0.1,random_state=42,stratify=sessiony)
    sessionmodel=CatBoostClassifier(iterations=500,learning_rate=0.05,depth=6,loss_function="Logloss",auto_class_weights="Balanced",random_seed=42,verbose=0,thread_count=1,allow_writing_files=False)
    sessionmodel.fit(sessionxtrain,sessionytrain)
    joblib.dump(sessionmodel,"models/sessionmodel.pkl")
    

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
        mousemodel=joblib.load("models/mousemodel.pkl")
        pred=mousemodel.predict(data)
        if pred[0]=="bot":
            return 1
        elif pred[0]=="human":
            return 0
        
    if model=="session":
        sessionmodel=joblib.load("models/sessionmodel.pkl")
        pred=sessionmodel.predict(data)
        return int(pred[0]) 

