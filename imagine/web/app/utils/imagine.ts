/** small helpers for the Imagine page */
export const imagineRaw = (p: string) => `/api/files/raw?root=files&p=${encodeURIComponent(p)}`
/** the sidecar's size word -> width / height ratio for the tile before the picture has loaded */
export const imagineRatio = (size: string) => size === 'phone' ? '576 / 1248' : size === 'portrait' ? '832 / 1216' : size === 'landscape' ? '1216 / 832' : '1 / 1'
