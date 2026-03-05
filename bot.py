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

# =========================
# CRIAR TABELA
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS transacoes (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    tipo TEXT,
    valor NUMERIC,
    categoria TEXT,
    descricao TEXT,
    mes TEXT,
    data TIMESTAMP
)
""")

conn.commit()

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
"""
🤖 Bot financeiro iniciado

Comandos:

/receita valor categoria descricao mes
/gasto valor categoria descricao mes

Exemplo:
/receita 2000 salario pagamento 03-2026
/gasto 150 mercado compras 03-2026

/resumo 03-2026
/historico
"""
)

# =========================
# RECEITA
# =========================

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    try:
        valor = float(context.args[0])
        categoria = context.args[1]
        descricao = context.args[2]
        mes = context.args[3]

        cursor.execute(
        """
        INSERT INTO transacoes (user_id,tipo,valor,categoria,descricao,mes,data)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,
        (user_id,"receita",valor,categoria,descricao,mes,datetime.now())
        )

        conn.commit()

        await update.message.reply_text("✅ Receita registrada!")

    except:
        await update.message.reply_text("❌ Use:\n/receita valor categoria descricao mes")

# =========================
# GASTO
# =========================

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    try:
        valor = float(context.args[0])
        categoria = context.args[1]
        descricao = context.args[2]
        mes = context.args[3]

        cursor.execute(
        """
        INSERT INTO transacoes (user_id,tipo,valor,categoria,descricao,mes,data)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,
        (user_id,"gasto",valor,categoria,descricao,mes,datetime.now())
        )

        conn.commit()

        await update.message.reply_text("💸 Gasto registrado!")

    except:
        await update.message.reply_text("❌ Use:\n/gasto valor categoria descricao mes")

# =========================
# RESUMO
# =========================

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    try:

        mes = context.args[0]

        cursor.execute(
        """
        SELECT tipo,SUM(valor)
        FROM transacoes
        WHERE user_id=%s AND mes=%s
        GROUP BY tipo
        """,
        (user_id,mes)
        )

        dados = cursor.fetchall()

        receitas = 0
        gastos = 0

        for d in dados:
            if d[0] == "receita":
                receitas = float(d[1])
            if d[0] == "gasto":
                gastos = float(d[1])

        saldo = receitas - gastos

        texto = f"""
📊 Resumo {mes}

💰 Receitas: {receitas}
💸 Gastos: {gastos}
📉 Saldo: {saldo}
"""

        # categorias

        cursor.execute(
        """
        SELECT categoria,SUM(valor)
        FROM transacoes
        WHERE user_id=%s AND mes=%s AND tipo='gasto'
        GROUP BY categoria
        """,
        (user_id,mes)
        )

        categorias = cursor.fetchall()

        if categorias:

            texto += "\n📂 Gastos por categoria\n"

            for c in categorias:
                texto += f"{c[0]}: {c[1]}\n"

        await update.message.reply_text(texto)

    except:
        await update.message.reply_text("Use:\n/resumo 03-2026")

# =========================
# HISTORICO
# =========================

async def historico(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    cursor.execute(
    """
    SELECT tipo,valor,categoria,descricao,mes
    FROM transacoes
    WHERE user_id=%s
    ORDER BY data DESC
    LIMIT 10
    """,
    (user_id,)
    )

    dados = cursor.fetchall()

    if not dados:

        await update.message.reply_text("Sem histórico ainda")

        return

    texto = "📜 Últimas movimentações\n\n"

    for d in dados:

        texto += f"{d[0]} | {d[1]} | {d[2]} | {d[3]} | {d[4]}\n"

    await update.message.reply_text(texto)

# =========================
# BOT
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("resumo", resumo))
app.add_handler(CommandHandler("historico", historico))

print("Bot iniciado...")

app.run_polling()
