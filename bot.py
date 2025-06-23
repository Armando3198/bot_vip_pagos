import sqlite3
from telegram import Update
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackContext

TOKEN = "7987617067:AAE8UE9RNuMUnk0OAZ5_jCbP48LU5qkNL4o"
ALLOWED_USERS = ["@AJavier98", "@lachi_prr"]

conn = sqlite3.connect('pagos.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
  CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT, apellidos TEXT, alias TEXT,
    monto REAL, fecha_pago TEXT, fecha_prox_pago TEXT
  )
''')
conn.commit()

(NOMBRE, APELLIDOS, ALIAS, MONTO, FPAGO, FPROX) = range(6)

def restricted(func):
    def wrapper(update: Update, ctx: CallbackContext):
        user = update.effective_user
        if f\"@{user.username}\" not in ALLOWED_USERS:
            return update.message.reply_text(\"❌ No tienes permisos.\")
        return func(update, ctx)
    return wrapper

@restricted
def start(update: Update, ctx: CallbackContext):
    return update.message.reply_text(\"¡Bienvenido al Bot de Pagos VIP!\\nUsa /agregar, /ver, /eliminar o /pendientes.\")

@restricted
def agregar_start(update: Update, ctx: CallbackContext):
    ctx.user_data.clear()
    update.message.reply_text(\"📥 Ingresa el *Nombre*:\", parse_mode='Markdown')
    return NOMBRE

def agregar_nombre(update, ctx):
    ctx.user_data['nombre'] = update.message.text
    update.message.reply_text(\"Apellidos:\")
    return APELLIDOS

def agregar_apellidos(update, ctx):
    ctx.user_data['apellidos'] = update.message.text
    update.message.reply_text(\"Alias:\")
    return ALIAS

def agregar_alias(update, ctx):
    ctx.user_data['alias'] = update.message.text
    update.message.reply_text(\"Monto pagado (ej: 150.00):\")
    return MONTO

def agregar_monto(update, ctx):
    ctx.user_data['monto'] = float(update.message.text)
    update.message.reply_text(\"Fecha de pago (YYYY-MM-DD):\")
    return FPAGO

def agregar_fpago(update, ctx):
    ctx.user_data['fecha_pago'] = update.message.text
    update.message.reply_text(\"Fecha próximo pago (YYYY-MM-DD):\")
    return FPROX

def agregar_fprox(update, ctx):
    ctx.user_data['fecha_prox_pago'] = update.message.text
    data = ctx.user_data
    c.execute('''
      INSERT INTO pagos (nombre, apellidos, alias, monto, fecha_pago, fecha_prox_pago)
      VALUES (?, ?, ?, ?, ?, ?)''',
      (data['nombre'], data['apellidos'], data['alias'],
       data['monto'], data['fecha_pago'], data['fecha_prox_pago'])
    )
    conn.commit()
    update.message.reply_text(\"✅ Pago agregado correctamente.\")
    return ConversationHandler.END

def cancelar(update, ctx):
    update.message.reply_text(\"Operación cancelada.\")
    return ConversationHandler.END

@restricted
def ver(update, ctx):
    rows = c.execute(\"SELECT id,alias,monto,fecha_prox_pago FROM pagos\").fetchall()
    if not rows:
        return update.message.reply_text(\"📭 No hay registros.\")
    resp = \"\\n\".join([f\"#{r[0]} {r[1]} – Pago: {r[2]} – Próx: {r[3]}\" for r in rows])
    update.message.reply_text(resp)

@restricted
def eliminar(update, ctx):
    try:
        idx = int(update.message.text.split()[1])
        c.execute(\"DELETE FROM pagos WHERE id=?\", (idx,))
        conn.commit()
        return update.message.reply_text(f\"🗑️ Registro #{idx} eliminado.\")
    except:
        return update.message.reply_text(\"Uso: /eliminar <id>\")

@restricted
def pendientes(update, ctx):
    rows = c.execute(\"SELECT alias,monto,fecha_prox_pago FROM pagos\").fetchall()
    from datetime import date
    hoy = date.today().isoformat()
    pendientes = [r for r in rows if r[2] <= hoy]
    if not pendientes:
        return update.message.reply_text(\"🎉 No hay pagos pendientes.\")
    resp = \"\\n\".join([f\"{r[0]}: {r[1]} – Próx en {r[2]}\" for r in pendientes])
    update.message.reply_text(resp)

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv = ConversationHandler(
        entry_points=[CommandHandler('agregar', agregar_start)],
        states={
            NOMBRE: [MessageHandler(Filters.text, agregar_nombre)],
            APELLIDOS: [MessageHandler(Filters.text, agregar_apellidos)],
            ALIAS: [MessageHandler(Filters.text, agregar_alias)],
            MONTO: [MessageHandler(Filters.text, agregar_monto)],
            FPAGO: [MessageHandler(Filters.text, agregar_fpago)],
            FPROX: [MessageHandler(Filters.text, agregar_fprox)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)],
    )

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(conv)
    dp.add_handler(CommandHandler('ver', ver))
    dp.add_handler(CommandHandler('eliminar', eliminar))
    dp.add_handler(CommandHandler('pendientes', pendientes))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
