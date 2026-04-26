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
ADMIN_ID = 7455385301

GROUP_LINK = "https://t.me/+9H9e4toM3kE3YmE9"

PLAN = {
    "name": "Shreya Private Hot Pictures 🔞",
    "pictures": "10 Hot N*de Pictures",
    "price": 500,
    # "features": [""],
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
            f"🎨 *Shreya Private Hot Pictures 🔞*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📸 *{PLAN['pictures']}* — ₹{PLAN['price']}\n\n"
            f"*Includes:*\n{features_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📲 *UPI ID:* `{UPI_ID}`\n\n"
            f"*Steps:*\n"
            f"1️⃣ Scan the QR code or copy UPI ID\n"
            f"2️⃣ Pay exactly ₹{PLAN['price']}\n"
            f"3️⃣ send 12-digit UTR Number \n"
            f"4️⃣ Send Screenshot of payment\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⬇️ *Now type 12-digit UTR Number and send it:*"
        ),
        parse_mode="Markdown"
    )
    return WAITING_UTR


async def receive_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not msg.text:
        await msg.reply_text(
            "❗ *Only send UTR Number in text.*\n\n"
            "📱 Payment app → Transaction history → Copy UTR\n"
            "Example: `123456789012`",
            parse_mode="Markdown"
        )
        return WAITING_UTR

    ref = msg.text.strip()

    if not is_valid_utr(ref):
        await msg.reply_text(
            "❗ *Not a valid UTR.*\n\n"
            "✅ UTR always *12 digits* long\n"
            "Example: `123456789012`\n\n"
            "📱 Payment app → Transaction history → Copy UTR.",
            parse_mode="Markdown"
        )
        return WAITING_UTR

    context.user_data["utr"] = ref
    await msg.reply_text(
        f"✅ *Your UTR has been saved:* `{ref}`\n\n"
        f"📸 *Now send Screenshot of payment.*\n\n"
        f"⚠️ Screenshot should be clear — amount and date should be visible.",
        parse_mode="Markdown"
    )
    return WAITING_SCREENSHOT


async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if context.user_data.get("submitted"):
        await msg.reply_text("⚠️ You have already submitted. Admin is verifying.")
        return ConversationHandler.END

    if msg.document:
        await msg.reply_text("❗ Don't send file, send screenshot. Select image from gallery.")
        return WAITING_SCREENSHOT

    if not msg.photo:
        await msg.reply_text("❗ Send screenshot image.")
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
        await msg.reply_text("⚠️ Technical issue. Please send screenshot again or contact @YourUsername.")
        return WAITING_SCREENSHOT

    await msg.reply_text(
        "🎉 *Submission Successful!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Payment proof submitted\n"
        "⏳ Admin will verify\n"
        "📩 Group link will be sent after approval\n\n"
        "📞 Support: @YourUsername",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Only admin can do this.", show_alert=True)
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
                    "🎉 Your group access is ready!\n\n"
                    f"👇 *Join here:*\n{GROUP_LINK}\n\n"
                    "⚠️ Link is only for you — don't share.\n"
                    "Thank you! 🙏"
                ),
                parse_mode="Markdown"
            )
            await query.edit_message_caption("✅ Approved — group link sent.")
        except Exception:
            await query.answer("User can't receive message — bot may be blocked.", show_alert=True)

    elif action == "reject":
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "❌ *Payment Not Verified*\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    "Possible reasons:\n"
                    "• Wrong UTR number\n"
                    "• Screenshot unclear\n"
                    "• Incorrect amount paid\n\n"
                    "Try again: /start\n"
                    "Help: @YourUsername"
                ),
                parse_mode="Markdown"
            )
            await query.edit_message_caption("❌ Rejected — user notified.")
        except Exception:
            await query.answer("User can't receive message — bot may be blocked.", show_alert=True)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelled. Start again with /start.")
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Type /start to begin.")


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
