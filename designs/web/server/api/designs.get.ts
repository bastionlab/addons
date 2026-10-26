/** this person's designs, everyone's shared ones, the built-ins and which one is in use */
export default defineEventHandler(event => listDesigns(uidOf(event)))
