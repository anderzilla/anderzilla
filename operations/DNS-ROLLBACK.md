# DNS antes da migração Azure

Leitura autenticada do painel Wix em 10/09/2026. Zona anderzilla.com.

- A raiz: 185.230.63.107, 185.230.63.186, 185.230.63.171; TTL 1 hora.
- CNAME www: cdn3.wixdns.net; TTL 1 hora.
- TXT raiz: SPF v=spf1 include:_spf.google.com ~all e verificação Google existente, preservados.
- MX raiz: aspmx.l.google.com prioridade10; alt1.aspmx.l.google.com20; alt2.aspmx.l.google.com30; alt3.aspmx.l.google.com40; alt4.aspmx.l.google.com50. Todos TTL1hora.
- NS: ns2.wixdns.net e ns3.wixdns.net; sem alteração de provedor.

Rollback web: restaurar os três A e o CNAME acima, mantendo os registros de correio. A propagação depende do cache DNS. O TXT de validação Azure pode permanecer sem alterar roteamento de tráfego.
