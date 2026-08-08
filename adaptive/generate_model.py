import base64
with open('assets/human_body_base_cartoon.glb', 'rb') as f1:
    b64 = base64.b64encode(f1.read()).decode()
with open('body_component/model_data.js', 'w') as f2:
    f2.write('const MODEL_B64 = "data:model/gltf-binary;base64,' + b64 + '";')
print("Done!")
