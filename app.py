# sekcja importowa
import os
import boto3
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# sekcja fromkowa
from io import BytesIO
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import logging

# Chwilowo, zamiast podawanego przy przekazaniu na naszą stronę ID z GOTOIT
ID_kursanta = 1

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ładowanie zmiennych środowiskowych
BUCKET_NAME = 'od-zera-do-ai-rafal'
load_dotenv()

# Globalne ustawianie szerokości
st.set_page_config(
    page_title="Kompas przekonań",
    page_icon="🔘",
    # layout="wide"
)

#
# ----------------------- STALE ---------------------
#
REQUIRED_ENV_VARS = [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_ENDPOINT_URL_S3"
]

CHART_COLORS = [
    '#d6018d', '#8511fe', '#0143fe', '#2a8cff', '#02d6e6',
    '#02f873', '#06de2d', '#01bd23', '#009c20', '#0c7210',
    '#9c9b01', '#dede01', '#efee02', '#fadd4c', '#f4a302',
    '#e08b09', '#fd4238', '#de0800', '#b9130c'
]

CHART_DIMENSIONS = {
    'main_figure': (8, 8),
    'polar_limit': 7.0,
    'center_circle_radius': 0.75,
    'outer_band_height': 0.33
}

# Lista 57 pytan Saloma Schwarza
QUESTIONS = [
    '1. Jest dla niego ważne, aby być niezależnym w kształtowaniu swoich poglądów.',
    '2. Jest dla niego ważne, aby jego kraj był bezpieczny i stabilny.',
    '3. Jest dla niego ważne, aby przyjemnie spędzać czas.',
    '4. Jest dla niego ważne, aby unikać irytowania innych.',
    '5. Jest dla niego ważne, aby słabi i bezbronni ludzie w społeczeństwie byli chronieni.',
    '6. Jest dla niego ważne, aby ludzie robili wszystko, cokolwiek im nakaże.',
    '7. Jest dla niego ważne, aby nigdy nie myśleć, że zasługuje na coś więcej niż inni ludzie.',
    '8. Jest dla niego ważne, aby troszczyć się o przyrodę.',
    '9. Jest dla niego ważne, aby nikt go nigdy nie upokorzył.',
    '10. Jest dla niego ważne, aby ciągle robić coś innego.',
    '11. Jest dla niego ważne, aby troszczyć się o bliskie mu osoby.',
    '12. Jest dla niego ważna siła, którą mogą dać pieniądze.',
    '13. Jest dla niego bardzo ważne, aby unikać chorób i chronić swoje zdrowie.',
    '14. Jest dla niego ważne, aby być tolerancyjnym w stosunku do wszystkich rodzajów ludzi i grup.',
    '15. Jest dla niego ważne, aby nigdy nie naruszać reguł lub regulaminu.',
    '16. Jest dla niego ważne, aby samemu podejmować decyzje dotyczące swojego życia.',
    '17. Jest dla niego ważne, aby wiele w życiu zdobyć.',
    '18. Jest dla niego ważne, aby podtrzymywać tradycyjne wartości i sposoby myślenia.',
    '19. Jest dla niego ważne, aby ludzie, których zna, mieli do niego pełne zaufanie.',
    '20. Jest dla niego ważne, aby być bogatym.',
    '21. Jest dla niego ważne, aby brać udział w działaniach na rzecz ochrony przyrody.',
    '22. Jest dla niego ważne, aby nigdy nikogo nie denerwować.',
    '23. Jest dla niego ważne, aby samemu kształtować swoje opinie na różne tematy.',
    '24. Jest dla niego ważna ochrona jego publicznego wizerunku.',
    '25. Jest dla niego bardzo ważne, by pomagać drogim mu osobom.',
    '26. Jest dla niego ważne osobiste bezpieczeństwo i brak zagrożeń.',
    '27. Jest dla niego ważne, aby być niezawodnym i godnym zaufania przyjacielem.',
    '28. Jest dla niego ważne, aby podejmować ryzyko, które sprawia, że życie jest bardziej ekscytujące.',
    '29. Jest dla niego ważne, aby mieć władzę, która sprawia, że ludzie robią to, co on chce.',
    '30. Jest dla niego ważne, aby być niezależnym wplanowaniu swoich działań.',
    '31. Jest dla niego ważne, aby postępować zgodnie z regułami nawet wtedy, gdy nikt tego nie widzi.',
    '32. Jest dla niego ważne, aby odnieść dużo sukcesów.',
    '33. Jest dla niego ważne, aby przestrzegać obyczajów swojej rodziny lub obyczajów religii.',
    '34. Jest dla niego ważne, aby słuchać i rozumieć ludzi, którzy się od niego różnią.',
    '35. Jest dla niego ważne, aby państwo było silne i mogło bronić swoich obywateli.',
    '36. Jest dla niego ważne, aby czerpać z życia przyjemności.',
    '37. Jest dla niego ważne, aby każdy człowiek na świecie miał równe szanse w życiu.',
    '38. Jest dla niego ważne, aby być skromnym człowiekiem.',
    '39. Jest dla niego ważne, aby po swojemu zrozumieć różne rzeczy.',
    '40. Jest dla niego ważne, aby szanować tradycyjne zwyczaje swojej kultury.',
    '41. Jest dla niego ważne, aby być tym, kto mówi innym, co mają robić.',
    '42. Jest dla niego ważne, aby przestrzegać wszystkich przepisów prawnych.',
    '43. Jest dla niego ważne, aby doświadczać wszelkich nowych przeżyć.',
    '44. Jest dla niego ważne, aby posiadać drogie rzeczy, które świadczą o jego bogactwie.',
    '45. Jest dla niego ważne, aby chronić środowisko naturalne przed zniszczeniem lub zanieczyszczeniem.',
    '46. Jest dla niego ważne, aby dobrze się bawić w każdej sytuacji.',
    '47. Jest dla niego ważne, aby zajmować się każdą potrzebą drogich mu osób.',
    '48. Jest dla niego ważne, aby ludzie docenili jego osiągnięcia.',
    '49. Jest dla niego ważne, aby nigdy nie zostać poniżonym.',
    '50. Jest dla niego ważne, aby jego kraj mógł obronić się przed wszystkimi zagrożeniami.',
    '51. Jest dla niego ważne, aby nigdy nikogo nie rozgniewać.',
    '52. Jest dla niego ważne, aby wszyscy byli traktowani sprawiedliwie, nawet ci, których nie zna.',
    '53. Jest dla niego ważne, aby unikać wszystkiego, co jest niebezpieczne.',
    '54. Jest dla niego ważne, aby być zadowolonym z tego, co posiada, i nie chcieć niczego więcej.',
    '55. Jest dla niego ważne, aby wszyscy jego przyjaciele i rodzina mogli na nim całkowicie polegać.',
    '56. Jest dla niego ważne, aby być wolnym w wyborze tego, co robi.',
    '57. Jest dla niego ważne, aby akceptować ludzi nawet wtedy, gdy się z nimi nie zgadza.'
]

# Opisy do każdej z pozycji suwaka
DESCRIPTIONS = [
    "Zupełnie niepodobny do mnie",
    "Niepodobny do mnie",
    "Trochę podobny do mnie",
    "Średnio podobny do mnie",
    "Podobny do mnie",
    "Bardzo podobny do mnie"
]

# Słownik ze wzorcami dla 19 kategorii
PATTERNS = {
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

#
# ------------------- FUNKCJE -----------------------
#


# Inicjalizacja session state
def init_session_state():
    if 'dane_19_do_wykresu_df' not in st.session_state:
        st.session_state.dane_19_do_wykresu_df = None
    if 'odpowiedzi_complete' not in st.session_state:
        st.session_state.odpowiedzi_complete = False
    if 'df' not in st.session_state:
        columns = ["ID_kursanta", "Płeć", "Wiek", "Miejsce", "Kurs (miesiące)", "Moduł_teraz", "Moduł_problem", "Podoba", "Niepodoba"]
        st.session_state.df = pd.DataFrame(columns=columns)


# Sprawdzenie zmiennych środowiskowych dla Digital Ocean
def check_environment() -> bool:
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        st.error(f"Brak wymaganych zmiennych środowiskowych: {', '.join(missing_vars)}")
        return False
    return True


# Inicjalizacja klienta S3 dla Digital Ocean
def init_s3_client():

    try:
        return boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            endpoint_url=os.getenv("AWS_ENDPOINT_URL_S3")
        )
    except Exception as e:
        logger.error(f"Błąd podczas inicjalizacji klienta S3: {str(e)}")
        st.error("Nie udało się połączyć z serwisem Digital Ocean.")
        return None


# Wczytanie danych z pliku CSV z Digital Ocean
@st.cache_data
def wczytaj_dataframe(_s3_client, bucket_name: str, nazwa_pliku: str) -> Optional[pd.DataFrame]:

    try:
        obj_data = _s3_client.get_object(Bucket=bucket_name, Key=nazwa_pliku)
        data = obj_data['Body'].read()
        return pd.read_csv(BytesIO(data), sep=';', encoding='utf-8')
    except Exception as e:
        logger.error(f"Błąd wczytywania pliku {nazwa_pliku}: {str(e)}")
        return None


# Wyliczam 19 wartosci
def oblicz_srednie_kategorii(df: pd.DataFrame) -> Optional[pd.DataFrame]:

    if df is None or df.empty:
        logger.error("Brak danych do analizy")
        return None

    try:
        dane_19_do_wykresu_df = pd.DataFrame(columns=PATTERNS.keys())

        for nazwa_kategorii, lista_numerow in PATTERNS.items():
            wartosci = []
            for numer in lista_numerow:
                pelne_pytanie = next(q for q in QUESTIONS if q.startswith(numer))
                if pelne_pytanie in df.columns:
                    wartosc = df[pelne_pytanie].values[0]
                    wartosci.append(wartosc)

            if wartosci:
                dane_19_do_wykresu_df[nazwa_kategorii] = [sum(wartosci) / len(wartosci)]

        return dane_19_do_wykresu_df
    except Exception as e:
        logger.error(f"Błąd podczas obliczania średnich: {str(e)}")
        return None


# Wykres gratyfikacyjny
def create_polar_chart(dane_19_do_wykresu_df: pd.DataFrame) -> Optional[plt.Figure]:

    try:
        names = list(PATTERNS.keys())
        values = [dane_19_do_wykresu_df[nazwa_kategorii].iloc[0] for nazwa_kategorii in names]

        fig = plt.figure(figsize=CHART_DIMENSIONS['main_figure'])
        ax = fig.add_subplot(111, projection='polar')

        # Ustawienia czcionki
        plt.rcParams['font.family'] = 'DejaVu Sans'

        # Obliczanie kątów
        angles = np.linspace(0, 2*np.pi, len(values), endpoint=False)
        width = (2*np.pi) / len(values) * 0.9

        # Rysowanie słupków
        bars = ax.bar(angles, values, width=width, bottom=0.0, alpha=0.85)
        for bar, color in zip(bars, CHART_COLORS):
            bar.set_facecolor(color)

        # Dodawanie zewnętrznych pasków
        outer_bars = ax.bar(
            angles,
            [CHART_DIMENSIONS['outer_band_height']] * len(values),
            width=width,
            bottom=6.67,
            alpha=0.85
        )
        for outer_bar, color in zip(outer_bars, CHART_COLORS):
            outer_bar.set_facecolor(color)

        # Add thin circular grid lines (every 0.1)
        theta = np.linspace(0, 2*np.pi, 200)
        for r in np.arange(1.1, 6.0, 0.1):
            if r not in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]:
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
            linewidth = 1.5 if is_thick else 0.25
            ax.plot([line_angle, line_angle], [0, 7], 'k-', linewidth=linewidth)

        # Customize the chart
        ax.set_theta_zero_location('E')
        ax.set_theta_direction(1)
        ax.set_rlim(0, 7.0)

        # Remove default grid
        ax.grid(False)
        ax.set_rticks([])
        ax.set_xticks([])

        # Add a white circle in the center
        center_circle = plt.Circle((0, 0), 0.75, transform=ax.transData._b, color='white', zorder=3)
        ax.add_artist(center_circle)

        plt.title('Radial Chart of Values', pad=20, size=14)
        plt.tight_layout()

        # Add curved text labels
        for idx, (angle, name) in enumerate(zip(angles, names)):

            middle_angle = angle

            # Convert angle to degrees for text rotation
            angle_deg = np.rad2deg(middle_angle)

            # Adjust text alignment based on position
            if 0 <= angle_deg <= 180:
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

        return fig

    except Exception as e:
        logger.error(f"Błąd podczas tworzenia wykresu: {str(e)}")
        return None


#
# ----------------------------- APLIKACJA: -----------------------------------
#

# Inicjalizacja
init_session_state()

if not check_environment():
    st.stop()

s3_client = init_s3_client()
if s3_client is None:
    st.stop()

# Tytuł i opis
st.markdown("<h1 style='text-align: center;'>Kompas przekonań</h1>", unsafe_allow_html=True)
st.write("")
st.write("")

# ------------------------- SIDEBAR ---------------------------
st.sidebar.header("Wypełnij też proszę poniższe pola")

# Ustawienia szerokości sidebaru
st.markdown(
    """
    <style>
    .css-1d391kg {
        width: 300px;  /* Zmienna szerokość - dostosuj według potrzeb */
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Metryczka
plec = st.sidebar.radio("Podaj płeć:", ["Kobieta", "Mężczyzna"], horizontal=True)
wiek = st.sidebar.radio("Podaj swój wiek:", ["<25", "25-45", "45-65", "65+"], horizontal=True)
miejsce = st.sidebar.radio("Podaj miejsce zamieszkania:", ["<10 tys.", "10-100 tys.", "100+ tys."], horizontal=True)

st.sidebar.markdown('------------ Kurs "Od zera_do_AI" ------------')

# Miesiąc i rok rozpoczęcia kursu
col1, col2 = st.sidebar.columns(2)
miesiac_start = col1.number_input("Miesiąc startu:", 1, 12, 1)
rok_start = col2.number_input("Rok startu:", 2024, 2025, 2024)

# Obliczanie liczby miesięcy kursu
miesiace_kursu = (max(datetime.now().month - miesiac_start, 1)
                  if datetime.now().year == rok_start
                  else (13 - miesiac_start) + datetime.now().month + (datetime.now().year - rok_start - 1) * 12)

# Moduły
modul_teraz = st.sidebar.number_input("Obecny moduł:", 1, 12, 1)
modul_problem = st.sidebar.number_input("Najtrudniejszy moduł:", 1, 12, 1)

# Opinie
podoba = st.sidebar.text_area("Co w kursie najbardziej Ci się podoba?", max_chars=250, height=150)
niepodoba = st.sidebar.text_area("Co w kursie najmniej Ci się podoba / chcesz zmienić?", max_chars=250, height=150)

# Przycisk zatwierdzający
data = {
    "ID_kursanta": ID_kursanta,
    "Płeć": plec,
    "Wiek": wiek,
    "Miejsce": miejsce,
    "Kurs (miesiące)": miesiace_kursu,
    "Moduł_teraz": modul_teraz,
    "Moduł_problem": modul_problem,
    "Podoba": podoba,
    "Niepodoba": niepodoba
}

if st.sidebar.button("Zatwierdź"):
    # Nadpisanie danych w DataFrame
    st.session_state.df.loc[0] = data

# Poczatkowy opis ankiety dla uzytkownika
st.markdown("""
<div style='text-align: justify;'>

Poświęć nam proszę kilka chwil, a na pewno nie pożałujesz :-)

Czy zastanawialiście się kiedyś, dlaczego jedne zadania wykonujecie chętniej niż inne? Albo że jedni ludzie wolą pracować samodzielnie, podczas gdy inni preferują pracę w grupie? Że podczas gdy jedni uczą się powoli i systematycznie, inni robią to zrywami; momenty intensywnej pracy przeplatając okresami pozornej bezczynności?

Jako ludzie różnimy się między sobą. Mamy różne cele, różne pragnienia i dążenia, różne sposoby osiągania naszych celów i różne przekonania. Często są one nieświadome. Ale czy tego chcemy, czy nie, wpływają na nasze życie. Są bowiem powiązane z emocjami, które nami kierują, popychając nas w stronę jednych rzeczy, a odpychając od innych. Stanowią motywację naszego działania.

Jeśli tylko szczerze odpowiesz na poniższe pytania, najprawdopodobniej dowiesz się, co tobą kieruje, co cię tak naprawdę w życiu motywuje. Ankieta jest oczywiście całkowicie anonimowa, żadne wrażliwe dane nie są tutaj ani zbierane, ani przechowywane.

</div>
""", unsafe_allow_html=True)

st.write("")
st.markdown("<h4>Instrukcja</h4>", unsafe_allow_html=True)

st.markdown("""
Poniżej znajduje się 57 zdań. Przeczytaj je i zastanów się, na ile przedstawiony w każdym z nich człowiek jest podobny lub nie jest podobny do Ciebie. Użyj suwaka, aby wybrać odpowiednią wartość.
""", unsafe_allow_html=True)

st.write("")
st.markdown("<h5>Skala odpowiedzi</h5>", unsafe_allow_html=True)

st.markdown("""
W jakim stopniu ten człowiek jest podobny do Ciebie?

1 - zupełnie niepodobny do mnie  
2 - niepodobny do mnie  
3 - trochę podobny do mnie  
4 - średnio podobny do mnie  
5 - podobny do mnie  
6 - bardzo podobny do mnie  
""", unsafe_allow_html=True)
st.write("")
st.write("")

# Słownik do przechowywania wyników
wyniki = {}

# Wyświetlanie pytań i suwaków
# Styl CSS dla horyzontalnego układu
st.markdown("""
    <style>
        div.row-widget.stRadio > div {
            flex-direction: row;
            align-items: center;
            justify-content: space-between;
        }
        div.row-widget.stRadio > div > label {
            font-size: 0.8em;
            padding: 0 0.1em;
            white-space: nowrap;
        }
         /* Ukrycie indeksów przed radiobutonami */
        div.row-widget.stRadio > div label span:first-child {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

for pytanie in QUESTIONS:
    st.write(pytanie)

    # Wyświetl opisy nad przyciskami
    cols = st.columns(7)
    descriptions = [
        "N/A",
        "zupełnie niepodobny do mnie",
        "niepodobny do mnie",
        "trochę podobny do mnie",
        "średnio podobny do mnie",
        "podobny do mnie",
        "bardzo podobny do mnie"
    ]

    for i, desc in enumerate(descriptions):
        with cols[i]:
            st.write(desc)

    # Radio przyciski
    selected = st.radio(
        "Wybierz pozycję",
        options=range(7),
        key=pytanie,
        label_visibility="hidden",
        horizontal=True
    )

    # Mapowanie wybranej opcji na wartość (0 -> NaN, 1-6 -> 1-6)
    wyniki[pytanie] = float('nan') if selected == 0 else selected

    st.write("")
    st.write("")

# Przycisk zatwierdzający
st.write("")
st.write("Jeśli jesteś pewny wszystkich odpowiedzi, naciśnij poniższy przycisk.")

if st.button('Zatwierdź odpowiedzi'):
    # Sprawdzenie, czy są jakieś NaN-y w odpowiedziach
    brakujace_odpowiedzi = [pytanie for pytanie, odpowiedz in wyniki.items() if pd.isna(odpowiedz)]

    if brakujace_odpowiedzi:
        st.error("⚠️ Nie odpowiedziałeś na wszystkie pytania!")
        st.write("Brakuje odpowiedzi dla następujących pytań:")
        for pytanie in brakujace_odpowiedzi:
            st.write(f"• {pytanie}")
        st.write("")
        st.write("Proszę przejrzyj swoje odpowiedzi i uzupełnij brakujące przed ponownym zatwierdzeniem.")
        st.stop()

    try:
        # Przygotowanie nowych danych - przekształcenie słownika na DataFrame
        odpowiedzi_df = pd.DataFrame([wyniki])
        odpowiedzi_df = odpowiedzi_df.reset_index(drop=True)

        # Dodanie ID_kursanta do odpowiedzi
        odpowiedzi_df.insert(0, 'ID_kursanta', ID_kursanta)

        # Scalenie dataframów
        if 'df' in st.session_state:
            # Używamy tylko jednego DataFrame z danymi metryczkowymi
            combined_df = st.session_state.df.copy()
            # Dodajemy kolumny z odpowiedziami
            for col in odpowiedzi_df.columns:
                combined_df[col] = odpowiedzi_df[col].values[0]
            try:
                s3_client.head_object(Bucket=BUCKET_NAME, Key='dane_kursantow.csv')
                # Plik istnieje, wczytaj go
                existing_df = wczytaj_dataframe(s3_client, BUCKET_NAME, 'dane_kursantow.csv')
                existing_df = existing_df.reset_index(drop=True)
                # Dodaj nowy wiersz
                updated_df = pd.concat([existing_df, combined_df], axis=0, ignore_index=True)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    # Plik nie istnieje, użyj tylko nowych danych
                    updated_df = combined_df
                else:
                    # Inny błąd S3
                    st.error(f"Błąd dostępu do S3: {str(e)}")
                    raise

            # Zapisz z powrotem do S3
            csv_buffer = BytesIO()
            updated_df.to_csv(csv_buffer, sep=';', index=False, encoding='utf-8')
            csv_buffer.seek(0)

            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key='dane_kursantow.csv',
                Body=csv_buffer.getvalue()
            )

        # Obliczenie średnich i generowanie wykresu
        dane_19_do_wykresu_df = oblicz_srednie_kategorii(odpowiedzi_df)

        if dane_19_do_wykresu_df is not None:
            fig = create_polar_chart(dane_19_do_wykresu_df)
            if fig is not None:
                st.pyplot(fig)

                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=300, bbox_inches='tight', transparent=False, facecolor='white', edgecolor='white')
                buf.seek(0)

                # Przycisk pobrania wykresu
                st.download_button(
                    label="💾 Zapisz wykres",
                    data=buf,
                    file_name="kompas_przekonan.png",
                    mime="image/png",
                    help="Kliknij, aby pobrać wykres w formacie PNG"
                )

                # Zamknięcie bufora
                buf.close()

            else:
                st.error("Nie udało się wygenerować wykresu")
    except Exception as e:
        st.error(f"Wystąpił błąd podczas przetwarzania danych: {str(e)}")

#         # ------------------------ WYKRES GRUPOWY -------------------------
#         st.subheader("Wykres grupowy")

#         if st.session_state.srednie_df is not None:
#             kolumny_1_57 = [col for col in st.session_state.srednie_df.columns if col.split(".")[0].isdigit()]
#             dane = st.session_state.srednie_df[kolumny_1_57].values
#             os_x = np.arange(1, len(kolumny_1_57) + 1)
#             ostatni_wiersz = dane[-1]

#             # Tworzenie figury i osi
#             fig, ax = plt.subplots(figsize=(20, 5))  # Zwiększone wymiary wykresu

#             # Iteruj przez wiersze (oprócz ostatniego)
#             for i in range(dane.shape[0]-1):
#                 ax.scatter(os_x, dane[i], color='blue', alpha=0.6, s=30)

#             # Rysowanie ostatniego wiersza
#             ax.scatter(os_x, ostatni_wiersz, color='red', s=50, zorder=5)

#             # Ustawienia osi
#             ax.set_xticks(os_x)
#             ax.set_xticklabels([])  # Usunięcie opisów osi X
#             ax.set_yticks(np.arange(-4, 5))  # Ustawienie kresek na osi Y
#             ax.set_yticklabels([])  # Usunięcie opisów osi Y
#             ax.set_ylim(-4, 4)
#             ax.axhline(0, color='black', linewidth=1)

#             # Tytuł
#             ax.set_title("Porównanie ostatniego wiersza z resztą danych")

#             # Dodanie siatki
#             ax.grid(True, linestyle='--', alpha=0.7)

#             # Dopasowanie układu
#             plt.tight_layout()

#             # Wyświetlenie wykresu w Streamlit
#             st.pyplot(fig)
