const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

// Ponemos a los vendedores que queremos monitorear
const vendedores = {
    "0": "1165630406",
    "5": "1164591316",
    "1_302": "1157528428"
    
};

async function iniciarSistema() {
    for (const [id_vendedor, telefono] of Object.entries(vendedores)) {
        
        // LocalAuth crea una carpeta secreta y GUARDA la sesión. No pide QR la próxima vez.
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
            console.log(`✅ Sesión guardada y activa: Vendedor ${id_vendedor}.`);
        });

        client.on('message', async (msg) => {
            if (msg.isGroupMsg || msg.isStatus) return;

            const contact = await msg.getContact();
            const esta_agendado = contact.isMyContact; 
            const nombre = contact.name || contact.pushname || "Desconocido";

            // Le avisa silenciosamente a tu servidor Flask
            try {
                await axios.post('http://localhost:5000/webhook-qr', {
                    vendedor_id: id_vendedor,
                    esta_agendado: esta_agendado,
                    telefono_cliente: msg.from.replace('@c.us', ''),
                    nombre_cliente: nombre
                });
            } catch (error) {
                // Ignora el error si el Flask está apagado un rato
            }
        });

        client.initialize();
        // Espera 15 segs para que tengas tiempo de escanear antes de pasar al siguiente
        await new Promise(res => setTimeout(res, 15000)); 
    }
}

iniciarSistema();