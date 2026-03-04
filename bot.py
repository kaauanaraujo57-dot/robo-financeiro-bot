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
    df = pd.DataFrame(columns=["Data", "Mes", "Ano", "Descricao", "Categoria", "Valor"])
    df.to_csv(ARQUIVO, index=False)

# Criar categorias padrão
if not os.path.exists(ARQ_CATEGORIAS):
    categorias_iniciais = [
        "mercado",
        "casa",
        "roupas",
        "celular",
        "pessoal",
        "lazer",
        "investimentos",
        "transporte"
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categorias = "\n".join(carregar_categorias())
    await update.message.reply_text(
        "💰 Robô Financeiro 4.0\n\n"
        "Comandos:\n"
        "/gasto valor categoria descricao (opcional MM-AAAA)\n"
        "/receita valor categoria descricao (opcional MM-AAAA)\n"
        "/resumo (ou /resumo 03-2026)\n"
        "/historico categoria\n"
        "/grafico\n"
        "/categorias\n"
        "/addcategoria nome\n\n"
        f"📂 Categorias disponíveis:\n{categorias}"
    )

async def categorias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lista = "\n".join(carregar_categorias())
    await update.message.reply_text(f"📂 Categorias disponíveis:\n{lista}")

async def addcategoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /addcategoria nome")
        return

    nova = context.args[0].lower().strip()
    categorias = carregar_categorias()

    if nova in categorias:
        await update.message.reply_text("Categoria já existe.")
        return

    salvar_categoria(nova)
    await update.message.reply_text(f"Categoria '{nova}' adicionada.")

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(context.args[0])
        mes, ano, args_limpos = extrair_data(context.args)
        categoria = args_limpos[1].lower().strip()
        descricao = " ".join(args_limpos[2:])
    except:
        await update.message.reply_text("Formato errado.")
        return

    categorias = carregar_categorias()
    if categoria not in categorias:
        await update.message.reply_text("Categoria inválida. Use /categorias para ver a lista.")
        return

    df = pd.read_csv(ARQUIVO)

    novo = pd.DataFrame([[
        f"01/{mes:02d}/{ano}",
        mes,
        ano,
        descricao,
        categoria,
        -abs(valor)
    ]], columns=["Data", "Mes", "Ano", "Descricao", "Categoria", "Valor"])

    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO, index=False)

    await update.message.reply_text(f"💸 Gasto registrado em {mes:02d}-{ano}")

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(context.args[0])
        mes, ano, args_limpos = extrair_data(context.args)
        categoria = args_limpos[1].lower().strip()
        descricao = " ".join(args_limpos[2:])
    except:
        await update.message.reply_text("Formato errado.")
        return

    categorias = carregar_categorias()
    if categoria not in categorias:
        await update.message.reply_text("Categoria inválida. Use /categorias para ver a lista.")
        return

    df = pd.read_csv(ARQUIVO)

    novo = pd.DataFrame([[
        f"01/{mes:02d}/{ano}",
        mes,
        ano,
        descricao,
        categoria,
        abs(valor)
    ]], columns=["Data", "Mes", "Ano", "Descricao", "Categoria", "Valor"])

    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO, index=False)

    await update.message.reply_text(f"💰 Receita registrada em {mes:02d}-{ano}")

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

    if df.empty:
        await update.message.reply_text("Sem registros neste período.")
        return

    receitas = df[df["Valor"] > 0]["Valor"].sum()
    despesas = df[df["Valor"] < 0]["Valor"].sum()
    saldo = receitas + despesas

    gastos_categoria = df[df["Valor"] < 0].groupby("Categoria")["Valor"].sum().abs()

    msg = (
        f"📊 Resumo {mes:02d}-{ano}\n\n"
        f"💰 Receitas: R$ {receitas:.2f}\n"
        f"💸 Despesas: R$ {abs(despesas):.2f}\n"
        f"💵 Saldo: R$ {saldo:.2f}\n\n"
        "📂 Gastos por Categoria:\n"
    )

    for cat, valor in gastos_categoria.items():
        msg += f"{cat}: R$ {valor:.2f}\n"

    await update.message.reply_text(msg)

async def historico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /historico categoria")
        return

    categoria = context.args[0].lower().strip()
    df = pd.read_csv(ARQUIVO)
    df = df[df["Categoria"] == categoria]

    if df.empty:
        await update.message.reply_text("Sem registros nessa categoria.")
        return

    msg = f"📜 Histórico - {categoria}\n\n"
    for _, row in df.tail(10).iterrows():
        msg += f"{row['Data']} - R$ {row['Valor']:.2f}\n"

    total = df["Valor"].sum()
    msg += f"\nTotal na categoria: R$ {total:.2f}"

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
app.add_handler(CommandHandler("categorias", categorias))
app.add_handler(CommandHandler("addcategoria", addcategoria))

app.run_polling()
