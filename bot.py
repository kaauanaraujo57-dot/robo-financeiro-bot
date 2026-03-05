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
    categoria TEXT,
    valor FLOAT,
    mes TEXT,
    data TIMESTAMP
)
""")

conn.commit()

# =========================
# COMANDO START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
💰 Controle Financeiro

Comandos:

/receita valor categoria
/gasto valor categoria
/resumo mes

Exemplo:

/receita 2000 salario
/gasto 50 mercado
/resumo 03-2026
"""
    )

# =========================
# RECEITA
# =========================

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        user_id = update.effective_user.id
        valor = float(context.args[0])
        categoria = context.args[1]

        mes = datetime.now().strftime("%m-%Y")

        cursor.execute("""
        INSERT INTO transacoes (user_id,tipo,categoria,valor,mes,data)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,(user_id,"receita",categoria,valor,mes,datetime.now()))

        conn.commit()

        await update.message.reply_text(f"✅ Receita registrada: R${valor} ({categoria})")

    except:
        await update.message.reply_text("Use: /receita valor categoria")

# =========================
# GASTO
# =========================

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        user_id = update.effective_user.id
        valor = float(context.args[0])
        categoria = context.args[1]

        mes = datetime.now().strftime("%m-%Y")

        cursor.execute("""
        INSERT INTO transacoes (user_id,tipo,categoria,valor,mes,data)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,(user_id,"gasto",categoria,valor,mes,datetime.now()))

        conn.commit()

        await update.message.reply_text(f"💸 Gasto registrado: R${valor} ({categoria})")

    except:
        await update.message.reply_text("Use: /gasto valor categoria")

# =========================
# RESUMO
# =========================

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        user_id = update.effective_user.id
        mes = context.args[0]

        cursor.execute("""
        SELECT tipo,categoria,valor FROM transacoes
        WHERE user_id=%s AND mes=%s
        """,(user_id,mes))

        dados = cursor.fetchall()

        receita = 0
        gasto = 0

        categorias = {}

        for tipo,categoria,valor in dados:

            if tipo == "receita":
                receita += valor
            else:
                gasto += valor

                if categoria not in categorias:
                    categorias[categoria] = 0

                categorias[categoria] += valor

        saldo = receita - gasto

        texto = f"📊 Resumo {mes}\n\n"
        texto += f"💰 Receitas: R${receita}\n"
        texto += f"💸 Gastos: R${gasto}\n"
        texto += f"📈 Saldo: R${saldo}\n\n"

        texto += "📂 Gastos por categoria:\n"

        for cat,val in categorias.items():
            texto += f"{cat}: R${val}\n"

        await update.message.reply_text(texto)

    except:
        await update.message.reply_text("Use: /resumo 03-2026")

# =========================
# BOT
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("resumo", resumo))

print("🤖 Bot iniciado")

app.run_polling()
