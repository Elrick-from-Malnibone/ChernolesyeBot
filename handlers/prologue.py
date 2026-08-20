import asyncio
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest, TelegramError

PROLOGUE_PARTS = [
    """Сквозь прутья своей клетки ты видишь покидающую деревню процессию. Возглавляет ее сам Рунмабур — повелитель Гномов Болотища. Облаченный в кольчужную рубаху, с рогатым шлемом на голове и огромным боевым топором в руках, он, несмотря на свой маленький рост, являет собой весьма внушительное зрелище. Следом стройными рядами шествуют ратники — свирепые, вооруженные сверкающими бердышами бородатые крепыши. Колонну лучников замыкают трубачи. Звуки бравурной музыки наполняют воздух — все свидетельствует о том, что обитатели Болотища готовятся выступить в боевой поход против своего извечного врага — Гномов Каменного Моста. Где именно произойдет решающая битва, тебе не ведомо.""",
    """Для многих поколений обитателей Аллансии ужасное Чернолесье, метко прозванное в народе Проклятым Лесом, олицетворяет собой квинтэссенцию абсолютного зла. В его мрачных чащобах, куда не проникает солнечный свет, вынашивают свои злобные замыслы тысячи и тысячи мерзких чудовищ, имени и названия которых нет ни в одном из ныне существующих языков. Дикие звери и орки, гоблины и тролли, великаны, ведьмы и ужасные умертвия нашли себе надежное пристанище под его покровом. И нечего удивляться тому, что путешественники и торговые караваны, следующие из дальних южных земель, предпочитают полный опасностей окольный путь, чреватый потерей трех-четырех дней и возможной встречей с бесчинствующими в этих краях многочисленными разбойничьими шайками, печальной перспективе провести хотя бы одну ночь в этой адской чаще, откуда, как гласит людская молва, нет дороги назад.""",
    """Что касается тебя, то давно уже нет у тебя иного желания, как, невзирая ни на что, вернуться под густые своды Чернолесья. Ибо ты — еще в младенчестве был похищен у любящей матери злокозненным повелителем Гномов Болотища королем Рунмабуром. Запертый в клетке, третируемый наподобие дикого зверя, ты стойко претерпевал жестокие издевательства и безмолвно сносил бесконечные унижения. Ты мечтал лишь об одном — вернуться в Проклятый Лес. Бежать, скрыться от проклятых Гномов и злобного Рунмабура, бежать... и отомстить!""",
    """Несмотря на то, что за долгие годы, проведенные в плену у Гномов Болотища, тебе не раз выпадала удобная возможность бежать, одно обстоятельство каждый раз останавливало тебя. Дело в том, что, сызмальства отрезанный от внешнего мира толстыми прутьями тюремной клетки, ты имеешь весьма условное представление о том, что поджидает тебя за пределами ненавистного Болотища, и в каком направлении тебе следует держать свой путь. Последние несколько недель обитатели Болотища находятся в состоянии войны со своими извечными врагами — Гномами соседнего Каменного Моста. Царящая в деревне суматоха дает тебе возможность отдохнуть и набраться сил. Ты чувствуешь себя настолько окрепшим, что позволяешь себе полностью расслабиться и сконцентрировать свой умственный взор на окружающих тебя гномах в попытке проникнуть в их мысли. В то же мгновение на тебя обрушивается волна смутных образов. Разочарованный тем, что не может узнать ничего полезного, ты уже отчаиваешься, как вдруг наподобие молнии воздух пронзает невидимая мысль: один из советников Рунмабура думает о встрече, которую повелитель Болотища назначил в самой глуши Чернолесья Гиллибрану — предводителю гномов Каменного Моста. Встреча должна состояться через четыре дня. По очевидным причинам место встречи держится в строгом секрете, известно лишь, что она состоится в самом сердце Проклятого Леса.""",
    """Ты понимаешь, что у тебя появился шанс! Если только тебе удастся бежать, пробраться в Чернолесье и, незаметно следуя за гномьей ратью, разузнать, где именно состоятся переговоры вождей. Тогда во время встречи, когда короля не будет окружать многочисленная стража, ты сможешь попытаться убить ненавистного Рунмабура, одним ударом отомстив и ему, и всем гномам Болотища."""
]


def _keyboard(part: int) -> InlineKeyboardMarkup:
    row = []
    if part < len(PROLOGUE_PARTS) - 1:
        row.append(InlineKeyboardButton("▶️ Далее", callback_data="next_prologue"))
    row.append(InlineKeyboardButton("⏭ Пропустить", callback_data="skip_prologue"))
    return InlineKeyboardMarkup([row])


async def _stream_draft(bot, chat_id: int, draft_id: int, text: str, cps: float = 40.0):
    """Стрим через draft. Без постоянного edit обычного сообщения."""
    start = asyncio.get_event_loop().time()
    last = ""

    while True:
        n = min(len(text), int((asyncio.get_event_loop().time() - start) * cps) + 1)
        chunk = text[:n]
        if chunk != last:
            try:
                await bot.send_message_draft(
                    chat_id=chat_id,
                    draft_id=draft_id,
                    text=chunk or "…",
                )
                last = chunk
            except TelegramError:
                # нет поддержки / ошибка — выходим, покажем текст целиком ниже
                return False
        if n >= len(text):
            break
        await asyncio.sleep(0.05)
    return True


async def _show_part(bot, chat_id: int, part: int, context: ContextTypes.DEFAULT_TYPE, old_msg_id: int | None = None):
    text = PROLOGUE_PARTS[part]
    draft_id = chat_id  # любой ненулевой int, стабильный на пользователя

    # стрим черновиком
    ok = await _stream_draft(bot, chat_id, draft_id, text, cps=45)

    # убрать старое сообщение с прошлой частью
    if old_msg_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=old_msg_id)
        except BadRequest:
            pass

    # финальное сообщение (draft сам исчезнет)
    msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=_keyboard(part),
    )
    context.user_data["prologue_msg_id"] = msg.message_id
    context.user_data["prologue_part"] = part
    return msg


async def send_prologue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # картинка: папка image в корне
    img = Path("image/prologue.jpg")
    if img.exists():
        with open(img, "rb") as f:
            await context.bot.send_photo(chat_id=chat_id, photo=f)
    else:
        await context.bot.send_message(chat_id, f"⚠️ нет файла: {img.resolve()}")

    await _show_part(context.bot, chat_id, 0, context)


async def next_prologue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    part = context.user_data.get("prologue_part", 0) + 1
    if part >= len(PROLOGUE_PARTS):
        return

    old_id = context.user_data.get("prologue_msg_id")
    await _show_part(context.bot, query.message.chat.id, part, context, old_msg_id=old_id)


async def skip_prologue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    mid = context.user_data.get("prologue_msg_id") or query.message.message_id
    full = "\n\n".join(PROLOGUE_PARTS)

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mid,
            text=full,
            reply_markup=None,
        )
    except BadRequest:
        await context.bot.send_message(chat_id, full)