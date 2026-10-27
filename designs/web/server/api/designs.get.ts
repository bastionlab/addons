/** this person's designs, everyone's shared ones, the built-ins and which one is in use (on this kind of device: ?device=) */
export default defineEventHandler(event => listDesigns(uidOf(event), okDevice(getQuery(event).device)))
