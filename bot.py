import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TOKEN")
ARQUIVO = "gastos.csv"

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================
# CRIAR CSV
# =========================

if not os.path.exists(ARQUIVO):
    df = pd.DataFrame(columns=["data", "valor", "categoria"])
    df.to_csv(ARQUIVO, index=False)

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    texto = """
💰 Controle de Gastos

Comandos:

/gasto 50 mercado
/resumo
/reset
"""

    await update.message.reply_text(texto)

# =========================
# GASTO
# =========================

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        valor = float(context.args[0])
        categoria = " ".join(context.args[1:])

        df = pd.read_csv(ARQUIVO)

        novo = pd.DataFrame([{
            "data": datetime.now().strftime("%Y-%m-%d"),
            "valor": valor,
            "categoria": categoria
        }])

        df = pd.concat([df, novo], ignore_index=True)

        df.to_csv(ARQUIVO, index=False)

        await update.message.reply_text(
            f"✅ Gasto registrado\n\nR$ {valor}\n{categoria}"
        )

    except Exception as e:

        logging.error(e)

        await update.message.reply_text(
            "Use assim:\n/gasto 50 mercado"
        )

# =========================
# RESUMO
# =========================

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        df = pd.read_csv(ARQUIVO)

        if df.empty:
            await update.message.reply_text("Nenhum gasto registrado.")
            return

        df["data"] = pd.to_datetime(df["data"])

        mes = datetime.now().month
        ano = datetime.now().year

        df_mes = df[(df["data"].dt.month == mes) & (df["data"].dt.year == ano)]

        total = df_mes["valor"].sum()

        categorias = df_mes.groupby("categoria")["valor"].sum()

        texto = f"📊 Resumo do mês\n\n💰 Total: R$ {total}\n\n"

        for cat, val in categorias.items():
            texto += f"{cat}: R$ {val}\n"

        await update.message.reply_text(texto)

    except Exception as e:

        logging.error(e)

        await update.message.reply_text("Erro ao gerar resumo.")

# =========================
# RESET
# =========================

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        df = pd.read_csv(ARQUIVO)

        df["data"] = pd.to_datetime(df["data"])

        mes = datetime.now().month
        ano = datetime.now().year

        df = df[~((df["data"].dt.month == mes) & (df["data"].dt.year == ano))]

        df.to_csv(ARQUIVO, index=False)

        await update.message.reply_text("🗑️ Mês atual apagado.")

    except Exception as e:

        logging.error(e)

        await update.message.reply_text("Erro ao resetar.")

# =========================
# MAIN
# =========================

def main():

    if TOKEN is None:
        print("TOKEN não encontrado!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gasto", gasto))
    app.add_handler(CommandHandler("resumo", resumo))
    app.add_handler(CommandHandler("reset", reset))

    print("Bot rodando...")

    app.run_polling()

if __name__ == "__main__":
    main()
