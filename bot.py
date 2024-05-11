#!/usr/bin/env python3

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from re import match, search

# Importing Credentials & Required Data
from config import Config

# Connecting to Bot
app = Client(
    "RequestTrackerBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Connecting To Database
mongo_client = MongoClient(Config.MONGO_STR)
db_bot = mongo_client['RequestTrackerBot']
collection_ID = db_bot['channelGroupID']

# Regular Expression for #request
requestRegex = "#[rR][eE][qQ][uU][eE][sS][tT] "

# Start & Help Handler
@app.on_message(filters.private & filters.command(["start", "help"]))
async def startHandler(_, msg):
    await msg.reply_text(
        "<b>Hi, I am CineSubz Request Bot🤖",
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🍿 Channel 🍿",
                        url="https://t.me/CineSubzMoviesOfficial"
                    )
                ]
            ]
        )
    )

# return group id when bot is added to group
@app.on_message(filters.new_chat_members)
async def chatHandler(_, msg):
    if msg.new_chat_members[0].is_self:  # If bot is added
        await msg.reply_text(
            f"<b>Hey😁, Your Group ID is <code>{msg.chat.id}</code></b>",
            parse_mode="html"
        )

# return channel id when message/post from channel is forwarded
@app.on_message(filters.forwarded & filters.private)
async def forwardedHandler(_, msg):
    forwardInfo = msg.forward_from_chat
    if forwardInfo.type == "channel":  # If message forwarded from channel
        await msg.reply_text(
            f"<b>Hey😁, Your Channel ID is <code>{forwardInfo.id}</code>\n\n😊Join @CineSubzMoviesOfficial for getting more awesome 🤖bots like this.</b>",
            parse_mode="html"
        )

# /add handler to add group id & channel id with database
@app.on_message(filters.private & filters.command("add"))
async def groupChannelIDHandler(_, msg):
    message = msg.text.split(" ")
    if len(message) == 3:  # If command is valid
        _, groupID, channelID = message
        try:
            int(groupID)
            int(channelID)
        except ValueError:  # If Ids are not integer type
            await msg.reply_text(
                "<b>Group ID & Channel ID should be integer type😒.</b>",
                parse_mode="html"
            )
            return

        documents = collection_ID.find()
        for document in documents:
            try:
                document[groupID]
            except KeyError:
                pass
            else:  # If group id found in database
                await msg.reply_text(
                    "<b>Your Group ID already Added.</b>",
                    parse_mode="html"
                )
                break
            for record in document:
                if record == "_id":
                    continue
                else:
                    if document[record][0] == channelID:  # If channel id found in database
                        await msg.reply_text(
                            "<b>Your Channel ID already Added.</b>",
                            parse_mode="html"
                        )
                        break
        else:  # If group id & channel not found in db
            try:
                botSelfGroup = await app.get_chat_member(int(groupID), 'me')
            except Exception:  # If given group id is invalid
                await msg.reply_text(
                    "<b>😒Group ID is wrong.\n\n😊Join @CineSubzMoviesOfficial for getting more awesome 🤖bots like this.</b>",
                    parse_mode="html"
                )
                return

            if botSelfGroup.status != "administrator":  # If bot is not admin in group
                await msg.reply_text(
                    "<b>🥲Make me admin in Group, Then add use /add.\n\n😊Join @CineSubzMoviesOfficial for getting more awesome 🤖bots like this.</b>",
                    parse_mode="html"
                )
                return

            try:
                botSelfChannel = await app.get_chat_member(int(channelID), 'me')
            except Exception:  # If given channel id is invalid
                await msg.reply_text(
                    "<b>😒Channel ID is wrong.\n\n😊Join @CineSubzMoviesOfficial for getting more awesome 🤖bots like this.</b>",
                    parse_mode="html"
                )
                return

            if not (botSelfChannel.can_post_messages and botSelfChannel.can_edit_messages and botSelfChannel.can_delete_messages and botSelfChannel.can_invite_users and botSelfChannel.can_restrict_members):  # If bot doesn't have enough rights in channel
                await msg.reply_text(
                    "<b>😒I don't have enough rights in channel.\n\n😊Join @CineSubzMoviesOfficial for getting more awesome 🤖bots like this.</b>",
                    parse_mode="html"
                )
                return

            try:  # If everything is okay, then add group & channel id in db
                collection_ID.insert_one(
                    {groupID: [channelID, False]}
                )
                await msg.reply_text(
                    "<b>😊Group & Channel ID Added Successfully.</b>",
                    parse_mode="html"
                )
            except Exception as e:  # If something goes wrong
                await msg.reply_text(
                    f"<b>{str(e)}</b>",
                    parse_mode="html"
                )
    else:  # If command is invalid
        await msg.reply_text(
            "<b>😒Use /add groupID channelID format.</b>",
            parse_mode="html"
        )

# /request handler to send request in channel
@app.on_message(filters.private & filters.command("request"))
async def requestHandler(_, msg):
    if msg.chat.type == "private":  # If command executed in private
        if len(msg.text.split(" ")) > 1:  # If request message found
            requestInfo = search(requestRegex, msg.text)
            if requestInfo:
                requestMessage = msg.text.split(
                    requestInfo.group())[1].strip()
            else:  # If request format not valid
                await msg.reply_text(
                    "<b>😒Request format is invalid.</b>",
                    parse_mode="html"
                )
                return

            documents = collection_ID.find()
            for document in documents:
                try:  # If user's group id found in db
                    document[str(msg.chat.id)]
                except KeyError:
                    pass
                else:
                    try:  # If user's channel id found in db
                        botSelfChannel = await app.get_chat_member(
                            int(document[str(msg.chat.id)][0]), 'me')
                    except Exception:  # If channel id is wrong
                        await msg.reply_text(
                            "<b>😒Your Channel ID is wrong.</b>",
                            parse_mode="html"
                        )
                        return
                    else:
                        if not botSelfChannel.status == "administrator":  # If bot is not admin in channel
                            await msg.reply_text(
                                "<b>😒Make me admin in your channel.</b>",
                                parse_mode="html"
                            )
                            return

                        if document[str(msg.chat.id)][1]:  # If request already sent by user
                            await msg.reply_text(
                                "<b>😒Your Previous Request Already Sent.</b>",
                                parse_mode="html"
                            )
                            return

                        try:  # If everything is okay, then send request
                            await app.send_message(
                                int(document[str(msg.chat.id)][0]),
                                requestMessage
                            )
                            collection_ID.update_one(
                                {str(msg.chat.id): document[str(msg.chat.id)]},
                                {"$set": {str(msg.chat.id): [document[str(msg.chat.id)][0], True]}}
                            )
                            await msg.reply_text(
                                "<b>😊Request Sent Successfully.</b>",
                                parse_mode="html"
                            )
                        except Exception as e:  # If something goes wrong
                            await msg.reply_text(
                                f"<b>{str(e)}</b>",
                                parse_mode="html"
                            )
                        break
            else:  # If user's group id not found in db
                await msg.reply_text(
                    "<b>😒You didn't added your Group ID yet.</b>",
                    parse_mode="html"
                )
        else:  # If request message not found
            await msg.reply_text(
                "<b>😒Use /request message format.</b>",
                parse_mode="html"
            )

# Run The Bot
app.run()
