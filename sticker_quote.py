import io
import itertools
import json
import logging
import os
import textwrap
from asyncio import sleep
from random import choice

from PIL import ImageFont, ImageDraw, Image
from telethon import TelegramClient, events, utils
from telethon.tl import types

logging.basicConfig(level=logging.DEBUG)

# CONSTS
BACKGROUND_COLOR = (0, 0, 0, 0)
BUBBLE_COLOR = "#182533"
TIME_COLOR = "#485e73"
FONT_FILE = "Segoe UI.ttf"
FONT_FILE_BOLD = "Segoe UI smallbold.ttf"
FONT_SIZE = 15
LINE_SPACE = 24
PADDING_LINES = 20
PADDING_TIME = 30
NAME_PADDING = 20
OFFSET_IMAGE = 70
MAX_LEN = 500
# Telethon related
api_id: int = 
api_hash: str = ""
token = ""
storage_file = "file.json"
session_file = "bot"
allowed_chats = [
    # list of allowed chats
]


def rounded_rectangle(self: ImageDraw, xy, corner_radius, fill=None, outline=None):
    upper_left_point = xy[0]
    bottom_right_point = xy[1]

    self.pieslice(
        [upper_left_point, (upper_left_point[0] + corner_radius * 2, upper_left_point[1] + corner_radius * 2)],
        180,
        270,
        fill=fill,
        outline=outline
    )
    self.pieslice(
        [(bottom_right_point[0] - corner_radius * 2, bottom_right_point[1] - corner_radius * 2),
         bottom_right_point],
        0,
        90,
        fill=fill,
        outline=outline
    )

    self.pieslice([(upper_left_point[0], bottom_right_point[1] - corner_radius * 2),
                   (upper_left_point[0] + corner_radius * 2, bottom_right_point[1])],
                  90,
                  180,
                  fill=fill,
                  outline=outline
                  )
    self.pieslice([(bottom_right_point[0] - corner_radius * 2, upper_left_point[1]),
                   (bottom_right_point[0], upper_left_point[1] + corner_radius * 2)],
                  270,
                  360,
                  fill=fill,
                  outline=outline
                  )

    self.rectangle(
        [
            (upper_left_point[0], upper_left_point[1] + corner_radius),
            (bottom_right_point[0], bottom_right_point[1] - corner_radius)
        ],
        fill=fill,
        outline=fill
    )

    self.rectangle(
        [
            (upper_left_point[0] - 1 + corner_radius, upper_left_point[1] + 1),
            (bottom_right_point[0] - corner_radius, bottom_right_point[1])
        ],
        fill=fill,
        outline=fill
    )

    self.line([(upper_left_point[0] + corner_radius, upper_left_point[1]),
               (bottom_right_point[0] - corner_radius, upper_left_point[1])], fill=outline)
    self.line([(upper_left_point[0] + corner_radius, bottom_right_point[1]),
               (bottom_right_point[0] - corner_radius, bottom_right_point[1])], fill=outline)
    self.line([(upper_left_point[0], upper_left_point[1] + corner_radius),
               (upper_left_point[0], bottom_right_point[1] - corner_radius)], fill=outline)
    self.line([(bottom_right_point[0], upper_left_point[1] + corner_radius),
               (bottom_right_point[0], bottom_right_point[1] - corner_radius)], fill=outline)


# get color
def get_user_color(user_id: int) -> str:
    colors = ["#FB6169", "#85DE85",
              "#F3BC5X", "#65BDF3",
              "#B48BF2", "#FF5694",
              "#62D4E3", "#FAA357"]
    pos = [0, 7, 4, 1, 6, 3, 5][user_id % 7]
    return colors[pos]


def create_sticker(name, user_id, text, profile_pic, date_time):
    ImageDraw.rounded_rectangle = rounded_rectangle
    font = ImageFont.truetype(FONT_FILE, FONT_SIZE)

    # Variables
    wrapper = textwrap.TextWrapper(width=50, break_long_words=True)
    text = [wrapper.wrap(i) for i in text.split('\n') if i != '']
    text = list(itertools.chain.from_iterable(text))

    # drawing chat bubble
    width_of_lines, _ = font.getsize(text[0])
    for x in text:
        temp_width, _ = font.getsize(x)
        if temp_width > width_of_lines:
            width_of_lines = temp_width

    length_of_line = len(text) * LINE_SPACE
    pad_for_time = PADDING_TIME
    if width_of_lines < MAX_LEN:
        pad_for_time = PADDING_TIME + 30

    width_of_lines = max(font.getsize(name)[0], width_of_lines)
    bubble = Image.new('RGBA',
                       (width_of_lines + PADDING_LINES + pad_for_time, length_of_line + PADDING_LINES + NAME_PADDING),
                       color=BUBBLE_COLOR)
    img = Image.new('RGBA', (width_of_lines + OFFSET_IMAGE + 40 + pad_for_time, length_of_line + 50 + NAME_PADDING),
                    (0, 0, 0, 0))

    d = ImageDraw.Draw(img)

    d.rounded_rectangle = rounded_rectangle

    x1 = OFFSET_IMAGE
    x2 = bubble.size[0] + OFFSET_IMAGE
    # CENTER Y axis
    y1 = int(.5 * img.size[1]) - int(.5 * bubble.size[1])
    y2 = int(.5 * img.size[1]) + int(.5 * bubble.size[1])
    d.rounded_rectangle(d, ((x1, y1), (x2, y2)), 14, fill=BUBBLE_COLOR, outline=BACKGROUND_COLOR)
    d.polygon([(x1 + 30, y2 - 1), (x1 + 30, y2 - 40), (x1 - 15, y2 - 1)], fill=BUBBLE_COLOR)
    d.pieslice(((x1 - 30, y2 - 30), (x1, y2)), 0, 90, fill=BACKGROUND_COLOR)

    # drawing image circle

    im = Image.open(io.BytesIO(profile_pic))
    bigsize = (im.size[0] * 3, im.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(im.size, Image.ANTIALIAS)
    im.putalpha(mask)
    im = im.resize((50, 50), Image.ANTIALIAS)
    img.paste(im, box=(5, y2 - 50, 55, y2), mask=im)
    text_draw = ImageDraw.Draw(img)

    # write text
    padd = 10 + NAME_PADDING
    for x in text:
        text_draw.text((x1 + 15, y1 + padd), font=font, text=x)
        padd += LINE_SPACE
    # draw time
    text_draw.text(
        (width_of_lines + PADDING_LINES + pad_for_time + 20, length_of_line + PADDING_LINES - 12 + NAME_PADDING),
        text=date_time,
        font=font, fill=TIME_COLOR)

    # write name
    # bigger font
    font = ImageFont.truetype(FONT_FILE_BOLD, FONT_SIZE)
    text_draw.text((x1 + 15, 22), font=font, text=name, fill=get_user_color(user_id))

    return img


class Storage:
    def __init__(self, file=None):
        self.file = file
        if self.file:
            if not os.path.exists(self.file):
                with open(self.file, "w", encoding="utf-8") as out:
                    out.write("{}")
            with open(self.file, "r", encoding="utf-8") as out:
                self._quotes = json.loads(out.read())
        else:
            self._quotes = {}

    @property
    def quotes(self):
        return self._quotes

    @quotes.setter
    def quotes(self, quotes):
        self._quotes = quotes

    def save(self, quotes):
        print("saving")
        self.quotes = quotes
        with open(self.file, "w", encoding="utf-8") as out:
            out.write(json.dumps(self.quotes))


storage = Storage(storage_file)

client = TelegramClient(session_file, api_id, api_hash, sequential_updates=True)
MIN_LEN = 3


@client.on(events.NewMessage(chats=allowed_chats, pattern=r"#q(uote)?"))
async def add_quote(event):
    chat = str(event.chat_id)  # JSON saves ints as string for keys
    if not event.is_reply:
        quotes = storage.quotes
        amount = len(quotes[chat])

        await event.reply(
            f"There are `{amount}` quotes saved for this group."
            + "\nReply to a message with `#quote` to cite that message, "
            + "and `#recall` to recall.")
        return

    reply_msg = await event.get_reply_message()
    # Forwards not allowed
    if reply_msg.forward:
        return

    text = reply_msg.raw_text
    # text length needs to be at least > MIN_LEN
    if len(text) < MIN_LEN:
        return
    # No files in the message
    if reply_msg.file:
        return

    sender: types.User = await reply_msg.get_sender()
    # no anonymous senders
    if isinstance(sender, types.Channel) or sender.bot:
        return

    quote = {"id": str(reply_msg.id),
             "text": text,
             "sender": sender.id,
             "date": reply_msg.date.strftime("%Y-%m-%d"),
             "msg_date": f"{event.date.hour}:{event.date.minute}"}

    quotes = storage.quotes
    if quotes.get(chat):
        for q in quotes[chat]:
            if quote["id"] == q["id"]:
                msg = await event.reply("Duplicate quote in database")
                await sleep(10)
                await msg.delete()
                return
        quotes[chat].append(quote)
    else:
        quotes[chat] = [quote]
    storage.save(quotes)

    await event.respond(f"Quote saved!  (ID:  `{reply_msg.id}`)")


@client.on(events.NewMessage(chats=allowed_chats, pattern=r"#rmq(?:uote)? (\d+)"))
async def rm_quote(event):
    query_id = event.pattern_match.group(1)
    chat = str(event.chat_id)
    quotes = storage.quotes
    try:
        for q in quotes[chat]:
            if query_id == q["id"]:
                quotes[chat].remove(q)
                storage.save(quotes)
                await event.reply(f"Quote `{query_id}` in chat: `{chat}` removed")
                return
    except KeyError:
        pass

    await event.reply(f"No quote with ID `{query_id}`")


# TODO maybe think of a better regex
@client.on(events.NewMessage(chats=allowed_chats, pattern=r"#recall ?(.*)"))
async def recall_quote(event):
    phrase = event.pattern_match.group(1)
    chat = str(event.chat_id)

    match_quotes = []
    quotes = storage.quotes.get(chat)

    if not quotes:
        msg = await event.reply(f"No quotes found for chat `{chat}`")
        await sleep(10)
        await msg.delete()
        return

    if not phrase:
        match_quotes = quotes
    else:
        phrase = phrase.lower()
        for q in quotes:
            id = q["id"]
            text = q["text"].lower()

            if phrase == id:
                match_quotes.append(q)
                break
            if phrase in text:
                match_quotes.append(q)

    if not match_quotes:
        msg = await event.reply(f"No quotes matching query:  `{phrase}`")
        await sleep(10)
        await msg.delete()
        return

    quote = choice(match_quotes)

    text = quote["text"]
    sender = await client.get_entity(int(quote["sender"]))
    quote_date = quote["date"]
    msg_date = quote["msg_date"]

    profile_pic = await client.download_profile_photo(sender, file=bytes)

    image = create_sticker(utils.get_display_name(sender), sender.id, text, profile_pic,
                           msg_date)
    image_stream = io.BytesIO()
    image_stream.name = "sticer.webp"
    image.save(image_stream, "WebP", transparency=0)
    image_stream.seek(0)
    await client.send_file(event.chat_id, image_stream, caption="original date: " + quote_date,
                           reply_to=event.message.reply_to_msg_id)


client.start(bot_token=token)
client.run_until_disconnected()