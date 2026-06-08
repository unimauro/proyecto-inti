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
  apiKey: "",                                          // Opción B: sk-or-v1-...
  proxy:  "",                                          // Opción A: https://tu-proxy.vercel.app/api/inti
  model:  "meta-llama/llama-3.3-70b-instruct:free",    // modelo OpenRouter
  endpoint: "https://openrouter.ai/api/v1/chat/completions"
};

// Turismo & economía local (Supabase) — la publishable key es pública y segura (RLS)
window.INTI_SUPABASE = {
  url:     "https://dmgvwksdlotqhfshlwzz.supabase.co",
  anonKey: "sb_publishable_sHyPPX3x0Zvguls_tSks4g_IWYhMriw"
};
