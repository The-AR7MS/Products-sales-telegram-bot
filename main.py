import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiohttp import web
from store import Store
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.types import FSInputFile
from aiogram.filters import StateFilter
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import arabic_reshaper
from bidi.algorithm import get_display
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import io
import arabic_reshaper
from bidi.algorithm import get_display
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import FSInputFile
import tempfile
import os
from aiogram.types import FSInputFile
from dotenv import load_dotenv

load_dotenv()

font_path = os.getenv("FONT_PATH", "fonts/Vazir.ttf")  
pdfmetrics.registerFont(TTFont("Vazir", font_path))

API_TOKEN = os.getenv("API_TOKEN")
bot = Bot(token=API_TOKEN)

dp = Dispatcher()

store = Store()

# -------------------- منو --------------------
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ افزودن محصول")],
        [KeyboardButton(text="🔍 جستجو")], 
        [KeyboardButton(text="📦 همه محصولات")],
        [KeyboardButton(text="⚠️ موجودی کم"),KeyboardButton(text="🧹 پاک کردن تاریخچه فروش")],
        [KeyboardButton(text="📊 گزارش فروش"), KeyboardButton(text="🗑️ حذف همه محصولات")],
        [KeyboardButton(text="📖 نحوه کار با ربات"), KeyboardButton(text="ℹ️ درباره ربات")],

   ],
    resize_keyboard=True
)

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏠 منو")]
    ],
    resize_keyboard=True
)


class AddProductFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_number = State()

class SellProductFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_number = State()

class SearchProductFSM(StatesGroup):
    waiting_for_name = State()

class DeleteProductFSM(StatesGroup):
    waiting_for_name = State()

class ReportFSM(StatesGroup):
    waiting_for_start = State()
    waiting_for_end = State()

HELP_TEXT = """
📖 نحوه کار با ربات مدیریت فروشگاه

سلام! 

این ربات برای مدیریت ساده و دقیق فروشگاه طراحی شده تا بتونی محصولات، فروش، موجودی، و گزارش‌ها رو به راحتی کنترل کنی.
در ادامه همهٔ بخش‌ها به صورت مرحله‌به‌مرحله توضیح داده شده تا هیچ چیز مبهم نباشه 👇


🏠 منوی اصلی ربات
وقتی ربات رو باز می‌کنی، منوی اصلی شامل دکمه‌های زیره:
•	➕ افزودن محصول
•	🔍 جستجو
•	📦 همه محصولات
•	⚠️ موجودی کم
•	📊 گزارش فروش
•	🗑️ حذف همه محصولات
•	🧹 پاک کردن تاریخچه فروش
•	📖 نحوه کار با ربات
•	ℹ️ درباره ربات
هرکدوم از این دکمه‌ها عملکرد خاص خودشون رو دارن که در ادامه کامل توضیح داده شده 👇

➕ افزودن محصول
برای ثبت یک محصول جدید:
1.	دکمه ➕ افزودن محصول رو بزن.
2.	ربات ازت می‌پرسه:
	نام محصول
	قیمت (به تومان)
	تعداد موجودی
3.	بعد از وارد کردن همه، محصول در لیست ذخیره میشه و پیام تأیید دریافت می‌کنی.

🔹 نکات:
•	نام محصول باید یکتا باشه (تکراری ثبت نمی‌شه).
•	قیمت و تعداد فقط عدد صحیح قبول می‌کنن.
-----------------------------------------------------
 جستجو — نقطه شروع برای فروش، ویرایش یا حذف

تقریباً برای هر عملیاتی اول باید محصولت رو جستجو کنی
1.	دکمه 🔍 جستجو رو بزن.
2.	اسم کامل یا بخشی از نام محصول رو وارد کن (مثلاً «چای»).
3.	ربات لیست نتایج مشابه رو نشون میده.
4.	زیر هر محصول سه دکمه داری:
	💰 فروش
	✏️ ویرایش
	❌ حذف
تمام عملیات‌های فروش، ویرایش و حذف از همین‌جا انجام می‌شن.
-----------------------------------------------------
🛒 فروش محصول

برای ثبت فروش :
1.	دکمه 🔍 جستجو رو بزن.
2.	محصول مورد نظرت رو پیدا کن.
3.	زیر محصول، دکمه 💰 فروش رو بزن.
4.	ربات ازت می‌پرسه چه تعدادی فروخته شده.
5.	بعد از وارد کردن تعداد:
موجودی محصول در دیتابیس کم میشه.
مبلغ کل محاسبه و نمایش داده میشه.
جزئیات فروش (نام محصول، تعداد، مبلغ کل، تاریخ و ساعت دقیق) در جدول فروش ذخیره میشه.

⚠️ اگر موجودی کافی نباشه، ربات پیام هشدار میده:
❌ تعداد محصول کافی نیست.
-----------------------------------------------------
✏️ ویرایش محصول

برای تغییر نام، قیمت یا تعداد یک محصول:
1.	🔍 جستجو رو بزن و محصول رو پیدا کن.
2.	زیر محصول، دکمه ✏️ ویرایش رو بزن.
3.	ربات ازت می‌پرسه که کدوم بخش رو می‌خوای تغییر بدی:
🔤 نام
💵 قیمت
📦 تعداد
4.	مقدار جدید رو وارد کن و تأیید بگیر.
-----------------------------------------------------

❌ حذف محصول

برای حذف یک محصول:
1.	🔍 جستجو کن و محصول رو پیدا کن.
2.	زیر محصول دکمه ❌ حذف رو بزن.
3.	ربات می‌پرسه «آیا مطمئن هستی؟»
4.	با زدن ✅ بله، محصول برای همیشه حذف میشه.

📦 همه محصولات — دو حالت نمایش

وقتی دکمه 📦 همه محصولات رو بزنی، ربات ازت می‌پرسه می‌خوای لیست محصولات چطور نمایش داده بشه:

1.	👁️ نمایش در چت
محصولات به‌صورت لیستی در چت نمایش داده می‌شن (نام، قیمت، تعداد).
اگر لیست بلند باشه، ربات خودش به چند بخش تقسیمش می‌کنه.
2.	📄 دریافت PDF
اگر بخوای می‌تونی لیست همه محصولات رو در قالب فایل PDF دریافت کنی.
فایل شامل جدول مرتب با ستون‌های ردیف، نام محصول، قیمت و تعداد است.
مناسب برای چاپ، ارسال یا نگهداری نسخه‌ی آفلاین.
-----------------------------------------------------
⚠️ موجودی کم

این بخش محصولات با موجودی کم (۰ یا ۱) رو نشون میده.
•	دکمه ⚠️ موجودی کم رو بزن تا لیست اون‌ها نمایش داده بشه.
•	ربات خودش لیست رو در چند پیام جدا ارسال می‌کنه تا محدودیت تلگرام رد نشه.
📌 برای سفارش مجدد یا یادآوری خیلی مفیده.
-----------------------------------------------------

📊 گزارش فروش — دو نوع گزارش

وقتی دکمه 📊 گزارش فروش رو بزنی، دو گزینه نمایش داده میشه:

1.	📈 گزارش سرجمع فروش
بعد از انتخاب، ربات ازت تاریخ شروع و پایان رو می‌پرسه (مثلاً 01-07-1403 تا 10-07-1403).
سپس مجموع کل مبلغ فروش در اون بازه‌ی تاریخی رو نمایش میده.
مثال خروجی:
💰 مجموع فروش از 01-07-1403 تا 10-07-1403 برابر است با 12,450,000 تومان.

2.	📄 گزارش ریز فروش (PDF)

در این حالت ربات تمام فروش‌های انجام‌شده در بازه‌ی تاریخی رو به‌صورت دقیق و خط‌به‌خط در فایل PDF می‌فرسته.
در فایل PDF، ستون‌ها شامل موارد زیر هستند:
🔹 نام محصول فروخته‌شده
🔹 مبلغ فروش (تومان)
🔹 تاریخ و ساعت دقیق فروش
فایل نهایی با فونت فارسی و فرمت مرتب برای دانلود ارسال میشه.
-----------------------------------------------------
🗑️ حذف همه محصولات

اگر بخوای کل محصولات دیتابیس رو پاک کنی:
1.	دکمه 🗑️ حذف همه محصولات رو بزن.
2.	ربات هشدار میده و ازت تأیید نهایی می‌خواد.
3.	اگر تأیید بدی، همه‌ی محصولات برای همیشه حذف می‌شن.
⚠️ هشدار: این عمل قابل بازگشت نیست. قبل از حذف، حتماً بکاپ بگیر.
-----------------------------------------------------
🧹 پاک کردن تاریخچه فروش

برای خالی کردن جدول فروش‌ها:
1.	دکمه 🧹 پاک کردن تاریخچه فروش رو بزن.
2.	ربات می‌پرسه «آیا مطمئن هستی که تاریخچه فروش پاک شود؟»
3.	با زدن ✅ بله تمام رکوردهای فروش حذف می‌شن.
4.	با زدن ❌ خیر عملیات لغو میشه.
📌 این قابلیت برای شروع دوباره یا پاک‌سازی فصلی کاربرد داره.

"""

ABOUT_TEXT = """
ℹ️ درباره ربات مدیریت هوشمند فروشگاه

این ربات با هدف ارائه یک راهکار جامع و فارسی‌زبان برای مدیریت موجودی کالا و ثبت دقیق تراکنش‌های فروشگاهی شما طراحی شده است. با استفاده از این ابزار قدرتمند، می‌توانید تمامی عملیات‌های روزمره فروشگاه خود را با سرعت و دقت بالا مدیریت کنید.

✨ قابلیت‌های کلیدی ربات:

مدیریت موجودی کالا:
➕ افزودن/✏️ ویرایش: ثبت سریع محصولات جدید و امکان به‌روزرسانی نام، قیمت یا موجودی پس از جستجو.

🔍 جستجوی هوشمند: پیدا کردن سریع محصولات بر اساس نام یا قسمتی از آن.

📦 نمایش محصولات: دریافت لیست کامل موجودی در چت یا به‌صورت فایل PDF منظم و قابل چاپ.

⚠️ هشدار موجودی کم: فیلتر و نمایش خودکار محصولاتی که موجودی آن‌ها به ۰ یا ۱ رسیده است (برای یادآوری سفارش مجدد).

مدیریت فروش و گزارش‌ها:

💰 ثبت فروش آنی: با جستجوی محصول، تعداد فروخته شده را وارد کنید تا موجودی کسر و مبلغ کل فروش محاسبه شود.

📊 گزارش فروش سرجمع: دریافت مجموع مبلغ فروش خالص در یک بازه زمانی مشخص.

📄 گزارش ریز فروش (PDF): دریافت فایل PDF شامل تمام جزئیات تراکنش‌ها (نام محصول، مبلغ، تعداد و تاریخ و ساعت دقیق فروش).

🧹 پاک‌سازی دیتابیس: قابلیت حذف تمامی محصولات یا صرفاً پاک کردن تاریخچه فروش با تأیید نهایی.

📌 چشم‌انداز ربات: سادگی و کارایی در ثبت، رصد و گزارش‌گیری برای کسب‌وکارهای کوچک و متوسط.

👨‍💻 توسعه‌دهنده: امیررضا محمدی سخا
📅 نسخه: 1.0

🌐 Telegram : @AR7MS
💻 GitHub: https://github.com/The-AR7MS
"""

@dp.message(F.text == "🏠 منو")
async def go_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 منوی اصلی:", reply_markup=main_kb)

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("سلام 👋\nیکی از گزینه‌ها رو انتخاب کن:", reply_markup=main_kb)

async def send_long_text(message, text, reply_markup=None, parse_mode=None):

    MAX_CHARS = 3500 
    remaining = text

    while remaining:
        if len(remaining) <= MAX_CHARS:
            part = remaining
            remaining = ""
        else:
            cut_point = MAX_CHARS
            
            last_newline = remaining[:MAX_CHARS].rfind('\n')
            if last_newline > MAX_CHARS * 0.7: 
                cut_point = last_newline
            else:
        
                last_space = remaining[:MAX_CHARS].rfind(' ')
                if last_space > MAX_CHARS * 0.7:
                    cut_point = last_space

            
            part = remaining[:cut_point]
            remaining = remaining[cut_point:].lstrip()


            star_count = part.count('*')
            if star_count % 2 != 0:

                part += '*'
                remaining = remaining.lstrip('*')


        await message.answer(part, parse_mode=parse_mode, reply_markup=reply_markup)
@dp.message(F.text == "📖 نحوه کار با ربات")
async def how_to_use(message: Message):
    await send_long_text(message, HELP_TEXT, reply_markup=main_kb)

@dp.message(F.text == "ℹ️ درباره ربات")
async def about_bot(message: Message):
    await send_long_text(message, ABOUT_TEXT, reply_markup=main_kb)


@dp.message(F.text == "➕ افزودن محصول")
async def add_product_start(message: Message, state: FSMContext):
    await message.answer("نام محصول را وارد کنید:", reply_markup=cancel_kb)
    await state.set_state(AddProductFSM.waiting_for_name)

@dp.message(AddProductFSM.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("قیمت محصول را وارد کنید (به تومان):", reply_markup=cancel_kb)
    await state.set_state(AddProductFSM.waiting_for_price)

@dp.message(AddProductFSM.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ فقط عدد صحیح وارد کن.", reply_markup=cancel_kb)
        return
    await state.update_data(price=int(message.text))
    await message.answer("تعداد محصول را وارد کنید:", reply_markup=cancel_kb)
    await state.set_state(AddProductFSM.waiting_for_number)

@dp.message(AddProductFSM.waiting_for_number)
async def process_number(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ فقط عدد صحیح وارد کن.", reply_markup=cancel_kb)
        return
    data = await state.get_data()
    name = data["name"]
    price = data["price"]
    number = int(message.text)

    ok = store.add_product(name, price, number)
    if ok:
        await message.answer(f"✅ محصول '{name}' با قیمت {price} و تعداد {number} اضافه شد.", reply_markup=main_kb)
    else:
        await message.answer("❌ محصولی با این نام وجود دارد.", reply_markup=main_kb)
    await state.clear()



@dp.message(F.text == "🔍 جستجو")
async def search_product_start(message: Message, state: FSMContext):
    await message.answer("نام محصول یا قسمتی از آن را وارد کنید:", reply_markup=cancel_kb)
    await state.set_state(SearchProductFSM.waiting_for_name)

@dp.message(SearchProductFSM.waiting_for_name)
async def search_process_name(message: Message, state: FSMContext):
    keyword = message.text.strip()
    results = store.search_products_partial(keyword)

    logging.info(f"[DEBUG] search for '{keyword}' => results: {results}")

    if not results:
        await message.answer("❌ محصولی پیدا نشد.", reply_markup=main_kb)
        await state.clear()
        return

    if isinstance(results, (tuple, list)) and results and not isinstance(results[0], (list, tuple, dict)):
        results = [results]
    if isinstance(results, dict):
        results = list(results.values())
    if not results:
        await message.answer("❌ محصولی پیدا نشد.", reply_markup=main_kb)
        await state.clear()
        return

    for p in results:
        try:
            prod_id = p[0]
            name = p[1]
            price = int(p[2])
            number = p[3]
        except Exception:
            if isinstance(p, dict):
                prod_id = p.get("id")
                name = p.get("name", "بدون نام")
                price = int(p.get("price", 0))
                number = int(p.get("number", 0))
            else:
                prod_id = None
                name = str(p)
                price = 0
                number = 0

        text = f"\u202B{name} - {price} تومان - تعداد {number}\u202C"
        buttons = [
    [
        InlineKeyboardButton(text="💰 فروش", callback_data=f"sell:{prod_id}"),
        InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"edit:{prod_id}"),
        InlineKeyboardButton(text="❌ حذف", callback_data=f"askdelete:{prod_id}")
    ]
]

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(text, reply_markup=kb)

    await state.clear()


@dp.message(F.text == "📦 همه محصولات")
async def ask_product_display_method(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄PDF دریافت",
                    callback_data="show_pdf"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👁️ نمایش در چت",
                    callback_data="show_inline"
                )
            ]
        ]
    )
    await message.answer(
        "📦 می‌خواهی محصولات را چگونه ببینی؟",
        reply_markup=kb
    )


@dp.callback_query(F.data == "show_pdf")
async def send_products_pdf(callback: CallbackQuery):
    store.load_products_from_db()
    products = store.products

    if not products:
        await callback.message.answer("❌ هیچ محصولی در دیتابیس وجود ندارد.", reply_markup=main_kb)
        await callback.answer()
        return

    pdf_path = "products_list.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    from reportlab.lib.styles import ParagraphStyle
    title_text = get_display(arabic_reshaper.reshape("📦 لیست همه محصولات فروشگاه"))
    title_style = ParagraphStyle('title_style', fontName='Vazir', fontSize=14, alignment=1)
    title = Paragraph(title_text, title_style)

    elements.append(title)
    elements.append(Spacer(1, 12))

    headers = ["ردیف", "نام محصول", "قیمت (تومان)", "تعداد"]
    headers_fixed = [get_display(arabic_reshaper.reshape(h)) for h in headers]
    data = [headers_fixed]

    for i, p in enumerate(products, start=1):
        name_fixed = get_display(arabic_reshaper.reshape(p[1]))
        price = int(p[2]) if p[2] is not None else 0
        number = int(p[3]) if p[3] is not None else 0
        price_str = "{:,}".format(price).replace(',', '،')
        data.append([str(i), name_fixed, price_str, str(number)])

    table = Table(data, colWidths=[50, 220, 100, 70],repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#013502")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Vazir'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
    ]))
    elements.append(table)

    doc.build(elements)

    pdf_file = FSInputFile(pdf_path)
    await callback.message.answer_document(pdf_file)
    os.remove(pdf_path)
    await callback.answer()



@dp.callback_query(F.data == "show_inline")
async def show_products_inline(callback: CallbackQuery, state: FSMContext):
    store.load_products_from_db()
    products = store.products

    if not products:
        await callback.message.answer("❌ هیچ محصولی وجود ندارد.", reply_markup=main_kb)
        await callback.answer()
        return

    await state.update_data(products=products, index=0)
    await send_next_products(callback.message, state)
    await callback.answer()


async def send_next_products(message: Message, state: FSMContext):
    data = await state.get_data()
    products = data.get("products", [])
    index = data.get("index", 0)

    next_index = index + 20
    batch = products[index:next_index]

    if not batch:
        await message.answer("✅ تمام محصولات نمایش داده شدند.", reply_markup=main_kb)
        await state.clear()
        return

    for i, p in enumerate(batch, start=index + 1):
        name = p[1]
        price = int(p[2])
        number = int(p[3])
        prod_id = p[0]

        text = f"📦 {i}. {name}\n💵 قیمت: {price} تومان\n📦 تعداد: {number}"

        buttons = [
            [
                InlineKeyboardButton(text="💰 فروش", callback_data=f"sell:{prod_id}"),
                InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"edit:{prod_id}"),
                InlineKeyboardButton(text="❌ حذف", callback_data=f"askdelete:{prod_id}")
            ]
        ]
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer(text, reply_markup=kb)



    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➡️ ادامه", callback_data="next_batch"),
            InlineKeyboardButton(text="❌ توقف", callback_data="stop_show")
        ]
    ])

    await message.answer(
        "⚠️ تعداد محصولات زیاد است — آیا می‌خواهی ادامه را ببینی یا متوقف کنی؟",
        reply_markup=kb
    )

    await state.update_data(index=next_index)


@dp.callback_query(F.data == "next_batch")
async def next_batch(callback: CallbackQuery, state: FSMContext):
    await send_next_products(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "stop_show")
async def stop_show(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🏠 نمایش متوقف شد", reply_markup=main_kb)
    await state.clear()
    await callback.answer()


@dp.callback_query(F.data.startswith("sell:"))
async def process_sell_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    product_id = callback.data.split(":")[1]
    store.load_products_from_db()
    name = next((p[1] for p in store.products if str(p[0]) == str(product_id)), None)
    if not name:
        await callback.message.answer("❌ محصول پیدا نشد.", reply_markup=main_kb)
        return
    await state.update_data(name=name)
    await callback.message.answer(f"💰 فروش محصول '{name}'\nتعداد را وارد کنید:", reply_markup=cancel_kb)
    await state.set_state(SellProductFSM.waiting_for_number)

@dp.message(SellProductFSM.waiting_for_number)
async def process_sell_number(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ لطفاً فقط عدد وارد کن.", reply_markup=cancel_kb)
        return

    data = await state.get_data()
    name = data.get("name")
    number = int(message.text)

    result = store.sell_product(name, number)

    await message.answer(result, reply_markup=main_kb)
    await state.clear()

@dp.callback_query(F.data.startswith("edit:"))
async def edit_product(callback: CallbackQuery):
    prod_id = callback.data.split(":")[1]

    kb = InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text="🔤 تغییر نام", callback_data=f"editname:{prod_id}")],
        [InlineKeyboardButton(text="💵 تغییر قیمت", callback_data=f"editprice:{prod_id}")],
        [InlineKeyboardButton(text="📦 تغییر تعداد", callback_data=f"editqty:{prod_id}")]
    ])

    await callback.message.answer("کدوم بخش رو میخوای تغییر بدی؟", reply_markup=kb)
    await callback.answer()


@dp.callback_query(F.data.startswith("editname:"))
async def edit_name_start(callback: CallbackQuery, state: FSMContext):
    prod_id = callback.data.split(":")[1]
    await state.update_data(edit_id=prod_id)
    await callback.message.answer("✏️ نام جدید محصول رو وارد کن:")
    await state.set_state("edit_name")
    await callback.answer()


@dp.callback_query(F.data.startswith("editprice:"))
async def edit_price_start(callback: CallbackQuery, state: FSMContext):
    prod_id = callback.data.split(":")[1]
    await state.update_data(edit_id=prod_id)
    await callback.message.answer("💵 قیمت جدید رو وارد کن:")
    await state.set_state("edit_price")
    await callback.answer()


@dp.callback_query(F.data.startswith("editqty:"))
async def edit_qty_start(callback: CallbackQuery, state: FSMContext):
    prod_id = callback.data.split(":")[1]
    await state.update_data(edit_id=prod_id)
    await callback.message.answer("📦 تعداد جدید رو وارد کن:")
    await state.set_state("edit_qty")
    await callback.answer()

@dp.message(StateFilter("edit_name"))
async def save_new_name(message: Message, state: FSMContext):
    data = await state.get_data()
    prod_id = data.get("edit_id")
    ok = store.edit_product_by_id(prod_id, "name", message.text)
    if ok:
        await message.answer("✅ نام محصول با موفقیت تغییر کرد.", reply_markup=main_kb)
    else:
        await message.answer("❌ خطا در تغییر نام محصول.", reply_markup=main_kb)
    await state.clear()


@dp.message(StateFilter("edit_price"))
async def save_new_price(message: Message, state: FSMContext):
    data = await state.get_data()
    prod_id = data.get("edit_id")

    if not message.text.isdigit():
        await message.answer("⚠️ لطفاً فقط عدد وارد کن.", reply_markup=cancel_kb)
        return

    ok = store.edit_product_by_id(prod_id, "price", message.text)
    if ok:
        await message.answer("✅ قیمت محصول تغییر کرد.", reply_markup=main_kb)
    else:
        await message.answer("❌ خطا در تغییر قیمت محصول.", reply_markup=main_kb)
    await state.clear()


@dp.message(StateFilter("edit_qty"))
async def save_new_qty(message: Message, state: FSMContext):
    data = await state.get_data()
    prod_id = data.get("edit_id")

    if not message.text.isdigit():
        await message.answer("⚠️ لطفاً فقط عدد وارد کن.", reply_markup=cancel_kb)
        return

    ok = store.edit_product_by_id(prod_id, "number", message.text)
    if ok:
        await message.answer("✅ تعداد محصول تغییر کرد.", reply_markup=main_kb)
    else:
        await message.answer("❌ خطا در تغییر تعداد محصول.", reply_markup=main_kb)
    await state.clear()



@dp.callback_query(F.data.startswith("askdelete:"))
async def ask_delete(callback: CallbackQuery):
    prod_id = callback.data.split(":")[1]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ بله، حذف کن", callback_data=f"delete:{prod_id}"),
                InlineKeyboardButton(text="❌ خیر", callback_data="cancel_delete")
            ]
        ]
    )
    await callback.message.answer(f"آیا مطمئنی که می‌خواهی محصول با کد {prod_id} حذف شود؟", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("delete:"))
async def process_delete(callback: CallbackQuery):
    prod_id = callback.data.split(":")[1]

    ok = store.delete_product(prod_id)  # 📌 متصل به store.py

    if ok:
        await callback.message.answer(f"✅ محصول با کد {prod_id} حذف شد.")
    else:
        await callback.message.answer("❌ خطا در حذف محصول یا محصول پیدا نشد.")

    await callback.answer()

@dp.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    await callback.message.answer("❌ عملیات حذف لغو شد.")
    await callback.answer()


@dp.message(F.text == "🗑️ حذف همه محصولات")
async def ask_delete_all(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ بله، همه را حذف کن", callback_data="confirm_delete_all"),
                InlineKeyboardButton(text="❌ خیر، منصرف شدم", callback_data="cancel_delete_all")
            ]
        ]
    )
    await message.answer(
        "⚠️ *حذف همه محصولات دائمی است و غیرقابل بازگشت می‌باشد.*\n\nآیا مطمئن هستید؟",
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.callback_query(F.data == "confirm_delete_all")
async def confirm_delete_all(callback: CallbackQuery):
    ok = store.delete_all_products()
    if ok:
        await callback.message.answer("✅ تمام محصولات با موفقیت حذف شدند.", reply_markup=main_kb)
    else:
        await callback.message.answer("❌ خطا در حذف محصولات یا دیتابیس خالی بود.", reply_markup=main_kb)
    await callback.answer()


@dp.callback_query(F.data == "cancel_delete_all")
async def cancel_delete_all(callback: CallbackQuery):
    await callback.message.answer("❌ عملیات حذف لغو شد.", reply_markup=main_kb)
    await callback.answer()


@dp.message(F.text == "⚠️ موجودی کم")
async def show_low_stock(message: Message):
    results = store.get_low_stock()
    if not results:
        await message.answer("✅ همه محصولات موجودی کافی دارند.", reply_markup=main_kb)
        return

    header = "⚠️ محصولات با موجودی کم (۰ یا ۱):\n"
    msg = header
    count = 0

    for p in results:
        line = f"\u202B{p[1]} - {int(p[2])} تومان - تعداد {p[3]}\u202C\n"
        if len(msg) + len(line) > 3500: 
            await message.answer(msg, reply_markup=main_kb)
        msg += line
        count += 1

    if msg.strip() != header.strip():
        await message.answer(msg, reply_markup=main_kb)

    await message.answer(f"✅ مجموع {count} محصول با موجودی کم یافت شد.", reply_markup=main_kb)



@dp.message(F.text == "📊 گزارش فروش")
async def report_start(message: Message):
    await message.answer(
        "نوع گزارش مورد نظر را انتخاب کنید 👇",
        reply_markup=sales_report_menu()
    )

@dp.message(ReportFSM.waiting_for_start)
async def report_get_start(message: Message, state: FSMContext):
    await state.update_data(start=message.text)
    await message.answer("📅 تاریخ پایان را وارد کن (مثال: 10-07-1403):", reply_markup=cancel_kb)
    await state.set_state(ReportFSM.waiting_for_end)

@dp.message(ReportFSM.waiting_for_end)
async def report_get_end(message: Message, state: FSMContext):
    data = await state.get_data()
    start = data.get("start")
    end = message.text
    report_type = data.get("report_type", "summary")

    if report_type == "summary":
        total = store.get_sales_summary(start, end)
        await message.answer(f"💰 مجموع فروش از {start} تا {end}: {total:,} تومان", reply_markup=main_kb)
    else:
        await send_sales_detailed_pdf(message.chat.id, start, end)

    await state.clear()



def sales_report_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 گزارش سرجمع", callback_data="sales_summary"),
            InlineKeyboardButton(text="📄 گزارش ریز", callback_data="sales_detailed"),
        ]
    ])
    return kb


@dp.callback_query(F.data == "sales_summary")
async def sales_summary_cb(callback: CallbackQuery, state: FSMContext):
    await state.update_data(report_type="summary")
    await callback.message.answer("📅 تاریخ شروع را وارد کن (مثال: 01-07-1403):", reply_markup=cancel_kb)
    await state.set_state(ReportFSM.waiting_for_start)
    await callback.answer()

@dp.callback_query(F.data == "sales_detailed")
async def sales_detailed_cb(callback: CallbackQuery, state: FSMContext):
    await state.update_data(report_type="detailed")
    await callback.message.answer("📅 تاریخ شروع را وارد کن (مثال: 01-07-1403):", reply_markup=cancel_kb)
    await state.set_state(ReportFSM.waiting_for_start)
    await callback.answer()



async def send_sales_detailed_pdf(chat_id, start_date, end_date):
    sales = store.get_sales_detailed(start_date, end_date)
    if not sales:
        await bot.send_message(chat_id, "❌ هیچ فروشی در این بازه ثبت نشده.", reply_markup=main_kb)
        return

    pdf_path = f"sales_detailed_{start_date}_{end_date}.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    elements = []

    from reportlab.lib.styles import ParagraphStyle
    title_text = get_display(arabic_reshaper.reshape("📄 گزارش ریز فروش"))
    title_style = ParagraphStyle('title_style', fontName='Vazir', fontSize=14, alignment=1)
    title = Paragraph(title_text, title_style)

    elements.append(title)
    elements.append(Spacer(1, 12))

    headers = ["ردیف", "نام محصول", "قیمت فروش (تومان)", "تعداد", "تاریخ و ساعت"]
    headers_fixed = [get_display(arabic_reshaper.reshape(h)) for h in headers]
    data = [headers_fixed]

    for i, row in enumerate(sales, start=1):
        name_fixed = get_display(arabic_reshaper.reshape(row[0]))
        number = int(row[1])
        price_str = "{:,}".format(int(row[2])).replace(",", "،")
        date_fixed = get_display(arabic_reshaper.reshape(row[3]))  

        data.append([str(i), name_fixed, price_str, str(number), date_fixed])

    table = Table(data, colWidths=[40, 160, 90, 50, 120],repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003504")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Vazir'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
    ]))
    elements.append(table)

    doc.build(elements)

    pdf_file = FSInputFile(pdf_path)
    await bot.send_document(chat_id, pdf_file, caption=f"📄 گزارش فروش از {start_date} تا {end_date}")
    os.remove(pdf_path)



@dp.message(F.text == "🧹 پاک کردن تاریخچه فروش")
async def ask_clear_sales_history(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ بله، پاک شود", callback_data="confirm_clear_sales"),
                InlineKeyboardButton(text="❌ خیر، لغو", callback_data="cancel_clear_sales")
            ]
        ]
    )
    await message.answer(
        "⚠️ آیا مطمئن هستید که تاریخچه‌ی فروش از ابتدا تا الان پاک شود؟",
        reply_markup=kb
    )


@dp.callback_query(F.data == "confirm_clear_sales")
async def confirm_clear_sales(callback: CallbackQuery):
    ok = store.clear_sales_history()
    if ok:
        await callback.message.answer("✅ تاریخچه فروش با موفقیت پاک شد.", reply_markup=main_kb)
    else:
        await callback.message.answer("❌ خطا در پاک کردن تاریخچه فروش.", reply_markup=main_kb)
    await callback.answer()


@dp.callback_query(F.data == "cancel_clear_sales")
async def cancel_clear_sales(callback: CallbackQuery):
    await callback.message.answer("❌ عملیات لغو شد.", reply_markup=main_kb)
    await callback.answer()

async def health(request):
    return web.Response(text="ok")

async def start_web_app():
    port = int(os.getenv("PORT", "8000"))
    app = web.Application()
    app.add_routes([web.get("/health", health)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"✅ Web server started on port {port}")

async def main():
    await start_web_app()

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())




