from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
import os
from database import save_transaction, update_transaction_status, get_transaction
from payments import generate_sellauth_checkout, check_sellauth_transaction_status
import asyncio

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

PRODUCTS = {
    "SerialKeyA": {
        "sellauth_product_id": 70,  # Replace with your Sellauth product ID
        "sellauth_variant_id": 65   # Replace with your Sellauth variant ID
    }
}
PAYMENT_METHODS = ["BTC", "LTC", "USDT_BEP20"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Buy Serial Key", callback_data="buy")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to KeyShopBot!", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy":
        keyboard = [[InlineKeyboardButton(p, callback_data=f"purchase_{p}")] for p in PRODUCTS.keys()]
        await query.edit_message_text("Choose a product:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("purchase_"):
        product = query.data.split("_")[1]
        keyboard = [[InlineKeyboardButton(m, callback_data=f"pay_{product}_{m}")] for m in PAYMENT_METHODS]
        await query.edit_message_text("Choose payment method:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("pay_"):
        _, product, currency = query.data.split("_")
        try:
            txid = generate_sellauth_checkout(
                product_id=PRODUCTS[product]["sellauth_product_id"],
                variant_id=PRODUCTS[product]["sellauth_variant_id"],
                quantity=1,
                gateway=currency
            )
            await query.edit_message_text(
                f"Payment initiated. Send {currency} to the address provided by Sellauth.\n"
                f"Transaction ID: {txid}\nChecking every 60s for confirmation."
            )
            save_transaction(query.from_user.id, product, txid, currency)
            asyncio.create_task(check_sellauth_payment(query.from_user.id, product, txid, context))
        except Exception as e:
            await query.edit_message_text(f"Payment setup failed: {str(e)}")

async def check_sellauth_payment(user_id, product, txid, context):
    while True:
        transaction = get_transaction(txid)
        if transaction["status"] == "completed":
            break  # Avoid duplicate delivery
        if check_sellauth_transaction_status(txid):
            update_transaction_status(txid, "completed")
            await context.bot.send_message(user_id, f"Payment confirmed for {product}! Check your Sellauth account for the key.")
            break
        await asyncio.sleep(60)

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == "__main__":
    main()
