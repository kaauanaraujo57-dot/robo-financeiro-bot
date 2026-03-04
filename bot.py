import os
import logging
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
ARQUIVO = "financas.csv"

logging.basicConfig(level=logging.INFO)

try:
    pd.read_csv(ARQUIVO)
except:
    df = pd.DataFrame(columns=["Descricao", "Valor"])
    df.to_csv(ARQUIVO, index=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Olá! Eu sou seu robô financeiro!")

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valor = float(context.args[0])
    descricao = " ".join(context.args[1:])
    df = pd.read_csv(ARQUIVO)
    novo = pd.DataFrame([[descricao, -abs(valor)]], columns=["Descricao", "Valor"])
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO, index=False)
    await update.message.reply_text(f"💸 Gasto registrado: R$ {valor}")

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valor = float(context.args[0])
    descricao = " ".join(context.args[1:])
    df = pd.read_csv(ARQUIVO)
    novo = pd.DataFrame([[descricao, abs(valor)]], columns=["Descricao", "Valor"])
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO, index=False)
    await update.message.reply_text(f"💰 Receita registrada: R$ {valor}")

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = pd.read_csv(ARQUIVO)
    receitas = df[df["Valor"] > 0]["Valor"].sum()
    despesas = df[df["Valor"] < 0]["Valor"].sum()
    saldo = receitas + despesas

    msg = (
        f"📊 Resumo:\n\n"
        f"💰 Receitas: R$ {receitas:.2f}\n"
        f"💸 Despesas: R$ {abs(despesas):.2f}\n"
        f"💵 Saldo: R$ {saldo:.2f}"
    )
    await update.message.reply_text(msg)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("resumo", resumo))

app.run_polling()
