import asyncio
import logging
import aiohttp
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8523978251:AAFizi4UHoFNL_kB4E4We50I16AYauAXVGM"
GROQ_KEY = "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"

logging.basicConfig(level=logging.WARNING)
groq_client = Groq(api_key=GROQ_KEY)

def kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Trending", callback_data="trending"),
         InlineKeyboardButton("🚀 Pump.fun", callback_data="pump")],
        [InlineKeyboardButton("🤖 Ask AI", callback_data="ai"),
         InlineKeyboardButton("📈 SOL Price", callback_data="sol")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome Micky!\n\n🤖 *MickyBot — Solana AI Trading Agent*\n\nPick an option below 👇",
        reply_markup=kb(),
        parse_mode="Markdown"
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "trending":
        await q.edit_message_text("⏳ Fetching trending tokens...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.dexscreener.com/latest/dex/search?q=solana",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as r:
                    data = await r.json()
                    pairs = [p for p in data.get("pairs", []) if p.get("chainId") == "solana"][:5]
                    msg = "🔥 *Trending Solana Tokens*\n\n"
                    for p in pairs:
                        sym = p.get("baseToken", {}).get("symbol", "???")
                        price = p.get("priceUsd", "N/A")
                        change = p.get("priceChange", {}).get("h1", 0)
                        e = "🟢" if float(change or 0) > 0 else "🔴"
                        msg += f"{e} *{sym}* | ${price} | {change}%\n"
        except Exception as ex:
            msg = f"⚠️ Could not load data. Try again."
        await q.edit_message_text(msg, parse_mode="Markdown", reply_markup=kb())

    elif q.data == "pump":
        await q.edit_message_text("⏳ Scanning Pump.fun...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.dexscreener.com/latest/dex/search?q=pump",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as r:
                    data = await r.json()
                    pairs = [p for p in data.get("pairs", []) if p.get("chainId") == "solana"][:5]
                    msg = "🚀 *Pump.fun Signals*\n\n"
                    for p in pairs:
                        sym = p.get("baseToken", {}).get("symbol", "???")
                        price = p.get("priceUsd", "N/A")
                        change = p.get("priceChange", {}).get("m5", 0)
                        msg += f"⚡ *{sym}* | ${price} | 5m: {change}%\n"
        except Exception as ex:
            msg = "⚠️ Could not load data. Try again."
        await q.edit_message_text(msg, parse_mode="Markdown", reply_markup=kb())

    elif q.data == "sol":
        await q.edit_message_text("⏳ Getting SOL price...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd&include_24hr_change=true",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as r:
                    data = await r.json()
                    price = data["solana"]["usd"]
                    change = data["solana"]["usd_24h_change"]
                    e = "🟢" if change > 0 else "🔴"
                    msg = f"📈 *Solana Price*\n\n{e} SOL: *${price:,.2f}*\n24h: *{change:.2f}%*"
        except Exception as ex:
            msg = "⚠️ Could not fetch SOL price."
        await q.edit_message_text(msg, parse_mode="Markdown", reply_markup=kb())

    elif q.data == "ai":
        context.user_data["waiting_ai"] = True
        await q.edit_message_text("🤖 Ask me anything about Solana tokens, trades, or alpha:")

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_ai"):
        context.user_data["waiting_ai"] = False
        await update.message.reply_text("🤖 Thinking...")
        try:
            response = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "You are MickyBot, an elite Solana memecoin trading AI. Give sharp, concise alpha. No fluff."},
                    {"role": "user", "content": update.message.text}
                ],
                max_tokens=300
            )
            reply = response.choices[0].message.content
        except:
            reply = "⚠️ AI unavailable right now."
        await update.message.reply_text(reply, reply_markup=kb())
    else:
        await update.message.reply_text("Use the buttons below or send /start 👇", reply_markup=kb())

def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))
    print("✅ MickyBot is online and running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, timeout=30)

if __name__ == "__main__":
    main()
