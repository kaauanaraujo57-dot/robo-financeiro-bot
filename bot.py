import os
import psycopg2
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

print("TOKEN:", TOKEN)
print("DATABASE_URL:", DATABASE_URL)

# =========================
# CONEXÃO COM O BANCO
# =========================

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# =========================
# CRIA TABELA SE NÃO EXISTIR
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS transacoes (
    id SERIAL PRIMARY KEY,
    usuario BIGINT,
    tipo TEXT,
    valor FLOAT,
    descricao TEXT,
    data TIMESTAMP
)
""")

conn.commit()

# =========================
# COMANDO START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Bot financeiro iniciado!\n\n"
        "Use:\n"
        "/entrada 100 Salário\n"
        "/saida 50 Mercado\n"
        "/saldo"
    )

# =========================
# ENTRADA
# =========================

async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        usuario = update.message.from_user.id
        valor = float(context.args[0])
        descricao = " ".join(context.args[1:])
        data = datetime.now()

        cursor.execute(
            "INSERT INTO transacoes (usuario, tipo, valor, descricao, data) VALUES (%s,%s,%s,%s,%s)",
            (usuario, "entrada", valor, descricao, data)
        )

        conn.commit()

        await update.message.reply_text(f"✅ Entrada registrada: R${valor}")

    except:
        await update.message.reply_text("❌ Use assim:\n/entrada 100 Salário")

# =========================
# SAÍDA
# =========================

async def saida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        usuario = update.message.from_user.id
        valor = float(context.args[0])
        descricao = " ".join(context.args[1:])
        data = datetime.now()

        cursor.execute(
            "INSERT INTO transacoes (usuario, tipo, valor, descricao, data) VALUES (%s,%s,%s,%s,%s)",
            (usuario, "saida", valor, descricao, data)
        )

        conn.commit()

        await update.message.reply_text(f"📉 Saída registrada: R${valor}")

    except:
        await update.message.reply_text("❌ Use assim:\n/saida 50 Mercado")

# =========================
# SALDO
# =========================

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.message.from_user.id

    cursor.execute(
        "SELECT tipo, valor FROM transacoes WHERE usuario=%s",
        (usuario,)
    )

    dados = cursor.fetchall()

    total = 0

    for tipo, valor in dados:
        if tipo == "entrada":
            total += valor
        else:
            total -= valor

    await update.message.reply_text(f"💰 Seu saldo é: R${total}")

# =========================
# BOT
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("entrada", entrada))
app.add_handler(CommandHandler("saida", saida))
app.add_handler(CommandHandler("saldo", saldo))

print("Bot rodando...")

app.run_polling()
