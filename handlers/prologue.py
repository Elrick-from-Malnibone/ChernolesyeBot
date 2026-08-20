import asyncio
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest, RetryAfter, TelegramError


PROLOGUE_PARTS = [
    """ПРОЛОГ"""
    """Сквозь прутья своей клетки ты видишь покидающую деревню процессию. Возглавляет ее сам Рунмабур — повелитель Гномов Болотища. Облаченный в кольчужную рубаху, с рогатым шлемом на голове и огромным боевым топором в руках, он, несмотря на свой маленький рост, являет собой весьма внушительное зрелище. Следом стройными рядами шествуют ратники — свирепые, вооруженные сверкающими бердышами бородатые крепыши. Колонну лучников замыкают трубачи. Звуки бравурной музыки наполняют воздух — все свидетельствует о том, что обитатели Болотища готовятся выступить в боевой поход против своего извечного врага — Гномов Каменного Моста. Где именно произойдет решающая битва, тебе не ведомо.""",
    """Для многих поколений обитателей Аллансии ужасное Чернолесье, метко прозванное в народе Проклятым Лесом, олицетворяет собой квинтэссенцию абсолютного зла. В его мрачных чащобах, куда не проникает солнечный свет, вынашивают свои злобные замыслы тысячи и тысячи мерзких чудовищ, имени и названия которых нет ни в одном из ныне существующих языков. Дикие звери и орки, гоблины и тролли, великаны, ведьмы и ужасные умертвия нашли себе надежное пристанище под его покровом. И нечего удивляться тому, что путешественники и торговые караваны, следующие из дальних южных земель, предпочитают полный опасностей окольный путь, чреватый потерей трех-четырех дней и возможной встречей с бесчинствующими в этих краях многочисленными разбойничьими шайками, печальной перспективе провести хотя бы одну ночь в этой адской чаще, откуда, как гласит людская молва, нет дороги назад.""",
    """Что касается тебя, то давно уже нет у тебя иного желания, как, невзирая ни на что, вернуться под густые своды Чернолесья. Ибо ты — еще в младенчестве был похищен у любящей матери злокозненным повелителем Гномов Болотища королем Рунмабуром. Запертый в клетке, третируемый наподобие дикого зверя, ты стойко претерпевал жестокие издевательства и безмолвно сносил бесконечные унижения. Ты мечтал лишь об одном — вернуться в Проклятый Лес. Бежать, скрыться от проклятых Гномов и злобного Рунмабура, бежать... и отомстить!""",
    """Несмотря на то, что за долгие годы, проведенные в плену у Гномов Болотища, тебе не раз выпадала удобная возможность бежать, одно обстоятельство каждый раз останавливало тебя. Дело в том, что, сызмальства отрезанный от внешнего мира толстыми прутьями тюремной клетки, ты имеешь весьма условное представление о том, что поджидает тебя за пределами ненавистного Болотища, и в каком направлении тебе следует держать свой путь. Последние несколько недель обитатели Болотища находятся в состоянии войны со своими извечными врагами — Гномами соседнего Каменного Моста. Царящая в деревне суматоха дает тебе возможность отдохнуть и набраться сил. Ты чувствуешь себя настолько окрепшим, что позволяешь себе полностью расслабиться и сконцентрировать свой умственный взор на окружающих тебя гномах в попытке проникнуть в их мысли. В то же мгновение на тебя обрушивается волна смутных образов. Разочарованный тем, что не может узнать ничего полезного, ты уже отчаиваешься, как вдруг наподобие молнии воздух пронзает невидимая мысль: один из советников Рунмабура думает о встрече, которую повелитель Болотища назначил в самой глуши Чернолесья Гиллибрану — предводителю гномов Каменного Моста. Встреча должна состояться через четыре дня. По очевидным причинам место встречи держится в строгом секрете, известно лишь, что она состоится в самом сердце Проклятого Леса.""",
    """Ты понимаешь, что у тебя появился шанс! Если только тебе удастся бежать, пробраться в Чернолесье и, незаметно следуя за гномьей ратью, разузнать, где именно состоятся переговоры вождей. Тогда во время встречи, когда короля не будет окружать многочисленная стража, ты сможешь попытаться убить ненавистного Рунмабура, одним ударом отомстив и ему, и всем гномам Болотища."""
]


def _keyboard(part: int) -> InlineKeyboardMarkup:
    """Кнопки под текущую часть пролога."""
    last = len(PROLOGUE_PARTS) - 1

    if part >= last:
        # последняя часть — только «Начать игру»
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Начать игру", callback_data="start_game")]
        ])

    # не последняя — Далее + Пропустить
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("▶️ Далее", callback_data="next_prologue"),
            InlineKeyboardButton("⏭ Пропустить", callback_data="skip_prologue"),
        ]
    ])


async def _safe_edit(bot, chat_id: int, message_id: int, text: str, reply_markup=None) -> bool:
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
        )
        return True
    except RetryAfter as e:
        await asyncio.sleep(float(e.retry_after) + 0.15)
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
            )
            return True
        except Exception:
            return False
    except BadRequest as e:
        if "not modified" in str(e).lower():
            return True
        return False
    except TelegramError:
        return False


async def _stream_chunks(
    bot,
    chat_id: int,
    message_id: int,
    text: str,
    max_edits: int = 14,
    delay: float = 0.22,
):
    """
    Медленная печать кусками.
    Число правок ограничено — Telegram не режет длинные части.
    В конце всегда полный текст.
    """
    if not text:
        return

    chunk_size = max(35, len(text) // max_edits)
    pos = chunk_size

    while pos < len(text):
        ok = await _safe_edit(bot, chat_id, message_id, text[:pos])
        if not ok:
            await asyncio.sleep(0.8)
        await asyncio.sleep(delay)
        pos += chunk_size

    # гарантия полного текста
    await _safe_edit(bot, chat_id, message_id, text)


async def _show_part(
    bot,
    chat_id: int,
    part: int,
    context: ContextTypes.DEFAULT_TYPE,
    old_msg_id: int | None = None,
):
    text = PROLOGUE_PARTS[part]

    if old_msg_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=old_msg_id)
        except BadRequest:
            pass

    msg = await bot.send_message(chat_id=chat_id, text="…")
    context.user_data["prologue_msg_id"] = msg.message_id
    context.user_data["prologue_part"] = part

    await _stream_chunks(bot, chat_id, msg.message_id, text)

    await asyncio.sleep(0.15)
    await _safe_edit(
        bot,
        chat_id,
        msg.message_id,
        text,
        reply_markup=_keyboard(part),
    )


async def send_prologue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # image/prologue.jpg относительно корня запуска
    img = Path("image/prologue.jpg")
    if not img.exists():
        img = Path(__file__).resolve().parent.parent / "image" / "prologue.jpg"

    if img.exists():
        with open(img, "rb") as f:
            await context.bot.send_photo(chat_id=chat_id, photo=f)
    else:
        await context.bot.send_message(
            chat_id,
            f"⚠️ Картинка не найдена:\n{img.resolve()}",
        )

    await _show_part(context.bot, chat_id, 0, context)


async def next_prologue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    part = context.user_data.get("prologue_part", 0) + 1
    if part >= len(PROLOGUE_PARTS):
        return

    old_id = context.user_data.get("prologue_msg_id")
    await _show_part(
        context.bot,
        query.message.chat.id,
        part,
        context,
        old_msg_id=old_id,
    )


async def skip_prologue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать весь пролог сразу и кнопку «Начать игру»."""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    mid = context.user_data.get("prologue_msg_id") or query.message.message_id
    full = "\n\n".join(PROLOGUE_PARTS)

    context.user_data["prologue_part"] = len(PROLOGUE_PARTS) - 1

    ok = await _safe_edit(
        context.bot,
        chat_id,
        mid,
        full,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Начать игру", callback_data="start_game")]
        ]),
    )
    if not ok:
        await context.bot.send_message(
            chat_id,
            full,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 Начать игру", callback_data="start_game")]
            ]),
        )


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка — сюда потом подключишь реальный старт игры."""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    mid = context.user_data.get("prologue_msg_id") or query.message.message_id

    # убираем кнопки
    try:
        await context.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=mid,
            reply_markup=None,
        )
    except BadRequest:
        pass

    await context.bot.send_message(
        chat_id,
        "⚔️ Игра начинается...\n\n(здесь будет старт игрового процесса)",
    )