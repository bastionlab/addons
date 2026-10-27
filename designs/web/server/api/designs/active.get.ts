/** the look to paint for this person (null = stock), fetched by the app on every load; ?device= picks that device's own */
export default defineEventHandler(event => ({ look: activeLook(uidOf(event), okDevice(getQuery(event).device)) }))
