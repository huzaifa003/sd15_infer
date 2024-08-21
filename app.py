import threading
import uuid
from flask_cors import CORS
from flask import Flask, request, jsonify
import requests
app = Flask(__name__)   
CORS(app)

# In-memory database
jobs = {}

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"pong": "pong"})
@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    data = data.get('request')
    prompts = data.get('prompt', ['Car', 'House', 'Cat'])
    negative_prompt = data.get('negative_prompt', 'Blurry, deformed, low quality, bad anatomy...')
    num_of_images = int(data.get('num_of_images', 1))
    loras = data.get('loras', [])
    guidance_scale = float(data.get('guidance_scale', 3))
    seed = int(data.get('seed', 0))
    sharpness = float(data.get('sharpness', 2.0))
    performance_selection = data.get("performance_selection", "Speed")
    webhook_url = data.get('webhook_url', 'https://obscure-fortnight-64qw6xjq5rgh45g4-5000.app.github.dev/webhook')
    job_id = str(uuid.uuid4())
    
    if not webhook_url:
        return jsonify({'error': 'webhook_url is required'}), 400
    
    jobs[job_id] = {
        'status': True,
        'status_code': 200,
        'message': "Success",
        "response": [
            {
                "job_id": job_id,
                "job_type": "Text to Image",
                "job_stage": "PENDING",
                "job_progress": 0,
                "job_status": "Started",
                "job_progress_info": {},
                "job_step_preview": '',
                "job_result": [],
            }
        ]
    }
    
    threading.Thread(target=start_job, args=(job_id, prompts, negative_prompt, num_of_images, loras, guidance_scale, seed, sharpness, performance_selection, webhook_url)).start()
    
    return jsonify({'job_id': job_id}), 200
    
def start_job(job_id, prompts, negative_prompt, num_of_images, loras, guidance_scale, seed, sharpness, performance_selection, webhook_url):

    json=                  {
            "request":{
                'prompt': prompts,
                'negative_prompt': negative_prompt,
                'num_of_images': num_of_images,
                'loras': loras,
                'guidance_scale': guidance_scale,
                'seed': seed,
                'sharpness': sharpness,
                'performance_selection': performance_selection,
                'webhook_url': webhook_url,
                'job_id': job_id,
            }
        }
    
    res = requests.post('https://api.cortex.cerebrium.ai/v4/p-bfb5eb26/sd15/predict', headers={
        'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJwcm9qZWN0SWQiOiJwLWJmYjVlYjI2IiwiaWF0IjoxNzI0MjE1ODgyLCJleHAiOjIwMzk3OTE4ODJ9.q_vaUwVr2bQ2ZEFo7r0VDa5j9xIvNFdxVe5ie8RnPO9I7lxaA-r6wba_CElkGFXmy34f55ncFxrS_r7koW3Fui7GAQXxOBXfuQnLPMX3uPdwQlvHsUYwQVZrBa1_7CZ5CRCLGT1Abl06uQOAE2FHHoo3obRRl4Gswjv7cjt2E5ZP6M0Zs1IFeduyduvBxe2ykTu5cLNok_vm5_aR2GOf2mSyFLUHMbkxCUCwuRcKDUw6qOmW9IQ9_OyYz4Urv-HPnrmf8lmCmfJaUHSMpr9XLa9wIzeHxdFh-IXeevCyAE7LsLpBGzLt-eX2_3blvQ1OVmnXi5qR3MHM9SL4cdb8Wg' 
    }, json=json
        
    )
    
    if res.status_code != 200:
        jobs[job_id] = {
            'status': False,
            'status_code': res.status_code,
            'message': res.json().get('message', 'Failed to start job'),
            'response': []
        }
        return

    response = res.json()
    
    jobs[job_id] = response
    
    
    
    
    
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(data)
    response = data.get('response')[0]
    job_id = response.get('job_id')

    jobs[job_id] = data

    print(jobs[job_id])
    
    return jsonify({'message': 'Success'}), 200

@app.route('/get_job', methods=['GET'])
def get_job():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'error': 'Job ID is required'}), 400
    
    job = jobs.get(job_id)
    if job is None:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(job), 200

