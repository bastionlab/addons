/** the Home card: how many fresh repos wait and the top few */
export default defineEventHandler(() => ({ top: topRepos(3), n: counts().new ?? 0, last: status().last }))
