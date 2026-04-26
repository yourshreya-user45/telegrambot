import os
import re
import io
import qrcode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

TOKEN = os.environ.get("TOKEN")
UPI_ID = "Q850464187@ybl"
ADMIN_ID = 123456789  # 👈 Apna Telegram ID daalo

GROUP_LINK = "https://t.me/+9H9e4toM3kE3YmE9"

PLAN = {
    "name": "📸 Photo Editing Pack",
    "pictures": "10 Pictures",
    "price": 500,
    "features": ["Professional Editing", "Color Correction", "Background Remove", "2 Revisions"],
}

WAITING_UTR = 1
WAITING_SCREENSHOT = 2


def make_qr(upi_id: str, amount: int) -> io.BytesIO:
    upi_url = f"upi://pay?pa={upi_id}&pn=PhotoStudio&am={amount}&cu=INR"
    img = qrcode.make(upi_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def is_valid_utr(text: str) -> bool:
    return bool(re.match(r'^\d{12}$', text.strip()))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    qr = make_qr(UPI_ID, PLAN["price"])
    features_text = "\n".join([f"   ✔️ {f}" for f in PLAN["features"]])

    await update.message.reply_photo(
        photo=qr,
        caption=(
            f"🎨 *PHOTO EDITING STUDIO*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📸 *{PLAN['pictures']}* — ₹{PLAN['price']}\n\n"
            f"*Includes:*\n{features_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📲 *UPI ID:* `{UPI_ID}`\n\n"
            f"*Steps:*\n"
            f"1️⃣ QR scan karo ya UPI ID copy karo\n"
            f"2️⃣ Exactly ₹{PLAN['price']} pay karo\n"
            f"3️⃣ 12-digit UTR Number bhejo\n"
            f"4️⃣ Screenshot bhejo\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⬇️ *Abhi 12-digit UTR Number type karke bhejo:*"
        ),
        parse_mode="Markdown"
    )
    return WAITING_UTR


async def receive_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not msg.text:
        await msg.reply_text(
            "❗ *Sirf text mein UTR Number bhejo.*\n\n"
            "📱 Payment app → Transaction history → UTR copy karo\n"
            "Example: `123456789012`",
            parse_mode="Markdown"
        )
        return WAITING_UTR

    ref = msg.text.strip()

    if not is_valid_utr(ref):
        await msg.reply_text(
            "❗ *Valid UTR nahi hai.*\n\n"
            "✅ UTR hamesha *12 digits* ka hota hai\n"
            "Example: `123456789012`\n\n"
            "📱 Payment app → Transaction history → UTR copy karo.",
            parse_mode="Markdown"
        )
        return WAITING_UTR

    context.user_data["utr"] = ref
    await msg.reply_text(
        f"✅ *UTR save ho gaya:* `{ref}`\n\n"
        f"📸 *Ab payment ka screenshot bhejo.*\n\n"
        f"⚠️ Screenshot clear hona chahiye — amount aur date dikh raha ho.",
        parse_mode="Markdown"
    )
    return WAITING_SCREENSHOT


async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if context.user_data.get("submitted"):
        await msg.reply_text("⚠️ Tumne already submit kar diya hai. Admin verify kar raha hai.")
        return ConversationHandler.END

    if msg.document:
        await msg.reply_text("❗ File nahi, screenshot bhejo. Gallery se image select karo.")
        return WAITING_SCREENSHOT

    if not msg.photo:
        await msg.reply_text("❗ Sirf screenshot image bhejo.")
        return WAITING_SCREENSHOT

    user = update.effective_user
    utr = context.user_data.get("utr", "N/A")
    context.user_data["submitted"] = True

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=msg.photo[-1].file_id,
            caption=(
                f"💰 *NEW PAYMENT*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *User:* [{user.first_name}](tg://user?id={user.id})\n"
                f"🆔 *User ID:* `{user.id}`\n"
                f"📦 *Plan:* {PLAN['name']} — ₹{PLAN['price']}\n"
                f"🖼 *Pictures:* {PLAN['pictures']}\n"
                f"🔖 *UTR:* `{utr}`\n"
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
        await msg.reply_text("⚠️ Technical issue. Dobara bhejo ya @YourUsername contact karo.")
        return WAITING_SCREENSHOT

    await msg.reply_text(
        "🎉 *Submission Complete!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Payment proof mil gaya\n"
        "⏳ Admin verify karega\n"
        "📩 Approve hone pe group link aayega\n\n"
        "📞 Support: @YourUsername",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Sirf admin kar sakta hai.", show_alert=True)
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
                    "🎉 Tumhara group access ready hai!\n\n"
                    f"👇 *Join karo:*\n{GROUP_LINK}\n\n"
                    "⚠️ Link sirf tumhare liye hai — share mat karna.\n"
                    "Shukriya! 🙏"
                ),
                parse_mode="Markdown"
            )
            await query.edit_message_caption("✅ Approved — group link bhej diya.")
        except Exception:
            await query.answer("User ko message nahi gaya — bot block hai shayad.", show_alert=True)

    elif action == "reject":
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "❌ *Payment Verify Nahi Hua*\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    "Possible reasons:\n"
                    "• Wrong UTR number\n"
                    "• Screenshot clear nahi tha\n"
                    "• Galat amount pay kiya\n\n"
                    "Dobara try karo: /start\n"
                    "Help: @YourUsername"
                ),
                parse_mode="Markdown"
            )
            await query.edit_message_caption("❌ Rejected — user ko notify kar diya.")
        except Exception:
            await query.answer("User ko message nahi gaya — bot block hai shayad.", show_alert=True)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Cancel ho gaya. /start se dobara shuru karo.")
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 /start likho.")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_UTR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_utr),
                MessageHandler(filters.PHOTO | filters.Document.ALL | filters.VOICE | filters.VIDEO | filters.Sticker.ALL, receive_utr),
            ],
            WAITING_SCREENSHOT: [
                MessageHandler(filters.PHOTO, receive_screenshot),
                MessageHandler(filters.Document.ALL | filters.VOICE | filters.VIDEO | filters.Sticker.ALL | (filters.TEXT & ~filters.COMMAND), receive_screenshot),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        allow_reentry=True
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_action, pattern="^(approve|reject)_"))
    app.add_handler(MessageHandler(filters.ALL, unknown))

    print("Bot chal raha hai...")
    app.run_polling()


if __name__ == "__main__":
    main()
