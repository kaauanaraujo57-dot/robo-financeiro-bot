import os
import psycopg2
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS financeiro (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    data DATE,
    tipo TEXT,
    valor FLOAT,
    categoria TEXT
)
""")

conn.commit()


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        """
💰 BOT FINANCEIRO

Comandos:

/receita valor categoria
/gasto valor categoria
/saldo
/mes
/categorias
/extrato
/reset
/ajuda
"""
    )


# RECEITA
async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        user = update.effective_user.id
        valor = float(context.args[0])
        categoria = " ".join(context.args[1:])
        data = datetime.now().date()

        cursor.execute(
            "INSERT INTO financeiro (user_id,data,tipo,valor,categoria) VALUES (%s,%s,%s,%s,%s)",
            (user, data, "receita", valor, categoria)
        )

        conn.commit()

        await update.message.reply_text(f"💰 Receita registrada: R$ {valor} - {categoria}")

    except:
        await update.message.reply_text("Use: /receita 2000 salario")


# GASTO
async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        user = update.effective_user.id
        valor = float(context.args[0])
        categoria = " ".join(context.args[1:])
        data = datetime.now().date()

        cursor.execute(
            "INSERT INTO financeiro (user_id,data,tipo,valor,categoria) VALUES (%s,%s,%s,%s,%s)",
            (user, data, "gasto", valor, categoria)
        )

        conn.commit()

        await update.message.reply_text(f"💸 Gasto registrado: R$ {valor} - {categoria}")

    except:
        await update.message.reply_text("Use: /gasto 50 mercado")


# SALDO
async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    cursor.execute("SELECT SUM(valor) FROM financeiro WHERE user_id=%s AND tipo='receita'", (user,))
    receitas = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(valor) FROM financeiro WHERE user_id=%s AND tipo='gasto'", (user,))
    gastos = cursor.fetchone()[0] or 0

    saldo = receitas - gastos

    await update.message.reply_text(
        f"""
📊 Resumo

Receitas: R$ {receitas}
Gastos: R$ {gastos}

Saldo: R$ {saldo}
"""
    )


# EXTRATO
async def extrato(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    cursor.execute(
        "SELECT data,tipo,valor,categoria FROM financeiro WHERE user_id=%s ORDER BY id DESC LIMIT 10",
        (user,)
    )

    dados = cursor.fetchall()

    if not dados:
        await update.message.reply_text("Sem registros.")
        return

    texto = "🧾 Últimos registros\n\n"

    for d in dados:
        texto += f"{d[0]} | {d[1]} | R$ {d[2]} | {d[3]}\n"

    await update.message.reply_text(texto)


# CATEGORIAS
async def categorias(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    cursor.execute("""
    SELECT categoria, SUM(valor)
    FROM financeiro
    WHERE user_id=%s AND tipo='gasto'
    GROUP BY categoria
    ORDER BY SUM(valor) DESC
    """, (user,))

    dados = cursor.fetchall()

    texto = "📊 Gastos por categoria\n\n"

    for c in dados:
        texto += f"{c[0]}: R$ {c[1]}\n"

    await update.message.reply_text(texto)


# MES
async def mes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    mes = datetime.now().month

    cursor.execute("""
    SELECT SUM(valor)
    FROM financeiro
    WHERE user_id=%s AND tipo='gasto'
    AND EXTRACT(MONTH FROM data)=%s
    """, (user, mes))

    total = cursor.fetchone()[0] or 0

    await update.message.reply_text(f"📅 Total gasto no mês: R$ {total}")


# RESET
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    cursor.execute("DELETE FROM financeiro WHERE user_id=%s", (user,))
    conn.commit()

    await update.message.reply_text("Dados apagados.")


# AJUDA
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
"""
📖 Como usar

/gasto 50 mercado
/receita 2000 salario

/saldo
/extrato
/categorias
"""
)


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("extrato", extrato))
app.add_handler(CommandHandler("categorias", categorias))
app.add_handler(CommandHandler("mes", mes))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(CommandHandler("ajuda", ajuda))

print("Bot rodando...")

app.run_polling()
