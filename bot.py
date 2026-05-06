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
ADMIN_ID = 7455385301 # 👈 Apna Telegram ID daalo
SUPPORT = "@shreya_rao22"

WAITING_UTR = 1
WAITING_SCREENSHOT = 2

PLANS = {
    "basic": {
        "emoji": "❤️‍🔥",
        "name": "❤️‍🔥",
        "price": 299,
        "pictures": "3 Hot Pictures",
        "talk": "10 Min Chat",
        "group": "https://t.me/+8Qr_3YGALQ81MTU1",  # 👈 Basic plan ka link
    },
    "pro": {
        "emoji": "🥵",
        "name": "🥵",
        "price": 599,
        "pictures": "5 Hot Pictures",
        "talk": "30 Min Chat",
        "group": "https://t.me/+Aug56KiJA9EwZTdl",    # 👈 Pro plan ka link
    },
    "vip": {
        "emoji": "💦",
        "name": "💦",
        "price": 1499,
        "pictures": "10 Hot Pictures",
        "talk": "1 Hour Chat",
        "group": "https://t.me/+VipDummyLink789",    # 👈 VIP plan ka link
    },
}


def make_qr(upi_id: str, amount: int) -> io.BytesIO:
    upi_url = f"upi://pay?pa={upi_id}&pn=Studio&am={amount}&cu=INR"
    img = qrcode.make(upi_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def is_valid_utr(text: str) -> bool:
    return bool(re.match(r'^\d{12}$', text.strip()))

def plan_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{p['emoji']} {p['name']} | {p['pictures']} + {p['talk']} | Rs.{p['price']}",
            callback_data=key
        )]
        for key, p in PLANS.items()
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Choose your plan:",
        reply_markup=plan_keyboard()
    )


async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if context.user_data.get("submitted"):
        await query.answer("Already submitted. Admin is verifying.", show_alert=True)
        return ConversationHandler.END

    plan_key = query.data
    plan = PLANS.get(plan_key)
    if not plan:
        await query.message.reply_text("Something went wrong. Type /start again.")
        return ConversationHandler.END

    context.user_data["plan"] = plan_key
    context.user_data["submitted"] = False

    qr = make_qr(UPI_ID, plan["price"])

    await query.message.reply_photo(
        photo=qr,
        caption=(
            f"{plan['emoji']} {plan['name']}\n"
            f"{'─'*22}\n"
            f"📸 {plan['pictures']}\n"
            f"🎙 {plan['talk']}\n"
            f"💰 Rs.{plan['price']}\n"
            f"{'─'*22}\n\n"
            f"UPI ID: {UPI_ID}\n\n"
            f"Steps:\n"
            f"1. QR scan or copy UPI ID\n"
            f"2. Pay exactly Rs.{plan['price']}\n"
            f"3. Send 12-digit UTR number\n"
            f"4. Send payment screenshot\n\n"
            f"Send UTR number now:"
        )
    )
    return WAITING_UTR


async def receive_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not msg.text:
        await msg.reply_text(
            "Send UTR number in text only.\n"
            "Example: 123456789012"
        )
        return WAITING_UTR

    ref = msg.text.strip()

    if not is_valid_utr(ref):
        await msg.reply_text(
            "Invalid UTR.\n\n"
            "UTR is always 12 digits.\n"
            "Example: 123456789012\n\n"
            "Find it in Payment app > Transaction history."
        )
        return WAITING_UTR

    context.user_data["utr"] = ref
    await msg.reply_text(
        f"UTR saved: {ref}\n\n"
        f"Now send payment screenshot.\n"
        f"Make sure amount and date are visible."
    )
    return WAITING_SCREENSHOT


async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if context.user_data.get("submitted"):
        await msg.reply_text("Already submitted. Wait for admin verification.")
        return ConversationHandler.END

    if msg.document:
        await msg.reply_text("Send screenshot image, not a file.")
        return WAITING_SCREENSHOT

    if not msg.photo:
        await msg.reply_text("Send screenshot image only.")
        return WAITING_SCREENSHOT

    user = update.effective_user
    plan_key = context.user_data.get("plan", "unknown")
    plan = PLANS.get(plan_key, {})
    utr = context.user_data.get("utr", "N/A")
    context.user_data["submitted"] = True

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=msg.photo[-1].file_id,
            caption=(
                f"NEW PAYMENT\n"
                f"{'─'*22}\n"
                f"User: {user.first_name}\n"
                f"User ID: {user.id}\n"
                f"Plan: {plan.get('name')} - Rs.{plan.get('price')}\n"
                f"Pictures: {plan.get('pictures')}\n"
                f"Talk: {plan.get('talk')}\n"
                f"UTR: {utr}\n"
                f"{'─'*22}"
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
            ]])
        )
    except Exception:
        context.user_data["submitted"] = False
        await msg.reply_text(f"Technical issue. Try again or contact {SUPPORT}.")
        return WAITING_SCREENSHOT

    await msg.reply_text(
        "Submission complete!\n\n"
        "Payment proof received.\n"
        "Admin will verify soon.\n"
        "You will get a message after approval.\n\n"
        f"Support: {SUPPORT}"
    )
    return ConversationHandler.END


async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if int(query.from_user.id) != int(ADMIN_ID):
        await query.answer("Only admin can do this.", show_alert=True)
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
            # User ka plan dhundo — caption se user_id match karke
            # Plan info admin ke caption mein stored hai
            # Hum user_data se plan nahi le sakte (alag context hai)
            # Isliye sabse safe: approve karte waqt caption mein plan store tha
            # Workaround: caption parse karke plan key nikalo
            caption = query.message.caption or ""
            plan_key = "basic"  # default
            for key in ["basic", "pro", "vip"]:
                plan_name = PLANS[key]["name"]
                if plan_name in caption:
                    plan_key = key
                    break
            
            group_link = PLANS[plan_key]["group"]
            
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"Payment Verified!\n\n"
                    f"Your order is confirmed.\n\n"
                    f"Join your group here:\n{group_link}\n\n"
                    f"Link is only for you - do not share.\n"
                    f"Thank you!"
                )
            )
            await query.edit_message_caption("Approved - group link sent to user.")
        except Exception as e:
            await query.answer(f"Error: {str(e)[:150]}", show_alert=True)

    elif action == "reject":
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "Payment not verified.\n\n"
                    "Reasons:\n"
                    "- Wrong UTR number\n"
                    "- Screenshot not clear\n"
                    "- Wrong amount paid\n\n"
                    "Try again: /start\n"
                    f"Help: {SUPPORT}"
                )
            )
            await query.edit_message_caption("Rejected - user notified.")
        except Exception as e:
            await query.answer(f"Error: {str(e)[:150]}", show_alert=True)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled. Type /start to begin again.")
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Type /start to begin.")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(plan_selected, pattern="^(basic|pro|vip)$")],
        states={
            WAITING_UTR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_utr),
                MessageHandler(
                    filters.PHOTO | filters.Document.ALL |
                    filters.VOICE | filters.VIDEO | filters.Sticker.ALL,
                    receive_utr
                ),
            ],
            WAITING_SCREENSHOT: [
                MessageHandler(filters.PHOTO, receive_screenshot),
                MessageHandler(
                    filters.Document.ALL | filters.VOICE | filters.VIDEO |
                    filters.Sticker.ALL | (filters.TEXT & ~filters.COMMAND),
                    receive_screenshot
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_action, pattern="^(approve|reject)_"))
    app.add_handler(MessageHandler(filters.ALL, unknown))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
