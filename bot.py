import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
ARQUIVO = "financas.csv"
ARQ_CATEGORIAS = "categorias.txt"

logging.basicConfig(level=logging.INFO)

# Criar base se não existir
if not os.path.exists(ARQUIVO):
    df = pd.DataFrame(columns=["UserID","Data","Mes","Ano","Descricao","Categoria","Valor"])
    df.to_csv(ARQUIVO, index=False)

# Criar categorias padrão
if not os.path.exists(ARQ_CATEGORIAS):
    categorias_iniciais = [
        "mercado","casa","roupas","celular",
        "pessoal","lazer","investimentos","transporte"
    ]
    with open(ARQ_CATEGORIAS, "w") as f:
        for c in categorias_iniciais:
            f.write(c + "\n")

def carregar_categorias():
    with open(ARQ_CATEGORIAS, "r") as f:
        return [linha.strip() for linha in f.readlines()]

def salvar_categoria(nova):
    with open(ARQ_CATEGORIAS, "a") as f:
        f.write(nova + "\n")

def mes_atual():
    hoje = datetime.now()
    return hoje.month, hoje.year

def extrair_data(args):
    if len(args) >= 3:
        ultimo = args[-1]
        try:
            mes, ano = ultimo.split("-")
            mes = int(mes)
            ano = int(ano)
            if 1 <= mes <= 12:
                return mes, ano, args[:-1]
        except:
            pass
    mes, ano = mes_atual()
    return mes, ano, args

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        valor = float(context.args[0])
        mes, ano, args_limpos = extrair_data(context.args)
        categoria = args_limpos[1].lower().strip()
        descricao = " ".join(args_limpos[2:])
    except:
        await update.message.reply_text("Formato errado.")
        return

    if categoria not in carregar_categorias():
        await update.message.reply_text("Categoria inválida.")
        return

    df = pd.read_csv(ARQUIVO)

    novo = pd.DataFrame([[
        user_id,
        f"01/{mes:02d}/{ano}",
        mes,
        ano,
        descricao,
        categoria,
        -abs(valor)
    ]], columns=["UserID","Data","Mes","Ano","Descricao","Categoria","Valor"])

    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO, index=False)

    await update.message.reply_text("💸 Gasto registrado.")

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        valor = float(context.args[0])
        mes, ano, args_limpos = extrair_data(context.args)
        categoria = args_limpos[1].lower().strip()
        descricao = " ".join(args_limpos[2:])
    except:
        await update.message.reply_text("Formato errado.")
        return

    if categoria not in carregar_categorias():
        await update.message.reply_text("Categoria inválida.")
        return

    df = pd.read_csv(ARQUIVO)

    novo = pd.DataFrame([[
        user_id,
        f"01/{mes:02d}/{ano}",
        mes,
        ano,
        descricao,
        categoria,
        abs(valor)
    ]], columns=["UserID","Data","Mes","Ano","Descricao","Categoria","Valor"])

    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO, index=False)

    await update.message.reply_text("💰 Receita registrada.")

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    df = pd.read_csv(ARQUIVO)

    df = df[df["UserID"] == user_id]

    if len(context.args) == 1:
        mes, ano = context.args[0].split("-")
        mes = int(mes)
        ano = int(ano)
    else:
        mes, ano = mes_atual()

    df = df[(df["Mes"] == mes) & (df["Ano"] == ano)]

    if df.empty:
        await update.message.reply_text("Sem registros.")
        return

    receitas = df[df["Valor"] > 0]["Valor"].sum()
    despesas = df[df["Valor"] < 0]["Valor"].sum()
    saldo = receitas + despesas

    await update.message.reply_text(
        f"📊 Resumo {mes:02d}-{ano}\n\n"
        f"Receitas: R$ {receitas:.2f}\n"
        f"Despesas: R$ {abs(despesas):.2f}\n"
        f"Saldo: R$ {saldo:.2f}"
    )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("resumo", resumo))

app.run_polling()
