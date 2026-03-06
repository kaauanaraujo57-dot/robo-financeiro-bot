import os
import psycopg2
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# =========================
# CRIAR TABELAS
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
user_id BIGINT PRIMARY KEY,
trial_ate TIMESTAMP,
premium BOOLEAN DEFAULT FALSE
)
""")

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

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    cursor.execute("SELECT * FROM usuarios WHERE user_id=%s",(user_id,))
    user = cursor.fetchone()

    if not user:

        trial = datetime.now() + timedelta(days=7)

        cursor.execute(
            "INSERT INTO usuarios (user_id, trial_ate) VALUES (%s,%s)",
            (user_id, trial)
        )

        conn.commit()

        await update.message.reply_text(
            "🎉 Bem vindo ao FinanceBot\n\n"
            "Você ganhou 7 dias grátis.\n\n"
            "Use:\n"
            "/gasto valor categoria\n"
            "/receita valor categoria\n"
            "/saldo"
        )

    else:
        await update.message.reply_text("Você já está cadastrado.")

# =========================
# VERIFICAR ACESSO
# =========================

def acesso(user_id):

    cursor.execute(
        "SELECT trial_ate,premium FROM usuarios WHERE user_id=%s",
        (user_id,)
    )

    user = cursor.fetchone()

    if user[1]:
        return True

    if datetime.now() <= user[0]:
        return True

    return False

# =========================
# GASTO
# =========================

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not acesso(user_id):

        await update.message.reply_text(
            "⚠️ Seu período gratuito terminou.\nUse /premium"
        )

        return

    try:

        valor = float(context.args[0])
        categoria = " ".join(context.args[1:])

        cursor.execute(
            """
            INSERT INTO transacoes
            (user_id,tipo,valor,categoria,data)
            VALUES (%s,%s,%s,%s,%s)
            """,
            (user_id,"gasto",valor,categoria,datetime.now())
        )

        conn.commit()

        await update.message.reply_text(
            f"💸 Gasto registrado\nR$ {valor} - {categoria}"
        )

    except:
        await update.message.reply_text(
            "Use:\n/gasto 50 mercado"
        )

# =========================
# RECEITA
# =========================

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not acesso(user_id):

        await update.message.reply_text(
            "⚠️ Seu período gratuito terminou.\nUse /premium"
        )

        return

    try:

        valor = float(context.args[0])
        categoria = " ".join(context.args[1:])

        cursor.execute(
            """
            INSERT INTO transacoes
            (user_id,tipo,valor,categoria,data)
            VALUES (%s,%s,%s,%s,%s)
            """,
            (user_id,"receita",valor,categoria,datetime.now())
        )

        conn.commit()

        await update.message.reply_text(
            f"💰 Receita registrada\nR$ {valor} - {categoria}"
        )

    except:

        await update.message.reply_text(
            "Use:\n/receita 200 salario"
        )

# =========================
# SALDO
# =========================

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    cursor.execute(
        """
        SELECT tipo,valor FROM transacoes
        WHERE user_id=%s
        """,
        (user_id,)
    )

    dados = cursor.fetchall()

    saldo = 0

    for tipo,valor in dados:

        if tipo == "receita":
            saldo += valor
        else:
            saldo -= valor

    await update.message.reply_text(
        f"💰 Seu saldo atual:\nR$ {saldo:.2f}"
    )

# =========================
# RELATORIO MES
# =========================

async def mes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    inicio_mes = datetime.now().replace(day=1)

    cursor.execute(
        """
        SELECT tipo,valor,categoria
        FROM transacoes
        WHERE user_id=%s AND data >= %s
        """,
        (user_id,inicio_mes)
    )

    dados = cursor.fetchall()

    texto = "📊 Relatório do mês\n\n"

    total = 0

    for tipo,valor,cat in dados:

        if tipo == "receita":
            texto += f"💰 +{valor} {cat}\n"
            total += valor
        else:
            texto += f"💸 -{valor} {cat}\n"
            total -= valor

    texto += f"\nSaldo: R$ {total:.2f}"

    await update.message.reply_text(texto)

# =========================
# RESET
# =========================

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    cursor.execute(
        "DELETE FROM transacoes WHERE user_id=%s",
        (user_id,)
    )

    conn.commit()

    await update.message.reply_text("🔄 Dados resetados.")

# =========================
# PREMIUM
# =========================

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "💎 Plano Premium\n\n"
        "R$ 9,90 / mês\n\n"
        "Em breve pagamento automático."
    )

# =========================
# MAIN
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("mes", mes))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(CommandHandler("premium", premium))

print("BOT ONLINE")

app.run_polling()
