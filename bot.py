import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "SEU_TOKEN_AQUI"

# =========================
# BANCO DE DADOS
# =========================

conn = sqlite3.connect("financeiro.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    tipo TEXT,
    valor REAL,
    descricao TEXT,
    data TEXT
)
""")

conn.commit()

# =========================
# COMANDOS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Bot Financeiro iniciado!\n\nDigite /ajuda para ver os comandos."
    )

# -------------------------

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = """
📊 COMANDOS DO BOT

/receita valor descricao
Ex:
/receita 1500 salario

/gasto valor descricao
Ex:
/gasto 200 mercado

/extrato
Mostra todas transações

/saldo
Mostra saldo atual

/reset
Apaga todos registros
"""
    await update.message.reply_text(texto)

# -------------------------

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(context.args[0])
        descricao = " ".join(context.args[1:])
    except:
        await update.message.reply_text("Use: /receita valor descricao")
        return

    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    cursor.execute(
        "INSERT INTO transacoes (user_id, tipo, valor, descricao, data) VALUES (?, ?, ?, ?, ?)",
        (update.effective_user.id, "receita", valor, descricao, data)
    )
    conn.commit()

    await update.message.reply_text(f"✅ Receita registrada\n💰 {valor} - {descricao}")

# -------------------------

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(context.args[0])
        descricao = " ".join(context.args[1:])
    except:
        await update.message.reply_text("Use: /gasto valor descricao")
        return

    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    cursor.execute(
        "INSERT INTO transacoes (user_id, tipo, valor, descricao, data) VALUES (?, ?, ?, ?, ?)",
        (update.effective_user.id, "gasto", valor, descricao, data)
    )
    conn.commit()

    await update.message.reply_text(f"💸 Gasto registrado\n{valor} - {descricao}")

# -------------------------

async def extrato(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cursor.execute(
        "SELECT tipo, valor, descricao, data FROM transacoes WHERE user_id=? ORDER BY id DESC LIMIT 20",
        (update.effective_user.id,)
    )

    dados = cursor.fetchall()

    if not dados:
        await update.message.reply_text("Nenhuma transação registrada.")
        return

    texto = "📊 Últimas transações\n\n"

    for tipo, valor, desc, data in dados:

        emoji = "💰" if tipo == "receita" else "💸"

        texto += f"{emoji} {valor} | {desc}\n📅 {data}\n\n"

    await update.message.reply_text(texto)

# -------------------------

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cursor.execute(
        "SELECT tipo, valor FROM transacoes WHERE user_id=?",
        (update.effective_user.id,)
    )

    dados = cursor.fetchall()

    saldo = 0

    for tipo, valor in dados:
        if tipo == "receita":
            saldo += valor
        else:
            saldo -= valor

    await update.message.reply_text(f"💰 Saldo atual: {saldo}")

# -------------------------

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cursor.execute(
        "DELETE FROM transacoes WHERE user_id=?",
        (update.effective_user.id,)
    )
    conn.commit()

    await update.message.reply_text("🗑 Todos os registros foram apagados.")

# =========================
# INICIAR BOT
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ajuda", ajuda))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("extrato", extrato))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("reset", reset))

print("BOT ONLINE...")

app.run_polling()
