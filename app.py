
from flask import Flask, render_template, request, jsonify
import json
import os
import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = 'pet_data.json'

def get_default_pet():
    return {
        "name": "Fluffy",
        "species": "Floof",
        "happiness": 50,
        "health": 50,
        "hunger": 50,
        "cleanliness": 50,
        "partner1_name": "Partner 1",
        "partner2_name": "Partner 2",
        "partner1_last_action": None,
        "partner2_last_action": None,
        "partner1_streak": 0,
        "partner2_streak": 0,
        "couple_activities_completed": 0,
        "created_date": datetime.datetime.now().isoformat(),
        "last_updated": datetime.datetime.now().isoformat(),
        "action_history": []
    }

def load_pet_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        default_pet = get_default_pet()
        save_pet_data(default_pet)
        return default_pet

def save_pet_data(pet_data):
    with open(DATA_FILE, 'w') as f:
        json.dump(pet_data, f)

def update_stats_based_on_time(pet_data):
    if not pet_data.get("last_updated"):
        pet_data["last_updated"] = datetime.datetime.now().isoformat()
        return pet_data
    
    last_updated = datetime.datetime.fromisoformat(pet_data["last_updated"])
    now = datetime.datetime.now()
    hours_passed = (now - last_updated).total_seconds() / 3600
    
    if hours_passed > 3:
        decay_rate = min(hours_passed / 24 * 10, 50)
        pet_data["hunger"] = max(0, pet_data["hunger"] - decay_rate)
        pet_data["cleanliness"] = max(0, pet_data["cleanliness"] - decay_rate)
        pet_data["happiness"] = max(0, pet_data["happiness"] - decay_rate)
        
        if pet_data["hunger"] < 20 or pet_data["cleanliness"] < 20 or pet_data["happiness"] < 20:
            pet_data["health"] = max(0, pet_data["health"] - decay_rate / 2)
    
    pet_data["last_updated"] = now.isoformat()
    return pet_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pet', methods=['GET'])
def get_pet():
    pet_data = load_pet_data()
    pet_data = update_stats_based_on_time(pet_data)
    save_pet_data(pet_data)
    return jsonify(pet_data)

@app.route('/api/pet', methods=['POST'])
def update_pet():
    data = request.json
    pet_data = load_pet_data()
    
    if 'name' in data:
        pet_data['name'] = data['name']
    if 'species' in data:
        pet_data['species'] = data['species']
    if 'partner1_name' in data:
        pet_data['partner1_name'] = data['partner1_name']
    if 'partner2_name' in data:
        pet_data['partner2_name'] = data['partner2_name']
    
    pet_data["last_updated"] = datetime.datetime.now().isoformat()
    save_pet_data(pet_data)
    return jsonify(pet_data)

@app.route('/api/action', methods=['POST'])
def perform_action():
    data = request.json
    pet_data = load_pet_data()
    pet_data = update_stats_based_on_time(pet_data)
    
    action_type = data['action']
    partner = data['partner']
    
    is_couple_activity = data.get('couple_activity', False)
    
    now = datetime.datetime.now()
    last_action_key = f"{partner}_last_action"
    streak_key = f"{partner}_streak"
    
    if pet_data[last_action_key]:
        last_action_time = datetime.datetime.fromisoformat(pet_data[last_action_key])
        days_since_last_action = (now - last_action_time).days
        
        if days_since_last_action <= 1:
            pet_data[streak_key] += 1
        else:
            pet_data[streak_key] = 1
    else:
        pet_data[streak_key] = 1
    
    pet_data[last_action_key] = now.isoformat()
    
    if action_type == 'feed':
        pet_data['hunger'] = min(100, pet_data['hunger'] + 20)
        pet_data['happiness'] = min(100, pet_data['happiness'] + 5)
    elif action_type == 'clean':
        pet_data['cleanliness'] = min(100, pet_data['cleanliness'] + 20)
        pet_data['health'] = min(100, pet_data['health'] + 5)
    elif action_type == 'play':
        pet_data['happiness'] = min(100, pet_data['happiness'] + 20)
        pet_data['hunger'] = max(0, pet_data['hunger'] - 5)
    elif action_type == 'treat':
        pet_data['happiness'] = min(100, pet_data['happiness'] + 10)
        pet_data['hunger'] = min(100, pet_data['hunger'] + 5)
    elif action_type == 'cuddle':
        pet_data['happiness'] = min(100, pet_data['happiness'] + 15)
    elif action_type == 'exercise':
        pet_data['health'] = min(100, pet_data['health'] + 15)
        pet_data['hunger'] = max(0, pet_data['hunger'] - 10)
    
    if is_couple_activity:
        pet_data['couple_activities_completed'] += 1
        pet_data['happiness'] = min(100, pet_data['happiness'] + 10)
        pet_data['health'] = min(100, pet_data['health'] + 5)
    
    pet_data['action_history'].append({
        'timestamp': now.isoformat(),
        'partner': partner,
        'action': action_type,
        'couple_activity': is_couple_activity
    })
    
    if len(pet_data['action_history']) > 100:
        pet_data['action_history'] = pet_data['action_history'][-100:]
    
    if pet_data['hunger'] < 20 or pet_data['cleanliness'] < 20:
        pet_data['health'] = max(0, pet_data['health'] - 5)
    
    pet_data["last_updated"] = now.isoformat()
    save_pet_data(pet_data)
    return jsonify(pet_data)

@app.route('/api/couple-activity', methods=['POST'])
def couple_activity():
    data = request.json
    pet_data = load_pet_data()
    pet_data = update_stats_based_on_time(pet_data)
    
    activity = data['activity']
    
    now = datetime.datetime.now()
    
    pet_data['happiness'] = min(100, pet_data['happiness'] + 30)
    pet_data['health'] = min(100, pet_data['health'] + 15)
    
    if activity == 'walk':
        pet_data['health'] = min(100, pet_data['health'] + 10)
    elif activity == 'groom':
        pet_data['cleanliness'] = min(100, pet_data['cleanliness'] + 30)
    elif activity == 'train':
        pet_data['happiness'] = min(100, pet_data['happiness'] + 10)
    
    pet_data['couple_activities_completed'] += 1
    
    pet_data['action_history'].append({
        'timestamp': now.isoformat(),
        'action': f"couple_{activity}",
        'couple_activity': True
    })
    
    if len(pet_data['action_history']) > 100:
        pet_data['action_history'] = pet_data['action_history'][-100:]
    
    pet_data["last_updated"] = now.isoformat()
    save_pet_data(pet_data)
    return jsonify(pet_data)

@app.route('/api/reset', methods=['POST'])
def reset_pet():
    default_pet = get_default_pet()
    current_pet = load_pet_data()
    default_pet['partner1_name'] = current_pet.get('partner1_name', 'Partner 1')
    default_pet['partner2_name'] = current_pet.get('partner2_name', 'Partner 2')
    save_pet_data(default_pet)
    return jsonify(default_pet)

# Only needed if running locally
if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
