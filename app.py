import os
from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# HTML form
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>VisitVisa.AI</title>
</head>
<body>
    <h2>VisitVisa.AI - Visa Success Checker</h2>
    <form method="post">
        <label for="nationality">Nationality:</label>
        <input type="text" name="nationality" value="Pakistan" required><br><br>

        <label for="residence">Country of Residence:</label>
        <input type="text" name="residence" value="Indonesia" required><br><br>

        <label for="purpose">Visa Purpose:</label>
        <input type="text" name="purpose" value="Tourism" required><br><br>

        <label for="region">Filter by Region (multi-select):</label><br>
        <select name="region" multiple size="6">
            <option value="all">All Regions</option>
            <option value="schengen">Schengen</option>
            <option value="asian">Asian</option>
            <option value="gcc">GCC</option>
            <option value="america">America</option>
            <option value="other">Other</option>
            <option value="africa">Africa</option>
            <option value="latin">Latin America</option>
        </select><br><br>

        <input type="submit" value="Find Countries">
    </form>
    {% if results %}
        <h3>Top Countries with Strong Visa Approval Rates for {{ nationality }} in {{ residence }}</h3>
        <img src="data:image/png;base64,{{ chart }}"/><br><br>
        <ol>
            {% for country in results %}
                <li><strong>{{ country['name'] }}</strong><br>
                    Visa Type: {{ country['type'] }}<br>
                    Approval Rate: {{ country['success_rate'] }}<br>
                    Notes: {{ country['note'] }}<br>
                    Apply here: <a href="{{ country['link'] }}" target="_blank">Visa Portal</a>
                </li>
            {% endfor %}
        </ol>
    {% endif %}
</body>
</html>
"""

def get_embassy_note(country_name):
    return f"Visit the official embassy website of {country_name} for details."

def get_visa_suggestions():
    countries = [
        {'name': 'Germany', 'type': 'Tourist Visa', 'success_rate': '96%', 'region': 'schengen', 'note': get_embassy_note('Germany'), 'link': 'https://jakarta.diplo.de/id-en'},
        {'name': 'France', 'type': 'Tourist Visa', 'success_rate': '94%', 'region': 'schengen', 'note': get_embassy_note('France'), 'link': 'https://id.ambafrance.org'},
        {'name': 'Spain', 'type': 'Tourist Visa', 'success_rate': '90%', 'region': 'schengen', 'note': get_embassy_note('Spain'), 'link': 'https://www.exteriores.gob.es'},
        {'name': 'Italy', 'type': 'Tourist Visa', 'success_rate': '93%', 'region': 'schengen', 'note': get_embassy_note('Italy'), 'link': 'https://vistoperitalia.esteri.it'},
        {'name': 'Japan', 'type': 'Visit Visa', 'success_rate': '80%', 'region': 'asian', 'note': get_embassy_note('Japan'), 'link': 'https://www.id.emb-japan.go.jp'},
        {'name': 'South Korea', 'type': 'Tourist Visa', 'success_rate': '78%', 'region': 'asian', 'note': get_embassy_note('South Korea'), 'link': 'https://overseas.mofa.go.kr'},
        {'name': 'Taiwan', 'type': 'Tourist Visa', 'success_rate': '75%', 'region': 'asian', 'note': get_embassy_note('Taiwan'), 'link': 'https://www.boca.gov.tw'},
        {'name': 'UAE', 'type': 'Tourist Visa', 'success_rate': '82%', 'region': 'gcc', 'note': get_embassy_note('UAE'), 'link': 'https://www.government.ae'},
        {'name': 'Qatar', 'type': 'Tourist Visa', 'success_rate': '84%', 'region': 'gcc', 'note': get_embassy_note('Qatar'), 'link': 'https://www.visitqatar.qa'},
        {'name': 'USA', 'type': 'B2 Tourist Visa', 'success_rate': '53%', 'region': 'america', 'note': get_embassy_note('USA'), 'link': 'https://www.ustraveldocs.com/id/'},
        {'name': 'Canada', 'type': 'Visitor Visa', 'success_rate': '60%', 'region': 'america', 'note': get_embassy_note('Canada'), 'link': 'https://www.canada.ca'},
        {'name': 'Brazil', 'type': 'Tourist Visa', 'success_rate': '74%', 'region': 'latin', 'note': get_embassy_note('Brazil'), 'link': 'https://www.gov.br/mre'},
        {'name': 'Argentina', 'type': 'Tourist Visa', 'success_rate': '72%', 'region': 'latin', 'note': get_embassy_note('Argentina'), 'link': 'https://www.argentina.gob.ar'},
        {'name': 'South Africa', 'type': 'Tourist Visa', 'success_rate': '70%', 'region': 'africa', 'note': get_embassy_note('South Africa'), 'link': 'http://www.dirco.gov.za'}
    ]
    return countries

def filter_by_regions(countries, selected_regions):
    if 'all' in selected_regions:
        return countries
    return [c for c in countries if c['region'] in selected_regions]

def generate_chart(countries):
    labels = [c['name'] for c in countries]
    success = [int(c['success_rate'].strip('%')) for c in countries]
    colors = ['green' if s >= 90 else 'orange' if s >= 75 else 'red' for s in success]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(labels, success, color=colors)
    ax.set_xlabel('Visa Approval Rate (%)')
    ax.set_title('Visa Approval Rates by Country')
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    chart_data = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    return chart_data

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    chart = None
    if request.method == 'POST':
        nationality = request.form['nationality']
        residence = request.form['residence']
        purpose = request.form['purpose']
        selected_regions = request.form.getlist('region')

        all_countries = get_visa_suggestions()
        results = filter_by_regions(all_countries, selected_regions)
        chart = generate_chart(results)

        return render_template_string(HTML_PAGE, results=results, nationality=nationality, residence=residence, chart=chart)
    return render_template_string(HTML_PAGE, results=None, chart=None)

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # default to 10000 if not set
    app.run(host='0.0.0.0', port=port)
