import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const rootDir = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const outputPath = resolve(rootDir, 'src', 'types', 'api.generated.ts')
const schemaUrl = 'http://localhost:8000/openapi.json'

execSync(`npx openapi-typescript ${schemaUrl} -o ${outputPath}`, { stdio: 'inherit' })
