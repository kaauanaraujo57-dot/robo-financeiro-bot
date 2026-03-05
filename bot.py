import os
import psycopg2
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# conexão banco
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# criar tabela se não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS transacoes (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    tipo TEXT,
    valor NUMERIC,
    data DATE
)
""")
conn.commit()


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """
🤖 Bot Financeiro

Comandos:

/receita 100
/despesa 50
/resumo
/reset
"""
    await update.message.reply_text(msg)


# RECEITA
async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    try:
        valor = float(context.args[0])
    except:
        await update.message.reply_text("Use: /receita 100")
        return

    cursor.execute(
        """
        INSERT INTO transacoes (user_id, tipo, valor, data)
        VALUES (%s,%s,%s,CURRENT_DATE)
        """,
        (user_id, "receita", valor)
    )

    conn.commit()

    await update.message.reply_text(f"💰 Receita registrada: R${valor}")


# DESPESA
async def despesa(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    try:
        valor = float(context.args[0])
    except:
        await update.message.reply_text("Use: /despesa 50")
        return

    cursor.execute(
        """
        INSERT INTO transacoes (user_id, tipo, valor, data)
        VALUES (%s,%s,%s,CURRENT_DATE)
        """,
        (user_id, "despesa", valor)
    )

    conn.commit()

    await update.message.reply_text(f"💸 Despesa registrada: R${valor}")


# RESUMO
async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    cursor.execute(
        """
        SELECT tipo, SUM(valor)
        FROM transacoes
        WHERE user_id = %s
        AND date_trunc('month', data) = date_trunc('month', CURRENT_DATE)
        GROUP BY tipo
        """,
        (user_id,)
    )

    dados = cursor.fetchall()

    receita = 0
    despesa = 0

    for tipo, valor in dados:

        if tipo == "receita":
            receita = valor

        if tipo == "despesa":
            despesa = valor

    saldo = receita - despesa

    msg = f"""
📊 Resumo do mês

💰 Receitas: R${receita}
💸 Despesas: R${despesa}

💵 Saldo: R${saldo}
"""

    await update.message.reply_text(msg)


# RESET DO MÊS
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    cursor.execute(
        """
        DELETE FROM transacoes
        WHERE user_id = %s
        AND date_trunc('month', data) = date_trunc('month', CURRENT_DATE)
        """,
        (user_id,)
    )

    conn.commit()

    await update.message.reply_text("🔄 Dados do mês atual foram resetados.")


# MAIN
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("despesa", despesa))
app.add_handler(CommandHandler("resumo", resumo))
app.add_handler(CommandHandler("reset", reset))

print("Bot rodando...")

app.run_polling()
