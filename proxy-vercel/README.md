# 🔒 Proxy IA (Vercel) — Proyecto INTI

Oculta tu API key de OpenRouter para que **no quede pública** en el sitio estático.
El navegador llama a este proxy; el proxy agrega la key (guardada como variable de
entorno en Vercel) y reenvía a OpenRouter.

## Desplegar (3 minutos)

1. Instala la CLI y entra a esta carpeta:
   ```bash
   npm i -g vercel
   cd proxy-vercel
   vercel        # sigue el asistente (crea el proyecto)
   ```
2. Agrega tu key de OpenRouter como variable de entorno:
   ```bash
   vercel env add OPENROUTER_API_KEY production
   # pega tu sk-or-v1-...
   vercel --prod
   ```
3. Copia la URL que te da Vercel (ej. `https://inti-proxy.vercel.app`) y ponla en
   el `config.js` del sitio:
   ```js
   window.INTI_IA = {
     apiKey: "",                                   // déjalo vacío
     model:  "meta-llama/llama-3.3-70b-instruct:free",
     proxy:  "https://inti-proxy.vercel.app/api/inti"   // ← tu URL del proxy
   };
   ```

Listo: la key vive solo en Vercel, nunca en el navegador. 🔒
