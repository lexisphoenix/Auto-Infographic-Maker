const express = require('express');
const puppeteer = require('puppeteer');
const cors = require('cors');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use((req, res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
    next();
});

let browser;

async function getBrowser() {
    if (!browser) {
        browser = await puppeteer.launch({
            executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || null,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        });
    }
    return browser;
}

app.post('/render', async (req, res) => {
    let page;
    try {
        const { html, width = 1080, height = 1920, format = 'png', deviceScaleFactor = 2 } = req.body;
        
        if (!html) return res.status(400).json({ error: 'HTML content is required' });

        const b = await getBrowser();
        page = await b.newPage();
        
        await page.setUserAgent('Auto-Infographic-Maker/1.0 (Render Service)');
        await page.setViewport({ width: parseInt(width), height: parseInt(height), deviceScaleFactor: parseFloat(deviceScaleFactor) });
        await page.setContent(html, { waitUntil: ['networkidle0', 'load', 'domcontentloaded'] });
        await page.evaluateHandle('document.fonts.ready');
        
        const imageBuffer = await page.screenshot({ type: format === 'jpeg' ? 'jpeg' : 'png', fullPage: false });
        res.set('Content-Type', `image/${format === 'jpeg' ? 'jpeg' : 'png'}`);
        res.send(imageBuffer);
    } catch (error) {
        console.error('Render error:', error);
        res.status(500).json({ error: 'Failed to render HTML', message: error.message });
    } finally {
        if (page) await page.close().catch(console.error);
    }
});

app.post('/render-base64', async (req, res) => {
    let page;
    try {
        const { html, width = 1080, height = 1920, format = 'png', deviceScaleFactor = 2 } = req.body;
        
        if (!html) return res.status(400).json({ error: 'HTML content is required' });

        const b = await getBrowser();
        page = await b.newPage();
        
        await page.setUserAgent('Auto-Infographic-Maker/1.0 (Render Service)');
        await page.setViewport({ width: parseInt(width), height: parseInt(height), deviceScaleFactor: parseFloat(deviceScaleFactor) });
        await page.setContent(html, { waitUntil: ['networkidle0', 'load', 'domcontentloaded'] });
        await page.evaluateHandle('document.fonts.ready');
        
        const imageBuffer = await page.screenshot({ type: format === 'jpeg' ? 'jpeg' : 'png', fullPage: false });
        res.json({
            image: `data:image/${format === 'jpeg' ? 'jpeg' : 'png'};base64,${imageBuffer.toString('base64')}`,
            width: parseInt(width),
            height: parseInt(height)
        });
    } catch (error) {
        console.error('Render base64 error:', error);
        res.status(500).json({ error: 'Failed to render HTML to base64', message: error.message });
    } finally {
        if (page) await page.close().catch(console.error);
    }
});

app.post('/animate', async (req, res) => {
    let page;
    const tempDir = path.join(__dirname, 'temp_' + crypto.randomBytes(4).toString('hex'));
    
    try {
        const { html, width = 1080, height = 1920, duration = 5, fps = 30 } = req.body;
        
        if (!html) return res.status(400).json({ error: 'HTML content is required' });

        fs.mkdirSync(tempDir, { recursive: true });
        const b = await getBrowser();
        page = await b.newPage();
        
        await page.setUserAgent('Auto-Infographic-Maker/1.0 (Animate Service)');
        await page.setViewport({ width: parseInt(width), height: parseInt(height), deviceScaleFactor: 2 });
        await page.setContent(html, { waitUntil: ['networkidle0', 'load'] });
        await page.evaluateHandle('document.fonts.ready');

        const totalFrames = duration * fps;
        
        for (let i = 0; i < totalFrames; i++) {
            const framePath = path.join(tempDir, `frame_${String(i).padStart(4, '0')}.png`);
            await page.screenshot({ path: framePath });
        }

        const mp4Path = path.join(tempDir, 'output.mp4');
        
        await new Promise((resolve, reject) => {
            const ffmpeg = spawn('ffmpeg', ['-y', '-framerate', String(fps), '-i', path.join(tempDir, 'frame_%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', mp4Path]);
            ffmpeg.on('close', code => code === 0 ? resolve() : reject(new Error(`ffmpeg exited with code ${code}`)));
        });

        const videoBuffer = fs.readFileSync(mp4Path);
        res.set('Content-Type', 'video/mp4');
        res.send(videoBuffer);
    } catch (error) {
        console.error('Animate error:', error);
        res.status(500).json({ error: 'Failed to animate HTML', message: error.message });
    } finally {
        if (page) await page.close().catch(console.error);
        if (fs.existsSync(tempDir)) fs.rmSync(tempDir, { recursive: true, force: true });
    }
});

app.get('/health', (req, res) => {
    res.json({ status: 'ok', puppeteer: !!browser });
});

const server = app.listen(PORT, () => {
    console.log(`Render service listening on port ${PORT}`);
    getBrowser().catch(console.error);
});
server.setTimeout(30000);
