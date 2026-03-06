import os
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

ADMIN_ID = 1323854764

conn = sqlite3.connect("financeiro.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
user_id INTEGER PRIMARY KEY,
plano TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transacoes (
user_id INTEGER,
tipo TEXT,
valor REAL,
descricao TEXT,
data TEXT
)
""")

conn.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    cursor.execute(
        "INSERT OR IGNORE INTO usuarios VALUES (?,?)",
        (user, "free")
    )

    conn.commit()

    await update.message.reply_text(
"""
💰 Bem vindo ao BOT FINANCEIRO

Comandos:

/receita valor descricao
/despesa valor descricao
/saldo
/extrato
/reset
/ajuda
"""
)


async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
"""
📊 COMANDOS

/receita valor descricao
Ex:
/receita 500 salario

/despesa valor descricao
Ex:
/despesa 100 mercado

/saldo
Mostra saldo atual

/extrato
Lista movimentações

/reset
Apaga seus dados
"""
)


async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if len(context.args) < 2:
        await update.message.reply_text("Use: /receita valor descricao")
        return

    valor = float(context.args[0])
    descricao = " ".join(context.args[1:])

    data = datetime.now().strftime("%d/%m/%Y")

    cursor.execute(
        "INSERT INTO transacoes VALUES (?,?,?,?,?)",
        (user, "receita", valor, descricao, data)
    )

    conn.commit()

    await update.message.reply_text(f"✅ Receita adicionada R$ {valor}")


async def despesa(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if len(context.args) < 2:
        await update.message.reply_text("Use: /despesa valor descricao")
        return

    valor = float(context.args[0])
    descricao = " ".join(context.args[1:])

    data = datetime.now().strftime("%d/%m/%Y")

    cursor.execute(
        "INSERT INTO transacoes VALUES (?,?,?,?,?)",
        (user, "despesa", valor, descricao, data)
    )

    conn.commit()

    await update.message.reply_text(f"❌ Despesa adicionada R$ {valor}")


async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    cursor.execute(
        "SELECT tipo, valor FROM transacoes WHERE user_id=?",
        (user,)
    )

    dados = cursor.fetchall()

    saldo = 0

    for tipo, valor in dados:

        if tipo == "receita":
            saldo += valor
        else:
            saldo -= valor

    await update.message.reply_text(f"💰 Saldo atual: R$ {saldo}")


async def extrato(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    cursor.execute(
        "SELECT tipo, valor, descricao, data FROM transacoes WHERE user_id=?",
        (user,)
    )

    dados = cursor.fetchall()

    if not dados:
        await update.message.reply_text("Sem movimentações.")
        return

    texto = "📄 EXTRATO\n\n"

    for tipo, valor, desc, data in dados:

        if tipo == "receita":
            emoji = "💰"
        else:
            emoji = "❌"

        texto += f"{emoji} {data} | {desc} | R$ {valor}\n"

    await update.message.reply_text(texto)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    cursor.execute(
        "DELETE FROM transacoes WHERE user_id=?",
        (user,)
    )

    conn.commit()

    await update.message.reply_text("♻️ Dados apagados.")


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    total = cursor.fetchone()[0]

    await update.message.reply_text(
f"""
👑 PAINEL ADMIN

Usuários: {total}

Comandos:

/addplano ID
"""
)


async def addplano(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Use: /addplano ID")
        return

    uid = int(context.args[0])

    cursor.execute(
        "INSERT OR REPLACE INTO usuarios VALUES (?,?)",
        (uid, "premium")
    )

    conn.commit()

    await update.message.reply_text("✅ Plano liberado!")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ajuda", ajuda))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("despesa", despesa))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("extrato", extrato))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("addplano", addplano))

print("BOT ONLINE")

app.run_polling()
