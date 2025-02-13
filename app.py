# sekcja importowa
import os
import boto3
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO
from dotenv import load_dotenv

# Globalne ustawianie szerokosci
st.set_page_config(layout="wide") 

# ---------------- DEFINICJA ZMIENNYCH GLOBALNYCH: ---------------

patterns = {
    'Osiągnięcia': ['17.', '32.', '48.'],
    'Hedonizm': ['3.', '36.', '46.'],
    'Stymulacja': ['10.', '28.', '43.'],
    'Kierowanie sobą w działaniu': ['16.', '30.', '56.'],
    'Kierowanie sobą w myśleniu': ['1.', '23.', '39.'],
    'Tolerancja': ['14.', '34.', '57.'],
    'Uniwersalizm ekologiczny': ['8.', '21.', '45.'],
    'Uniwersalizm społeczny': ['5.', '37.', '52.'],
    'Życzliwość-troskliwość': ['11.', '25.', '47.'],
    'Życzliwość-niezawodność': ['19.', '27.', '55.'],
    'Pokora': ['7.', '38.', '54.'],
    'Przystosowanie do ludzi': ['4.', '22.', '51.'],
    'Przystosowanie do reguł': ['15.', '31.', '42.'],
    'Tradycja': ['18.', '33.', '40.'],
    'Bezpieczeństwo społeczne': ['2.', '35.', '50.'],
    'Bezpieczeństwo osobiste': ['13.', '26.', '53.'],
    'Prestiż': ['9.', '24.', '49.'],
    'Władza nad zasobami': ['12.', '20.', '44.'],
    'Władza nad ludźmi': ['6.', '29.', '41.'],
}

# ----------------------------- FUNKCJE: -----------------------------------


def wczytaj_dataframe(nazwa_pliku):
    try:
        obj_data = s3.get_object(Bucket=BUCKET_NAME, Key=nazwa_pliku)
        data = obj_data['Body'].read()
        df = pd.read_csv(BytesIO(data), sep=';', encoding='utf-8')

        return df
    except Exception as e:
        st.write(f"❌ Błąd wczytywania pliku {nazwa_pliku}: {str(e)}")
        return None


def oblicz_srednie_kategorii(df):

    df_kopia = df.copy()
    for nazwa_kategorii, lista_numerow in patterns.items():
        kolumny_pasujace = [kolumna for kolumna in df_kopia.columns if any(kolumna.startswith(numer) for numer in lista_numerow)]
        if len(kolumny_pasujace) == 3:
            df_kopia[nazwa_kategorii] = df_kopia[kolumny_pasujace].mean(axis=1)

    return df_kopia


# ----------------------------- APLIKACJA: -----------------------------------

# Ustawienie początkowych wartości w session_state
if 'df_przetworzone' not in st.session_state:
    st.session_state.df_przetworzone = None

if 'dane_pobrane' not in st.session_state:
    st.session_state.dane_pobrane = False
    st.session_state.df = None
    st.session_state.srednie_df = None

# Tytuł aplikacji
st.markdown("<h1 style='text-align: center;'>Aplikacja do rysowania wykresów dla Kompasu Przekonań</h1>", unsafe_allow_html=True)

# Tekst powitalny
st.write('Witaj w naszej pierwszej wersji aplikacji do rysowania wykresów. Naciśnij poniższy przycisk, aby pobrać dane.')

# Przycisk do pobrania danych
if st.button("Pobierz dane"):
    if not st.session_state.dane_pobrane:
        load_dotenv()
        BUCKET_NAME = 'od-zera-do-ai-rafal'

        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            endpoint_url=os.getenv("AWS_ENDPOINT_URL_S3")
        )

        try:
            s3.head_bucket(Bucket=BUCKET_NAME)
            st.write('✅ Połączenie z Digital Ocean działa poprawnie.')

            st.write("Pobieranie danych z bucketu...")
            df = wczytaj_dataframe('kompas_dane.csv')

            if df is not None:
                df_kopia = df.copy()

                # Przetwarzanie danych
                for nazwa_kategorii, numery_pytan in patterns.items():
                    kolumny_pasujace = []

                    for numer in numery_pytan:
                        # Szukamy dokładnego dopasowania początku nazwy kolumny
                        for kolumna in df_kopia.columns:
                            if kolumna.startswith(numer):
                                kolumny_pasujace.append(kolumna)
                                break  # Przechodzimy do następnego numeru po znalezieniu dopasowania

                    if len(kolumny_pasujace) == 3:
                        df_kopia[nazwa_kategorii] = df_kopia[kolumny_pasujace].mean(axis=1)
                    else:
                        st.write(f"ERROR! Znalezione kolumny: {kolumny_pasujace}")

                st.session_state.df_przetworzone = df_kopia
                st.session_state.srednie_df = wczytaj_dataframe('kompas_srednie_dane.csv')
                st.session_state.dane_pobrane = True

        except Exception as e:
            st.write(f"❌ Błąd połączenia: {str(e)}")

# Jeśli dane są załadowane, pokazujemy wybór wiersza i przycisk do generowania wykresów
if st.session_state.dane_pobrane:
    wiersz = st.number_input("Wybierz numer wiersza", min_value=1, max_value=len(st.session_state.df_przetworzone), value=len(st.session_state.df_przetworzone))

    if st.button("Zatwierdź wiersz"):
        if st.session_state.df_przetworzone is None:
            st.error("Dane nie zostały jeszcze przetworzone!")
        else:
            # Sprawdzamy, czy wszystkie kategorie istnieją
            missing_categories = [cat for cat in patterns.keys() if cat not in st.session_state.df_przetworzone.columns]
            if missing_categories:
                st.error(f"Brakujące kategorie: {missing_categories}")
                st.write("\nDostępne kolumny:")
                st.write(st.session_state.df_przetworzone.columns.tolist())
            else:
                names = list(patterns.keys())
                values = [st.session_state.df_przetworzone[nazwa_kategorii].iloc[wiersz-1] for nazwa_kategorii in names]

        # Rysowanie pierwszego wykresu (kołowego)
        names = list(patterns.keys())
        values = [st.session_state.df_przetworzone[nazwa_kategorii].iloc[wiersz-1] for nazwa_kategorii in names]

        # ------------------------ WYKRES w NAGRODE -----------------------------

        # Create figure dla pierwszego wykresu
        fig_kolowy = plt.figure(figsize=(8, 8))
        ax = fig_kolowy.add_subplot(111, projection='polar')

        plt.rcParams['font.family'] = 'DejaVu Sans'  # lub 'Liberation Sans'

        # KOLORY
        colors = ['#d6018d', '#8511fe', '#0143fe', '#2a8cff', '#02d6e6', '#02f873', '#06de2d', '#01bd23', '#009c20', '#0c7210', '#9c9b01', '#dede01', '#efee02', '#fadd4c', '#f4a302', '#e08b09', '#fd4238', '#de0800', '#b9130c']

        # Calculate angles for each slice
        angles = np.linspace(0, 2*np.pi, len(values), endpoint=False)

        # Width of each bar (with gap)
        width = (2*np.pi) / len(values) * 0.9

        # Plot bars
        bars = ax.bar(angles, values, width=width, bottom=0.0, alpha=0.85)

        # Color each bar
        for bar, color in zip(bars, colors):
            bar.set_facecolor(color)

        # Add outer color bands
        outer_height = 0.33  # Height of the outer band (1/3 of the space between 6 and 7)
        outer_bars = ax.bar(angles, [outer_height] * len(values), width=width, bottom=6.67, alpha=0.85)

        # Color outer bars
        for outer_bar, color in zip(outer_bars, colors):
            outer_bar.set_facecolor(color)

        # Add thin circular grid lines (every 0.1)
        theta = np.linspace(0, 2*np.pi, 200)
        for r in np.arange(1.1, 6.0, 0.1):
            if r not in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]:  # Skip the positions where thick lines will be
                ax.plot(theta, [r]*len(theta), color='black', alpha=0.3, linewidth=0.5)

        # Add thick circular lines at main positions
        for r in [0.75, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]:
            ax.plot(theta, [r]*len(theta), color='black', linewidth=1.0)

        # Define pairs between which thick lines should be drawn
        thick_lines_between = [
            ('Osiągnięcia', 'Hedonizm'),
            ('Hedonizm', 'Stymulacja'),
            ('Kierowanie sobą w myśleniu', 'Tolerancja'),
            ('Życzliwość-niezawodność', 'Pokora'),
            ('Pokora', 'Przystosowanie do ludzi'),
            ('Przystosowanie do reguł', 'Tradycja'),
            ('Tradycja', 'Bezpieczeństwo społeczne'),
            ('Bezpieczeństwo osobiste', 'Prestiż'),
            ('Prestiż', 'Władza nad zasobami'),
            ('Władza nad ludźmi', 'Osiągnięcia')
        ]

        # Add radial lines between slices
        for i, angle in enumerate(angles):
            line_angle = angle + (2*np.pi)/(len(values)*2)
            current_value = names[i]
            next_value = names[(i+1) % len(names)]

            # Check if this pair should have a thick line
            is_thick = (current_value, next_value) in thick_lines_between or (next_value, current_value) in thick_lines_between

            # Draw the line with appropriate thickness
            linewidth = 1.5 if is_thick else 0.25  # Grubsze linie 1.5, cieńsze 0.25
            ax.plot([line_angle, line_angle], [0, 7], 'k-', linewidth=linewidth)

        # Customize the chart
        ax.set_theta_zero_location('E')  # Start at 3 o'clock
        ax.set_theta_direction(1)  # Counter-clockwise
        ax.set_rlim(0, 7.0)  # Extend limit to accommodate labels

        # Remove default grid
        ax.grid(False)
        ax.set_rticks([])  # Remove radial ticks
        ax.set_xticks([])  # Remove angular ticks

        # Add a white circle in the center
        center_circle = plt.Circle((0, 0), 0.75, transform=ax.transData._b, color='white', zorder=3)
        ax.add_artist(center_circle)

        plt.title('Radial Chart of Values', pad=20, size=14)
        plt.tight_layout()

        # Add curved text labels
        for idx, (angle, name) in enumerate(zip(angles, names)):
            # Calculate the middle angle of the bar
            middle_angle = angle

            # Convert angle to degrees for text rotation
            angle_deg = np.rad2deg(middle_angle)

            # Adjust text alignment based on position
            if 0 <= angle_deg <= 180:  # górny prawy kwadrant
                rotation = angle_deg - 90
            else:  # dolna połowa
                rotation = angle_deg + 90

            # Split long names into two lines
            if len(name) > 12:
                split_point = name.find('-') if '-' in name else len(name)//2
                if '-' in name:
                    name = name.replace('-', '\n')
                else:
                    words = name.split()
                    if len(words) > 1:
                        mid = len(words) // 2
                        name = ' '.join(words[:mid]) + '\n' + ' '.join(words[mid:])
                    else:
                        name = name[:split_point] + '\n' + name[split_point:]

            # Add the text
            ax.text(middle_angle, 6.3, name,
                    ha='center', va='center',
                    rotation=rotation,
                    rotation_mode='anchor',
                    fontsize=8)
        # plt.show()
        st.pyplot(fig_kolowy)

        # ------------------------ WYKRES GRUPOWY -------------------------
        st.subheader("Wykres grupowy")

        if st.session_state.srednie_df is not None:
            kolumny_1_57 = [col for col in st.session_state.srednie_df.columns if col.split(".")[0].isdigit()]
            dane = st.session_state.srednie_df[kolumny_1_57].values
            os_x = np.arange(1, len(kolumny_1_57) + 1)
            ostatni_wiersz = dane[-1]

            # Tworzenie figury i osi
            fig, ax = plt.subplots(figsize=(20, 5))  # Zwiększone wymiary wykresu

            # Iteruj przez wiersze (oprócz ostatniego)
            for i in range(dane.shape[0]-1):
                ax.scatter(os_x, dane[i], color='blue', alpha=0.6, s=30)

            # Rysowanie ostatniego wiersza
            ax.scatter(os_x, ostatni_wiersz, color='red', s=50, zorder=5)

            # Ustawienia osi
            ax.set_xticks(os_x)
            ax.set_xticklabels([])  # Usunięcie opisów osi X
            ax.set_yticks(np.arange(-4, 5))  # Ustawienie kresek na osi Y
            ax.set_yticklabels([])  # Usunięcie opisów osi Y
            ax.set_ylim(-4, 4)
            ax.axhline(0, color='black', linewidth=1)

            # Tytuł
            ax.set_title("Porównanie ostatniego wiersza z resztą danych")

            # Dodanie siatki
            ax.grid(True, linestyle='--', alpha=0.7)

            # Dopasowanie układu
            plt.tight_layout()

            # Wyświetlenie wykresu w Streamlit
            st.pyplot(fig)
