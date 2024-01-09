import requests
import telebot
import os
from telebot import types
import time
from webserver import keep_alive

# Set up your Telegram bot token
telegram_token = os.environ['TELEGRAM_TOKEN']

# Initialize the Telegram bot
bot = telebot.TeleBot(telegram_token)

# API keys
api_key = os.environ["API_KEY1"]
    



# Function to convert x.com URL to twitter.com format
def convert_to_twitter_url(url):
    if "x.com" in url:
        return url.replace("x.com", "twitter.com")
    else:
        return url

# Command handler for the /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Send me a Twitter link and I'll fetch information about it.")

# Handling non-twitter.com or x.com links
@bot.message_handler(func=lambda message: "twitter.com" not in message.text and "x.com" not in message.text)
def handle_other_links(message):
    bot.reply_to(message, "Sorry, I can only process Twitter links. Please provide a valid Twitter link.")
    return  # Return to avoid processing further if it's not a Twitter link


# Handler for regular text messages
@bot.message_handler(func=lambda message: True)
def fetch_twitter_info(message):
    try:
        # Get the Twitter URL from the user's message
        twitter_url = convert_to_twitter_url(message.text)

        # Set up the RapidAPI endpoint
        url = "https://twitter65.p.rapidapi.com/api/twitter/links"

        # Set up the payload
        payload = {"url": twitter_url}

        # Set up the headers
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "twitter65.p.rapidapi.com"
        }

        # Make a request to the RapidAPI endpoint
        response = requests.post(url, json=payload, headers=headers)

        # Check if the response code is 200
        if response.status_code == 200:
            # Parse the JSON response
            json_response = response.json()

            # Extract and send URLs as buttons
            for entry in json_response:
                if "urls" in entry:
                    markup = types.InlineKeyboardMarkup()
                    for url_entry in entry["urls"]:
                        url_button = types.InlineKeyboardButton(text=f"Quality: {url_entry['quality']}p", url=url_entry["url"])
                        markup.add(url_button)

                    bot.send_message(message.chat.id, f"Choose a video quality:", reply_markup=markup)

            # Inform the user about video download
            download_message = bot.send_message(message.chat.id, "Downloading the video...")

            # Download and send the highest quality video
            for entry in json_response:
                if "urls" in entry and entry["urls"]:
                    # Sort URLs by quality and select the highest quality URL
                    urls_sorted_by_quality = sorted(entry["urls"], key=lambda x: x.get("quality", 0), reverse=True)
                    highest_quality_url = urls_sorted_by_quality[0]["url"]

                    # Download the video
                    video_content = requests.get(highest_quality_url).content

                    # Update the message to inform the user about video upload
                    bot.edit_message_text(chat_id=message.chat.id, message_id=download_message.message_id,
                                          text="Uploading the Highest_quality video...")

                    # Upload the video to Telegram
                    bot.send_video(message.chat.id, video_content)

                    # Optionally, save the video locally
                    video_file = f"video_{message.chat.id}.mp4"
                    with open(video_file, 'wb') as file:
                        file.write(video_content)

                    # Optionally, remove the locally saved video file
                    os.remove(video_file)

            # Update the message to inform the user that the video upload is complete
            bot.edit_message_text(chat_id=message.chat.id, message_id=download_message.message_id,
                                  text="Video upload complete!")
      
        else:
            bot.reply_to(message, f"Error: {response.status_code}")

    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

# Start the bot
keep_alive()

while True:
    try:
        bot.polling(none_stop=True, timeout=30)
    except Exception as e:
        print(f"Bot polling error occurred: {e}")
        time.sleep(10)  # Wait for 10 seconds before restarting the bot polling
