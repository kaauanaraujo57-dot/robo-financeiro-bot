import os
import psycopg2
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

print("TOKEN:", TOKEN)
print("DATABASE_URL:", DATABASE_URL)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS gastos (
    id SERIAL PRIMARY KEY,
    data DATE,
    valor FLOAT,
    categoria TEXT
)
""")
conn.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot financeiro ativo ✅\n\n"
        "/gasto valor categoria\n"
        "/saldo\n"
        "/reset"
    )


async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(context.args[0])
        categoria = " ".join(context.args[1:])
        data = datetime.now().date()

        cursor.execute(
            "INSERT INTO gastos (data, valor, categoria) VALUES (%s,%s,%s)",
            (data, valor, categoria)
        )
        conn.commit()

        await update.message.reply_text(
            f"Gasto registrado ✅\nR$ {valor} - {categoria}"
        )

    except:
        await update.message.reply_text(
            "Use assim:\n/gasto 50 mercado"
        )


async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT SUM(valor) FROM gastos")
    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    await update.message.reply_text(f"Total gasto: R$ {total}")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("DELETE FROM gastos")
    conn.commit()

    await update.message.reply_text("Dados resetados ✅")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("reset", reset))

print("Bot rodando...")

app.run_polling()
