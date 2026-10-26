/** create (no id) or update one of your own designs: { id?, name, tokens, shared } */
export default defineEventHandler(async event => saveDesign(uidOf(event), await readBody(event)))
