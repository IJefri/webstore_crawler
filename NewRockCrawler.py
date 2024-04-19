import os
import telebot
import pandas as pd
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# Retrieve bot token from environment variable
#BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Use the name of the environment variable

# Initialize bot
#bot = telebot.TeleBot(BOT_TOKEN)

BOT_TOKEN = "7176877320:AAGLMiDHUVe3J6fpqyzFrxBKLEYyJgLndkE"
def remove_files_in_dir(directory):
    files = os.listdir(directory)
    for file in files:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Removed file: {file_path}")
            
# Initialize bot with the token
bot = telebot.TeleBot(BOT_TOKEN)
#-----------------------------------------------------------
def create_df(name):
    url = "https://www.newrock.com/ru/outlet/"
    all_urls = []
    page_number = 1
    prev_len = 0
    
    while True:
        page_url = f"{url}?page={page_number}"
        print(page_url)
        response = requests.get(page_url)
        if response.status_code != 200:
            print("Error: Failed to retrieve page")
            break  # Exit the loop if the page is not found or another error occurs
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("div", class_="product-description-short text-muted")
        for link in links:
            product_link = link.find("a", href=True)
            if product_link:
                all_urls.append(product_link["href"])
        print("Number of product links on this page:", len(all_urls))
        if len(all_urls) == prev_len:
            print("No new URLs found, exiting loop")
            break  # Exit the loop if no new URLs are found
        prev_len = len(all_urls)
        page_number += 1
    
    df_urls = pd.DataFrame(all_urls, columns=['url'])
    df_valid_urls = df_urls[df_urls['url'] != '#'].drop_duplicates().reset_index(drop=True)
    print("Number of valid URLs:", len(df_valid_urls))
    df_valid_urls.to_csv(f'{name}.csv')
    print(f"DataFrame saved to {name}.csv")
#-----------------------------------------------------------
def get_product(row):
    print('getting product')
    url = row['url']
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    price_tag = soup.find("span", class_="product-price")
    price = price_tag.text.strip()

    sizes_tags = soup.find_all("span", class_="radio-label")
    sizes = [size_tag.text.strip() for size_tag in sizes_tags]

    image_div = soup.find("a", class_="js-easyzoom-trigger")
    images = image_div.get('href')
    
    return pd.Series({'price': price, 'sizes': sizes,'images': images})
#-----------------------------------------------------------
chat_id = 430697715
#result_new = handle_new(chat_id)



#-----------------------------------------------------------
#bot.send_message(430697715, f'{result_new}')
#-----------------------------------------------------------
@bot.message_handler(commands=['sendmessage'])
def handle_send_message(message):
    chat_id = message.chat.id 

    for index, row in df_valid_urls.iterrows():
        image_url = row["images"]
        descriptions = row["sizes"]
        caption = ", ".join(map(str, descriptions))
        bot.send_photo(chat_id, image_url, caption=caption)
#-----------------------------------------------------------
@bot.message_handler(commands=['updateold'])
def hande_update(message):
    if type(message) == telebot.types.Message:
        chat_id = message.chat.id
    else:
        chat_id = message
        
    current_date_time = datetime.now()
    current_date = current_date_time.date()
    create_df(f'newrock_old/newrock_{current_date}')
    print(f'created newrock_{current_date}')
    # Get the current date and time
    
    print("Current date:", current_date)
    bot.send_message(chat_id, f'created newrock_{current_date}')
#-----------------------------------------------------------
@bot.message_handler(commands=['id'])
def hande_id(message):
    chat_id = message.chat.id
    
    bot.send_message(chat_id, f"chat id: {chat_id}")
#-----------------------------------------------------------
@bot.message_handler(commands=['new'])
def handle_new(message):
    if type(message) == telebot.types.Message:
        chat_id = message.chat.id
    else:
        chat_id = message

    create_df('all_info_newrock') # updating all products .csv
    df = pd.read_csv('all_info_newrock.csv')
    #diff_count = df['url'].nunique()
    if 'newrock13042024.csv' in os.listdir('newrock_old'):
        print('newrock 13.04.2024')
        df = pd.read_csv('all_info_newrock.csv')

        files = os.listdir('newrock_old')
        last_file = files[-1]
        df_old = pd.read_csv(f'newrock_old/{last_file}')
        diff = df[~df['url'].isin(df_old['url'])]
        diff = diff.drop(columns='Unnamed: 0').reset_index(drop=True)
        #bot.send_message(chat_id, f"new: {diff.nunique()}")    
        print(diff.nunique())
        if not diff.empty:
            diff_parsed = diff.apply(get_product, axis=1)
            print('starting for:')
            for index, row in diff_parsed.iterrows():
                print(index)
                image_url = row["images"]
                descriptions = row["sizes"]
                caption = ", ".join(map(str, descriptions)) # ????
                bot.send_photo(chat_id, image_url, caption=caption)
            print('saving new df')
            hande_update(message)
#-----------------------------------------------------------
scheduler = BackgroundScheduler()
scheduler.add_job(handle_new, 'interval', minutes=5, args=[430697715]) 
scheduler.start()

bot.polling()
