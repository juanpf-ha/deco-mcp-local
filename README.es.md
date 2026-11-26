# deco-mcp-local

MCP de **solo lectura** para TP-Link Deco, ejecutado en tu servidor Linux con
Docker y accesible por SSH/stdio. No abre un puerto MCP ni usa la nube de TP-Link.

Es experimental: ninguna compatibilidad con modelos físicos se da por confirmada
sin una prueba real. La API del Deco no está documentada oficialmente.

## Privacidad

Por defecto no devuelve nombres y reemplaza MAC/IP por alias HMAC estables. Los
alias permiten relacionar dispositivos y nodos entre consultas. Es
**seudonimización**, no anonimato: modelos, firmware, topología, cantidades y
tráfico todavía revelan información. Los resultados llegan al cliente MCP y,
si usás un modelo en la nube, pueden enviarse a su proveedor.

Cuatro herramientas: `deco_status`, `deco_clients`, `deco_reservations` y
`deco_traffic`. No hay cambios, reinicios ni consultas arbitrarias. Las listas
usan `limit` y `offset`; dispositivos admite `online_only` booleano.

## Instalación

1. Leé [el modelo de seguridad](SECURITY.md) y descargá el código en el servidor.
2. Construí y probá los contenedores con los comandos del [README](README.md).
3. Obtené la huella SHA-256 del certificado con `--inspect-certificate` y
   **verificala por una vía confiable** antes de aceptarla.
4. Ejecutá `python3 scripts/enroll.py` en una terminal local del servidor, o por
   SSH con terminal. La contraseña se pide de forma oculta y queda en `secrets/`.
   Nunca la pegues en el chat ni la pases como argumento.
5. Ejecutá `chmod 755 scripts/run-mcp.sh` y luego
   `docker compose run --rm -T --no-deps deco-mcp --check`.
6. Adaptá localmente [la plantilla Codex](examples/codex-config.toml) con tu
   usuario, host y ruta. No publiques esa configuración personalizada.

El contenedor se inicia por cada sesión MCP; no uses `compose up -d`.
La primera ejecución de Compose crea su propia red bridge. No toca servicios
existentes, no necesita modo privilegiado y no monta el socket Docker.

La huella es obligatoria y se comprueba antes de enviar la contraseña. Si cambia,
se bloquea la conexión hasta que la vuelvas a verificar. Copiar una huella sin
verificar no demuestra que el dispositivo sea tu router.

`DECO_REVEAL_IDENTIFIERS=1` en el `.env` local permite mostrar nombres y direcciones
para diagnosticar; esos datos pueden llegar al modelo. Ninguna herramienta puede
activar ese modo. Conservá el valor predeterminado `0` salvo necesidad concreta.

## Publicación segura

El repositorio usa ejemplos ficticios, conserva la licencia MIT y la atribución
original. `.env` y `secrets/` están ignorados y no entran en la imagen Docker.
Revisá archivos e historial completo antes de publicar. No subas salidas reales,
capturas, credenciales, respaldos ni configuración SSH.

El bloqueo de destinos implementado en Python no reemplaza un firewall de salida
contra una dependencia maliciosa. Para aislamiento adicional usá una VM/VLAN y
reglas que permitan únicamente TCP 443 al router. No se cambia automáticamente
el firewall de un servidor que ya aloja otros servicios.

Ver [README completo](README.md), [SECURITY](SECURITY.md) y
[atribuciones](NOTICE.md) para límites, pruebas y mantenimiento.
