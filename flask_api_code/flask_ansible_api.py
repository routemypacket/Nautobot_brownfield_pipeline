
from flask import Flask, request, jsonify
import subprocess
import shlex

app = Flask(__name__)

@app.route('/run_playbook', methods=['POST'])
def run_playbook():
    playbook_path = '/mnt/c/Users/Media Server/Desktop/Nautobot work/Nautobot code/ansible_playbooks/example_playbook.yml'
    inventory_path = '/mnt/c/Users/Media Server/Desktop/Nautobot work/Nautobot code/ansible_playbooks/inventory.ini'

    try:
        command = f'ansible-playbook -i "{inventory_path}" "{playbook_path}"'
        result = subprocess.run(
            shlex.split(command),
            check=True,
            capture_output=True,
            text=True
        )
        return jsonify({
            "status": "success",
            "output": result.stdout
        })
    except subprocess.CalledProcessError as e:
        # Include both stdout and stderr in the error response for better debugging
        return jsonify({
            "status": "error",
            "error": e.stderr,
            "output": e.stdout
        }), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)