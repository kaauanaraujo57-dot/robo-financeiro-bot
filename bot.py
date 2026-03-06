import os
import logging
import pandas as pd
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# CONFIG
# =========================

TOKEN = "SEU_TOKEN_AQUI"
ARQUIVO = "gastos.csv"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================
# CRIAR ARQUIVO SE NAO EXISTIR
# =========================

if not os.path.exists(ARQUIVO):
    df = pd.DataFrame(columns=["data", "valor", "categoria"])
    df.to_csv(ARQUIVO, index=False)

# =========================
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = """
💰 *Bot de Controle de Gastos*

Comandos:

/gasto valor categoria  
Exemplo:
/gasto 50 mercado

/resumo → resumo do mês

/reset → apagar gastos do mês atual
"""
    await update.message.reply_text(mensagem, parse_mode="Markdown")

# =========================
# /gasto
# =========================

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        valor = float(context.args[0])
        categoria = " ".join(context.args[1:]).lower()

        data = datetime.now().strftime("%Y-%m-%d")

        df = pd.read_csv(ARQUIVO)

        novo = pd.DataFrame([{
            "data": data,
            "valor": valor,
            "categoria": categoria
        }])

        df = pd.concat([df, novo], ignore_index=True)

        df.to_csv(ARQUIVO, index=False)

        await update.message.reply_text(
            f"✅ Gasto registrado!\n\n💸 R$ {valor:.2f}\n📂 {categoria}"
        )

    except:
        await update.message.reply_text(
            "❌ Use assim:\n\n/gasto 50 mercado"
        )

# =========================
# /resumo
# =========================

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    df = pd.read_csv(ARQUIVO)

    if df.empty:
        await update.message.reply_text("Nenhum gasto registrado.")
        return

    df["data"] = pd.to_datetime(df["data"])

    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    df_mes = df[(df["data"].dt.month == mes_atual) &
                (df["data"].dt.year == ano_atual)]

    if df_mes.empty:
        await update.message.reply_text("Nenhum gasto esse mês.")
        return

    total = df_mes["valor"].sum()

    categorias = df_mes.groupby("categoria")["valor"].sum()

    mensagem = f"📊 *Resumo do mês*\n\n💰 Total: R$ {total:.2f}\n\n"

    for cat, val in categorias.items():
        mensagem += f"• {cat}: R$ {val:.2f}\n"

    await update.message.reply_text(mensagem, parse_mode="Markdown")

# =========================
# /reset
# =========================

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    df = pd.read_csv(ARQUIVO)

    df["data"] = pd.to_datetime(df["data"])

    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    df = df[~((df["data"].dt.month == mes_atual) &
              (df["data"].dt.year == ano_atual))]

    df.to_csv(ARQUIVO, index=False)

    await update.message.reply_text("🗑️ Gastos do mês atual apagados.")

# =========================
# MAIN
# =========================

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gasto", gasto))
    app.add_handler(CommandHandler("resumo", resumo))
    app.add_handler(CommandHandler("reset", reset))

    print("Bot rodando...")

    app.run_polling()


if __name__ == "__main__":
    main()
