const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const fs = require('fs');
const sqlite3 = require('sqlite3').verbose();

const DB_PATH = './estado_whatsapp.db';

// 1. Funciones para hablar con la Base de Datos de Python
function actualizarEstado(id_vendedor, estado) {
    let db = new sqlite3.Database(DB_PATH);
    // Vuelve a poner la barra original para la base de datos (Ej: "0_A" a "0_A", "1_302" a "1/302")
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

// 2. Lee los vendedores desde el archivo dinámico que crea Python
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
            actualizarEstado(id_vendedor, '🟢'); // Le avisa al Gestor visual!
        });

        client.on('disconnected', () => {
            actualizarEstado(id_vendedor, '❌');
        });

        client.on('message', async (msg) => {
            if (msg.isGroupMsg || msg.isStatus) return;

            const contact = await msg.getContact();
            const esta_agendado = contact.isMyContact; 
            const nombre = contact.name || contact.pushname || "Desconocido";
            const tel_limpio = msg.from.replace('@c.us', '');

            // Avisar a Flask (para Google Sheets)
            try {
                await axios.post('http://localhost:5000/webhook-qr', {
                    vendedor_id: id_vendedor.replace('_', '/'),
                    esta_agendado: esta_agendado,
                    telefono_cliente: tel_limpio,
                    nombre_cliente: nombre
                });
            } catch (error) {}

            // Avisar a la BD local (Para el conteo en pantalla)
            registrarChatLocal(id_vendedor, tel_limpio);
        });

        client.initialize();
        await new Promise(res => setTimeout(res, 15000)); 
    }
}

iniciarSistema();