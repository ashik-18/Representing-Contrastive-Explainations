from flask import Flask, request, render_template, flash, redirect, url_for
import os 
import tempfile

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        reasoner = request.form.get('reasoner')
        explainer = request.form.get('explainer')
        owl = request.files.get('owlfile')
        action = request.form.get('action')

        if not owl or owl.filename == '':
            flash('No file selected!', 'error')
            return redirect(url_for('index'))
        
        tmp_dir = tempfile.gettempdir()
        owl_path = os.path.join(tmp_dir, owl.filename)
        owl.save(owl_path)

        if explainer == 'openai':
            api_key = request.form.get('openi_key')
        else:
            api_key = None 

        if action == 'generate':
            #logic to be built
            flash(f'Generated with {reasoner} and {explainer}', 'info')
        else:
            #logic to be built
            flash(f'Visualizing with {reasoner}', 'info')

        return redirect(url_for('index')) 
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)

