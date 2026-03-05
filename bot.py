import os
import psycopg2
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não encontrada!")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# =========================
# CRIAÇÃO DAS TABELAS
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    user_id BIGINT PRIMARY KEY,
    plano TEXT DEFAULT 'free',
    expira_em DATE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transacoes (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    tipo TEXT,
    valor NUMERIC,
    categoria TEXT,
    data DATE
)
""")

conn.commit()

# =========================
# FUNÇÕES
# =========================

def registrar_usuario(user_id):

    cursor.execute("SELECT user_id FROM usuarios WHERE user_id=%s", (user_id,))
    existe = cursor.fetchone()

    if not existe:

        cursor.execute("""
        INSERT INTO usuarios (user_id, plano)
        VALUES (%s,'free')
        """, (user_id,))

        conn.commit()


def verificar_plano(user_id):

    cursor.execute("""
    SELECT plano, expira_em
    FROM usuarios
    WHERE user_id=%s
    """, (user_id,))

    user = cursor.fetchone()

    if not user:
        return "free"

    plano, expira = user

    if plano == "pro" and expira:

        if datetime.now().date() > expira:
            cursor.execute("""
            UPDATE usuarios
            SET plano='free'
            WHERE user_id=%s
            """, (user_id,))
            conn.commit()
            return "free"

    return plano

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    registrar_usuario(user_id)

    msg = """
🤖 Bot Financeiro

Comandos:

/receita 100 salario
/despesa 50 mercado

/resumo
/historico
/reset

Plano atual: FREE
"""

    await update.message.reply_text(msg)

# =========================
# RECEITA
# =========================

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    registrar_usuario(user_id)

    try:
        valor = float(context.args[0])
        categoria = context.args[1]
    except:
        await update.message.reply_text("Use: /receita 100 salario")
        return

    cursor.execute("""
    INSERT INTO transacoes (user_id,tipo,valor,categoria,data)
    VALUES (%s,'receita',%s,%s,CURRENT_DATE)
    """,(user_id,valor,categoria))

    conn.commit()

    await update.message.reply_text(f"💰 Receita registrada: R${valor}")

# =========================
# DESPESA
# =========================

async def despesa(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    registrar_usuario(user_id)

    try:
        valor = float(context.args[0])
        categoria = context.args[1]
    except:
        await update.message.reply_text("Use: /despesa 50 mercado")
        return

    cursor.execute("""
    INSERT INTO transacoes (user_id,tipo,valor,categoria,data)
    VALUES (%s,'despesa',%s,%s,CURRENT_DATE)
    """,(user_id,valor,categoria))

    conn.commit()

    await update.message.reply_text(f"💸 Despesa registrada: R${valor}")

# =========================
# RESUMO
# =========================

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    cursor.execute("""
    SELECT tipo,SUM(valor)
    FROM transacoes
    WHERE user_id=%s
    AND date_trunc('month',data)=date_trunc('month',CURRENT_DATE)
    GROUP BY tipo
    """,(user_id,))

    dados = cursor.fetchall()

    receita = 0
    despesa = 0

    for tipo,valor in dados:

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

# =========================
# HISTORICO
# =========================

async def historico(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    cursor.execute("""
    SELECT tipo,valor,categoria,data
    FROM transacoes
    WHERE user_id=%s
    ORDER BY data DESC
    LIMIT 10
    """,(user_id,))

    dados = cursor.fetchall()

    if not dados:
        await update.message.reply_text("Sem registros.")
        return

    msg = "📜 Últimos lançamentos:\n\n"

    for tipo,valor,categoria,data in dados:

        emoji = "💰" if tipo=="receita" else "💸"

        msg += f"{emoji} {categoria} - R${valor} ({data})\n"

    await update.message.reply_text(msg)

# =========================
# RESET
# =========================

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    cursor.execute("""
    DELETE FROM transacoes
    WHERE user_id=%s
    AND date_trunc('month',data)=date_trunc('month',CURRENT_DATE)
    """,(user_id,))

    conn.commit()

    await update.message.reply_text("🔄 Mês atual resetado.")

# =========================
# BOT
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("despesa", despesa))
app.add_handler(CommandHandler("resumo", resumo))
app.add_handler(CommandHandler("historico", historico))
app.add_handler(CommandHandler("reset", reset))

print("Bot rodando...")

app.run_polling()
