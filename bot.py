import os
import psycopg2
from datetime import datetime
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

print("TOKEN:", TOKEN)
print("DATABASE_URL:", DATABASE_URL)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# =========================
# CRIAR TABELA
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS transacoes (
    id SERIAL PRIMARY KEY,
    tipo TEXT,
    valor FLOAT,
    descricao TEXT,
    data TIMESTAMP
)
""")

conn.commit()

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
"""🤖 Bot Financeiro

Comandos:

/gasto valor descricao
/receita valor descricao
/saldo
/mes
/resetmes
/grafico
"""
)

# =========================
# ADICIONAR GASTO
# =========================

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valor = float(context.args[0])
    descricao = " ".join(context.args[1:])

    cursor.execute(
        "INSERT INTO transacoes (tipo, valor, descricao, data) VALUES (%s,%s,%s,%s)",
        ("gasto", valor, descricao, datetime.now())
    )

    conn.commit()

    await update.message.reply_text(f"💸 Gasto registrado: R${valor} - {descricao}")

# =========================
# ADICIONAR RECEITA
# =========================

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valor = float(context.args[0])
    descricao = " ".join(context.args[1:])

    cursor.execute(
        "INSERT INTO transacoes (tipo, valor, descricao, data) VALUES (%s,%s,%s,%s)",
        ("receita", valor, descricao, datetime.now())
    )

    conn.commit()

    await update.message.reply_text(f"💰 Receita registrada: R${valor} - {descricao}")

# =========================
# SALDO
# =========================

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cursor.execute("SELECT SUM(valor) FROM transacoes WHERE tipo='receita'")
    receitas = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(valor) FROM transacoes WHERE tipo='gasto'")
    gastos = cursor.fetchone()[0] or 0

    saldo = receitas - gastos

    await update.message.reply_text(
f"""
💰 Receitas: R${receitas}
💸 Gastos: R${gastos}

📊 Saldo: R${saldo}
"""
)

# =========================
# GASTOS DO MES
# =========================

async def mes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cursor.execute("""
    SELECT descricao, valor FROM transacoes
    WHERE tipo='gasto'
    AND date_trunc('month', data) = date_trunc('month', CURRENT_DATE)
    """)

    dados = cursor.fetchall()

    if not dados:
        await update.message.reply_text("Nenhum gasto esse mês.")
        return

    msg = "📊 Gastos do mês:\n\n"

    total = 0

    for desc, valor in dados:
        msg += f"{desc} - R${valor}\n"
        total += valor

    msg += f"\nTotal: R${total}"

    await update.message.reply_text(msg)

# =========================
# RESET MES
# =========================

async def resetmes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cursor.execute("""
    DELETE FROM transacoes
    WHERE date_trunc('month', data) = date_trunc('month', CURRENT_DATE)
    """)

    conn.commit()

    await update.message.reply_text("✅ Dados do mês apagados.")

# =========================
# GRAFICO
# =========================

async def grafico(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cursor.execute("""
    SELECT descricao, valor FROM transacoes
    WHERE tipo='gasto'
    AND date_trunc('month', data) = date_trunc('month', CURRENT_DATE)
    """)

    dados = cursor.fetchall()

    if not dados:
        await update.message.reply_text("Sem dados para gráfico.")
        return

    labels = [d[0] for d in dados]
    valores = [d[1] for d in dados]

    plt.figure()

    plt.bar(labels, valores)

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig("grafico.png")

    await update.message.reply_photo(photo=open("grafico.png","rb"))

# =========================
# MAIN
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("mes", mes))
app.add_handler(CommandHandler("resetmes", resetmes))
app.add_handler(CommandHandler("grafico", grafico))

print("Bot rodando...")

app.run_polling()
