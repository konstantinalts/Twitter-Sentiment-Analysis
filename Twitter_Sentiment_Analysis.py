# Importing the libraries needed for the project
import tweepy 
import pandas as pd
import mysql.connector
from mysql.connector import Error 
import regex as re
from textblob import TextBlob
import matplotlib.pyplot as plt
import seaborn as sns


# Establishing connection with twitter. The below are the required access from twitter to connect to the twitter API
consumer_key = '###############'
consumer_secret = '##########################'
access_token = '######################'
access_token_secret = '######################'


#Connecting with mySQL database for creating table TWEETS
try:
    db = mysql.connector.connect(host = 'localhost', port = '3306', database = 'tweets_db', user = 'root', password='')
    if db.is_connected():
        print("Connected to mySQL \n")
        cur = db.cursor()
    
     
    #Create table called TWEETS
    
    query = "CREATE TABLE TWEETS (ID INT NOT NULL AUTO_INCREMENT, KEYWORD VARCHAR(100), USER_ACCOUNT VARCHAR(255), NUM_FOLLOWERS INT, NUM_TWEETS INT, NUM_RETWEETS INT, TEXT  TEXT, DATE DATE, LOCATION VARCHAR(255), HASHTAGS VARCHAR(255), SENTIMENT VARCHAR(10), SENTIMENT_SCORE FLOAT(4,2), PRIMARY KEY (ID))"
    cur.execute(query)
    print("executed\n")

    
    
    
except Error as e:
    print(e)

finally:
    db.close()
    print("\n Database connection closed")
    
#Authorising twitter used the tweepy lib
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth,wait_on_rate_limit=True)


#Connecting with mySQL database for inserting tweets

try:
    db = mysql.connector.connect(host = 'localhost', port = '3306', database = 'tweets_db', user = 'root', password='', charset = 'utf8')
    
    if db.is_connected():
        cur = db.cursor()
        
     
        #the list keywords we are searching for
        keywords = ['covid19','covid-19','coronavirus']   
        for keyword in keywords:
            
            #positive = 0
            #neutral = 0
            #negative = 0
            
            for tweet in tweepy.Cursor(api.search,q=keyword+' -filter:retweets', until = '2020-02-29',lang="en", tweet_mode="extended").items(200):
                
                key = keyword #the keyword we are searching for
                user_account = tweet.user.screen_name #User account
                num_followers = tweet.user.followers_count #Number of accounts followers
                num_tweets = tweet.user.statuses_count #Number of accounts tweets
                num_retweets = tweet.retweet_count #Number of accounts retweets
                txt = tweet.full_text #Tweet text
                date = tweet.created_at #Date
                location = tweet.user.location #Location
                
            
                #Hashtags
                hashtags_texts = []
                hashtags = tweet.entities['hashtags']
                
                for hashtag in hashtags:
                    hashtags_texts.append(hashtag['text'])

                #cleaning tweets from urls and mentions
                text = re.sub(r"(?:\@|https?\://)\S+", "", txt)
                
                #Sentiment Analysis
                analysis = TextBlob(text)
                sentiment_score = analysis.sentiment.polarity
     
                if sentiment_score>0:
                    sentiment = 'Positive'
                    positive+=1
                elif sentiment_score==0:
                    sentiment = 'Neutral'
                    neutral+=1
                elif sentiment_score<0:
                   sentiment = 'Negative'
                   negative+=1    
            
                #Store them in the corresponding table in the database
                query = "INSERT INTO tweets(KEYWORD, USER_ACCOUNT, NUM_FOLLOWERS, NUM_TWEETS, NUM_RETWEETS, TEXT, DATE, LOCATION, HASHTAGS, SENTIMENT , SENTIMENT_SCORE) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cur.execute(query, (key, user_account, num_followers, num_tweets, num_retweets, text, date, location, str(hashtags_texts), sentiment, sentiment_score))
                db.commit()
                
                
                
              
           #Pie plot with positive/negative/neutral tweet count
            colors = ['indianred', 'silver', 'cornflowerblue']
            sizes = [positive, neutral, negative]
            labels = 'Positive', 'Neutral', 'Negative'
            
            sentiment_pie = plt.pie(
               x=sizes,
               colors=colors,
               labels=labels,
               startangle=90,
               autopct='%1.1f%%')
            
            plt.legend()
            plt.title("Sentiment Analysis of {} Tweets about {}".format(2700, key))
            plt.show()
            
            #Plotting the sentiment how it changes over time
            q = "SELECT keyword, date, sentiment_score FROM tweets"
    
            #convert the query result to dataframe
            df = pd.read_sql(q, con=db)
            
            
            plt.figure(figsize=(10,4))
            plt.plot(df['date'], df['sentiment_score'])
            sns.set() 
            plt.xlabel('Date')
            plt.ylabel('Sentiment Score')
            plt.title("Sentiment Analysis about {} how it changes over time".format(key))
            plt.show()
            
        #Plotting the sentiment how it is affected by the number of tweets for the three keywords
        query = 'SELECT keyword, sentiment, date, sentiment_score, user_account, num_tweets, num_followers FROM tweets' 
        dataframe = pd.read_sql(query, con=db)
        dataframe.pivot_table(index = 'keyword', columns = 'sentiment', values = 'num_tweets', aggfunc='sum').plot.bar(edgecolor = "white")
        plt.xticks(rotation = 0)
        plt.ylabel("Number of Tweets")
        plt.show()
        
        #Plotting the sentiment how it is affected by the number of followers for the three keywords
        dataframe.pivot_table(index = 'keyword', columns = 'sentiment', values = 'num_followers', aggfunc='sum').plot.bar(edgecolor = "white")
        plt.xticks(rotation = 0)
        plt.ylabel("Number of Followers")
        plt.show()
        
                
     
except Error as e:
    print(e)

finally:
    db.close()
    print("\n Database connection closed")
    
