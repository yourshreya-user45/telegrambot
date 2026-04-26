import os
import qrcode
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(
            f"{p['emoji']}  {p['name']}  |  {p['pictures']}  |  ₹{p['price']}",
            callback_data=key
        )]
        for key, p in PLANS.items()
    ]
    keyboard.append([InlineKeyboardButton("📞 Support", url="https://t.me/shreya_rao22")])

    await update.message.reply_text(
        "🎨 *PHOTO EDITING STUDIO*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Professional Editing\n"
        "⚡ Fast Delivery — 24hrs\n"
        "💯 100% Satisfaction\n"
        "🔒 Secure UPI Payment\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 *Apna plan select karo:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def make_qr(upi_id, amount):
    upi_url = f"upi://pay?pa={upi_id}&pn=PhotoStudio&am={amount}&cu=INR"
    img = qrcode.make(upi_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plan_key = query.data
    plan = PLANS.get(plan_key)
    if not plan:
        return ConversationHandler.END

    context.user_data["plan"] = plan_key
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
            f"1️⃣ QR scan karo ya UPI ID se pay karo\n"
            f"2️⃣ Transaction/Reference ID bhejo\n"
            f"3️⃣ Screenshot bhejo\n\n"
            f"⬇️ *Abhi Reference ID bhejo:*"
        ),
        parse_mode="Markdown"
    )
    return WAITING_REF


async def receive_ref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ref = update.message.text.strip()
    if len(ref) < 4:
        await update.message.reply_text("❗ Sahi Reference ID daalo.")
        return WAITING_REF

    context.user_data["ref_id"] = ref
    await update.message.reply_text(
        "✅ *Reference ID mil gaya!*\n\n"
        "📸 *Ab payment ka screenshot bhejo:*",
        parse_mode="Markdown"
    )
    return WAITING_SCREENSHOT


async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❗ Screenshot image format mein bhejo.")
        return WAITING_SCREENSHOT

    user = update.effective_user
    plan_key = context.user_data.get("plan", "unknown")
    plan = PLANS.get(plan_key, {})
    ref_id = context.user_data.get("ref_id", "N/A")

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=(
            f"💰 *NEW PAYMENT*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* [{user.first_name}](tg://user?id={user.id})\n"
            f"🆔 *User ID:* `{user.id}`\n"
            f"📦 *Plan:* {plan.get('name')} — ₹{plan.get('price')}\n"
            f"🖼 *Pictures:* {plan.get('pictures')}\n"
            f"🔖 *Ref ID:* `{ref_id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
        ]])
    )

    await update.message.reply_text(
        "🎉 *Submission Complete!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Payment proof mil gaya\n"
        "⏳ Admin 1-2 ghante mein verify karega\n"
        "📩 Confirm hone pe message aayega\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📞 Support: @shreya_rao22",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if "_" not in query.data:
        return

    action, user_id = query.data.split("_", 1)
    user_id = int(user_id)

    if action == "approve":
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

    elif action == "reject":
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ *Payment Verify Nahi Hua*\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "Possible reasons:\n"
                "• Wrong reference ID\n"
                "• Screenshot clear nahi tha\n\n"
                "Dobara try karo /start\n"
                "Help: @YourUsername"
            ),
            parse_mode="Markdown"
        )
        await query.edit_message_caption("❌ Rejected — user ko notify kar diya.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Cancelled.\n/start se dobara shuru karo.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(plan_selected, pattern="^(basic|pro|vip)$")],
        states={
            WAITING_REF: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_ref)],
            WAITING_SCREENSHOT: [MessageHandler(filters.PHOTO, receive_screenshot)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_action, pattern="^(approve|reject)_"))

    print("Bot chal raha hai...")
    app.run_polling()


if __name__ == "__main__":
    main()
