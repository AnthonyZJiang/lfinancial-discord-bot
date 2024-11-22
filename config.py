import json

def load_config():
    try:
        with open('config.json') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "channels_to_relay": [],
            "target_channel": 0
        }
    
def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
