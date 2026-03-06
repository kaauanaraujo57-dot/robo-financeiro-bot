import os
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

ADMIN_ID = 1323854764

# =========================
# BANCO
# =========================

conn = sqlite3.connect("dados.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transacoes (
user_id INTEGER,
tipo TEXT,
valor REAL,
categoria TEXT,
data TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS planos (
user_id INTEGER,
plano TEXT
)
""")

conn.commit()

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    cursor.execute("INSERT OR IGNORE INTO usuarios VALUES (?)",(user_id,))
    cursor.execute("INSERT OR IGNORE INTO planos VALUES (?,?)",(user_id,"free"))
    conn.commit()

    await update.message.reply_text(
"""
💰 BOT FINANCEIRO

Comandos principais:

/gasto valor categoria
/receita valor categoria

/extrato
/saldo
/reset

/ajuda
"""
)

# =========================
# AJUDA
# =========================

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
"""
📚 COMO USAR

Adicionar gasto:
/gasto 50 mercado

Adicionar receita:
/receita 1200 salario

Ver extrato:
/extrato

Ver saldo:
/saldo

Resetar mês:
/reset
"""
)

# =========================
# GASTO
# =========================

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    try:

        valor = float(context.args[0])
        categoria = " ".join(context.args[1:])

        data = datetime.now().strftime("%d/%m")

        cursor.execute(
        "INSERT INTO transacoes VALUES (?,?,?,?,?)",
        (user_id,"gasto",valor,categoria,data)
        )

        conn.commit()

        await update.message.reply_text(f"💸 Gasto adicionado: {valor} - {categoria}")

    except:

        await update.message.reply_text("Use: /gasto 50 mercado")

# =========================
# RECEITA
# =========================

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    try:

        valor = float(context.args[0])
        categoria = " ".join(context.args[1:])

        data = datetime.now().strftime("%d/%m")

        cursor.execute(
        "INSERT INTO transacoes VALUES (?,?,?,?,?)",
        (user_id,"receita",valor,categoria,data)
        )

        conn.commit()

        await update.message.reply_text(f"💰 Receita adicionada: {valor} - {categoria}")

    except:

        await update.message.reply_text("Use: /receita 1000 salario")

# =========================
# EXTRATO
# =========================

async def extrato(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    cursor.execute(
    "SELECT tipo,valor,categoria,data FROM transacoes WHERE user_id=?",
    (user_id,)
    )

    dados = cursor.fetchall()

    if not dados:

        await update.message.reply_text("Sem movimentações.")
        return

    texto = "📄 EXTRATO\n\n"

    for tipo,valor,categoria,data in dados:

        if tipo == "gasto":

            texto += f"{data} 💸 -{valor} {categoria}\n"

        else:

            texto += f"{data} 💰 +{valor} {categoria}\n"

    await update.message.reply_text(texto)

# =========================
# SALDO
# =========================

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    cursor.execute(
    "SELECT tipo,valor FROM transacoes WHERE user_id=?",
    (user_id,)
    )

    dados = cursor.fetchall()

    saldo = 0

    for tipo,valor in dados:

        if tipo == "receita":
            saldo += valor
        else:
            saldo -= valor

    await update.message.reply_text(f"💰 Saldo atual: {saldo}")

# =========================
# RESET
# =========================

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    cursor.execute(
    "DELETE FROM transacoes WHERE user_id=?",
    (user_id,)
    )

    conn.commit()

    await update.message.reply_text("♻️ Dados resetados.")

# =========================
# ADMIN - USUARIOS
# =========================

async def usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM usuarios")

    total = cursor.fetchone()[0]

    await update.message.reply_text(f"👥 Total de usuários: {total}")

# =========================
# ADMIN - PREMIUM
# =========================

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:

        user_id = int(context.args[0])

        cursor.execute(
        "UPDATE planos SET plano='premium' WHERE user_id=?",
        (user_id,)
        )

        conn.commit()

        await update.message.reply_text("Usuário virou PREMIUM")

    except:

        await update.message.reply_text("Use: /premium ID")

# =========================
# APP
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ajuda", ajuda))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("extrato", extrato))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("reset", reset))

app.add_handler(CommandHandler("usuarios", usuarios))
app.add_handler(CommandHandler("premium", premium))

print("BOT ONLINE")

app.run_polling()
