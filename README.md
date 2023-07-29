# ChatGPT Image Bot Project

This is a project for the course, which aims to create a Telegram bot that utilizes the power of OpenAI's GPT language model to assist users with text and visual-related tasks.

## Overview

The ChatGPT Image Bot is designed to respond to user messages with text and, when needed, generate images based on the user's image description. It leverages the OpenAI Chat API and Image API to achieve these functionalities.

## Prerequisites

To run this project, you need to have the following components set up:

1. Python 3.7 or higher
2. aiogram library
3. pandas library
4. re (regular expression) library
5. OpenAI Python library (`openai`)

Additionally, you need an OpenAI API key (`YOUR_TOKEN`) to access the OpenAI Chat API for language model responses and the Image API for generating images.

## Setup

1. Clone the project repository and navigate to the project directory.
2. Install the required dependencies using `pip install aiogram pandas openai`.
3. Set your OpenAI API key by replacing `"YOUR_TOKEN"` with your actual API key in the code.

## Usage

1. The bot responds to the `/start` command, which registers the user if they are new or welcomes them back if they are already registered.

2. The `/get_tokens` command increases the token capacity of the user if a cooldown period has passed since the last increase.

3. The `/get_pic` command allows the user to provide a description of the image they want to generate.

4. To generate an image, use the `[IMAGE]{description of the image}` tool in the message. The bot will then attempt to generate the image based on the provided description.

## Important Notes

- Since the GPT language model cannot directly generate images, it uses a special tool format (`[IMAGE]{description of the image}`) to indicate the appearance of the picture in the response.

- Make sure to use a detailed image description in the tool format to get more accurate and relevant image generation results.

## Project Structure

- `main.py`: The main script containing the bot's functionality, message handlers, and API integration.
- `users.csv`: A CSV file to store user data, including token capacity and context for conversation history.

## How to Run

1. After setting up the prerequisites and updating the API key, run the `main.py` script.

2. The bot will start listening for incoming messages and respond accordingly.

3. User data (including token capacity) will be saved to `users.csv` after each execution.

## Credits

This project is built using the `aiogram` library for Telegram bot interactions and the `pandas` library for managing user data. The powerful language model is provided by OpenAI's GPT.

Note: Make sure to adhere to OpenAI's guidelines and terms of use when using the GPT language model and API.

Enjoy exploring the capabilities of the ChatGPT Image Bot! If you have any questions or feedback, feel free to reach out.

Happy coding!
