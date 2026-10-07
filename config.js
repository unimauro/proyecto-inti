// ============================================================
//  Proyecto INTI — Configuración del motor de IA (OpenRouter)
//  https://openrouter.ai/keys
//
//  OPCIÓN A (segura, recomendada): usa un PROXY en Vercel para que la key
//  NO quede pública. Despliega proxy-vercel/ y pon su URL en "proxy".
//  Deja "apiKey" vacío.
//
//  OPCIÓN B (rápida, demo): pon tu "apiKey" aquí. ⚠️ Quedará VISIBLE
//  públicamente (sitio estático). Usa una key con límite bajo o un modelo :free.
//
//  Si dejas "apiKey" y "proxy" vacíos, el motor usa respuestas heurísticas locales.
// ============================================================
window.INTI_IA = {
  gateway: "https://ai.tunky.net/v1/chat",            // Gateway propio (Tunky). Política del proyecto "proyecto-inti" en el servidor.
  token:   "",                                         // X-Client-Token público del proyecto (inti_...). Vacío = modo memoria sin LLM.
  apiKey: "",                                          // Opción B: sk-or-v1-...
  proxy:  "",                                          // Opción A: https://tu-proxy.vercel.app/api/inti
  model:  "meta-llama/llama-3.3-70b-instruct:free",    // modelo OpenRouter
  endpoint: "https://openrouter.ai/api/v1/chat/completions"
};
