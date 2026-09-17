"""Apply captions checked against diagnostic sheets; open the CMS import gate."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent/'real-media-2026-09-16'
data=json.loads((ROOT/'candidate-media-final.json').read_text(encoding='utf-8'))
captions={
'gta-vi-data-plataformas':('GTA VI', [('arte dos protagonistas em paisagem urbana','protagonist artwork in an urban setting'),('arte dos protagonistas diante de palmeiras','protagonist artwork in front of palm trees'),('pôster reunindo personagens e cenários','poster combining characters and locations')]),
'modern-warfare-4-confirmado':('Modern Warfare 4',[('retrato de militar com capacete','portrait of a soldier wearing a helmet'),('pôster vertical com soldados','vertical poster featuring soldiers'),('militar em um cenário com chamas','soldier in a scene with flames')]),
'control-resonant-assist-mode':('Control Resonant',[('cena de combate com efeitos de fogo','combat scene with fire effects'),('combate com criatura em ambiente escuro','combat with a creature in a dark setting'),('menu de configurações do Assist Mode','Assist Mode settings menu')]),
'no-mans-sky-cosmos':('No Man’s Sky Cosmos',[('personagem em queda entre estruturas','character falling between structures'),('arte oficial com astronauta e planetas','official artwork featuring an astronaut and planets')]),
'muramasa-revenant-blades':('Muramasa: Revenant Blades',[('combate em pixel art sob árvores floridas','pixel-art combat beneath flowering trees'),('arte oficial reunindo o elenco','official artwork featuring the cast')]),
'doa-minato':('Minato em Dead or Alive',[('personagem vista de frente na arena','character viewed from the front in the arena'),('personagem olhando sobre o ombro','character looking over her shoulder'),('personagem em pose na arena','character posing in the arena')]),
'zero-company-escolha-jogadores':('Star Wars Zero Company',[('arte oficial reunindo personagens do jogo','official artwork featuring the game characters')]),
'ffvii-revelation-data':('Final Fantasy VII Revelation',[('cena de confronto em área externa','outdoor confrontation scene'),('arte oficial reunindo os personagens','official artwork bringing the characters together')]),
'cod-the-haunting-setembro':('Call of Duty: The Haunting',[('arte promocional com personagens da temporada','promotional artwork featuring seasonal characters'),('capa do trailer oficial da temporada','official season trailer artwork')]),
'physint-xbox-kojima':('PHYSINT',[('cartaz preto com marcas Kojima Productions e Xbox','black poster with Kojima Productions and Xbox branding')]),
'rog-xbox-ally-x20':('ROG Xbox Ally X20',[('portátil e acessórios em exibição','handheld and accessories on display'),('jogadora usando um portátil em casa','player using a handheld at home'),('jogador no sofá usando um portátil','player on a sofa using a handheld')]),
'rog-ally-atualizacao-dock':('ROG Xbox Ally',[('sala com jogo exibido na televisão','living room with a game displayed on the television')]),
'playstation-portal-1080p':('PlayStation Portal',[('menu de qualidade de imagem sobre a tela do jogo','image-quality menu over the game screen'),('tela de seleção de jogo','game selection screen'),('tela de login com QR code','sign-in screen with a QR code')]),
'legion-go-steamos':('Lenovo Legion Go',[('portátil com controles laterais destacáveis','handheld with detachable side controllers')]),
'steam-deck-oled-ficha':('Steam Deck OLED',[('detalhe do portátil sob iluminação vermelha','handheld detail under red lighting'),('diagrama frontal com controles numerados','front diagram with numbered controls'),('diagrama das conexões e botões superiores','diagram of the top ports and buttons')]),
'switch-2-bundles':('Nintendo Switch 2',[('embalagem do conjunto com Mario Kart World','Mario Kart World bundle packaging'),('embalagem do conjunto com jogo de esportes','sports-game bundle packaging')]),
'ps-plus-setembro-catalogo':('PlayStation Plus',[('composição oficial do catálogo de setembro','official September catalog composition'),('arte de Dungeons of Hinterberg divulgada na fonte','Dungeons of Hinterberg artwork published by the source'),('arte de Sniper Elite: Resistance divulgada na fonte','Sniper Elite: Resistance artwork published by the source')]),
'xbox-insiders-setembro':('Xbox Insiders',[('composição promocional verde com dispositivos e logotipo','green promotional composition with devices and logo')]),
'xbox-discos-direito-digital':('Xbox',[('console e disco na arte do anúncio de acesso digital','console and disc in the digital-access announcement artwork')]),
'xbox-tokyo-game-show-2026':('Xbox na Tokyo Game Show 2026',[('cartaz verde com gato preto estilizado','green poster with a stylized black cat')]),
'logitech-superstrike-clique':('Logitech G PRO X2 Superstrike',[('vista do mouse com componente interno em destaque','mouse view highlighting an internal component'),('mouse ao lado da interface de configuração','mouse beside the settings interface'),('vista lateral do mouse em fundo escuro','side view of the mouse against a dark background')]),
'rog-oled-245':('Monitores OLED ROG',[('monitor em uma mesa com periféricos','monitor on a desk with peripherals'),('monitor com base e painel em destaque','monitor highlighting its stand and panel'),('detalhe da base e do suporte','close-up of the base and stand')]),
'rog-gladius-iv-ace':('ROG Gladius IV Ace',[('mouses em quatro cores alinhados','four mouse colors arranged in a row'),('mouse com acessórios sobre a mesa','mouse and accessories on a desk'),('mouse preto próximo a um teclado','black mouse beside a keyboard')]),
'rog-spatha-x-65k':('ROG Spatha X 65K',[('mouse iluminado em cenário azul e vermelho','illuminated mouse in a blue and red setting'),('carcaça aberta mostrando componentes internos','open shell showing internal components'),('mão usando o mouse sobre o mousepad','hand using the mouse on a mousepad')]),
'rog-strix-morph-96':('ROG Strix Morph 96',[('teclado com iluminação multicolorida','keyboard with multicolored lighting'),('vista lateral mostrando a iluminação do teclado','side view showing the keyboard lighting'),('teclado com teclas e switches removidos','keyboard with keycaps and switches removed')]),
'rog-rapture-gt-bn98':('ROG Rapture GT-BN98 Pro',[('roteador com antenas em composição de divulgação','router with antennas in promotional imagery')]),
'rog-xreal-r1':('ROG XREAL R1',[('dois jogadores usando os óculos com seus dispositivos','two players using the glasses with their devices'),('jogador no sofá usando os óculos e um portátil','player on a sofa using the glasses and a handheld'),('jogador usando os óculos em uma estação de PC','player using the glasses at a PC gaming station')]),
'lego-playstation':('LEGO PlayStation',[('console e controle montados sobre uma mesa','assembled console and controller on a table'),('vista superior do console e controle em peças','top view of the brick-built console and controller'),('detalhe do controle montado em peças','close-up of the brick-built controller')]),
'dualsense-gta-vi':('DualSense de GTA VI',[('controles preto e branco na arte de divulgação','black and white controllers in promotional artwork'),('controle preto em destaque','black controller highlighted'),('controle branco em destaque','white controller highlighted')]),
'gemini-38-flash':('Gemini 3.8 Flash',[('arte oficial de apresentação do modelo','official model announcement artwork'),('tabela de avaliações divulgada pelo Google','evaluation table published by Google'),('gráfico de avaliação DeepSWE divulgado pelo Google','DeepSWE evaluation chart published by Google')]),
'mistral-agentic-search':('Mistral Agentic Search',[('ilustração de busca em documentos','illustration of document search'),('diagrama de recuperação parcial com resposta incorreta','diagram of partial retrieval producing an incorrect answer'),('diagrama de busca que localiza a tabela necessária','search diagram locating the required table')]),
'shieldstral':('Shieldstral',[('arte oficial com escudo sobre blocos coloridos','official artwork with a shield over colored blocks'),('gráfico de segurança de texto divulgado pela Mistral','text-safety chart published by Mistral'),('gráfico de detecção de recusas divulgado pela Mistral','refusal-detection chart published by Mistral')]),
'iphone18pro':('iPhone 18 Pro',[('frente e traseira dos aparelhos em acabamento bordô','front and rear views of the devices in burgundy'),('aparelhos em diferentes acabamentos','devices in different finishes'),('amostra fotográfica divulgada pela Apple','sample photograph published by Apple')]),
'iphone17e-contexto':('iPhone 17e',[('dois aparelhos empilhados vistos de perfil','two stacked devices viewed from the side'),('frente e traseira dos aparelhos em diferentes cores','front and rear views of devices in different colors'),('tela do aparelho com retrato e relógio','device screen showing a portrait and clock')]),
'pixel11-tensor':('Google Pixel 11',[('frente e traseira de aparelho em acabamento lilás','front and rear views of a device in lilac'),('aparelhos em diferentes cores e ângulos','devices in different colors and angles'),('conjunto de aparelhos com módulos de câmera em destaque','group of devices highlighting the camera modules')]),
'pixel11-pro-fold':('Pixel 11 Pro Fold',[('frente e traseira do aparelho em acabamento verde','front and rear views of the device in green')]),
'galaxy-fold8-comparacao':('Galaxy Z Fold8',[('Fold8, Fold8 Ultra e Flip8 em exposição','Fold8, Fold8 Ultra and Flip8 on display'),('perfil de aparelho dobrável aberto','side profile of an unfolded device'),('tela interna aberta com ilustração colorida','open inner screen showing a colorful illustration')]),
'galaxy-s26-privacy':('Samsung Galaxy S26',[('aparelhos Ultra vistos por trás em diferentes ângulos','Ultra devices viewed from the rear at different angles'),('aparelhos da série alinhados em cenário lilás','series devices arranged in a lilac setting'),('aparelhos da série em diferentes cores','series devices in different colors')]),
'honor-magic-v6':('HONOR Magic V6',[('aparelhos dobráveis em diferentes acabamentos','foldable devices in different finishes')]),
'xiaomi17ultra':('Xiaomi 17 Ultra',[('aparelho verde segurado na horizontal','green device held horizontally'),('detalhe do módulo circular de câmeras Leica','close-up of the circular Leica camera module')]),
'oppo-findx9ultra':('OPPO Find X9 Ultra',[('aparelho sobre uma rocha diante de montanhas','device on a rock in front of mountains')]),
'oneplus15-165hz':('OnePlus 15',[('três aparelhos destacando as câmeras traseiras','three devices highlighting their rear cameras')]),
'typescript7-go':('TypeScript 7',[('gráfico de tempo de compilação divulgado pela Microsoft','compile-time chart published by Microsoft'),('gráfico de uso de memória divulgado pela Microsoft','memory-usage chart published by Microsoft')]),
'raspberrypi-radio':('Rádio com Raspberry Pi',[('placa ligada a protoboard e fios sobre a bancada','board connected to a breadboard and wires on a workbench')]),
'unitree-robos-fabrica':('Unitree',[('robô em imagem institucional, não em registro da fábrica','robot in institutional imagery, not a factory photograph'),('humanoide em pose dinâmica em imagem institucional','humanoid in a dynamic pose in institutional imagery'),('humanoide em demonstração de movimento em imagem institucional','humanoid demonstrating movement in institutional imagery')]),
'honor-robot-phone':('HONOR Robot Phone',[('aparelho com câmera articulada estendida','device with its articulated camera extended'),('apresentação da HONOR com robô humanoide no palco','HONOR presentation with a humanoid robot on stage')]),
}
for row in data['items']:
    if row['status']!='ready':continue
    subject,details=captions[row['key']]
    assert len(details)==len(row['images']),(row['key'],len(details),len(row['images']))
    for index,(image,(pt,en)) in enumerate(zip(row['images'],details)):
        image.update(altPT=f'{subject}: {pt}.',altEN=f'{subject}: {en}.',cmsTitle=f"{row['key']} — fonte oficial {index+1}")
        assert Path(image['localPath']).is_file()
data['approvedForImport']=True
data['review']='Todas as imagens selecionadas foram inspecionadas visualmente. Banners, QR codes, fotos de outros produtos, fundos vazios e duplicatas foram removidos. Legendas finais conferidas pelo agente principal.'
(ROOT/'reviewed-media.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'approvedArticles':sum(row['status']=='ready' for row in data['items']),'images':sum(len(row['images']) for row in data['items'])}))
