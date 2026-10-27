/** upload an image for a design: { data: 'data:image/…;base64,…' } → { url } to use in the stylesheet */
export default defineEventHandler(async event => saveDesignImage(String((await readBody(event))?.data ?? '')))
