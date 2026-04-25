import os
import re
import io
import qrcode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

TOKEN = os.environ.get("TOKEN")
UPI_ID = "Q850464187@ybl"
ADMIN_ID = 7455385301  # 👈 Apna Telegram ID daalo (@userinfobot se milega)

WAITING_REF = 1
WAITING_SCREENSHOT = 2

PLANS = {
    "basic": {
        "name": "✨ Starter Pack",
        "pictures": "3 Pictures",
        "price": 299,
        "features": ["Basic Editing", "Color Correction", "1 Revision"],
        "emoji": "🥉"
    },
    "pro": {
        "name": "🔥 Pro Pack",
        "pictures": "6 Pictures",
        "price": 549,
        "features": ["Advanced Editing", "Background Remove", "2 Revisions"],
        "emoji": "🥈"
    },
    "vip": {
        "name": "👑 VIP Pack",
        "pictures": "15+ Pictures",
        "price": 999,
        "features": ["Premium Editing", "Special Effects", "Unlimited Revisions"],
        "emoji": "🥇"
    },
}

# ── Helpers ──────────────────────────────────────────────

def make_qr(upi_id: str, amount: int) -> io.BytesIO:
    upi_url = f"upi://pay?pa={upi_id}&pn=PhotoStudio&am={amount}&cu=INR"
    img = qrcode.make(upi_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def is_valid_utr(text: str) -> bool:
    """
    UTR number hamesha exactly 12 digits ka hota hai.
    """
    text = text.strip()
    return bool(re.match(r'^\d{12}$', text))

def main_keyboard():
    """Bottom mein dikhne wala Reply Keyboard"""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🥉 Starter Pack — ₹299"), KeyboardButton("🔥 Pro Pack — ₹549")],
            [KeyboardButton("👑 VIP Pack — ₹999")],
            [KeyboardButton("📞 Support"), KeyboardButton("ℹ️ About")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Plan choose karo..."
    )


# ── Handlers ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🎨 *PHOTO EDITING STUDIO*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Professional Editing\n"
        "⚡ Fast Delivery — 24hrs\n"
        "💯 100% Satisfaction\n"
        "🔒 Secure UPI Payment\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 *Niche se apna plan select karo:*",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )


async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply keyboard buttons handle karo"""
    text = update.message.text

    if "Starter Pack" in text:
        context.user_data["plan"] = "basic"
        await send_plan_qr(update, context, "basic")
        return WAITING_REF

    elif "Pro Pack" in text:
        context.user_data["plan"] = "pro"
        await send_plan_qr(update, context, "pro")
        return WAITING_REF

    elif "VIP Pack" in text:
        context.user_data["plan"] = "vip"
        await send_plan_qr(update, context, "vip")
        return WAITING_REF

    elif "Support" in text:
        await update.message.reply_text(
            "📞 *Support*\n\n"
            "Kisi bhi problem ke liye:\n"
            "@YourUsername pe message karo",
            parse_mode="Markdown"
        )

    elif "About" in text:
        await update.message.reply_text(
            "ℹ️ *About Us*\n\n"
            "🎨 Professional photo editing service\n"
            "⚡ 24hr delivery\n"
            "💯 100% satisfaction guarantee\n\n"
            "Plan lene ke liye niche buttons dabao.",
            parse_mode="Markdown"
        )


async def send_plan_qr(update: Update, context: ContextTypes.DEFAULT_TYPE, plan_key: str):
    """QR aur plan details bhejo"""
    plan = PLANS[plan_key]
    context.user_data["submitted"] = False
    qr = make_qr(UPI_ID, plan["price"])
    features_text = "\n".join([f"   ✔️ {f}" for f in plan["features"]])

    await update.message.reply_text(
        "⏳ QR generate ho raha hai...",
        reply_markup=ReplyKeyboardRemove()
    )

    await update.message.reply_photo(
        photo=qr,
        caption=(
            f"{plan['emoji']} *{plan['name']}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🖼 *{plan['pictures']}*\n"
            f"💰 *Price: ₹{plan['price']}*\n\n"
            f"*Includes:*\n{features_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📲 *UPI ID:* `{UPI_ID}`\n\n"
            f"*Steps:*\n"
            f"1️⃣ QR scan karo ya UPI ID copy karo\n"
            f"2️⃣ Exactly ₹{plan['price']} pay karo\n"
            f"3️⃣ 12-digit UTR Number bhejo\n"
            f"4️⃣ Screenshot bhejo\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⬇️ *Abhi 12-digit UTR Number type karke bhejo:*"
        ),
        parse_mode="Markdown"
    )


async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline callback buttons ke liye (agar future mein use ho)"""
    query = update.callback_query
    await query.answer()

    if context.user_data.get("submitted"):
        await query.answer(
            "✅ Tumne already submit kar diya hai. Admin verify kar raha hai.",
            show_alert=True
        )
        return ConversationHandler.END

    plan_key = query.data
    plan = PLANS.get(plan_key)
    if not plan:
        await query.message.reply_text("❗ Kuch galat hua. /start dobara karo.")
        return ConversationHandler.END

    context.user_data["plan"] = plan_key
    context.user_data["submitted"] = False

    qr = make_qr(UPI_ID, plan["price"])
    features_text = "\n".join([f"   ✔️ {f}" for f in plan["features"]])

    await query.message.reply_photo(
        photo=qr,
        caption=(
            f"{plan['emoji']} *{plan['name']}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🖼 *{plan['pictures']}*\n"
            f"💰 *Price: ₹{plan['price']}*\n\n"
            f"*Includes:*\n{features_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📲 *UPI ID:* `{UPI_ID}`\n\n"
            f"*Steps:*\n"
            f"1️⃣ QR scan karo ya UPI ID copy karo\n"
            f"2️⃣ Exactly ₹{plan['price']} pay karo\n"
            f"3️⃣ 12-digit UTR Number bhejo\n"
            f"4️⃣ Screenshot bhejo\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⬇️ *Abhi 12-digit UTR Number type karke bhejo:*"
        ),
        parse_mode="Markdown"
    )
    return WAITING_REF



async def receive_ref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    # Non-text bheja (sticker, voice, photo, video, document)
    if not msg.text:
        await msg.reply_text(
            "❗ *Sirf text mein UTR Number bhejo.*\n\n"
            "📱 Payment app → Transaction history → UTR copy karo\n"
            "Example: `123456789012`",
            parse_mode="Markdown"
        )
        return WAITING_REF

    ref = msg.text.strip()

    if not is_valid_utr(ref):
        await msg.reply_text(
            "❗ *Yeh valid UTR number nahi hai.*\n\n"
            "✅ UTR hamesha *12 digits* ka hota hai\n"
            "Example: `123456789012`\n\n"
            "📱 Payment app → Transaction history → UTR copy karo.",
            parse_mode="Markdown"
        )
        return WAITING_REF

    context.user_data["ref_id"] = ref
    await msg.reply_text(
        f"✅ *UTR Number save:* `{ref}`\n\n"
        f"📸 *Ab payment ka screenshot bhejo.*\n\n"
        f"⚠️ Screenshot:\n"
        f"• Clear hona chahiye\n"
        f"• Amount aur date dikh raha ho\n"
        f"• Cropped mat karna",
        parse_mode="Markdown"
    )
    return WAITING_SCREENSHOT


async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    # Already submitted
    if context.user_data.get("submitted"):
        await msg.reply_text(
            "⚠️ *Tumne already submit kar diya hai.*\n"
            "Admin verify kar raha hai. Wait karo.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    # Document bheja (PDF ya file)
    if msg.document:
        await msg.reply_text(
            "❗ *File nahi, Screenshot chahiye.*\n\n"
            "Phone ki gallery se payment screenshot select karo.",
            parse_mode="Markdown"
        )
        return WAITING_SCREENSHOT

    # Text, sticker, voice, video bheja
    if not msg.photo:
        await msg.reply_text(
            "❗ *Sirf screenshot image bhejo.*\n\n"
            "Gallery open karo → Payment screenshot select karo → Bhejo.",
            parse_mode="Markdown"
        )
        return WAITING_SCREENSHOT

    user = update.effective_user
    plan_key = context.user_data.get("plan", "unknown")
    plan = PLANS.get(plan_key, {})
    ref_id = context.user_data.get("ref_id", "N/A")

    context.user_data["submitted"] = True  # Duplicate block karo

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=msg.photo[-1].file_id,
            caption=(
                f"💰 *NEW PAYMENT*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *User:* [{user.first_name}](tg://user?id={user.id})\n"
                f"🆔 *User ID:* `{user.id}`\n"
                f"📦 *Plan:* {plan.get('name')} — ₹{plan.get('price')}\n"
                f"🖼 *Pictures:* {plan.get('pictures')}\n"
                f"🔖 *UTR Number:* `{ref_id}`\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
            ]])
        )
    except Exception:
        context.user_data["submitted"] = False
        await msg.reply_text(
            "⚠️ Technical issue aaya. Dobara bhejo.\n"
            "Agar phir bhi na ho: @YourUsername"
        )
        return WAITING_SCREENSHOT

    await msg.reply_text(
        "🎉 *Submission Complete!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Payment proof mil gaya\n"
        "⏳ Admin 1-2 ghante mein verify karega\n"
        "📩 Confirm hone pe message aayega\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📞 Support: @YourUsername",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Sirf admin approve/reject kar sakta hai
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Sirf admin yeh kar sakta hai.", show_alert=True)
        return

    if "_" not in query.data:
        return

    action, user_id_str = query.data.split("_", 1)
    try:
        user_id = int(user_id_str)
    except ValueError:
        return

    if action == "approve":
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "✅ *Payment Verified!*\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    "🎨 Tumhari editing shuru ho gayi!\n"
                    "📩 24 ghante mein edited photos bheje jayenge\n\n"
                    "Shukriya! 🙏"
                ),
                parse_mode="Markdown"
            )
            await query.edit_message_caption("✅ Approved — user ko notify kar diya.")
        except Exception:
            await query.answer(
                "User ko message nahi gaya — shayad bot block hai.",
                show_alert=True
            )

    elif action == "reject":
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "❌ *Payment Verify Nahi Hua*\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    "Possible reasons:\n"
                    "• Wrong reference ID\n"
                    "• Screenshot clear nahi tha\n"
                    "• Galat amount pay kiya\n\n"
                    "Dobara try karo: /start\n"
                    "Help chahiye: @YourUsername"
                ),
                parse_mode="Markdown"
            )
            await query.edit_message_caption("❌ Rejected — user ko notify kar diya.")
        except Exception:
            await query.answer(
                "User ko message nahi gaya — shayad bot block hai.",
                show_alert=True
            )


async def unknown_outside_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bina /start ke message bheja"""
    await update.message.reply_text(
        "👋 /start likho aur plan select karo."
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ *Cancelled.*\n\n/start se dobara shuru karo.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END


async def plans_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/plans — saare plans dikhao"""
    text = "📋 *Hamare Plans:*\n\n"
    for p in PLANS.values():
        features = "\n".join([f"   ✔️ {f}" for f in p["features"]])
        text += (
            f"{p['emoji']} *{p['name']}*\n"
            f"🖼 {p['pictures']} | 💰 ₹{p['price']}\n"
            f"{features}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )
    text += "👇 Niche buttons se plan choose karo:"
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())


async def change_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/change — plan badlo, flow reset karo"""
    context.user_data.clear()
    await update.message.reply_text(
        "🔄 *Plan Change*\n\n"
        "Purana selection reset ho gaya.\n"
        "Niche se naya plan choose karo:",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/support — contact info"""
    await update.message.reply_text(
        "📞 *Support*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Kisi bhi problem ke liye:\n"
        "👤 @YourUsername pe message karo\n\n"
        "⏰ Response time: 1-2 ghante",
        parse_mode="Markdown"
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/about — service info"""
    await update.message.reply_text(
        "ℹ️ *About Us*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎨 Professional photo editing service\n"
        "⚡ 24hr delivery guarantee\n"
        "💯 100% satisfaction\n"
        "🔒 Secure UPI payment\n\n"
        "📸 3 se 15+ photos edit karte hain\n"
        "✨ Color correction, background remove aur bahut kuch",
        parse_mode="Markdown"
    )


async def set_bot_commands(app):
    """Bot mein / likhte hi suggestions dikhao"""
    from telegram import BotCommand
    await app.bot.set_my_commands([
        BotCommand("start",   "Bot shuru karo"),
        BotCommand("plans",   "Saare plans dekho"),
        BotCommand("change",  "Plan badlo"),
        BotCommand("support", "Help lो"),
        BotCommand("about",   "Hamare baare mein"),
        BotCommand("cancel",  "Current order cancel karo"),
    ])


# ── Main ─────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(plan_selected, pattern="^(basic|pro|vip)$"),
            MessageHandler(
                filters.TEXT & filters.Regex(r"(Starter Pack|Pro Pack|VIP Pack|Support|About)"),
                handle_menu_buttons
            ),
        ],
        states={
            WAITING_REF: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_ref),
                MessageHandler(
                    filters.PHOTO | filters.Document.ALL |
                    filters.Sticker.ALL | filters.VOICE | filters.VIDEO,
                    receive_ref
                ),
            ],
            WAITING_SCREENSHOT: [
                MessageHandler(filters.PHOTO, receive_screenshot),
                MessageHandler(
                    filters.Document.ALL | filters.Sticker.ALL |
                    filters.VOICE | filters.VIDEO |
                    (filters.TEXT & ~filters.COMMAND),
                    receive_screenshot
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("change", change_plan),
            CommandHandler("start",  start),
        ],
        allow_reentry=True
    )

    # Commands register karo
    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("plans",   plans_command))
    app.add_handler(CommandHandler("change",  change_plan))
    app.add_handler(CommandHandler("support", support_command))
    app.add_handler(CommandHandler("about",   about_command))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_action, pattern="^(approve|reject)_"))
    app.add_handler(MessageHandler(filters.ALL, unknown_outside_conv))

    # / likhte hi suggestions set karo
    import asyncio
    asyncio.get_event_loop().run_until_complete(set_bot_commands(app))

    print("Bot chal raha hai...")
    app.run_polling()


if __name__ == "__main__":
    main()
