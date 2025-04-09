from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
import os
from database import add_key, get_available_key, mark_key_sold, save_transaction, update_transaction_status
from payments import generate_address, check_payment
import asyncio

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Prices (in crypto units)
PRICES = {"ProductA": {"BTC": 0.0001, "LTC": 0.01, "USDT_BEP20": 5.0}}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Buy Serial Key", callback_data="buy")],
        [InlineKeyboardButton("Check Balance", callback_data="balance")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to KeyShopBot!", reply_markup=reply_markup)

async def add_key_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Unauthorized!")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /addkey <product> <key>")
        return
    product, key = args[0], args[1]
    add_key(product, key)
    await update.message.reply_text(f"Added {product} key: {key}")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy":
        keyboard = [[InlineKeyboardButton(p, callback_data=f"purchase_{p}")] for p in PRICES.keys()]
        await query.edit_message_text("Choose a product:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("purchase_"):
        product = query.data.split("_")[1]
        key = get_available_key(product)
        if not key:
            await query.edit_message_text("Out of stock!")
            return

        keyboard = [
            [InlineKeyboardButton("BTC", callback_data=f"pay_{product}_BTC")],
            [InlineKeyboardButton("LTC", callback_data=f"pay_{product}_LTC")],
            [InlineKeyboardButton("USDT (BEP-20)", callback_data=f"pay_{product}_USDT_BEP20")]
        ]
        await query.edit_message_text("Choose payment method:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("pay_"):
        _, product, currency = query.data.split("_")
        key = get_available_key(product)
        amount = PRICES[product][currency]
        address = generate_address(currency)
        
        save_transaction(query.from_user.id, product, address, currency, amount)
        await query.edit_message_text(
            f"Send {amount} {currency} to:\n{address}\nI’ll check every 60s for payment."
        )
        
        # Start payment check
        asyncio.create_task(check_payment_loop(query.from_user.id, product, address, currency, amount, context))

async def check_payment_loop(user_id, product, address, currency, amount, context):
    while True:
        if check_payment(address, currency, amount):
            key = get_available_key(product)
            mark_key_sold(key["_id"])
            update_transaction_status(address, "completed")
            await context.bot.send_message(user_id, f"Payment confirmed! Your key: {key['key']}")
            break
        await asyncio.sleep(60)  # Check every minute

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addkey", add_key_cmd))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == "__main__":
    main()
