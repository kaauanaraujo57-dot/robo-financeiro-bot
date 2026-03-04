import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
ARQUIVO = "financas.csv"

logging.basicConfig(level=logging.INFO)

# Criar arquivo se não existir
try:
    pd.read_csv(ARQUIVO)
except:
    df = pd.DataFrame(columns=["Data", "Mes", "Ano", "Descricao", "Categoria", "Valor"])
    df.to_csv(ARQUIVO, index=False)

def mes_atual():
    hoje = datetime.now()
    return hoje.month, hoje.year

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Robô Financeiro 2.0\n\n"
        "Comandos:\n"
        "/gasto valor categoria descricao\n"
        "/receita valor categoria descricao\n"
        "/resumo (ou /resumo 03-2026)\n"
        "/historico categoria\n"
        "/grafico"
    )

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(context.args[0])
        categoria = context.args[1]
        descricao = " ".join(context.args[2:])
    except:
        await update.message.reply_text("Formato errado.\nUse: /gasto valor categoria descricao")
        return

    hoje = datetime.now()
    df = pd.read_csv(ARQUIVO)

    novo = pd.DataFrame([[
        hoje.strftime("%d/%m/%Y"),
        hoje.month,
        hoje.year,
        descricao,
        categoria,
        -abs(valor)
    ]], columns=["Data", "Mes", "Ano", "Descricao", "Categoria", "Valor"])

    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO, index=False)

    await update.message.reply_text(f"💸 Gasto registrado: R$ {valor}")

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(context.args[0])
        categoria = context.args[1]
        descricao = " ".join(context.args[2:])
    except:
        await update.message.reply_text("Formato errado.\nUse: /receita valor categoria descricao")
        return

    hoje = datetime.now()
    df = pd.read_csv(ARQUIVO)

    novo = pd.DataFrame([[
        hoje.strftime("%d/%m/%Y"),
        hoje.month,
        hoje.year,
        descricao,
        categoria,
        abs(valor)
    ]], columns=["Data", "Mes", "Ano", "Descricao", "Categoria", "Valor"])

    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO, index=False)

    await update.message.reply_text(f"💰 Receita registrada: R$ {valor}")

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = pd.read_csv(ARQUIVO)

    if len(context.args) == 1:
        try:
            mes, ano = context.args[0].split("-")
            mes = int(mes)
            ano = int(ano)
        except:
            await update.message.reply_text("Use formato: /resumo 03-2026")
            return
    else:
        mes, ano = mes_atual()

    df = df[(df["Mes"] == mes) & (df["Ano"] == ano)]

    receitas = df[df["Valor"] > 0]["Valor"].sum()
    despesas = df[df["Valor"] < 0]["Valor"].sum()
    saldo = receitas + despesas

    gastos_categoria = df[df["Valor"] < 0].groupby("Categoria")["Valor"].sum().abs()

    msg = (
        f"📊 Resumo {mes:02d}-{ano}\n\n"
        f"💰 Receitas: R$ {receitas:.2f}\n"
        f"💸 Despesas: R$ {abs(despesas):.2f}\n"
        f"💵 Saldo: R$ {saldo:.2f}\n\n"
        f"📂 Gastos por Categoria:\n"
    )

    for cat, valor in gastos_categoria.items():
        msg += f"{cat}: R$ {valor:.2f}\n"

    await update.message.reply_text(msg)

async def historico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Use: /historico categoria")
        return

    categoria = context.args[0]
    df = pd.read_csv(ARQUIVO)
    df = df[df["Categoria"] == categoria].sort_values(by=["Ano", "Mes"], ascending=False)

    if df.empty:
        await update.message.reply_text("Sem registros nessa categoria.")
        return

    msg = f"📜 Histórico - {categoria}\n\n"
    for _, row in df.tail(10).iterrows():
        msg += f"{row['Data']} - R$ {row['Valor']:.2f}\n"

    await update.message.reply_text(msg)

async def grafico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mes, ano = mes_atual()
    df = pd.read_csv(ARQUIVO)
    df = df[(df["Mes"] == mes) & (df["Ano"] == ano)]
    despesas = df[df["Valor"] < 0]

    if despesas.empty:
        await update.message.reply_text("Sem dados neste mês.")
        return

    resumo = despesas.groupby("Categoria")["Valor"].sum().abs()

    plt.figure()
    plt.pie(resumo, labels=resumo.index, autopct='%1.1f%%')
    plt.title(f"Gastos {mes:02d}-{ano}")
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
app.add_handler(CommandHandler("historico", historico))
app.add_handler(CommandHandler("grafico", grafico))

app.run_polling()
