import sys
print("Zaimportowano bibliotekę - sys")
import pandas as pd
print("Zaimportowano bibliotekę - pandas")
import numpy as np
print("Zaimportowano bibliotekę - numpy")
import matplotlib.pyplot as plt
print("Zaimportowano bibliotekę - matplotlib.pyplot")
import seaborn as sns
print("Zaimportowano bibliotekę - seaborn")
import string
print("Zaimportowano bibliotekę - string")
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
print("Zaimportowano bibliotekę - nltk")
from collections import Counter
print("Zaimportowano bibliotekę - collections")
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, cohen_kappa_score, roc_auc_score
from sklearn.utils import resample
print("Zaimportowano fragmenty biblioteki - sklearn")
pd.set_option('future.no_silent_downcasting', True)

print("\n--- KONFIGURACJA ---")
print("Proszę wpisać liczbę opinii do przeanalizowania (max. 50000).")
print("Wpisanie '0' lub naciśnięcie ENTER, spowoduje analizę całego zbioru")
user_input = input("Twój wybór: ").strip()

SAMPLE_SIZE = 0
if user_input.isdigit() and int(user_input) > 0:
    SAMPLE_SIZE = int(user_input)
    print(f"--> Wybrano tryb szybki: losowe {SAMPLE_SIZE} opinii.")
else:
    print("--> Wybrano tryb pełny: analiza wszystkich dostępnych opinii.")

# --- POBIERANIE NLTK ---
print("\n[1/6] Sprawdzanie bibliotek językowych...")
try:
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
    nltk.data.find('corpora/omw-1.4')
except LookupError:
    print("   -> Pobieranie danych NLTK...")
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

# --- WCZYTYWANIE DANYCH ---
print("[2/6] Wczytywanie danych...")
try:
    ds1 = pd.read_csv('DS1.csv');
    ds1['game_name'] = "Dark Souls 1"
    ds2 = pd.read_csv('DS2.csv');
    ds2['game_name'] = "Dark Souls 2"
    ds3 = pd.read_csv('DS3.csv');
    ds3['game_name'] = "Dark Souls 3"
    sek = pd.read_csv('SEKIRO.csv');
    sek['game_name'] = "Sekiro"
    er = pd.read_csv('ER.csv');
    er['game_name'] = "Elden Ring"
    x = [ds1, ds2, ds3, sek, er]
    df = pd.concat(x, ignore_index=True)

    # TUTAJ NASTĘPUJE OGRANICZENIE PRÓBKI
    if SAMPLE_SIZE > 0 and len(df) > SAMPLE_SIZE:
        df = df.sample(n=SAMPLE_SIZE, random_state=42)
        print(f"   -> Ograniczono zbiór danych do {len(df)} wierszy.")

except FileNotFoundError as e:
    print(f"BŁĄD: Nie znaleziono pliku {e.filename}. Upewnij się, że pliki CSV są w folderze.")
    input("Enter by zamknąć...")
    sys.exit()

# --- DALSZA CZĘŚĆ KODU BEZ ZMIAN ---
print("[3/6] Przetwarzanie tekstu i dat...")

# Oczyszczanie
df['review_text'] = df['review_text'].str.replace(r'^Posted:.*?\n', '', regex=True)
df['review_text'] = df['review_text'].str.replace(r'\n', ' ', regex=True)
df['date_posted'] = df['date_posted'].str.replace('Posted: ', '', regex=False)
df['recommendation'] = df['recommendation'].replace({'Recommended': True, 'Not Recommended': False})


def parse_universal_date(date_str):
    default_year = 2025
    if not isinstance(date_str, str): return (None, None, None)
    parts = date_str.replace(',', '').split()
    day, month_name, year = None, None, None
    if len(parts) == 3:
        month_name = parts[0];
        day = int(parts[1]);
        year = int(parts[2])
    elif len(parts) == 2:
        year = default_year
        if parts[0].isdigit():
            day = int(parts[0]); month_name = parts[1]
        else:
            month_name = parts[0]; day = int(parts[1])
    return (day, month_name, year)


date_parts = df['date_posted'].apply(parse_universal_date)
df[['day', 'month_name', 'year']] = pd.DataFrame(date_parts.tolist(), index=df.index)
month_map = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6, 'July': 7, 'August': 8,
             'September': 9, 'October': 10, 'November': 11, 'December': 12}
df['month'] = df['month_name'].map(month_map)
df['date'] = pd.to_datetime(df[['year', 'month', 'day']], errors='coerce')
df = df.drop(columns=['month_name', 'date_posted', 'day', 'month', 'year'])


def filter_spam_optimized(df):
    lengths = df['review_text'].str.len()
    non_alnum_counts = df['review_text'].str.count(r'[^a-zA-Z0-9\s]')
    ratios = non_alnum_counts / lengths
    mask = (ratios <= 0.40) & (lengths > 10)
    return df[mask]


df = filter_spam_optimized(df)

words_to_keep = {'no', 'not', 'nor', 'neither', 'none', "don't", "couldn't"}
custom_stopwords = set(stopwords.words('english')) - words_to_keep
stop_words = custom_stopwords
punct_table = str.maketrans('', '', string.punctuation)

df['cleaned_review'] = df['review_text'].apply(lambda x: " ".join(
    [word for word in x.lower().translate(punct_table).split() if word not in stop_words]) if isinstance(x,
                                                                                                         str) else "")
df = df.drop(columns=['review_text'])

lemmatizer = WordNetLemmatizer()
df['cleaned_review'] = df['cleaned_review'].apply(
    lambda x: " ".join([lemmatizer.lemmatize(word) for word in x.split()]))

df = df[["cleaned_review", "recommendation", "date", "game_name"]]
df = df.dropna(subset=['cleaned_review', 'recommendation'])
df.to_excel("clean_df.xlsx", index=False)

print("[4/6] Analiza słów kluczowych...")
wordlist = [word for text in df['cleaned_review'] for word in str(text).split()]
token_counts = Counter(wordlist)
df_counts = pd.DataFrame(token_counts.items(), columns=['token', 'count']).sort_values(by='count',
                                                                                       ascending=False).reset_index(
    drop=True)

all_bigrams = [" ".join(bigram) for text in df['cleaned_review'] for words in [str(text).split()] for bigram in
               zip(words, words[1:])]
bigram_counts = Counter(all_bigrams)
df_bigrams = pd.DataFrame(bigram_counts.items(), columns=['token', 'count']).sort_values(by='count',
                                                                                         ascending=False).reset_index(
    drop=True)

y = [df_counts, df_bigrams]
df_counters = pd.concat(y, ignore_index=True).sort_values(by='count', ascending=False).reset_index(drop=True)

print("[5/6] Trenowanie modelu ML...")
df['target'] = df['recommendation'].astype(int)
X_raw = df['cleaned_review']
y_raw = df['target']

# Zabezpieczenie dla bardzo małych próbek
if len(df) < 50:
    print("UWAGA: Zbyt mała próba do podziału stratified. Pomijam stratify.")
    X_train_raw, X_test, y_train_raw, y_test = train_test_split(X_raw, y_raw, test_size=0.30, random_state=42)
else:
    X_train_raw, X_test, y_train_raw, y_test = train_test_split(X_raw, y_raw, test_size=0.30, random_state=42,
                                                                stratify=y_raw)

train_data = pd.DataFrame({'text': X_train_raw, 'target': y_train_raw})
neg_train = train_data[train_data['target'] == 0]
pos_train = train_data[train_data['target'] == 1]

if len(pos_train) > len(neg_train):
    pos_train_downsampled = resample(pos_train, replace=False, n_samples=len(neg_train) * 2, random_state=42)
    balanced_train = pd.concat([neg_train, pos_train_downsampled])
else:
    balanced_train = train_data

X_train_bal = balanced_train['text']
y_train_bal = balanced_train['target']

tfidf = TfidfVectorizer(max_features=20000, ngram_range=(1, 2), min_df=5)
X_train_vec = tfidf.fit_transform(X_train_bal)
X_test_vec = tfidf.transform(X_test)

model = LogisticRegression(max_iter=5000, solver='liblinear')
model.fit(X_train_vec, y_train_bal)

y_pred = model.predict(X_test_vec)
y_pred_proba = model.predict_proba(X_test_vec)[:, 1]
auc_score = roc_auc_score(y_test, y_pred_proba)

print("\n--- WYNIKI ---")
print(f"Accuracy:       {accuracy_score(y_test, y_pred):.4f}")
print(f"Cohen's Kappa: {cohen_kappa_score(y_test, y_pred):.4f}")
print(f"AUC:     {auc_score:.4f}")
print(classification_report(y_test, y_pred, target_names=['Negative', 'Positive']))

print("[6/6] Analiza tematyczna...")
feature_names = tfidf.get_feature_names_out()
coefs = model.coef_[0]
word_sentiment = pd.DataFrame({'word': feature_names, 'coefficient': coefs}).rename(columns={"word": "token"})
merged = word_sentiment.merge(df_counters, on='token', how='left')

topic_dictionary = {
    'Cena  ': ['price', 'cost', 'money', 'cheap', 'expensive', 'sale', 'worth', 'dollar', 'euro', 'buy', 'refund'],
    'Udźwiękowienie': ['sound', 'music', 'soundtrack', 'audio', 'voice', 'ost', 'song', 'dub', 'hearing', 'sfx'],
    'Fabuła': ['story', 'lore', 'narrative', 'plot', 'ending', 'npc', 'quest', 'writing', 'character', 'dialogue',
              'cutscene'],
    'Wsparcie': ['support', 'bug', 'fix', 'patch', 'dev', 'developer', 'update', 'broken', 'error', 'issue', 'glitch',
                'devs', 'dlc'],
    'Sterowanie': ['control', 'keyboard', 'mouse', 'controller', 'gamepad', 'keybind', 'input', 'clunky', 'camera',
                 'bind'],
    'Rozgrywka': ['action', 'combat', 'boss', 'fight', 'mechanic', 'dodge', 'parry', 'difficult', 'hard', 'easy',
                 'challenge', 'fun', 'gameplay', 'attack', 'level', 'weapon', 'build'],
    'Grafika': ['graphic', 'visual', 'art', 'map', 'world', 'beautiful', 'ugly', 'texture', 'look', 'style', 'view',
                 'atmosphere', 'environment', 'lighting'],
    'Tryb Wieloosobowy': ['multiplayer', 'pvp', 'coop', 'summon', 'invade', 'invasion', 'online', 'server', 'lag',
                    'connection'],
    'Optymalizacja': ['performance', 'fps', 'optimize', 'crash', 'stutter', 'frame', 'run', 'pc', 'freeze',
                    'optimization']
}
all_topic_values = set([val for vals in topic_dictionary.values() for val in vals])
value_to_topic = {val: topic for topic, vals in topic_dictionary.items() for val in vals}

topics_list = []
for token_str in merged['token']:
    found_topics = set()
    if isinstance(token_str, str):
        parts = token_str.split()
        for part in parts:
            if part in all_topic_values:
                found_topics.add(value_to_topic[part])
    topics_list.append(sorted(list(found_topics))[0] if found_topics else None)

merged['topics'] = topics_list
merged.to_excel("wynik.xlsx", index=False)

print("\nDziałanie aplikacji zakończone.\nUtworzono pliki 'clean_df.xlsx' oraz 'wynik.xlsx'.")
input("Naciśnij ENTER, aby zakończyć...")