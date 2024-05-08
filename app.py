from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from io import BytesIO
import base64

app = Flask(__name__)

# Wczytanie danych z pliku CSV
data = pd.read_csv('apple_stock_data.csv', parse_dates=['Date'], index_col='Date')

# Usunięcie niepotrzebnych kolumn
data.drop(['High', 'Low', 'Adj Close'], axis=1, inplace=True)

# Pobranie daty maksymalnej i minimalnej z danych
min_date = data.index.min().strftime('%Y-%m-%d')
max_date = data.index.max().strftime('%Y-%m-%d')
exchange_rate_usd_to_pln = 4.02

@app.route('/')
def index():
    return render_template('index.html', min_date=min_date, max_date=max_date)

@app.route('/plot', methods=['POST'])
def plot():
    start_date = pd.to_datetime(request.form['start_date'])
    end_date = pd.to_datetime(request.form['end_date'])
    plot_type = request.form['plot_type']
    convert_to_pln = 'convert_to_pln' in request.form
    
    # Wybór danych z wybranego zakresu dat
    selected_data = data[(data.index >= start_date) & (data.index <= end_date)]
    
    # Konwersja cen na PLN, jeśli wybrano opcję
    if convert_to_pln:
        selected_data['Open'] *= exchange_rate_usd_to_pln
        selected_data['Close'] *= exchange_rate_usd_to_pln
    
    # Generowanie wykresu głównego (liniowego)
    plt.figure(figsize=(12, 8))

    if plot_type == 'open':
        plt.plot(selected_data['Open'], label='Cena otwarcia', color='green')
        prices = selected_data['Open']
    elif plot_type == 'close':
        plt.plot(selected_data['Close'], label='Cena zamknięcia', color='blue')
        prices = selected_data['Close']
    elif plot_type == 'combined':
        plt.plot(selected_data['Open'], label='Cena otwarcia', color='green')
        plt.plot(selected_data['Close'], label='Cena zamknięcia', color='blue')
        prices = selected_data[['Open', 'Close']].stack()

    plt.title('Ceny akcji Apple')
    plt.xlabel('Data')
    plt.ylabel('Cena ({})'.format('PLN' if convert_to_pln else '$'))
    plt.legend()

    # Dodanie wykresu słupkowego (Volume)
    plt.figure(figsize=(12, 4))
    plt.bar(selected_data.index, selected_data['Volume'], color='purple', alpha=0.5)
    plt.title('Wolumen')
    plt.xlabel('Data')
    plt.ylabel('Wolumen')

    # Obliczenie dziennych zmian procentowych
    daily_returns = selected_data['Close'].pct_change() * 100
    
    # Generowanie histogramu zmian procentowych
    plt.figure(figsize=(10, 6))
    plt.hist(daily_returns.dropna(), bins=30, color='skyblue', edgecolor='black')
    plt.title('Histogram dziennych zwrotów')
    plt.xlabel('Dzieny zwrot (%)')
    plt.ylabel('Częstotliwość')

    # Dodanie scatterplotu (Open vs. Close)
    plt.figure(figsize=(10, 6))
    plt.scatter(selected_data['Open'], selected_data['Close'], color='orange', alpha=0.7)
    plt.title('Wykres punktowy (Otwarcie vs. Zamknięcie)')
    plt.xlabel('Cena otwarcia')
    plt.ylabel('Cena zamknięcia')

    # Generowanie wykresu gęstości (KDE)
    plt.figure(figsize=(10, 6))
    sns.kdeplot(prices, shade=True, color='magenta')
    plt.title('Kernel Density Estimation (KDE)')
    plt.xlabel('Ceny')
    plt.ylabel('Gęstość')

    # Obliczenie podstawowych statystyk
    basic_stats = prices.describe().to_frame().reset_index()
    basic_stats.columns = ['Rodzaj', 'Wartość']
    print(basic_stats)

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

    kde_img = BytesIO()
    plt.figure(5)  # Zapisujemy wykres gęstości (KDE)
    plt.savefig(kde_img, format='png')
    kde_img.seek(0)

    # Konwersja wykresów do base64, aby można było je wyświetlić w HTML
    main_plot_url = base64.b64encode(main_plot_img.getvalue()).decode()
    volume_plot_url = base64.b64encode(volume_plot_img.getvalue()).decode()
    histogram_url = base64.b64encode(histogram_img.getvalue()).decode()
    scatterplot_url = base64.b64encode(scatterplot_img.getvalue()).decode()
    kde_url = base64.b64encode(kde_img.getvalue()).decode()

    plt.close('all')  # Zamknięcie wszystkich otwartych wykresów

    return render_template('index.html', min_date=min_date, max_date=max_date, 
                           main_plot_url=main_plot_url, volume_plot_url=volume_plot_url, 
                           histogram_url=histogram_url, scatterplot_url=scatterplot_url,
                           kde_url=kde_url, basic_stats=basic_stats.to_html(index=False))

if __name__ == '__main__':
    app.run(debug=True)
