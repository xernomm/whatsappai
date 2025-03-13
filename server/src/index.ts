import makeWASocket, { useMultiFileAuthState, DisconnectReason } from '@whiskeysockets/baileys'
import { Boom } from '@hapi/boom'
import qr from 'qrcode-terminal'
import axios from 'axios'

const FLASK_API_URL = 'http://127.0.0.1:5000/ask'  // Ganti dengan URL server Flask jika berbeda

async function startBot() {
    const { state, saveCreds } = await useMultiFileAuthState('src/session')
    const sock = makeWASocket({
        auth: state,
        printQRInTerminal: true,
    })

    sock.ev.on('creds.update', saveCreds)

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr: qrCode } = update

        if (qrCode) {
            console.log('🔄 Scan QR Code untuk login:')
            qr.generate(qrCode, { small: true })
        }

        if (connection === 'open') {
            console.log('✅ Bot berhasil terhubung ke WhatsApp!')
        } else if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error as Boom)?.output?.statusCode !== DisconnectReason.loggedOut
            console.log('⚠️ Koneksi terputus, mencoba menyambungkan kembali...')
            if (shouldReconnect) {
                await startBot()
            } else {
                console.log('❌ Anda telah logout. Hapus folder "src/session" untuk login ulang.')
            }
        }
    })

    // Menangani pesan yang masuk
    sock.ev.on('messages.upsert', async ({ messages }) => {
        const message = messages[0]
        if (!message.message || message.key.fromMe) return

        const remoteJid = message.key.remoteJid!
        const phone_number = remoteJid.split('@')[0]

        const userMessage = message.message.conversation || message.message.extendedTextMessage?.text
        if (!userMessage) return

        console.log(`📩 Pesan dari ${phone_number}: ${userMessage}`)

        try {
            // Kirim ke Flask API
            const { data } = await axios.post(FLASK_API_URL, {
                question: userMessage,
                phone_number: phone_number
            })

            const botResponse = data.response || '⚠️ Tidak ada respons dari server.'
            console.log(`🤖 Balasan ke ${phone_number}: ${botResponse}`)

            // Kirim balasan ke WhatsApp
            await sock.sendMessage(remoteJid, { text: botResponse })
        } catch (error) {
            console.error('❌ Error mengirim ke Flask API:', error)
            await sock.sendMessage(remoteJid, { text: '⚠️ Terjadi kesalahan dalam memproses pesan.' })
        }
    })
}

async function main() {
    console.log('🚀 Memulai bot WhatsApp...')
    await startBot()
}

main().catch(console.error)
