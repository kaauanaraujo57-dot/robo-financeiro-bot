import os
import logging
import pandas as pd
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# CONFIGURAÇÃO
# =========================

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")  # pega variável de ambiente do banco

ARQUIVO = "financas.csv"
ARQ_METAS = "metas.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =========================
# VERIFICAÇÃO DO BANCO
# =========================

if DATABASE_URL:
    print(f"Conectando ao banco: {DATABASE_URL}")
    # Aqui você colocaria a conexão com o PostgreSQL, ex: psycopg2 ou sqlalchemy
    # Por enquanto, vamos deixar o bot funcionando com CSV
else:
    print("DATABASE_URL não configurada, usando CSV local.")

# =========================
# CRIAÇÃO DE ARQUIVOS CSV (se não existir)
# =========================

if not os.path.exists(ARQUIVO):
    df = pd.DataFrame(columns=[
        "UserID","Data","Mes","Ano",
        "Descricao","Categoria","Valor"
    ])
    df.to_csv(ARQUIVO, index=False)

if not os.path.exists(ARQ_METAS):
    df_meta = pd.DataFrame(columns=[
        "UserID","Categoria","Meta"
    ])
    df_meta.to_csv(ARQ_METAS, index=False)

# =========================
# FUNÇÕES AUXILIARES
# =========================

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
    return *mes_atual(), args

# =========================
# COMANDOS DO BOT
# =========================

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        valor = float(context.args[0])
        mes, ano, args_limpos = extrair_data(context.args)
        categoria = args_limpos[1].lower()
        descricao = " ".join(args_limpos[2:])
    except:
        await update.message.reply_text("Formato errado. Exemplo: /gasto 50 comida almoço 03-2026")
        return

    df = pd.read_csv(ARQUIVO)

    novo = pd.DataFrame([[user_id, f"01/{mes:02d}/{ano}", mes, ano, descricao, categoria, -abs(valor)]],
                        columns=df.columns)
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO, index=False)

    await verificar_meta(update, user_id, categoria, mes, ano)
    await update.message.reply_text("💸 Gasto registrado.")

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        valor = float(context.args[0])
        mes, ano, args_limpos = extrair_data(context.args)
        categoria = args_limpos[1].lower()
        descricao = " ".join(args_limpos[2:])
    except:
        await update.message.reply_text("Formato errado. Exemplo: /receita 100 salario 03-2026")
        return

    df = pd.read_csv(ARQUIVO)

    novo = pd.DataFrame([[user_id, f"01/{mes:02d}/{ano}", mes, ano, descricao, categoria, abs(valor)]],
                        columns=df.columns)
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQUIVO, index=False)

    await update.message.reply_text("💰 Receita registrada.")

# =========================
# METAS
# =========================

async def setmeta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        categoria = context.args[0].lower()
        valor = float(context.args[1])
    except:
        await update.message.reply_text("Use: /setmeta categoria valor")
        return

    df_meta = pd.read_csv(ARQ_METAS)
    df_meta = df_meta[~((df_meta["UserID"] == user_id) & (df_meta["Categoria"] == categoria))]

    nova = pd.DataFrame([[user_id, categoria, valor]], columns=df_meta.columns)
    df_meta = pd.concat([df_meta, nova], ignore_index=True)
    df_meta.to_csv(ARQ_METAS, index=False)

    await update.message.reply_text("🎯 Meta definida.")

async def verificar_meta(update, user_id, categoria, mes, ano):
    df = pd.read_csv(ARQUIVO)
    df_meta = pd.read_csv(ARQ_METAS)

    df_user = df[(df["UserID"] == user_id) & (df["Mes"] == mes) & (df["Ano"] == ano) & (df["Categoria"] == categoria)]
    gasto_total = abs(df_user[df_user["Valor"] < 0]["Valor"].sum())

    meta = df_meta[(df_meta["UserID"] == user_id) & (df_meta["Categoria"] == categoria)]
    if meta.empty:
        return

    limite = meta.iloc[0]["Meta"]
    if gasto_total >= limite:
        await update.message.reply_text(f"🚨 Você ultrapassou a meta de {categoria}")
    elif gasto_total >= limite * 0.8:
        await update.message.reply_text(f"⚠️ Você já usou 80% da meta de {categoria}")

# =========================
# RESUMO
# =========================

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    df = pd.read_csv(ARQUIVO)
    df = df[df["UserID"] == user_id]

    if len(context.args) == 1:
        mes, ano = map(int, context.args[0].split("-"))
    else:
        mes, ano = mes_atual()

    df = df[(df["Mes"] == mes) & (df["Ano"] == ano)]

    if df.empty:
        await update.message.reply_text("Sem registros.")
        return

    receitas = df[df["Valor"] > 0]["Valor"].sum()
    despesas = abs(df[df["Valor"] < 0]["Valor"].sum())
    saldo = receitas - despesas

    ranking = df[df["Valor"] < 0].groupby("Categoria")["Valor"].sum().abs().sort_values(ascending=False)

    msg = f"📊 Resumo {mes:02d}-{ano}\n\n"
    msg += f"Receitas: R$ {receitas:.2f}\n"
    msg += f"Despesas: R$ {despesas:.2f}\n"
    msg += f"Saldo: R$ {saldo:.2f}\n\n"
    msg += "🏆 Ranking de Gastos:\n"

    for i, (cat, val) in enumerate(ranking.items(), start=1):
        msg += f"{i}º {cat} - R$ {val:.2f}\n"

    await update.message.reply_text(msg)

# =========================
# COMPARAÇÃO ENTRE MESES
# =========================

async def comparar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) != 2:
        await update.message.reply_text("Use: /comparar 02-2026 03-2026")
        return

    df = pd.read_csv(ARQUIVO)
    df = df[df["UserID"] == user_id]

    mes1, ano1 = map(int, context.args[0].split("-"))
    mes2, ano2 = map(int, context.args[1].split("-"))

    total1 = abs(df[(df["Mes"]==mes1)&(df["Ano"]==ano1)&(df["Valor"]<0)]["Valor"].sum())
    total2 = abs(df[(df["Mes"]==mes2)&(df["Ano"]==ano2)&(df["Valor"]<0)]["Valor"].sum())

    if total1 == 0:
        await update.message.reply_text("Primeiro mês sem dados.")
        return

    variacao = ((total2 - total1) / total1) * 100
    await update.message.reply_text(
        f"📊 Comparação:\n{mes1:02d}-{ano1}: R$ {total1:.2f}\n{mes2:02d}-{ano2}: R$ {total2:.2f}\nVariação: {variacao:.2f}%"
    )

# =========================
# BOT
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("receita", receita))
app.add_handler(CommandHandler("resumo", resumo))
app.add_handler(CommandHandler("setmeta", setmeta))
app.add_handler(CommandHandler("comparar", comparar))

# =========================
# EXECUÇÃO
# =========================

if __name__ == "__main__":
    app.run_polling()
