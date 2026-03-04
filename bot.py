import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
ARQUIVO = "financas.csv"

logging.basicConfig(level=logging.INFO)

# Criar arquivo se não existir
try:
    pd.read_csv(ARQUIVO)
except:
    df = pd.DataFrame(columns=["Descricao", "Categoria", "Valor"])
    df.to_csv(ARQUIVO, index=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Robô financeiro ativo!\n\n"
        "Use:\n"
        "/gasto valor categoria descricao\n"
        "/receita valor categoria descricao\n"
        "/resumo\n"
        "/grafico"
    )

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valor = float(context.args[0])
    categoria = context.args[1]
    descricao = " ".join(context.args[2:])

    df = pd.read_csv(ARQUIVO)
    novo = pd.DataFrame([[descricao, categoria, -abs(valor)]],
                        columns=["Descricao", "Categoria", "Valor"])
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO, index=False)

    await update.message.reply_text(
        f"💸 Gasto registrado!\nCategoria: {categoria}\nValor: R$ {valor}"
    )

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valor = float(context.args[0])
    categoria = context.args[1]
    descricao = " ".join(context.args[2:])

    df = pd.read_csv(ARQUIVO)
    novo = pd.DataFrame([[descricao, categoria, abs(valor)]],
                        columns=["Descricao", "Categoria", "Valor"])
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO, index=False)

    await update.message.reply_text(
        f"💰 Receita registrada!\nCategoria: {categoria}\nValor: R$ {valor}"
    )

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = pd.read_csv(ARQUIVO)

    receitas = df[df["Valor"] > 0]["Valor"].sum()
    despesas = df[df["Valor"] < 0]["Valor"].sum()
    saldo = receitas + despesas

    resumo_categoria = df.groupby("Categoria")["Valor"].sum()

    msg = (
        f"📊 Resumo Geral\n\n"
        f"💰 Receitas: R$ {receitas:.2f}\n"
        f"💸 Despesas: R$ {abs(despesas):.2f}\n"
        f"💵 Saldo: R$ {saldo:.2f}\n\n"
        f"📂 Por Categoria:\n"
    )

    for cat, valor in resumo_categoria.items():
        msg += f"{cat}: R$ {valor:.2f}\n"

    await update.message.reply_text(msg)

async def grafico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = pd.read_csv(ARQUIVO)
    despesas = df[df["Valor"] < 0]

    if despesas.empty:
        await update.message.reply_text("Sem dados para gerar gráfico.")
        return

    resumo = despesas.groupby("Categoria")["Valor"].sum().abs()

    plt.figure()
    resumo.plot(kind="bar")
    plt.title("Gastos por Categoria")
    plt.ylabel("Valor (R$)")
    plt.tight_layout()
    plt.savefig("grafico.png")
    plt.close()

    with open("grafico.png", "rb") as img:
        await update.message.reply_photo(photo=img)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("resumo", resumo))
app.add_handler(CommandHandler("grafico", grafico))

app.run_polling()
