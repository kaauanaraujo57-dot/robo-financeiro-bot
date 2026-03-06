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
CREATE TABLE IF NOT EXISTS transacoes (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    tipo TEXT,
    valor FLOAT,
    categoria TEXT,
    data TIMESTAMP
)
""")

conn.commit()


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = """
👋 Bem vindo ao *Bot Financeiro*

Controle seu dinheiro direto no Telegram.

Digite:
/ajuda
"""
    await update.message.reply_text(texto, parse_mode="Markdown")


# AJUDA
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):

    texto = """
📊 *Comandos do Bot*

💰 Receitas
/receita VALOR CATEGORIA

Ex:
/receita 2500 salario

💸 Gastos
/gasto VALOR CATEGORIA

Ex:
/gasto 50 mercado

📊 Relatórios
/saldo
/extrato
/mes

⚙️ Sistema
/reset
/ajuda
"""

    await update.message.reply_text(texto, parse_mode="Markdown")


# RECEITA
async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    try:
        valor = float(context.args[0])
        categoria = " ".join(context.args[1:])
    except:
        await update.message.reply_text("Use: /receita VALOR CATEGORIA")
        return

    cursor.execute(
        "INSERT INTO transacoes (user_id,tipo,valor,categoria,data) VALUES (%s,%s,%s,%s,%s)",
        (user_id, "receita", valor, categoria, datetime.now())
    )

    conn.commit()

    await update.message.reply_text(f"✅ Receita registrada\nR$ {valor} - {categoria}")


# GASTO
async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    try:
        valor = float(context.args[0])
        categoria = " ".join(context.args[1:])
    except:
        await update.message.reply_text("Use: /gasto VALOR CATEGORIA")
        return

    cursor.execute(
        "INSERT INTO transacoes (user_id,tipo,valor,categoria,data) VALUES (%s,%s,%s,%s,%s)",
        (user_id, "gasto", valor, categoria, datetime.now())
    )

    conn.commit()

    await update.message.reply_text(f"💸 Gasto registrado\nR$ {valor} - {categoria}")


# SALDO
async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    cursor.execute("""
    SELECT 
    SUM(CASE WHEN tipo='receita' THEN valor ELSE 0 END),
    SUM(CASE WHEN tipo='gasto' THEN valor ELSE 0 END)
    FROM transacoes
    WHERE user_id=%s
    """, (user_id,))

    receitas, gastos = cursor.fetchone()

    receitas = receitas or 0
    gastos = gastos or 0

    saldo = receitas - gastos

    texto = f"""
📊 Saldo atual

💰 Receitas: R$ {receitas:.2f}
💸 Gastos: R$ {gastos:.2f}

🟢 Saldo: R$ {saldo:.2f}
"""

    await update.message.reply_text(texto)


# EXTRATO
async def extrato(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    cursor.execute("""
    SELECT tipo,valor,categoria,data
    FROM transacoes
    WHERE user_id=%s
    ORDER BY data DESC
    LIMIT 10
    """, (user_id,))

    dados = cursor.fetchall()

    if not dados:
        await update.message.reply_text("Sem movimentações.")
        return

    texto = "📋 Últimas movimentações\n\n"

    for tipo, valor, categoria, data in dados:

        emoji = "💰" if tipo == "receita" else "💸"

        texto += f"{emoji} {categoria} - R$ {valor}\n"

    await update.message.reply_text(texto)


# RESUMO DO MES
async def mes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    mes_atual = datetime.now().month

    cursor.execute("""
    SELECT 
    SUM(CASE WHEN tipo='receita' THEN valor ELSE 0 END),
    SUM(CASE WHEN tipo='gasto' THEN valor ELSE 0 END)
    FROM transacoes
    WHERE user_id=%s AND EXTRACT(MONTH FROM data)=%s
    """, (user_id, mes_atual))

    receitas, gastos = cursor.fetchone()

    receitas = receitas or 0
    gastos = gastos or 0

    saldo = receitas - gastos

    texto = f"""
📅 Resumo do mês

💰 Receitas: R$ {receitas:.2f}
💸 Gastos: R$ {gastos:.2f}

Saldo: R$ {saldo:.2f}
"""

    await update.message.reply_text(texto)


# RESET
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    cursor.execute("DELETE FROM transacoes WHERE user_id=%s", (user_id,))
    conn.commit()

    await update.message.reply_text("🗑 Todos dados foram apagados.")


# MAIN
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ajuda", ajuda))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("extrato", extrato))
app.add_handler(CommandHandler("mes", mes))
app.add_handler(CommandHandler("reset", reset))

print("BOT ONLINE 🚀")

app.run_polling()
