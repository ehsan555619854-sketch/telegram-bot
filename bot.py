import json, os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "8756210620:AAFTqulxKyeaHgpZzNiyubzMq6Uq6Q7WTkk"
ADMIN_ID = 6552154689

def load(f, d=None):
    if d is None: d = {}
    if not os.path.exists(f): return d
    try:
        with open(f, "r", encoding="utf-8") as file: return json.load(file)
    except: return d

def save(f, data):
    with open(f, "w", encoding="utf-8") as file: json.dump(data, file, ensure_ascii=False, indent=2)

def cfg():
    c = load("config.json", {})
    d = {
        "welcome": "به ربات خوش آمدید",
        "force_join": "در کانال‌ها عضو شوید سپس عضو شدم را بزنید",
        "referral": "لینک زیرمجموعه شما:",
        "withdraw": "یکی از گزینه‌ها را انتخاب کنید",
        "support": "پیام خود را بنویسید:",
        "sponsor": "برای اسپان سری:\n@Zstneh",
        "account": "اطلاعات شما:",
        "points_per_ref": 1,
        "enable_ref": True, "enable_wd": True, "enable_acc": True, "enable_sup": True, "enable_sp": True
    }
    for k, v in d.items():
        if k not in c: c[k] = v
    return c

def save_cfg(c): save("config.json", c)
def users(): return load("users.json", {})
def save_users(u): save("users.json", u)
def channels(): return load("channels.json", [])
def save_channels(c): save("channels.json", c)

def get_user(uid, name="", uname=None):
    u = users()
    s = str(uid)
    if s not in u:
        u[s] = {"name": name, "username": uname, "points": 0, "refs": 0, "ref_by": None, "date": datetime.now().strftime("%Y/%m/%d")}
        save_users(u)
    return u[s]

async def is_member(uid, ctx):
    for ch in channels():
        try:
            m = await ctx.bot.get_chat_member(ch["id"], uid)
            if m.status in ["left", "kicked"]: return False
        except: return False
    return True

async def force_join(update, ctx):
    btns = [[InlineKeyboardButton(ch["title"], url=ch["link"])] for ch in channels()]
    btns.append([InlineKeyboardButton("✅ عضو شدم", callback_data="check")])
    text = cfg()["force_join"]
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btns))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(btns))

def kb(uid):
    c = cfg()
    rows = []
    if c["enable_ref"]: rows.append([KeyboardButton("زیرمجموعه گیری")])
    r2 = []
    if c["enable_wd"]: r2.append(KeyboardButton("برداشت"))
    if c["enable_acc"]: r2.append(KeyboardButton("حساب کاربری"))
    if r2: rows.append(r2)
    r3 = []
    if c["enable_sup"]: r3.append(KeyboardButton("پشتیبانی"))
    if c["enable_sp"]: r3.append(KeyboardButton("اسپان سری ربات"))
    if r3: rows.append(r3)
    if uid == ADMIN_ID: rows.append([KeyboardButton("پنل ادمین")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def withdraw_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("⭐ ۱ استارز"), KeyboardButton("❤️ تدی رایگان")],
        [KeyboardButton("بازگشت")]
    ], resize_keyboard=True)

async def start(update, ctx):
    user = update.effective_user
    data = get_user(user.id, user.first_name, user.username)
    c = cfg()

    if ctx.args and ctx.args[0].startswith("ref_"):
        try:
            rid = int(ctx.args[0][4:])
            if rid != user.id and data.get("ref_by") is None:
                u = users()
                u[str(user.id)]["ref_by"] = rid
                if str(rid) in u:
                    u[str(rid)]["points"] = u[str(rid)].get("points", 0) + c["points_per_ref"]
                    u[str(rid)]["refs"] = u[str(rid)].get("refs", 0) + 1
                    save_users(u)
                    try:
                        await ctx.bot.send_message(rid, f"🎉 کاربر جدید با لینک شما وارد شد\n\nنام: {user.first_name}\nآیدی: {user.id}")
                    except:
                        pass
                else:
                    save_users(u)
        except:
            pass

    if not await is_member(user.id, ctx):
        await force_join(update, ctx)
        return

    await update.message.reply_text(c["welcome"], reply_markup=kb(user.id))

async def check(update, ctx):
    q = update.callback_query
    await q.answer()
    if await is_member(q.from_user.id, ctx):
        try: await q.message.delete()
        except: pass
        await ctx.bot.send_message(q.from_user.id, cfg()["welcome"], reply_markup=kb(q.from_user.id))
    else:
        await q.answer("هنوز عضو نشدید!", show_alert=True)

async def account(update, ctx):
    if not await is_member(update.effective_user.id, ctx):
        await force_join(update, ctx)
        return
    user = update.effective_user
    d = get_user(user.id)
    text = f"{cfg()['account']}\n\nنام: {user.first_name}\nیوزرنیم: @{user.username or 'ندارد'}\nآیدی: {user.id}\nموجودی: {d.get('points',0)} امتیاز\nزیرمجموعه: {d.get('refs',0)}\nعضویت: {d.get('date','-')}"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="back")]]))

async def referral(update, ctx):
    if not await is_member(update.effective_user.id, ctx):
        await force_join(update, ctx)
        return
    bot = await ctx.bot.get_me()
    link = f"https://t.me/{bot.username}?start=ref_{update.effective_user.id}"
    await update.message.reply_text(cfg()["referral"] + "\n" + link, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="back")]]))

async def withdraw(update, ctx):
    if not await is_member(update.effective_user.id, ctx):
        await force_join(update, ctx)
        return
    await update.message.reply_text(cfg()["withdraw"], reply_markup=withdraw_kb())

async def support_start(update, ctx):
    if not await is_member(update.effective_user.id, ctx):
        await force_join(update, ctx)
        return
    ctx.user_data["waiting_support"] = True
    await update.message.reply_text(cfg()["support"], reply_markup=ReplyKeyboardMarkup([[KeyboardButton("بازگشت")]], resize_keyboard=True))

async def reply_cb(update, ctx):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID: return
    ctx.user_data["reply_to"] = int(q.data[2:])
    await q.message.reply_text("پیام پاسخ را بنویسید:")

async def sponsor(update, ctx):
    if not await is_member(update.effective_user.id, ctx):
        await force_join(update, ctx)
        return
    await update.message.reply_text(cfg()["sponsor"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="back")]]))

async def back(update, ctx):
    q = update.callback_query
    await q.answer()
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_message(q.from_user.id, "منوی اصلی", reply_markup=kb(q.from_user.id))

async def admin(update, ctx):
    if update.effective_user.id != ADMIN_ID: return
    btns = [
        [InlineKeyboardButton("📢 مدیریت چنل‌ها", callback_data="a_ch")],
        [InlineKeyboardButton("⭐ امتیاز زیرمجموعه", callback_data="a_pt")],
        [InlineKeyboardButton("🔘 فعال/غیرفعال دکمه‌ها", callback_data="a_tg")],
        [InlineKeyboardButton("📊 آمار ربات", callback_data="a_st")],
    ]
    await update.message.reply_text("⚙️ پنل مدیریت ربات", reply_markup=InlineKeyboardMarkup(btns))

async def admin_cb(update, ctx):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID: return
    d = q.data
    c = cfg()

    if d == "a_ch":
        t = "📢 چنل‌ها:\n\n"
        for i, ch in enumerate(channels(), 1): t += f"{i}. {ch['title']}\n"
        t += "\n/addchannel آیدی لینک عنوان\n/removechannel شماره"
        await q.message.edit_text(t)
    elif d == "a_pt":
        ctx.user_data["waiting_edit"] = "points_per_ref"
        await q.message.edit_text(f"امتیاز فعلی هر زیرمجموعه: {c['points_per_ref']}\nعدد جدید را بفرستید:")
    elif d == "a_tg":
        btns = [
            [InlineKeyboardButton(f"{'✅' if c['enable_ref'] else '❌'} زیرمجموعه", callback_data="t_ref")],
            [InlineKeyboardButton(f"{'✅' if c['enable_wd'] else '❌'} برداشت", callback_data="t_wd")],
            [InlineKeyboardButton(f"{'✅' if c['enable_acc'] else '❌'} حساب", callback_data="t_acc")],
            [InlineKeyboardButton(f"{'✅' if c['enable_sup'] else '❌'} پشتیبانی", callback_data="t_sup")],
            [InlineKeyboardButton(f"{'✅' if c['enable_sp'] else '❌'} اسپانسر", callback_data="t_sp")],
        ]
        await q.message.edit_text("وضعیت دکمه‌ها:", reply_markup=InlineKeyboardMarkup(btns))
    elif d.startswith("t_"):
        key = "enable_" + d[2:]
        c[key] = not c.get(key, True)
        save_cfg(c)
        btns = [
            [InlineKeyboardButton(f"{'✅' if c['enable_ref'] else '❌'} زیرمجموعه", callback_data="t_ref")],
            [InlineKeyboardButton(f"{'✅' if c['enable_wd'] else '❌'} برداشت", callback_data="t_wd")],
            [InlineKeyboardButton(f"{'✅' if c['enable_acc'] else '❌'} حساب", callback_data="t_acc")],
            [InlineKeyboardButton(f"{'✅' if c['enable_sup'] else '❌'} پشتیبانی", callback_data="t_sup")],
            [InlineKeyboardButton(f"{'✅' if c['enable_sp'] else '❌'} اسپانسر", callback_data="t_sp")],
        ]
        await q.message.edit_text("وضعیت دکمه‌ها:", reply_markup=InlineKeyboardMarkup(btns))
    elif d == "a_st":
        u = users()
        t = f"📊 آمار\n\nکاربران: {len(u)}\nامتیاز کل: {sum(x.get('points',0) for x in u.values())}\nزیرمجموعه: {sum(x.get('refs',0) for x in u.values())}"
        await q.message.edit_text(t)

async def add_ch(update, ctx):
    if update.effective_user.id != ADMIN_ID: return
    a = ctx.args
    if len(a) < 3:
        await update.message.reply_text("/addchannel آیدی لینک عنوان")
        return
    chs = channels()
    chs.append({"id": a[0], "link": a[1], "title": " ".join(a[2:])})
    save_channels(chs)
    await update.message.reply_text("✅ اضافه شد.")

async def rem_ch(update, ctx):
    if update.effective_user.id != ADMIN_ID: return
    a = ctx.args
    if not a or not a[0].isdigit(): return
    chs = channels()
    i = int(a[0]) - 1
    if 0 <= i < len(chs):
        chs.pop(i)
        save_channels(chs)
        await update.message.reply_text("✅ حذف شد.")

async def msg(update, ctx):
    t = update.message.text
    u = update.effective_user
    c = cfg()

    if ctx.user_data.get("waiting_post"):
        wd = ctx.user_data.pop("waiting_post")
        us = users()
        cost = 2 if wd == "star" else 10
        us[str(u.id)]["points"] = max(0, us[str(u.id)].get("points", 0) - cost)
        save_users(us)
        kind = "۱ استارز" if wd == "star" else "تدی رایگان"
        text = f"📤 درخواست برداشت\n\nنوع: {kind}\nکاربر: {u.first_name}\nآیدی: {u.id}\n\nلینک پست:\n{t}"
        await ctx.bot.send_message(ADMIN_ID, text)
        await update.message.reply_text("✅ درخواست ثبت شد.", reply_markup=kb(u.id))
        return

    if ctx.user_data.get("waiting_support"):
        ctx.user_data.pop("waiting_support", None)
        if t == "بازگشت":
            await update.message.reply_text("منوی اصلی", reply_markup=kb(u.id))
            return
        await ctx.bot.send_message(ADMIN_ID, f"📩 پشتیبانی\n{u.first_name} | {u.id}\n\n{t}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("پاسخ", callback_data=f"r_{u.id}")]]))
        await update.message.reply_text("✅ ارسال شد.", reply_markup=kb(u.id))
        return

    if ctx.user_data.get("reply_to"):
        tid = ctx.user_data.pop("reply_to")
        try:
            await ctx.bot.send_message(tid, f"📬 پاسخ پشتیبانی:\n\n{t}")
            await update.message.reply_text("✅ ارسال شد.")
        except Exception as e:
            await update.message.reply_text(f"خطا: {e}")
        return

    if ctx.user_data.get("waiting_edit"):
        key = ctx.user_data.pop("waiting_edit")
        conf = cfg()
        try:
            conf[key] = int(t)
            save_cfg(conf)
            await update.message.reply_text("✅ ذخیره شد.", reply_markup=kb(ADMIN_ID))
        except:
            await update.message.reply_text("عدد وارد کنید.")
            ctx.user_data["waiting_edit"] = key
        return

    if t == "⭐ ۱ استارز":
        d = get_user(u.id)
        if d.get("points", 0) < 2:
            await update.message.reply_text("موجود شما کافی نیست\n(نیاز به ۲ امتیاز)", reply_markup=kb(u.id))
        else:
            ctx.user_data["waiting_post"] = "star"
            await update.message.reply_text("لطفاً آیدی یا لینک پست را وارد کنید:", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("بازگشت")]], resize_keyboard=True))
        return

    if t == "❤️ تدی رایگان":
        d = get_user(u.id)
        if d.get("points", 0) < 10:
            await update.message.reply_text("موجود شما کافی نیست\n(نیاز به ۱۰ امتیاز)", reply_markup=kb(u.id))
        else:
            ctx.user_data["waiting_post"] = "teddy"
            await update.message.reply_text("لطفاً آیدی یا لینک پست را وارد کنید:", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("بازگشت")]], resize_keyboard=True))
        return

    if t == "حساب کاربری" and c["enable_acc"]: await account(update, ctx)
    elif t == "زیرمجموعه گیری" and c["enable_ref"]: await referral(update, ctx)
    elif t == "برداشت" and c["enable_wd"]: await withdraw(update, ctx)
    elif t == "پشتیبانی" and c["enable_sup"]: await support_start(update, ctx)
    elif t == "اسپان سری ربات" and c["enable_sp"]: await sponsor(update, ctx)
    elif t == "پنل ادمین": await admin(update, ctx)
    elif t == "بازگشت":
        await update.message.reply_text("منوی اصلی", reply_markup=kb(u.id))
    else:
        if not await is_member(u.id, ctx): await force_join(update, ctx)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check, pattern="^check$"))
    app.add_handler(CallbackQueryHandler(reply_cb, pattern="^r_"))
    app.add_handler(CallbackQueryHandler(back, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(admin_cb, pattern="^a_|^t_"))
    app.add_handler(CommandHandler("addchannel", add_ch))
    app.add_handler(CommandHandler("removechannel", rem_ch))
    app.add_handler(MessageHandler(filters.TEXT, msg))
    print("✅ ربات آماده است")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
