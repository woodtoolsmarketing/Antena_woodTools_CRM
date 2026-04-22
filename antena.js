const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const fs = require('fs');
const sqlite3 = require('sqlite3').verbose();

const DB_PATH = './estado_whatsapp.db';

function actualizarEstado(id_vendedor, estado) {
    let db = new sqlite3.Database(DB_PATH);
    let id_original = id_vendedor.replace('_', '/');
    db.run(`UPDATE vendedores SET estado = ? WHERE numero = ?`, [estado, id_original]);
    db.close();
}

function registrarChatLocal(id_vendedor, telefono) {
    let db = new sqlite3.Database(DB_PATH);
    let id_original = id_vendedor.replace('_', '/');
    const fecha = new Date().toISOString().split('T')[0];
    db.run(`INSERT INTO actividad_diaria (fecha, numero_vendedor, telefono_cliente) VALUES (?, ?, ?)`, [fecha, id_original, telefono]);
    db.close();
}

// NUEVA FUNCIÓN PARA EL BACKUP DE CHATS
function guardarMensajeBackup(id_vendedor, telefono_cliente, tipo, contenido, timestamp) {
    let db = new sqlite3.Database(DB_PATH);
    let id_original = id_vendedor.replace('_', '/');
    
    // Inserta el mensaje en una nueva tabla (asegurate de crearla en tu Python)
    db.run(`INSERT INTO backup_mensajes (numero_vendedor, telefono_cliente, tipo_mensaje, contenido, fecha_hora) VALUES (?, ?, ?, ?, ?)`, 
        [id_original, telefono_cliente, tipo, contenido, timestamp], (err) => {
            if (err) console.error("Error guardando backup:", err.message);
        });
    db.close();
}

// FUNCIÓN PARA EXTRAER HISTORIAL ANTIGUO DE FORMA SEGURA
async function extraerHistorialSeguro(client, id_vendedor) {
    console.log(`⏳ [${id_vendedor}] Iniciando backup de conversaciones antiguas...`);
    
    try {
        // Obtenemos todos los chats sincronizados en esta sesión web
        const chats = await client.getChats();
        
        // Filtramos para quedarnos solo con chats de clientes (ignoramos grupos)
        const chatsIndividuales = chats.filter(chat => !chat.isGroup);
        console.log(`Encontrados ${chatsIndividuales.length} chats para procesar del vendedor ${id_vendedor}.`);

        for (const chat of chatsIndividuales) {
            try {
                // Extraemos los últimos 50 mensajes de este chat 
                // (Podés subir este número a 100 o 200, pero tarda más)
                const mensajes = await chat.fetchMessages({ limit: 50 });

                for (const msg of mensajes) {
                    // Evitamos procesar estados o mensajes de sistema
                    if (msg.isStatus) continue;

                    const esSaliente = msg.fromMe; 
                    const tel_limpio = esSaliente ? msg.to.replace('@c.us', '') : msg.from.replace('@c.us', '');
                    const tipo_mensaje = esSaliente ? 'Vendedor a Cliente' : 'Cliente a Vendedor';
                    const contenido = msg.body || "[Multimedia/Sticker]"; 
                    const fecha_hora = new Date(msg.timestamp * 1000).toLocaleString('es-AR');

                    // Llamamos a la función que armamos en la respuesta anterior
                    guardarMensajeBackup(id_vendedor, tel_limpio, tipo_mensaje, contenido, fecha_hora);
                }
                
                // 🛑 PAUSA OBLIGATORIA: Esperamos 2 segundos antes de pasar al siguiente chat
                // Esto es vital para que WhatsApp no bloquee el número del vendedor.
                await new Promise(resolve => setTimeout(resolve, 2000));

            } catch (errChat) {
                console.error(`Error leyendo un chat específico:`, errChat.message);
            }
        }
        
        console.log(`✅ [${id_vendedor}] Backup del historial antiguo completado con éxito.`);
    } catch (error) {
        console.error(`⚠️ Error general extrayendo historial de ${id_vendedor}:`, error);
    }
}

let vendedores = {};
try {
    vendedores = JSON.parse(fs.readFileSync('./vendedores.json', 'utf8'));
} catch (error) {
    console.log("Esperando a que el Gestor agregue vendedores...");
}

async function iniciarSistema() {
    for (const [id_vendedor, telefono] of Object.entries(vendedores)) {
        
        const client = new Client({
            authStrategy: new LocalAuth({ clientId: `vendedor_${id_vendedor}` }),
            puppeteer: { headless: true, args: ['--no-sandbox'] }
        });

        client.on('qr', (qr) => {
            console.log(`\n=========================================`);
            console.log(`ESCANEA ESTE QR PARA EL VENDEDOR: ${id_vendedor} (${telefono})`);
            console.log(`=========================================`);
            qrcode.generate(qr, { small: true });
        });

        client.on('ready', () => {
            console.log(`✅ Sesión lista: Vendedor ${id_vendedor}`);
            actualizarEstado(id_vendedor, '✅'); 
            
            // Disparamos el backup en segundo plano para no trabar el resto de la app.
            // NOTA: Una vez que hagas la extracción inicial, comentá la línea de abajo 
            // para que no vuelva a descargar todo cada vez que se reinicia PM2.
            extraerHistorialSeguro(client, id_vendedor);
        });

        client.on('disconnected', () => {
            actualizarEstado(id_vendedor, '❌');
        });

        // CAMBIO CLAVE: Usar 'message_create' para leer lo que entra Y lo que sale
        client.on('message_create', async (msg) => {
            if (msg.isGroupMsg || msg.isStatus) return;

            // Determinar si el mensaje lo envió el vendedor o el cliente
            const esSaliente = msg.fromMe; 
            const tel_limpio = esSaliente ? msg.to.replace('@c.us', '') : msg.from.replace('@c.us', '');
            const tipo_mensaje = esSaliente ? 'Vendedor a Cliente' : 'Cliente a Vendedor';
            
            // Si no tiene cuerpo de texto (ej. es un sticker sin texto), le ponemos un aviso
            const contenido = msg.body || "[Multimedia/Sticker]"; 
            
            // Convertir el timestamp de Unix a formato legible
            const fecha_hora = new Date(msg.timestamp * 1000).toLocaleString('es-AR');

            // 1. Ejecutar el backup en SQLite en tiempo real
            guardarMensajeBackup(id_vendedor, tel_limpio, tipo_mensaje, contenido, fecha_hora);

            // 2. Solo disparamos el Webhook y la métrica si es un mensaje ENTRANTE 
            // (para no duplicar conteos ni volver loco al CRM cuando el vendedor responde)
            if (!esSaliente) {
                try {
                    const contact = await msg.getContact();
                    const esta_agendado = contact.isMyContact; 
                    const nombre = contact.name || contact.pushname || "Desconocido";

                    await axios.post('http://localhost:5000/webhook-qr', {
                        vendedor_id: id_vendedor.replace('_', '/'),
                        esta_agendado: esta_agendado,
                        telefono_cliente: tel_limpio,
                        nombre_cliente: nombre
                    });
                } catch (error) {}

                registrarChatLocal(id_vendedor, tel_limpio);
            }
        });

        client.initialize();
        await new Promise(res => setTimeout(res, 15000)); 
    }
}

iniciarSistema();