/** Approved artwork. Keep intrinsic aspect ratios; never recreate the wordmark as text. */
export function BrandWordmark({className = ""}:{className?:string}) {
 return <img className={`az-wordmark ${className}`} src="/brand/lettering.webp" alt="AnderZilla" width={960} height={320} decoding="async"/>;
}
export function BrandAvatar({size = 62}:{size?:number}) {
 return <img className="az-avatar" src={size < 48 ? "/brand/micro-caveira-marfim.svg" : "/brand/avatar.webp"} alt="AnderZilla" width={size} height={size} decoding="async"/>;
}
