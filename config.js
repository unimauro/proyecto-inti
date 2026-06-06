// ============================================================
//  Proyecto INTI — Configuración del motor de IA (OpenRouter)
//  https://openrouter.ai/keys
//
//  ⚠️ IMPORTANTE: esto es un sitio ESTÁTICO (GitHub Pages). Si pones
//  aquí tu API key quedará VISIBLE públicamente. Recomendaciones:
//   • Usa una key con LÍMITE DE GASTO bajo en OpenRouter, o
//   • Usa un modelo :free, o
//   • Mejor: pon un proxy (Vercel) y apunta "endpoint" a él.
//
//  Si dejas la key vacía, el motor usa respuestas heurísticas locales.
// ============================================================
window.INTI_IA = {
  apiKey: "",                                   // sk-or-v1-... (OpenRouter)
  model:  "meta-llama/llama-3.3-70b-instruct:free",  // modelo OpenRouter
  endpoint: "https://openrouter.ai/api/v1/chat/completions"
};
