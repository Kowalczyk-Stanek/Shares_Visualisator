from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from scipy.stats import shapiro, normaltest


app = Flask(__name__)

# Wczytanie danych z pliku CSV
data = pd.read_csv('apple_stock_data.csv', parse_dates=['Date'], index_col='Date')

# Usunięcie niepotrzebnych kolumn
data.drop(['High', 'Low', 'Adj Close'], axis=1, inplace=True)

# Pobranie daty maksymalnej i minimalnej z danych
min_date = data.index.min().strftime('%Y-%m-%d')
max_date = data.index.max().strftime('%Y-%m-%d')


@app.route('/')
def index():
    return render_template('index.html', min_date=min_date, max_date=max_date)

@app.route('/plot', methods=['POST'])
def plot():
    start_date = pd.to_datetime(request.form['start_date'])
    end_date = pd.to_datetime(request.form['end_date'])
    plot_type = request.form['plot_type']

    
    # Wybór danych z wybranego zakresu dat
    selected_data = data[(data.index >= start_date) & (data.index <= end_date)]
    max_open_price = selected_data['Open'].max()
    min_open_price = selected_data['Open'].min()
    max_close_price = selected_data['Close'].max()
    min_close_price = selected_data['Close'].min()
    
    # Obliczenie średniej i odchylenia standardowego dla cen otwarcia i zamknięcia
    mean_open_price = selected_data['Open'].mean()
    std_open_price = selected_data['Open'].std()
    mean_close_price = selected_data['Close'].mean()
    std_close_price = selected_data['Close'].std()
    median_open_price = selected_data['Open'].median()
    median_close_price = selected_data['Close'].median()

    
    # Generowanie wykresu głównego (liniowego)
    plt.figure(figsize=(12, 8))

    if plot_type == 'open':
        plt.plot(selected_data['Open'], label='Cena otwarcia', color='green')
    elif plot_type == 'close':
        plt.plot(selected_data['Close'], label='Cena zamknięcia', color='blue')
    elif plot_type == 'combined':
        plt.plot(selected_data['Open'], label='Cena otwarcia', color='green')
        plt.plot(selected_data['Close'], label='Cena zamknięcia', color='blue')

    plt.title('Ceny akcji Apple')
    plt.xlabel('Data')
    plt.ylabel('Cena ($)')
    plt.legend()

    # Dodanie wykresu słupkowego (Volume)
    plt.figure(figsize=(12, 8))
    plt.bar(selected_data.index, selected_data['Volume'], color='purple', alpha=0.5)
    plt.title('Wolumen')
    plt.xlabel('Data')
    plt.ylabel('Wolumen')

    # Obliczenie dziennych zmian procentowych
    daily_returns = selected_data['Close'].pct_change() * 100
    
    # Generowanie histogramu zmian procentowych
    plt.figure(figsize=(12, 8))
    plt.hist(daily_returns.dropna(), bins=30, color='skyblue', edgecolor='black')
    plt.title('Histogram dziennych zwrotów')
    plt.xlabel('Dzieny zwrot (%)')
    plt.ylabel('Częstotliwość')

    # Dodanie scatterplotu (Open vs. Close)
    plt.figure(figsize=(12, 8))
    plt.scatter(selected_data['Open'], selected_data['Close'], 
                c=['green' if o < c else 'red' for o, c in zip(selected_data['Open'], selected_data['Close'])],
                alpha=0.7)    
    plt.title('Wykres punktowy (Otwarcie vs. Zamknięcie)')
    plt.xlabel('Cena otwarcia')
    plt.ylabel('Cena zamknięcia')


    # Zapisanie wykresów do obiektu BytesIO
    main_plot_img = BytesIO()
    plt.figure(1)  # Zapisujemy główny wykres
    plt.savefig(main_plot_img, format='png')
    main_plot_img.seek(0)
    
    volume_plot_img = BytesIO()
    plt.figure(2)  # Zapisujemy wykres słupkowy
    plt.savefig(volume_plot_img, format='png')
    volume_plot_img.seek(0)

    histogram_img = BytesIO()
    plt.figure(3)  # Zapisujemy histogram
    plt.savefig(histogram_img, format='png')
    histogram_img.seek(0)

    scatterplot_img = BytesIO()
    plt.figure(4)  # Zapisujemy scatterplot
    plt.savefig(scatterplot_img, format='png')
    scatterplot_img.seek(0)

    # Konwersja wykresów do base64, aby można było je wyświetlić w HTML
    main_plot_url = base64.b64encode(main_plot_img.getvalue()).decode()
    volume_plot_url = base64.b64encode(volume_plot_img.getvalue()).decode()
    histogram_url = base64.b64encode(histogram_img.getvalue()).decode()
    scatterplot_url = base64.b64encode(scatterplot_img.getvalue()).decode()

    plt.close('all')  # Zamknięcie wszystkich otwartych wykresów

    data_startowa=str(start_date)
    data_koncowa=str(end_date)

    return render_template('index.html', min_date=min_date, max_date=max_date, 
                           main_plot_url=main_plot_url, volume_plot_url=volume_plot_url, 
                           histogram_url=histogram_url, scatterplot_url=scatterplot_url,
                           max_open_price=max_open_price, min_open_price=min_open_price,
                           mean_open_price=mean_open_price, std_open_price=std_open_price,
                           median_open_price=median_open_price,
                           max_close_price=max_close_price, min_close_price=min_close_price,
                           mean_close_price=mean_close_price, std_close_price=std_close_price,
                           median_close_price=median_close_price, data_startowa=data_startowa, data_koncowa=data_koncowa)

if __name__ == '__main__':
    app.run(debug=True)
