#-------------------------------------------------
# Wrapper module to make the API call to openAI's models
# 
#
# CHORE: Convert GPT response to json list then assign it to the key (url) see OpenAI API json object parameter
# also, implement tiktoken to properly count number of tokens in a comment string
#-------------------------------------------------------

import os
import openai
from openai import OpenAI
from dotenv import load_dotenv
from json_helper import reddit_worker
import time
#import tiktoken # Not using yet


#-------------------------
# Constants
#--------------------------

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, "..", ".env")
load_dotenv(env_path)
#openai.api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key = os.environ.get("OPENAI_API_KEY"),)
delimiter = "%%%"
prompt = f'Acting as a therapist. You will be given a block of text which contains comments that end with "{delimiter}". Go through the text to count how many comments there are and use that to determine how many indications you will make. After you have identified the number of comments analyze each one as "+" for positive, "0" for neutral, or "-" for negative. Each comment will have a single value. Finally put each value for each comment together as a string with no white space in the order of which you evaluated them. For example your response might look like "0-+00---+" for nine comments.' # GPT behaviour
MAX_CHAR_BYTES = 4096 # Token max for request

#----------------------------
# Functions
#----------------------------

def format_gpt_request(url_comments):
     comments_str = delimiter.join(url_comments)
     curr_diff = 0
     min_diff = float('inf')
     trim_pos = 0
     
     t_comments = 0
     t_comments = comments_str.count(delimiter)
     print("total comments: ", t_comments)
     
     for i in range(len(comments_str)):
          if comments_str[i:i + len(delimiter)] == delimiter:
               curr_diff = abs(len(comments_str[:i + len(delimiter)].encode()) - MAX_CHAR_BYTES)
               
               if curr_diff < min_diff:
                    trim_pos = i + len(delimiter)
                    min_diff = curr_diff
                    
     comments_str = comments_str[:trim_pos]
     return comments_str
               
def request_sentiment(user_prompt, prompt_content):
     sentiments = ""
     comment_count = 0
     comment_count = prompt_content.count(delimiter)
     print("comment count in request: ", comment_count)
     # See OpenAI doc for usage
     response = client.chat.completions.create(
          model="gpt-3.5-turbo-1106",
          temperature=0.7,
          messages=[
               {"role": "system", "content": user_prompt},
               {"role": "user", "content": prompt_content}
          ],
     )
     if response.choices[0].finish_reason == 'length':
          time.sleep(10)
          print("Max tokens for model reached. Contact support")
          return None
     else:
          time.sleep(10)
          sentiments = response.choices[0].message.content
          print("sentiments len: ", len(sentiments))
          return sentiments
     
def get_vibe(url, tag_data, vibe_dir):
     try:
          analysis = ""
          vibe_values = []
          vibe_dict = {}
          analysis = request_sentiment(prompt, format_gpt_request(tag_data))
          vibe_values = [value for value in analysis]
          vibe_dict[url] = vibe_values
          vibe_fname = os.path.join(vibe_dir, f"{url.replace('https://old.reddit.com', 'reddit').replace('/', '_')}sentiment.json")
          
          if reddit_worker.write_dict(vibe_dict, vibe_fname):
               return vibe_dict
          
     except Exception as e:
          print(f"Error: {e}")
          return None
