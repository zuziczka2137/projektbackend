import os
import pathlib
import google.auth.transport.requests
import mysql.connector
import requests
import paypalrestsdk
from flask import Flask, session, abort, redirect, request, render_template, jsonify, url_for
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
from datetime import timedelta, datetime, date




app = Flask("Projekt")
app.secret_key = "Backend"
app.config.from_pyfile('config.py')
# Tworzenie połączenia z bazą danych
mydb = mysql.connector.connect(
    host=app.config['DATABASE_HOST'],
    user=app.config['DATABASE_USER'],
    password=app.config['DATABASE_PASSWORD'],
    database=app.config['DATABASE_DB']
)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

paypalrestsdk.configure({
  "mode": "sandbox", 
  "client_id": "AV2VHFrD4AweTRExmC5HnS5K2G-14GhZmu9p76TtwT1OmCHOBk644QXo93th7S9BM5JyBXGOIeiko6lF",
  "client_secret": "EJCliwDj_qy4Xuv4pyI0Be315t9jRzls5zZntPm9spBoURvJ_B82_FYigRsfv2nm7_KbdKDBffiX0Cl1" })

GOOGLE_CLIENT_ID = "109643064719-bjed946gd151i14bvolkonlta3rjgpci.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper

@app.route("/rejestracja_google")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    return redirect("/protected_area")

@app.route("/wyloguj")
def logout():
    session.clear()
    return redirect("/")

@app.route('/logowanie')
def zaloguj():
    return render_template("logowanie.html")

@app.route("/")
def stronaglowna():
    return "Witaj w przychodni! <a href='/rejestracja_google'><button>Zarejestruj się za pomocą Google</button></a><a href='/rejestracja_lokalna'><button>Stwórz konto</button></a><a href='/logowanie'><button>Zaloguj się</button></a>"

@app.route("/protected_area")
@login_is_required
def protected_area():
    return render_template('rejgoogle.html')

@app.route("/zarejestrowano")
def dodano():
    return "Pomyślnie dodano użytkownika! <a href='/wyloguj'><button>Wyloguj się</button></a><a href='/zalogowano'><button>Strona główna</button></a>"

@app.route('/zalogowano')
def zalogowano():
    return f"Witaj, {session['name']} <a href='/wyloguj'><button>Wyloguj</button></a><a href='/wizyty'><button>Umów wizytę</button></a>"

@app.route("/rejestracja_lokalna")
def index():
    return render_template('index.html')

@app.route('/rejestruj', methods=['POST','GET'])
def add_user():
    name = request.form['name']
    session['name'] = name
    tel = request.form['tel']
    pesel = request.form['pesel']
    haslo = request.form['haslo']
    pesel2 = []
    pesel2.append(pesel)
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM pacjenci WHERE pesel = %s", pesel2)
    user = cursor.fetchone()
    if user:
        user = dict(zip(cursor.column_names, user))
        session['pesel'] = user['pesel']
        return "Taki użytkownik już istnieje! <a href='/'><button>Powrót</button></a>"
    else:
        sql = "INSERT INTO pacjenci (imie_nazwisko, nr_tel, pesel, hasło) VALUES (%s, %s, %s, %s)"
        val = (name, tel, pesel, haslo)
        cursor.execute(sql, val)
        mydb.commit()
        cursor.execute('SELECT id_pacjenta FROM pacjenci WHERE imie_nazwisko = %s AND nr_tel = %s AND pesel = %s AND hasło = %s', (name, tel, pesel, haslo))
        id_pacjenta = cursor.fetchone()
        session['id_pacjenta'] = id_pacjenta[0]
        return redirect("/zarejestrowano")

@app.route('/rejestrujg', methods=['POST','GET'])
def add_userg():
    name = session['name'] 
    tel = request.form['tel']
    pesel = request.form['pesel']
    haslo = request.form['haslo']
    pesel2 = []
    pesel2.append(pesel)
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM pacjenci WHERE pesel = %s", pesel2)
    user = cursor.fetchone()
    if user:
        user = dict(zip(cursor.column_names, user))
        session['pesel'] = user['pesel']
        return "Taki użytkownik już istnieje! <a href='/'><button>Powrót</button></a>"
    else:
        sql = "INSERT INTO pacjenci (imie_nazwisko, nr_tel, pesel, hasło) VALUES (%s, %s, %s, %s)"
        val = (name, tel, pesel, haslo)
        cursor.execute(sql, val)
        mydb.commit()
        cursor.execute('SELECT id_pacjenta FROM pacjenci WHERE imie_nazwisko = %s AND nr_tel = %s AND pesel = %s AND hasło = %s', (name, tel, pesel, haslo))
        id_pacjenta = cursor.fetchone()
        session['id_pacjenta'] = id_pacjenta[0]
        return redirect("/zarejestrowano")
    

@app.route('/zaloguj', methods=['POST'])
def logowanie():
    pesel = request.form['pesel']
    haslo = request.form['haslo']
    pesel2 = []
    pesel2.append(pesel)
    haslo2 = []
    haslo2.append(haslo)
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM pacjenci WHERE pesel = %s AND hasło = %s", (pesel, haslo))
    user = cursor.fetchone()
    if user:
        user = dict(zip(cursor.column_names, user))
        session['pesel'] = user['pesel']
        session['haslo'] = user['hasło']
        session['name'] = user['imie_nazwisko']
        session['id_pacjenta'] = user['id_pacjenta']
        return redirect("/zalogowano")
    
@app.route('/wizyty', methods=['GET'])
def wizyty():
    cursor = mydb.cursor()
    id_pacjenta = session['id_pacjenta']

    query = """
    SELECT wizyty.*, lekarze.imie_nazwisko
    FROM wizyty
    INNER JOIN lekarze ON wizyty.id_lekarza = lekarze.id_lekarza
    WHERE wizyty.id_pacjenta = %s
    LIMIT 20
    """
    cursor.execute(query, (id_pacjenta,))
    rekordy = cursor.fetchall()
    return render_template('wizyty.html', records=rekordy)


@app.route('/nowawizyta', methods=['GET'])
def lekarze():
    cursor = mydb.cursor()
    query = "SELECT imie_nazwisko, specjalnosc FROM lekarze"
    cursor.execute(query)
    # imiona_lekarzy = [rekord[0] for rekord in cursor.fetchall()]
    imiona_lekarzy = cursor.fetchall()
    return render_template('lekarze.html', imiona_lekarzy=imiona_lekarzy)

@app.route('/wybrany-lekarz', methods=['POST'])
def wybrany_lekarz():
    imie_lekarza = request.form['imie']
    cursor = mydb.cursor()
    query = "SELECT id_lekarza FROM lekarze WHERE imie_nazwisko = %s"
    cursor.execute(query, (imie_lekarza,))
    row = cursor.fetchone()
    session['id_lekarza']=row[0]
    return redirect('/kalendarz')

@app.route('/kalendarz',methods=['POST','GET'])
def podglad_wizyt():
    godziny = [timedelta(seconds=36000),timedelta(seconds=39600),timedelta(seconds=43200),timedelta(seconds=46800),timedelta(seconds=50400)]
    najblizsze_daty = []
    dzisiaj = date.today()
    for i in range(7):
        data = dzisiaj + timedelta(days=i)
        najblizsze_daty.append(data.strftime("%Y-%m-%d"))
    if request.method == 'POST':
        id_lekarza=session['id_lekarza']
        wybrana_data = request.form['data']
        session['wybrana_data']=wybrana_data
        cursor = mydb.cursor()
        query = "SELECT data,godzina FROM wizyty WHERE id_lekarza = %s AND data = %s"
        cursor.execute(query, (id_lekarza, wybrana_data))
        wizyty = cursor.fetchall()
        godziny_niepokrywajace = []
        if wizyty:
            for godzina in godziny:
                godzina_pokrywa_sie = False
                for krotka in wizyty:
                    _, godzina_krotki = krotka  # Rozpakowanie krotki na datę i godzinę (jeśli jest dostępna)
                    if godzina == godzina_krotki:
                        godzina_pokrywa_sie = True
                        break
                if not godzina_pokrywa_sie:
                    godziny_niepokrywajace.append(godzina)
                    

        return render_template('kalendarz.html',wizyty=wizyty, daty=najblizsze_daty, godziny=godziny_niepokrywajace,data=wybrana_data)
    else:
        return render_template('kalendarz.html', daty=najblizsze_daty)
@app.route('/rezerwacja',methods=['POST'])
def rezerwacja():
    wybrana_godzina = request.form.get('wybrana_godzina')
    session['wybrana_godzina']=wybrana_godzina
    id_lekarza = session['id_lekarza']
    wybrana_data=session['wybrana_data']
    cursor = mydb.cursor()
    query = "SELECT kwota,imie_nazwisko FROM lekarze WHERE id_lekarza = %s"
    cursor.execute(query,(id_lekarza,))
    lekarz = cursor.fetchone()
    return render_template('rezerwacja.html', wybrana_godzina=wybrana_godzina,lekarz=lekarz, wybrana_data=wybrana_data)

@app.route('/platnosc_offline')
def platnosc_off():
    wybrana_data = session['wybrana_data']
    wybrana_godzina = session['wybrana_godzina']
    id_lekarza = session['id_lekarza']
    id_pacjenta = session['id_pacjenta']
    cursor = mydb.cursor()
    cursor.execute("INSERT INTO wizyty (id_pacjenta, data, godzina, id_lekarza) VALUES (%s, %s, %s, %s) ", (id_pacjenta, wybrana_data,wybrana_godzina,id_lekarza))
    mydb.commit()
    cursor.execute("SELECT id_wizyty FROM wizyty WHERE id_pacjenta = %s AND data = %s AND godzina = %s AND id_lekarza = %s",(id_pacjenta, wybrana_data,wybrana_godzina,id_lekarza))
    id_wizyty = cursor.fetchone()
    cursor.execute("INSERT INTO platnosci (rodzaj_platnosci, id_wizyty) VALUES (%s, %s)", ("offline",id_wizyty[0]))
    mydb.commit()
    return "Wizyta została potwierdzona<a href='/zalogowano'><button>Powrót do konta</button></a>"

@app.route('/platnosc')
def platnosc():
    return render_template('platnosc.html')

@app.route('/payment', methods=['POST'])
def payment():
    cursor = mydb.cursor()
    id_lekarza = session['id_lekarza']
    cursor.execute("SELECT kwota from lekarze WHERE id_lekarza = %s",(id_lekarza,))
    cena = cursor.fetchone()
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "http://localhost:5000/payment/execute",
            "cancel_url": "http://localhost:5000/kalendarz"},
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": "wizyta",
                    "sku": "12345",
                    "price": str(cena[0]),
                    "currency": "PLN",
                    "quantity": 1}]},
            "amount": {
                "total": str(cena[0]),
                "currency": "PLN"},
            "description":"Opłata"}]})

    if payment.create():
        print('Opłacono')
    else:
        print(payment.error)
    return jsonify({'paymentID' : payment.id})

@app.route('/execute', methods=['POST'])
def execute():
    success = False
    payment = paypalrestsdk.Payment.find(request.form['paymentID'])
    if payment.execute({'payer_id' : request.form['payerID']}):
        success = True
    else:
        print(payment.error)
    if success:
        wybrana_data = session['wybrana_data']
        wybrana_godzina = session['wybrana_godzina']
        id_lekarza = session['id_lekarza']
        id_pacjenta = session['id_pacjenta']
        cursor = mydb.cursor()
        cursor.execute("INSERT INTO wizyty (id_pacjenta, data, godzina, id_lekarza) VALUES (%s, %s, %s, %s) ", (id_pacjenta, wybrana_data,wybrana_godzina,id_lekarza))
        mydb.commit()
        cursor.execute("SELECT id_wizyty FROM wizyty WHERE id_pacjenta = %s AND data = %s AND godzina = %s AND id_lekarza = %s",(id_pacjenta, wybrana_data,wybrana_godzina,id_lekarza))
        id_wizyty = cursor.fetchone()
        cursor.execute("INSERT INTO platnosci (rodzaj_platnosci, id_wizyty) VALUES (%s, %s)", ("online",id_wizyty[0]))
        mydb.commit()
        return redirect(url_for('potwierdzenie'))
    else:
        return "Błąd podczas płatności<a href='/zalogowano'><button>Powrót do konta</button></a>"

@app.route('/potwierdzenie')
def potwierdzenie():
    return "Wizyta potwierdzona<a href='/zalogowano'><button>Powrót do konta</button></a>"
if __name__ == "__main__":
    app.run(debug=True)