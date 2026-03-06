import os
import logging
import pandas as pd
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

logging.basicConfig(level=logging.INFO)

ARQUIVO = "dados.csv"

# Criar arquivo se não existir
if not os.path.exists(ARQUIVO):
    df = pd.DataFrame(columns=["data", "tipo", "valor", "categoria"])
    df.to_csv(ARQUIVO, index=False)


def carregar_dados():
    return pd.read_csv(ARQUIVO)


def salvar_dados(df):
    df.to_csv(ARQUIVO, index=False)


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = """
💰 *Bem vindo ao Bot Financeiro*

Use os comandos:

/gasto valor categoria
Ex: /gasto 50 mercado

/receita valor categoria
Ex: /receita 200 salario

/extrato
Mostra todas movimentações

/resumo
Resumo do mês

/reset_mes
Apaga dados do mês atual

/ajuda
Ver comandos
"""
    await update.message.reply_text(mensagem, parse_mode="Markdown")


# AJUDA
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


# GASTO
async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(context.args[0])
        categoria = context.args[1]

        df = carregar_dados()

        nova_linha = {
            "data": datetime.now().strftime("%d/%m/%Y"),
            "tipo": "gasto",
            "valor": valor,
            "categoria": categoria
        }

        df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        salvar_dados(df)

        await update.message.reply_text(f"💸 Gasto registrado\nValor: R${valor}\nCategoria: {categoria}")

    except:
        await update.message.reply_text("Use:\n/gasto 50 mercado")


# RECEITA
async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(context.args[0])
        categoria = context.args[1]

        df = carregar_dados()

        nova_linha = {
            "data": datetime.now().strftime("%d/%m/%Y"),
            "tipo": "receita",
            "valor": valor,
            "categoria": categoria
        }

        df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        salvar_dados(df)

        await update.message.reply_text(f"💰 Receita registrada\nValor: R${valor}\nCategoria: {categoria}")

    except:
        await update.message.reply_text("Use:\n/receita 500 salario")


# EXTRATO
async def extrato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = carregar_dados()

    if df.empty:
        await update.message.reply_text("Nenhuma movimentação ainda.")
        return

    mensagem = "📄 Extrato:\n\n"

    for _, row in df.iterrows():
        emoji = "💰" if row["tipo"] == "receita" else "💸"
        mensagem += f"{emoji} {row['data']} | {row['categoria']} | R${row['valor']}\n"

    await update.message.reply_text(mensagem)


# RESUMO
async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = carregar_dados()

    receitas = df[df["tipo"] == "receita"]["valor"].sum()
    gastos = df[df["tipo"] == "gasto"]["valor"].sum()

    saldo = receitas - gastos

    mensagem = f"""
📊 Resumo Financeiro

💰 Receitas: R${receitas}

💸 Gastos: R${gastos}

💵 Saldo: R${saldo}
"""

    await update.message.reply_text(mensagem)


# RESET MES
async def reset_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    df = pd.DataFrame(columns=["data", "tipo", "valor", "categoria"])
    salvar_dados(df)

    await update.message.reply_text("🧹 Dados do mês apagados.")


# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("gasto", gasto))
    app.add_handler(CommandHandler("receita", receita))
    app.add_handler(CommandHandler("extrato", extrato))
    app.add_handler(CommandHandler("resumo", resumo))
    app.add_handler(CommandHandler("reset_mes", reset_mes))

    print("Bot rodando...")
    app.run_polling()


if __name__ == "__main__":
    main()
