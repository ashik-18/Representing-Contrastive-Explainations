import subprocess
import zipfile

from flask import Flask, request, render_template, flash, send_file
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/run-script', methods=['POST'])
def run_script():
    reasoner = request.form.get('reasoner')
    explainer = request.form.get('explainer')
    action = request.form.get('action')

    owl_file = request.files['owl_file']
    # query_file = request.form['query_input_text']

    filename = secure_filename(owl_file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    owl_file.save(filepath)

    # todo extract fact, foil, query from query_file.
    #  Call the reasoner and generate the log file and store in the logs folder

    if explainer == 'openai':
        api_key = request.form.get('openai_key')
    else:
        api_key = ""

    if action == 'generate':
        subprocess.run(
            ['bash', '../scripts/verbaliser.sh', "../User_Interface/" + filepath, api_key],
            capture_output=True,
            text=True
        )
        flash(f'Generated with {reasoner} and {explainer}', 'info')
        output_dir = "../output/verbalizer"
    else:
        subprocess.run(
            ['bash', '../scripts/graph_representation.sh', "../User_Interface/" + filepath],
            capture_output=True,
            text=True
        )
        flash(f'Visualizing with {reasoner}', 'info')
        output_dir = "../output/graphs"

    zip_path = f"{output_dir}.zip"

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, start=output_dir)
                zipf.write(full_path, arcname)

    return send_file(zip_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
