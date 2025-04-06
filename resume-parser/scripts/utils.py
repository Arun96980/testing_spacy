import os
import json
from datetime import datetime

def load_config():
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'input',
        'config.json'
    )
    with open(config_path) as f:
        return json.load(f)

def save_report(report_dir, filename=None, error=None):
    report_path = os.path.join(report_dir, f"report_{datetime.now().strftime('%Y%m%d')}.log")
    
    with open(report_path, 'a') as f:
        if filename and error:
            f.write(f"[{datetime.now()}] Error processing {filename}: {error}\n")
        else:
            f.write(f"[{datetime.now()}] Processing started\n")