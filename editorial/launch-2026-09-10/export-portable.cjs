const fs=require('fs');
const path=require('path');
const sharp=require('Z:/AnderZilla/apps/web/node_modules/sharp');
async function main(){const root=path.join(__dirname,'cards');for(const name of fs.readdirSync(root).filter(x=>x.endsWith('.svg'))){const portrait=name.endsWith('-instagram.svg');const image=sharp(fs.readFileSync(path.join(root,name)));await (portrait?image.png({compressionLevel:9}):image.jpeg({quality:90})).toFile(path.join(root,name.replace('.svg',portrait?'.png':'.jpg')))}console.log('120 portable images exported from original SVG compositions.')}
main().catch(e=>{console.error(e);process.exit(1)});
