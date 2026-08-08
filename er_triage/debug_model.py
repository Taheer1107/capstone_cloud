import joblib
from pathlib import Path
base = Path(__file__).resolve().parent / 'triage_v3'
print('cwd', base)
for name in ['features_final.pkl','stacking_final.pkl','threshold_final.pkl']:
    print(name, (base/name).exists())
features = joblib.load(base / 'features_final.pkl')
print('features count', len(features))
print(features[:50])
model = joblib.load(base / 'stacking_final.pkl')
print('model type', type(model))
if hasattr(model, 'feature_names_in_'):
    print('feature_names_in_', getattr(model, 'feature_names_in_'))
if hasattr(model, 'classes_'):
    print('classes', model.classes_)
try:
    print('predict_proba sample shape', model.predict_proba([[0]*len(features)]).shape)
except Exception as e:
    print('predict error', repr(e))
