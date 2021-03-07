from PIL import ImageFont, ImageDraw, Image
from expiringdict import ExpiringDict
from random import choice
from asyncio import sleep
import itertools
import textwrap
import logging
import asyncio
import json
import os
import io


# CONSTS
MULTIPLIER = 20

BACKGROUND_COLOR = (0, 0, 0, 0)
BUBBLE_COLOR = "#182533"
TIME_COLOR = "#485e73"
FONT_FILE = "Segoe UI.ttf"
FONT_FILE_BOLD = "Segoe UI smallbold.ttf"
FONT_SIZE = 25 * MULTIPLIER
TIME_FONT_SIZE = 20 * MULTIPLIER
LINE_SPACE = 34 * MULTIPLIER
PADDING_LINES = 30 * MULTIPLIER
PADDING_TIME = 40 * MULTIPLIER
NAME_PADDING = 20 * MULTIPLIER
OFFSET_IMAGE = 60 * MULTIPLIER
MAX_LEN = 500 * MULTIPLIER

USER_COLORS = (
    "#FB6169",
    "#62D4E3",
    "#65BDF3",
    "#85DE85",
    "#FF5694",
    "#F3BC5X",
    "#B48BF2",
)
PROFILE_COLORS = (
    "#DD4554",
    "#DB863B",
    "#7965C1",
    "#63AA55",
    "#41A4A6",
    "#4388B9",
    "#CB4F87",
)


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
    return USER_COLORS[user_id % 7]


def get_profile_color(user_id: int) -> str:
    return PROFILE_COLORS[user_id % 7]


def create_sticker(name, user_id, text, profile_pic, date_time):
    ImageDraw.rounded_rectangle = rounded_rectangle
    font = ImageFont.truetype(FONT_FILE, FONT_SIZE)

    # Variables
    wrapper = textwrap.TextWrapper(width=45, break_long_words=True)
    text = [wrapper.wrap(i) for i in text.split("\n") if i != ""]
    text = list(itertools.chain.from_iterable(text))
    # Get the highest possible font size from name or text
    width_of_lines = max(font.getsize(name)[0], *(font.getsize(line)[0] for line in text))
    length_of_line = len(text) * LINE_SPACE

    # drawing chat bubble
    pad_for_time = PADDING_TIME
    if width_of_lines < MAX_LEN:
        pad_for_time += 30

    bubble = Image.new(
        "RGBA",
        (
            width_of_lines + PADDING_LINES + pad_for_time + 20 * MULTIPLIER,
            length_of_line + PADDING_LINES + NAME_PADDING
        ),
        color=BUBBLE_COLOR
    )
    img = Image.new(
        "RGBA",
        (
            width_of_lines + OFFSET_IMAGE + 80 * MULTIPLIER + pad_for_time,
            length_of_line + 70 * MULTIPLIER + NAME_PADDING
        ),
        BACKGROUND_COLOR
    )
    logging.debug("img size: (%d, %d)", *img.size)
    d = ImageDraw.Draw(img)

    d.rounded_rectangle = rounded_rectangle

    x1 = OFFSET_IMAGE
    logging.debug("x1 is %d", x1)
    x2 = bubble.size[0] + OFFSET_IMAGE
    logging.debug("x2 is %d", x2)

    # CENTER Y axis
    y1 = int(.5 * img.size[1]) - int(.5 * bubble.size[1])
    y2 = int(.5 * img.size[1]) + int(.5 * bubble.size[1])
    lower = -0.1
    d.rounded_rectangle(
        d, ((x1, y1), (x2 + 7 * MULTIPLIER, y2 + 5 * MULTIPLIER)), 7 * MULTIPLIER,
        fill=BUBBLE_COLOR, outline=BACKGROUND_COLOR
    )
    d.polygon(
        [
            (x1 + 35 * MULTIPLIER, y2 + 5 * MULTIPLIER + lower * MULTIPLIER),
            (x1 + 35 * MULTIPLIER, y2 - 49 * MULTIPLIER),
            (x1 - 15 * MULTIPLIER, y2 + 5 * MULTIPLIER + lower * MULTIPLIER)
        ],
        fill=BUBBLE_COLOR
    )
    d.pieslice(((x1 - 30 * MULTIPLIER, y2 - 30 * MULTIPLIER), (x1, y2 + 5 * MULTIPLIER)), 0, 90, fill=BACKGROUND_COLOR)

    # drawing image circle
    if profile_pic:
        im = Image.open(io.BytesIO(profile_pic))
    else:
        im = Image.new("RGB", (5000, 5000), color=get_profile_color(user_id))
        to_draw = name[0]
        profile_pic_drawer = ImageDraw.Draw(im)
        name_font = ImageFont.truetype(FONT_FILE, 125 * MULTIPLIER)
        w, h = profile_pic_drawer.textsize(to_draw, font=name_font)

        profile_pic_drawer.text(((5000 - w) // 2, (4000 - h) // 2), to_draw, fill="white", font=name_font)

    bigsize = (im.size[0] * 3, im.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(im.size, Image.LANCZOS)
    im.putalpha(mask)
    im = im.resize((40 * MULTIPLIER, 40 * MULTIPLIER), Image.LANCZOS)
    img.paste(im, box=(5 * MULTIPLIER, y2 - 35 * MULTIPLIER, 45 * MULTIPLIER, y2 + 5 * MULTIPLIER), mask=im)
    text_draw = ImageDraw.Draw(img)

    # write text
    padd = 23 * MULTIPLIER + NAME_PADDING
    for x in text:
        text_draw.text((x1 + 18 * MULTIPLIER, y1 + padd), font=font, text=x)
        padd += LINE_SPACE
    # draw time
    # smaller font
    font = ImageFont.truetype(FONT_FILE, TIME_FONT_SIZE)

    text_draw.text(
        (width_of_lines + PADDING_LINES + pad_for_time + 21 * MULTIPLIER,
         length_of_line + PADDING_LINES - 8 * MULTIPLIER + NAME_PADDING),
        text=date_time,
        font=font, fill=TIME_COLOR)

    # write name
    # bigger font
    font = ImageFont.truetype(FONT_FILE_BOLD, FONT_SIZE)
    text_draw.text((x1 + 18 * MULTIPLIER, 28 * MULTIPLIER), font=font, text=name, fill=get_user_color(user_id))
    img.thumbnail((500, 500), Image.LANCZOS)

    return img


class Storage:
    def __init__(self, fn: str = None):
        self.file = fn
        if self.file and os.path.exists(self.file):
            with open(self.file, "r", encoding="utf-8") as out:
                self.quotes = json.loads(out.read())
        else:
            self.quotes = {}
        # Two hours per cache
        self.cache = ExpiringDict(max_len=1000, max_age_seconds=60 * 60 * 2)

    def save(self, quotes):
        logging.debug("Saving quotes..")
        self.quotes = quotes
        if self.file:
            logging.debug("Writing to file")
            with open(self.file, "w", encoding="utf-8") as out:
                out.write(json.dumps(self.quotes))
        else:
            logging.debug("No file to write to. Skipping...")


if __name__ == "__main__":
    from telethon import TelegramClient, events, utils
    from telethon.tl import types

    logging.basicConfig(level=logging.INFO)
    # Storage
    storage = Storage("file.json")
    # Fill this if you want to run it
    api_id: int   = 94575
    api_hash: str = "a3406de8d171bb422bb6ddf3bbd800e2"
    token         = "<INSERT TOKEN HERE>"
    client        = TelegramClient("bot", api_id, api_hash, sequential_updates=True)
    allowed_chats = None
    MIN_LEN = 3


    async def create_cached(client, quote: dict):
        key = f"{quote['id']}{quote['sender']}"
        cached  = storage.cache.get(key)
        if cached:
            return cached

        message_id = quote["id"]
        text       = quote["text"]
        msg_date   = quote["msg_date"]
        sender     = await client.get_entity(int(quote["sender"]))
        picture    = await client.download_profile_photo(sender, file=bytes)

        image = create_sticker(
            utils.get_display_name(sender),
            sender.id,
            text,
            picture,
            msg_date,
        )
        image_out      = io.BytesIO()
        image_out.name = "sticer.webp"
        image.save(image_out, "WebP", transparency=0)
        image_out.seek(0)

        new_quote = await client.upload_file(image_out)
        storage.cache[key] = new_quote
        return new_quote


    @client.on(events.NewMessage(chats=allowed_chats, pattern=r"#q(uote)?"))
    async def add_quote(event):
        chat = str(event.chat_id)  # JSON saves ints as string for keys
        if not event.is_reply:
            quotes = storage.quotes
            amount = len(quotes.get(chat, []))

            await event.reply(
                f"There are `{amount}` quotes saved for this group."
                "\nReply to a message with `#quote` to cite that message, "
                "and `#recall` to recall."
            )
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

        quote = {
            "id": str(reply_msg.id),
            "text": text,
            "sender": sender.id,
            "msg_date": reply_msg.date.strftime("%H:%M")
        }

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
        # Prepare quote for best user experience
        asyncio.create_task(create_cached(client, quote))
        await event.respond(f"Quote saved!  (ID:  `{reply_msg.id}`)")


    @client.on(events.NewMessage(chats=allowed_chats, pattern=r"#rmq(?:uote)? (\d+)"))
    async def rm_quote(event):
        query_id = event.pattern_match.group(1)
        chat = str(event.chat_id)
        quotes = storage.quotes
        if chat in quotes:
            for q in quotes[chat]:
                if query_id == q["id"]:
                    quotes[chat].remove(q)
                    key = f"{q['id']}{q['sender']}"
                    if key in storage.cache:
                        # clear from cache
                        del storage.cache[key]
                    storage.save(quotes)
                    await event.reply(f"Quote `{query_id}` in chat: `{chat}` removed")
                    return
        else:
            await event.reply(f"No quote with ID `{query_id}`")


    # TODO maybe think of a better regex
    @client.on(events.NewMessage(chats=allowed_chats, pattern=r"#recall ?(.*)"))
    async def recall_quote(event):
        query = event.pattern_match.group(1)
        chat  = str(event.chat_id)

        matched = []
        quotes  = storage.quotes.get(chat)

        if not quotes:
            msg = await event.reply(f"No quotes found for chat `{chat}`")
            await sleep(10)
            await msg.delete()
            return

        if not query:
            matched = quotes
        else:
            query = query.lower()
            for q in quotes:
                if query == q["id"]:
                    matched.append(q)
                    break
                if query in q["text"].lower():
                    matched.append(q)
                    continue

        if not matched:
            msg = await event.reply(f"No quotes matching query:  `{query}`")
            await sleep(10)
            await msg.delete()
            return

        quote = choice(matched)
        cached = await create_cached(client, quote)

        await client.send_file(
            event.chat_id, cached,
            caption=f"message id: {quote['id']}",
            reply_to=event.message.reply_to_msg_id
        )


    client.start(bot_token=token)
    client.run_until_disconnected()

