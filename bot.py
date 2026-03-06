import sqlite3
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = 8654443090:AAGjfMQDEU8o9S47rJnly5FS-l4BMoM2OHU
ADMIN_ID = KA030303

# =========================
# BANCO DE DADOS
# =========================

conn = sqlite3.connect("finance.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
expira TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transacoes(
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
# FUNÇÃO VERIFICAR PLANO
# =========================

def plano_ativo(user_id):

    cursor.execute("SELECT expira FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()

    if not result:
        return False

    data_expira = datetime.strptime(result[0], "%Y-%m-%d")

    if datetime.now() > data_expira:
        return False

    return True

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Bem vindo ao Bot Financeiro\n\n"
        "Use /ajuda para ver os comandos."
    )

# =========================
# AJUDA
# =========================

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):

    texto = """
📊 Comandos disponíveis

/receita valor descrição
/gasto valor descrição

/extrato
/saldo

/plano
"""

    await update.message.reply_text(texto)

# =========================
# PLANO
# =========================

async def plano(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    cursor.execute("SELECT expira FROM users WHERE user_id=?", (user,))
    result = cursor.fetchone()

    if not result:
        await update.message.reply_text("❌ Você não possui plano ativo.")
        return

    await update.message.reply_text(f"📦 Seu plano expira em {result[0]}")

# =========================
# RECEITA
# =========================

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    if not plano_ativo(user):
        await update.message.reply_text("⚠️ Seu plano expirou.")
        return

    try:

        valor = float(context.args[0])
        descricao = " ".join(context.args[1:])

        data = datetime.now().strftime("%d/%m/%Y %H:%M")

        cursor.execute("""
        INSERT INTO transacoes(user_id,tipo,valor,descricao,data)
        VALUES(?,?,?,?,?)
        """,(user,"receita",valor,descricao,data))

        conn.commit()

        await update.message.reply_text("✅ Receita adicionada!")

    except:
        await update.message.reply_text("Use:\n/receita 100 salario")

# =========================
# GASTO
# =========================

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    if not plano_ativo(user):
        await update.message.reply_text("⚠️ Seu plano expirou.")
        return

    try:

        valor = float(context.args[0])
        descricao = " ".join(context.args[1:])

        data = datetime.now().strftime("%d/%m/%Y %H:%M")

        cursor.execute("""
        INSERT INTO transacoes(user_id,tipo,valor,descricao,data)
        VALUES(?,?,?,?,?)
        """,(user,"gasto",valor,descricao,data))

        conn.commit()

        await update.message.reply_text("✅ Gasto registrado!")

    except:
        await update.message.reply_text("Use:\n/gasto 50 mercado")

# =========================
# SALDO
# =========================

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    cursor.execute("""
    SELECT tipo,valor FROM transacoes WHERE user_id=?
    """,(user,))

    dados = cursor.fetchall()

    saldo = 0

    for tipo,valor in dados:

        if tipo == "receita":
            saldo += valor
        else:
            saldo -= valor

    await update.message.reply_text(f"💰 Saldo atual: R${saldo:.2f}")

# =========================
# EXTRATO
# =========================

async def extrato(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    cursor.execute("""
    SELECT tipo,valor,descricao,data
    FROM transacoes
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT 10
    """,(user,))

    dados = cursor.fetchall()

    if not dados:
        await update.message.reply_text("Sem movimentações.")
        return

    texto = "📊 Últimas movimentações\n\n"

    for tipo,valor,desc,data in dados:

        emoji = "💰" if tipo=="receita" else "💸"

        texto += f"{emoji} {desc}\nR${valor}\n📅 {data}\n\n"

    await update.message.reply_text(texto)

# =========================
# ADMIN
# =========================

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    user_id = int(context.args[0])
    dias = int(context.args[1])

    expira = datetime.now() + timedelta(days=dias)

    cursor.execute("""
    INSERT OR REPLACE INTO users(user_id,expira)
    VALUES(?,?)
    """,(user_id,expira.strftime("%Y-%m-%d")))

    conn.commit()

    await update.message.reply_text("✅ Usuário liberado.")

async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    user_id = int(context.args[0])

    cursor.execute("DELETE FROM users WHERE user_id=?",(user_id,))
    conn.commit()

    await update.message.reply_text("❌ Usuário removido.")

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT * FROM users")

    dados = cursor.fetchall()

    texto = "👥 Usuários\n\n"

    for user,expira in dados:
        texto += f"{user} - {expira}\n"

    await update.message.reply_text(texto)

# =========================
# BOT
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ajuda", ajuda))
app.add_handler(CommandHandler("plano", plano))

app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("extrato", extrato))

app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("deluser", deluser))
app.add_handler(CommandHandler("users", users))

print("BOT RODANDO...")

app.run_polling()
