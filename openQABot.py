#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

"""A telegram bot making use of OpenQA"""
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
from telegram.error import TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError
from SPARQLWrapper import SPARQLWrapper, JSON
from emoji import emojize



import logging, sys, requests, telegram, re, thread, time

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

global RESTURL, showMePicturesStr, tellMeMoreStr, nothingStr, resList, CANCELLED
RESTURL = "http://localhost:8081/openqa.webserver-v0.0.7-beta-full/api/rest/search?q="
showMePicturesStr = "Show me a Picture!"
tellMeMoreStr = "Tell me more!"
nothingStr = "Nothing"
CANCELLED = False


QUESTION, ASK_USER = range(2)

def start(bot, update):
    update.message.reply_text(
        'Hi! I am a simple bot able to answer questions.'
        'Send /cancel to stop talking to me.\n\n',
        reply_markup=ReplyKeyboardRemove())

    return QUESTION

""" Shows a clock emoji going from 1 to 12 while the REST request is being processed. Gets called as seperate thread"""
def showTickingClock(bot, update):
    count = 1
    time.sleep(5)
    while resList is None and CANCELLED is False:
        update.message.reply_text((emojize(":clock" + str(count) + ":", use_aliases=True)))
        time.sleep(5)
        if(count == 12):
            count = 0
        count = count + 1


def question(bot, update):
    answerContainsPic = False
    answerContainsAbstract = False
    chat_id = update.message.chat_id

    global resList
    resList = None

    try:
        thread.start_new_thread(showTickingClock, (bot, update) )
    except:
        print "Error: unable to start thread"

    r = requests.get(RESTURL + update.message.text)
    logger.info('Question "%s" had answer "%s"' % (update.message.text, r.text)) 
    resList = getInfo(r)
    if(len(resList)==0):
        update.message.reply_text("Hmmm... I think I don't know the answer to this one yet...")
    else:
        count = 0
        for jsonObject in resList:
            for res in jsonObject["results"]["bindings"]:
                update.message.reply_text(res["label"]["value"] + " (" + r.json()[count]['URI_PARAM'] + ")")
                if("thumbnail" in res):
                    answerContainsPic = True
                if("abstract" in res):
                    answerContainsAbstract = True
        if(answerContainsPic and answerContainsAbstract):
            reply_keyboard=[[showMePicturesStr, tellMeMoreStr, nothingStr]]
        elif(answerContainsPic):
            reply_keyboard=[[showMePicturesStr, nothingStr]]
        elif(answerContainsAbstract):
            reply_keyboard=[[tellMeMoreStr, nothingStr]]
        else:
            update.message.reply_text('Please ask me something!', reply_markup=ReplyKeyboardRemove())
            return QUESTION
        update.message.reply_text('What do you want me to do with this answer?', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return ASK_USER

"""Runs a sparql query to find thumbnails and/or abstracts"""
def getInfo(r):
    print type(r)
    jsonObject = r.json()
    resultList = []
    for i in jsonObject:
         sparql = SPARQLWrapper("http://dbpedia.org/sparql")
         sparql.setQuery("""
                     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                     PREFIX dbo: <http://dbpedia.org/ontology/>
                     SELECT DISTINCT ?label ?abstract ?thumbnail
                     WHERE { <%s> rdfs:label ?label .
                            OPTIONAL{<%s> dbo:abstract ?abstract FILTER(LANG(?abstract)='en') } .
                            OPTIONAL{<%s> dbo:thumbnail ?thumbnail}
                     FILTER(LANG(?label)='en')
                     }

         """ % (i['URI_PARAM'], i['URI_PARAM'], i['URI_PARAM']))
         sparql.setReturnFormat(JSON)
         results = sparql.query().convert()
         print "SPARQL RESULT \n"
         print results
         resultList.append(results)
    return resultList

"""Depending wether the answer ressource has a thumbnail or abstract the user can choose which one to see"""
def askUser(bot, update):
    userAnswer = update.message.text
    if(userAnswer == showMePicturesStr):
        showMePictures(bot, update)
    elif(userAnswer == tellMeMoreStr):
        tellMeMore(bot, update)
    elif(userAnswer == nothingStr):
        update.message.reply_text('Oookay')

    update.message.reply_text('Please ask another question!', reply_markup=ReplyKeyboardRemove())
    return QUESTION

def showMePictures(bot, update):
    for jsonObject in resList:
        for res in jsonObject["results"]["bindings"]:
            if("thumbnail" in res):
                update.message.reply_text(res["label"]["value"])
                update.message.reply_photo(res["thumbnail"]["value"])
            else:
                update.message.reply_text('I could not find a picture for %s' % res["label"]["value"])

def tellMeMore(bot, update):
    for jsonObject in resList:
        for res in jsonObject["results"]["bindings"]:
            if("abstract" in res):
                update.message.reply_text(res["abstract"]["value"])
            else:
                update.message.reply_text('I could not find an abstract for %s' % res["label"]["value"])


def cancel(bot, update):
    global CANCELLED
    CANCELLED = True
    user = update.message.from_user
    logger.info("User %s canceled the conversation." % user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(bot, update, error):
    update.message.reply_text('Ooops something went wrong, I\'m sorry!')
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(sys.argv[1])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            QUESTION: [MessageHandler(Filters.text, question)],
            ASK_USER: [RegexHandler('^('+ re.escape(tellMeMoreStr) + '|'+ re.escape(showMePicturesStr) + '|' + re.escape(nothingStr) + ')$', askUser)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
