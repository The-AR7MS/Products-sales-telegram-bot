    # store.py
import sqlite3
import jdatetime
import unicodedata
import re

PERSIAN_ALPHABET = [
    'ا','ب','پ','ت','ث','ج','چ','ح','خ','د','ذ','ر','ز','ژ',
    'س','ش','ص','ض','ط','ظ','ع','غ','ف','ق','ک','گ','ل','م','ن','و','ه','ی'
]

def normalize_persian(text):

    if text is None:
        return ''
    text = str(text)

    text = unicodedata.normalize('NFKC', text)

    replacements = {
        'ي': 'ی', 'ي': 'ی', 'ك': 'ک', 'ة': 'ه', 'ۀ': 'ه',
        'ؤ': 'و', 'ئ': 'ی', 'أ': 'ا', 'إ': 'ا', 'ٱ': 'ا', 'آ': 'ا'
    }
    for a, b in replacements.items():
        text = text.replace(a, b)

    text = ''.join(ch for ch in unicodedata.normalize('NFKD', text) if unicodedata.category(ch) != 'Mn')

    text = re.sub(r'^[\s\(\[\{]*\d+[\)\]\}\s]*', '', text)

    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)

    text = text.replace('_', ' ')
    text = re.sub(r'\s+', ' ', text).strip()

    return text.lower()

def persian_sort_key(s):

    s_norm = normalize_persian(s)
    order_map = {ch: idx for idx, ch in enumerate(PERSIAN_ALPHABET)}
    key = []
    for ch in s_norm:
        if ch in order_map:
            key.append(order_map[ch])
        else:
            key.append(1000 + ord(ch))
    return tuple(key)



class Store:
    
    
    def _to_iso_jalali_datetime(self, s):
        if not s:
            return ''
        s = s.strip()
        s = s.replace('/', '-').replace('.', '-')
        parts = s.split(' ')
        date_part = parts[0]
        time_part = ' ' + ' '.join(parts[1:]) if len(parts) > 1 else ''
        dmy = date_part.split('-')
        if len(dmy) == 3:
            if len(dmy[0]) == 4: 
                yyyy, mm, dd = dmy
                return f"{yyyy.zfill(4)}-{mm.zfill(2)}-{dd.zfill(2)}{time_part}"
            else:
                dd, mm, yyyy = dmy
                return f"{yyyy.zfill(4)}-{mm.zfill(2)}-{dd.zfill(2)}{time_part}"
        return s
    
    
    
    def __init__(self):
        self.products = []
        self.total_sales = 0
        self.init_db()
        self.ensure_sort_column()
        self.load_products_from_db()

    def init_db(self):
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS products 
                       (id INTEGER PRIMARY KEY, name TEXT UNIQUE, price INTEGER, number INTEGER)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS sales 
                       (id INTEGER PRIMARY KEY, product_name TEXT, number INTEGER, total_price INTEGER, date TEXT)""")
        conn.commit()
        conn.close()



    def ensure_sort_column(self):
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(products)")
        cols = [r[1] for r in cur.fetchall()]
        if 'sort_name' not in cols:
            cur.execute("ALTER TABLE products ADD COLUMN sort_name TEXT")
            conn.commit()
            cur.execute("SELECT id, name FROM products")
            rows = cur.fetchall()
            for rid, name in rows:
                try:
                    cur.execute("UPDATE products SET sort_name=? WHERE id=?", (normalize_persian(name), rid))
                except Exception:
                    pass
            conn.commit()
        conn.close()



    def load_products_from_db(self):
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(products)")
        cols = [r[1] for r in cur.fetchall()]
        if 'sort_name' in cols:
            cur.execute("SELECT id, name, price, number, sort_name FROM products ORDER BY sort_name ASC")
            rows = cur.fetchall()
        else:
            cur.execute("SELECT id, name, price, number FROM products")
            rows = cur.fetchall()

        clean_rows = []
        for r in rows:
            try:
                pid = r[0]
                name = r[1]
                price = int(float(r[2])) if r[2] is not None else 0
                number = int(float(r[3])) if r[3] is not None else 0
                if len(r) >= 5:
                    sort_name = r[4]
                    clean_rows.append((pid, name, price, number, sort_name))
                else:
                    clean_rows.append((pid, name, price, number))
            except Exception:
                clean_rows.append(r)

        if 'sort_name' in cols:
            self.products = clean_rows
        else:
            try:
                self.products = sorted(clean_rows, key=lambda p: persian_sort_key(p[1]))
            except Exception:
                self.products = clean_rows

        conn.close()


    def add_product(self, name, price, number):
        for product in self.products:
            if product[1] == name:
                return False
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        try:
            cur.execute("PRAGMA table_info(products)")
            cols = [r[1] for r in cur.fetchall()]
            if 'sort_name' in cols:
                cur.execute("INSERT INTO products (name, price, number, sort_name) VALUES (?, ?, ?, ?)",
                            (name, int(price), int(number), normalize_persian(name)))
            else:
                cur.execute("INSERT INTO products (name, price, number) VALUES (?, ?, ?)",
                            (name, int(price), int(number)))
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            return False
        finally:
            conn.close()
        self.load_products_from_db()
        return True




    def sell_product(self, name, number):
        self.load_products_from_db()
        for product in self.products:
            if product[1] == name:
                if product[3] < number:
                    return "❌ تعداد محصول کافی نیست."
                total_price = int(number * int(product[2]))
                new_number = product[3] - number
                self.update_product_number(product[0], new_number)
                self.load_products_from_db()
                today_jalali_iso = jdatetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn = sqlite3.connect('products.db')
                cur = conn.cursor()
                cur.execute("INSERT INTO sales (product_name, number, total_price, date) VALUES (?, ?, ?, ?)",
                            (name, number, total_price, today_jalali_iso))
                conn.commit()
                conn.close()

                return f"✅ مبلغ کل: {total_price} تومان"
        return "❌ محصول یافت نشد."





    def update_product_number(self, product_id, new_number):
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        cur.execute("UPDATE products SET number=? WHERE id=?", (new_number, product_id))
        conn.commit()
        conn.close()




        conn = sqlite3.connect("products.db")
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM products WHERE id=?", (product_id,))
            conn.commit()
            deleted = cur.rowcount
        except Exception as e:
            print("Error deleting product:", e)
            deleted = 0
        finally:
            conn.close()

        if deleted:
            self.load_products_from_db()

        return deleted > 0





    def delete_all_products(self):
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM products")
            conn.commit()
            deleted = cur.rowcount
        except Exception as e:
            print("Error deleting all products:", e)
            deleted = 0
        finally:
            conn.close()

        if deleted > 0:
            self.load_products_from_db()
            return True
        else:
            return False



    def search_products_partial(self, keyword):
        self.load_products_from_db()
        result = []
        key_norm = normalize_persian(keyword)
        for p in self.products:
            name_norm = normalize_persian(p[1])
            if key_norm in name_norm:
                result.append(p)
        return result





    def get_low_stock(self):
        self.load_products_from_db()
        return [p for p in self.products if p[3] <= 1]





    def edit_product(self, old_name, field, new_value):
        self.load_products_from_db()
        for product in self.products:
            if product[1] == old_name:
                conn = sqlite3.connect('products.db')
                cur = conn.cursor()
                if field == "name":
                    cur.execute("UPDATE products SET name=? WHERE id=?", (new_value, product[0]))
                    try:
                        cur.execute("PRAGMA table_info(products)")
                        cols = [r[1] for r in cur.fetchall()]
                        if 'sort_name' in cols:
                            cur.execute("UPDATE products SET sort_name=? WHERE id=?", (normalize_persian(new_value), product[0]))
                    except Exception:
                        pass
                elif field == "price":
                    cur.execute("UPDATE products SET price=? WHERE id=?", (int(new_value), product[0]))
                elif field == "number":
                    cur.execute("UPDATE products SET number=? WHERE id=?", (int(new_value), product[0]))
                conn.commit()
                conn.close()
                self.load_products_from_db()
                return True
        return False




    def edit_product_by_id(self, product_id, field, new_value):

        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        try:
            if field == "name":
                cur.execute("UPDATE products SET name=? WHERE id=?", (new_value, product_id))
                try:
                    cur.execute("PRAGMA table_info(products)")
                    cols = [r[1] for r in cur.fetchall()]
                    if 'sort_name' in cols:
                        cur.execute("UPDATE products SET sort_name=? WHERE id=?", (normalize_persian(new_value), product_id))
                except Exception:
                    pass
            elif field == "price":
                cur.execute("UPDATE products SET price=? WHERE id=?", (int(new_value), product_id))
            elif field == "number":
                cur.execute("UPDATE products SET number=? WHERE id=?", (int(new_value), product_id))
            else:
                return False
            conn.commit()
            success = cur.rowcount > 0
        except Exception as e:
            print("Error editing product by id:", e)
            success = False
        finally:
            conn.close()

        self.load_products_from_db()
        return success





    def get_sales_report(self, start_date, end_date):
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()

        start_iso = self._to_iso_jalali_datetime(start_date)
        end_iso = self._to_iso_jalali_datetime(end_date)

        if len(start_iso) == 10:
            start_iso += " 00:00:00"
        if len(end_iso) == 10:
            end_iso += " 23:59:59"

        cur.execute("SELECT * FROM sales WHERE date BETWEEN ? AND ?", (start_iso, end_iso))
        sales = cur.fetchall()
        conn.close()
        return sales




    def get_sales_summary(self, start_date, end_date):
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        cur.execute("""
            SELECT SUM(total_price)
            FROM sales
            WHERE substr(date, 1, 10) BETWEEN ? AND ?
        """, (start_date, end_date))
        total = cur.fetchone()[0]
        conn.close()
        return int(total) if total else 0


    def get_sales_detailed(self, start_date, end_date):
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()

        start_iso = self._to_iso_jalali_datetime(start_date)
        end_iso = self._to_iso_jalali_datetime(end_date)

        if len(start_iso) == 10:
            start_iso += " 00:00:00"
        if len(end_iso) == 10:
            end_iso += " 23:59:59"

        cur.execute("""
            SELECT product_name, number, total_price, date
            FROM sales
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC
        """, (start_iso, end_iso))

        rows = cur.fetchall()
        conn.close()
        return rows




    def clear_sales_history(self):

        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM sales")
            conn.commit()
            deleted = cur.rowcount
        except Exception as e:
            print("Error clearing sales history:", e)
            deleted = 0
        finally:
            conn.close()
        return deleted >= 0


