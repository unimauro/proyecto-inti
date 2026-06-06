// Proxy serverless (Vercel) para Proyecto INTI → OpenRouter
// Oculta la API key: el navegador llama a este endpoint y NUNCA ve la key.
// La key se guarda como variable de entorno OPENROUTER_API_KEY en Vercel.
export default async function handler(req, res) {
  // CORS (permite que GitHub Pages llame a este proxy)
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const key = process.env.OPENROUTER_API_KEY;
  if (!key) return res.status(500).json({ error: 'Falta OPENROUTER_API_KEY en el servidor' });

  try {
    const { model, messages } = req.body || {};
    const r = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: model || 'meta-llama/llama-3.3-70b-instruct:free',
        messages: messages || []
      })
    });
    const data = await r.json();
    return res.status(r.status).json(data);
  } catch (e) {
    return res.status(500).json({ error: String(e) });
  }
}
