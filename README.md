# 🤖 Telegram Sales & Inventory Bot

A **Telegram bot** for managing products, stock, and sales — featuring PDF report generation (with Persian/RTL text), Jalali (Shamsi) dates, and a modern UI built using **Aiogram 3**.

---

## 🚀 Features

1. **🛍 Add, Edit, Delete Products**  
   - Manage your inventory directly in Telegram.  
   - Each product is stored in a local SQLite database (`products.db`) with unique names, price, and stock quantity.

2. **💰 Record Sales**  
   - Automatically updates stock levels when a sale is recorded.  
   - Every sale is logged with product name, count, total price, and date.

3. **⚠️ Low Stock Alerts**  
   - Detects and displays products with stock ≤ 1 (editable threshold).  
   - Implemented in `store.py` → `get_low_stock()`.

4. **📊 Generate PDF Reports (Summary + Detailed)**  
   - Produces bilingual PDF reports with Persian text rendered correctly using `reportlab`, `arabic-reshaper`, and `python-bidi`.  
   - Uses the Persian font **Vazirmatn-Regular.ttf** and Jalali dates via `jdatetime`.  
   - Reports can be exported or sent directly in Telegram.

5. **🇮🇷 Persian Text Normalization & Sorting**  
   - Ensures consistent sorting and search for Persian product names.

6. **🧠 FSM Conversation Flow**  
   - Multi-step data entry (e.g. add/edit product, generate report) using Aiogram FSM states.

7. **🧾 Built-in Command Guide**  
   - The bot includes an **in-bot help/instruction guide**, explaining all commands and usage directly within the chat.

8. **🧰 Local Database (SQLite)**  
   - Two tables:  
     - `products(id, name, price, number)`  
     - `sales(id, product_name, number, total_price, date)`

9. **🖋 Tech Stack Highlights**  
   - `aiogram 3` (async Telegram framework)  
   - `reportlab`, `arabic-reshaper`, `python-bidi` (PDF with Persian text)  
   - `sqlite3` (local DB)  
   - `python-dotenv` (environment configuration)  
   - `jdatetime` (Jalali calendar support)  
   - `aiohttp` (light web server for health checks)

---

## ⚙️ Setup Instructions

### 1️⃣ Installation
```bash
pip install -r requirements.txt
```

### 2️⃣ Configuration (.env)
Edit `.env` to include your Telegram bot token and font path:

```bash
API_TOKEN=YOUR_BOTFATHER_TOKEN_HERE
FONT_PATH=.fontaddress/Vazirmatn-Regular.ttf
```

### 3️⃣ Run the Bot
```bash
cd telegram bot
python main.py
```
The bot runs using **long polling**, so no webhook configuration is required.

### 4️⃣ Database & Files
- A SQLite database file `products.db` is automatically created.
- Font file `Vazirmatn-Regular.ttf` must be in the same folder or a valid path in `.env`.

### 5️⃣ Low Stock Threshold
Default low-stock limit is `1`. To change it, edit:
```python
# in store.py
def get_low_stock(self):
    self.load_products_from_db()
    return [p for p in self.products if p[3] <= 1]  # Change 1 to desired value
```

---

## 🧩 File Structure
```
telegram bot/
│
├── main.py              # Bot logic, handlers, PDF generation, polling
├── store.py             # Database & business logic (CRUD, reports)
├── .env                 # API token & font path config
├── Vazirmatn-Regular.ttf # Persian font for PDF output
├── products.db          # Auto-created SQLite database
└── requirements.txt     # Dependencies
```

---

## 🔒 Notes
- Keep `.env` and `products.db` private (they are in `.gitignore` by default).  
- The bot guide and usage instructions are available **inside the bot**.  
- Recommended for portfolio & demonstration projects.  

---

## 🧠 Future Enhancements
- Docker + Webhook deployment  
- User role system (admin / cashier)  
- Image support for products  
- Web dashboard for analytics  

---

## photos
![Screenshot 1]()
