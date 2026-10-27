// share links live in CT 104's dash-share (addons/dev/share/share.mjs); its control port only listens on localhost
export const shareCtl = <T = any>(path: string, body?: any) =>
  $fetch<T>(`http://127.0.0.1:3101${path}`, body ? { method: 'POST', body } : {}).catch((e: any) => {
    throw createError({ statusCode: e?.statusCode === 400 ? 400 : 502, statusMessage: e?.data?.error || 'dash-share is not running in the dashboard CT' })
  })
