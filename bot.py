import os
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

ADMIN_ID = 123456789  # coloque seu ID aqui

conn = sqlite3.connect("financeiro.db", check_same_thread=False)
cursor = conn.cursor()

# =========================
# TABELAS
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
user_id INTEGER PRIMARY KEY,
ativo INTEGER DEFAULT 0
)
""")

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
# VERIFICAR PLANO
# =========================

def verificar_plano(user):

    cursor.execute(
        "SELECT ativo FROM usuarios WHERE user_id=?",
        (user,)
    )

    result = cursor.fetchone()

    if result and result[0] == 1:
        return True

    if user == ADMIN_ID:
        return True

    return False


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    cursor.execute(
        "INSERT OR IGNORE INTO usuarios (user_id) VALUES (?)",
        (user,)
    )

    conn.commit()

    await update.message.reply_text(
        "💰 Bot Financeiro\n\n"
        "Controle seus gastos direto no Telegram.\n\n"
        "Use /ajuda"
    )

# =========================
# AJUDA
# =========================

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):

    texto = """
📊 Comandos

/gasto 50 mercado
/receita 1000 salario
/saldo
/extrato

💳 Plano

/plano
/pagar

ℹ️ Outros

/id
"""

    await update.message.reply_text(texto)

# =========================
# ID
# =========================

async def id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Seu ID:\n{update.message.from_user.id}")

# =========================
# PLANO
# =========================

async def plano(update: Update, context: ContextTypes.DEFAULT_TYPE):

    texto = """
💎 PLANO PREMIUM

Acesso completo ao bot

💰 Valor: R$19/mês

Para pagar use:

/pagar
"""

    await update.message.reply_text(texto)

# =========================
# PAGAR
# =========================

async def pagar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    texto = """
💳 PAGAMENTO

Envie PIX para:

email@pix.com

Após pagar envie o comprovante para o admin.
"""

    await update.message.reply_text(texto)

# =========================
# GASTO
# =========================

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    if not verificar_plano(user):
        await update.message.reply_text("❌ Você precisa do plano.\nUse /plano")
        return

    try:

        valor = float(context.args[0])
        descricao = " ".join(context.args[1:])
        data = datetime.now().strftime("%d/%m/%Y")

        cursor.execute(
            "INSERT INTO transacoes VALUES (NULL,?,?,?,?,?)",
            (user, "gasto", valor, descricao, data)
        )

        conn.commit()

        await update.message.reply_text(
            f"💸 Gasto registrado\nR${valor} - {descricao}"
        )

    except:
        await update.message.reply_text("Use:\n/gasto 50 mercado")

# =========================
# RECEITA
# =========================

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    if not verificar_plano(user):
        await update.message.reply_text("❌ Você precisa do plano.\nUse /plano")
        return

    try:

        valor = float(context.args[0])
        descricao = " ".join(context.args[1:])
        data = datetime.now().strftime("%d/%m/%Y")

        cursor.execute(
            "INSERT INTO transacoes VALUES (NULL,?,?,?,?,?)",
            (user, "receita", valor, descricao, data)
        )

        conn.commit()

        await update.message.reply_text(
            f"💰 Receita registrada\nR${valor} - {descricao}"
        )

    except:
        await update.message.reply_text("Use:\n/receita 1000 salario")

# =========================
# SALDO
# =========================

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    if not verificar_plano(user):
        await update.message.reply_text("❌ Você precisa do plano.")
        return

    cursor.execute(
        "SELECT tipo,valor FROM transacoes WHERE user_id=?",
        (user,)
    )

    dados = cursor.fetchall()

    saldo = 0

    for tipo, valor in dados:

        if tipo == "receita":
            saldo += valor
        else:
            saldo -= valor

    await update.message.reply_text(f"💰 Saldo: R${saldo:.2f}")

# =========================
# EXTRATO
# =========================

async def extrato(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    if not verificar_plano(user):
        await update.message.reply_text("❌ Você precisa do plano.")
        return

    cursor.execute(
        "SELECT tipo,valor,descricao,data FROM transacoes WHERE user_id=? ORDER BY id DESC LIMIT 10",
        (user,)
    )

    dados = cursor.fetchall()

    if not dados:
        await update.message.reply_text("Nenhuma transação.")
        return

    texto = "📄 Extrato\n\n"

    for tipo, valor, desc, data in dados:

        emoji = "💰" if tipo == "receita" else "💸"

        texto += f"{emoji} R${valor} - {desc}\n📅 {data}\n\n"

    await update.message.reply_text(texto)

# =========================
# ADMIN
# =========================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        """
👑 Painel Admin

/usuarios
/liberar ID
/bloquear ID
"""
    )

# =========================
# USUARIOS
# =========================

async def usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM usuarios")

    total = cursor.fetchone()[0]

    await update.message.reply_text(f"👥 Total usuários: {total}")

# =========================
# LIBERAR
# =========================

async def liberar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    user = int(context.args[0])

    cursor.execute(
        "UPDATE usuarios SET ativo=1 WHERE user_id=?",
        (user,)
    )

    conn.commit()

    await update.message.reply_text("✅ Usuário liberado")

# =========================
# BLOQUEAR
# =========================

async def bloquear(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    user = int(context.args[0])

    cursor.execute(
        "UPDATE usuarios SET ativo=0 WHERE user_id=?",
        (user,)
    )

    conn.commit()

    await update.message.reply_text("❌ Usuário bloqueado")

# =========================
# MAIN
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ajuda", ajuda))
app.add_handler(CommandHandler("id", id))
app.add_handler(CommandHandler("plano", plano))
app.add_handler(CommandHandler("pagar", pagar))

app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("extrato", extrato))

app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("usuarios", usuarios))
app.add_handler(CommandHandler("liberar", liberar))
app.add_handler(CommandHandler("bloquear", bloquear))

print("Bot rodando...")

app.run_polling()
