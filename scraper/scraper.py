print("Inicjalizacja...")

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

GAMES_CONFIG = {
    "1": {"name": "Dark Souls 1 (Remastered)", "id": "570940", "filename": "DS1.csv"},
    "2": {"name": "Dark Souls 2 (SotFS)", "id": "335300", "filename": "DS2.csv"},
    "3": {"name": "Dark Souls 3", "id": "374320", "filename": "DS3.csv"},
    "4": {"name": "Sekiro", "id": "814380", "filename": "SEKIRO.csv"},
    "5": {"name": "Elden Ring", "id": "1245620", "filename": "ER.csv"}
}

def get_reviews(driver, num_reviews, game_name):
    reviews_data = []
    reviews_scraped = 0
    last_height = driver.execute_script("return document.body.scrollHeight")

    print(f"--- Rozpoczynam pobieranie {num_reviews} opinii dla: {game_name} ---")

    while reviews_scraped < num_reviews:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Czas na załadowanie nowych opinii

        reviews_on_page = driver.find_elements(By.CLASS_NAME, "apphub_Card")

        current_batch = reviews_on_page

        start_index = reviews_scraped

        if len(current_batch) > num_reviews:
            current_batch = current_batch[:num_reviews]

        for i in range(reviews_scraped, len(current_batch)):
            if reviews_scraped >= num_reviews:
                break

            review = current_batch[i]
            try:
                username = review.find_element(By.CLASS_NAME, "apphub_CardContentAuthorName").text
                review_text = review.find_element(By.CLASS_NAME, "apphub_CardTextContent").text
                date_posted = review.find_element(By.CLASS_NAME, "date_posted").text
                recommendation = review.find_element(By.CLASS_NAME, "title").text

                reviews_data.append({
                    "username": username,
                    "review_text": review_text,
                    "date_posted": date_posted,
                    "recommendation": recommendation,
                })
                reviews_scraped += 1

                if reviews_scraped % 50 == 0:
                    print(f"[{game_name}] Pobrano: {reviews_scraped}/{num_reviews}")

            except Exception:
                continue

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print(f"[{game_name}] Koniec dostępnych recenzji na stronie.")
                break
        last_height = new_height

    return reviews_data


def main():
    print("--- SCRAPER RECENZJI STEAM ---")

    raw_count = input(f"Ile opinii chcesz pobrać dla każdej gry?\n").strip()
    if not raw_count.isdigit():
        print("Niepoprawna liczba. Ustawiam domyślnie 100.")
        NUM_REVIEWS = 50
    else:
        NUM_REVIEWS = int(raw_count)

    print("\nWybierz opinie do pobrania (wpisz cyfry pokolei, np. '125').")
    print("Wpisanie '0' pobierze opinie o wszystkich grach.")
    print("1 - Dark Souls 1")
    print("2 - Dark Souls 2")
    print("3 - Dark Souls 3")
    print("4 - Sekiro")
    print("5 - Elden Ring")

    selection = input("Twój wybór\n").strip()

    selected_games = []

    if selection == "0":
        print("Wybrano opcję: Opinie o wszystkich grach.")
        for key in GAMES_CONFIG:
            selected_games.append(GAMES_CONFIG[key])
    else:
        for char in selection:
            if char in GAMES_CONFIG:
                selected_games.append(GAMES_CONFIG[char])

    if not selected_games:
        print("Nie wybrano żadnych poprawnych gier. Zamykam.")
        return

    print(f"\nWybrano do pobrania: {', '.join([g['name'] for g in selected_games])}")
    print("Uruchamiam przeglądarkę...\n")

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    try:
        for game in selected_games:
            url = f"https://steamcommunity.com/app/{game['id']}/reviews/?browsefilter=mostrecent&p=1&l=english"

            print(f"Nawigacja do: {game['name']}...")
            driver.get(url)
            time.sleep(3)  # Czekamy na załadowanie

            try:
                driver.find_element(By.ID, "view_product_page_btn").click()
                print(" -> Kliknięto bramkę wiekową.")
                time.sleep(2)
            except Exception:
                pass

            # Pobieranie
            reviews = get_reviews(driver, NUM_REVIEWS, game['name'])

            # Zapisywanie
            df = pd.DataFrame(reviews)
            df.to_csv(game['filename'], index=False)
            print(f" -> SUKCES: Zapisano {len(reviews)} opinii do pliku '{game['filename']}'\n")

    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")
    finally:
        driver.quit()
        print("Praca zakończona.")
        input("Naciśnij ENTER, aby zamknąć okno...")


if __name__ == "__main__":
    main()